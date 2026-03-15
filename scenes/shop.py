"""ショップシーン（v2: ランク制品揃え・BGM/SE対応）"""
import pyxel

from data.items import ITEMS, get_available_items
from input_helper import btn_up, btn_down, btn_confirm, btn_cancel


class ShopScene:
    def __init__(self, game):
        self.game = game
        self.shop_id = ""
        self.shop_items = []
        self.cursor = 0
        self.mode = "menu"
        self.menu_index = 0
        self.message = ""
        self.message_timer = 0
        self.scroll_offset = 0

    def on_enter(self, **kwargs):
        self.shop_id = kwargs.get("shop_id", "my_shop")
        self._refresh_items()
        self.cursor = 0
        self.mode = "menu"
        self.menu_index = 0
        self.message = ""
        self.message_timer = 0
        self.game.play_bgm("shop")

        # 店主の挨拶
        greetings = {
            "my_shop": "いらっしゃい！\n何を仕入れていく？",
            "weapon_shop": "おう、来たか！\n良い資格があるぜ。",
            "armor_shop": "ようこそ。\nメンタルケア商品はいかがですか？",
        }
        greeting = greetings.get(self.shop_id)
        if greeting:
            self.game.message_window.show(greeting)

    def _refresh_items(self):
        """パートナーランクに応じた品揃えを取得"""
        rank = self.game.partner_system.rank
        item_ids = get_available_items(self.shop_id, rank, self.game.partner_system)
        self.shop_items = [
            {"id": iid, **ITEMS[iid]} for iid in item_ids if iid in ITEMS
        ]

    def _show_message(self, text, duration=60):
        self.message = text
        self.message_timer = duration

    def _get_contract_for_shop(self):
        """現在のショップに対応するパートナー契約を取得"""
        return self.game.partner_system.get_contract_for_shop(self.shop_id)

    def update(self):
        if self.game.message_window.active:
            self.game.message_window.update()
            return

        if self.message_timer > 0:
            self.message_timer -= 1
            if btn_confirm():
                self.message_timer = 0
            return

        if self.mode == "menu":
            if btn_up():
                self.menu_index = max(0, self.menu_index - 1)
                self.game.play_se("cursor")
            if btn_down():
                self.menu_index = min(2, self.menu_index + 1)
                self.game.play_se("cursor")

            if btn_confirm():
                self.game.play_se("confirm")
                if self.menu_index == 0:
                    self.mode = "buy"
                    self.cursor = 0
                elif self.menu_index == 1:
                    self.mode = "sell"
                    self.cursor = 0
                elif self.menu_index == 2:
                    self.game.change_scene_with_transition("field")

        elif self.mode == "buy":
            if btn_cancel():
                self.mode = "menu"
                return

            if btn_up():
                self.cursor = max(0, self.cursor - 1)
                self.game.play_se("cursor")
            if btn_down():
                self.cursor = min(len(self.shop_items) - 1, self.cursor + 1)
                self.game.play_se("cursor")

            if btn_confirm():
                if self.cursor < len(self.shop_items):
                    item = self.shop_items[self.cursor]
                    actual_price = item["price"]

                    # 紹介代理店のパートナー商品は仕入れ不要（無料で紹介チケット取得）
                    is_partner_item = item.get("shop") == "partner_shop"
                    if is_partner_item:
                        contract = self.game.partner_system.get_contract_for_shop(self.shop_id)
                        if contract and contract.contract_type == "referral":
                            actual_price = 0

                    if self.game.player.gold >= actual_price:
                        self.game.player.gold -= actual_price
                        self.game.inventory.add_item(item["id"])

                        # リセラー契約なら在庫にも追加
                        contract = self._get_contract_for_shop()
                        if contract and contract.contract_type == "reseller":
                            if item.get("type") in ("weapon", "armor", "shield"):
                                self.game.partner_system.add_partner_inventory(
                                    item["id"], 1
                                )
                        self.game.play_se("trade")
                        # 装備品を購入した場合、自動装備
                        if item.get("type") in ("weapon", "armor", "shield"):
                            self.game.inventory.equip(item["id"])
                            self._show_message(f"{item['name']}を\n仕入れて装備した！")
                        elif is_partner_item and actual_price == 0:
                            self._show_message(f"{item['name']}の\n紹介チケットを入手!")
                        else:
                            self._show_message(f"{item['name']}を\n仕入れた！")
                    else:
                        self.game.play_se("miss")
                        self._show_message("お金が足りない！")

        elif self.mode == "sell":
            if btn_cancel():
                self.mode = "menu"
                return

            player_items = self.game.inventory.get_all_items()
            if not player_items:
                self._show_message("売れるものがない！")
                self.mode = "menu"
                return

            if btn_up():
                self.cursor = max(0, self.cursor - 1)
                self.game.play_se("cursor")
            if btn_down():
                self.cursor = min(len(player_items) - 1, self.cursor + 1)
                self.game.play_se("cursor")

            if btn_confirm():
                if self.cursor < len(player_items):
                    item_info = player_items[self.cursor]
                    item = ITEMS.get(item_info["id"])
                    if item and self.game.inventory.remove_item(item_info["id"]):
                        sell_price = item["sell_price"]

                        # パートナーフィー
                        contract = self._get_contract_for_shop()
                        fee = 0
                        rank_up = False
                        if contract and item.get("type") in ("weapon", "armor", "shield"):
                            fee, rank_up = self.game.partner_system.sell_partner_item(
                                item_info["id"], sell_price
                            )

                        total = sell_price + fee
                        self.game.player.gold += total
                        self.game.play_se("trade")
                        msg = f"{item['name']}を\n{sell_price}Gで売った！"
                        if fee > 0:
                            msg += f"\nパートナーフィー+{fee}G!"
                        if rank_up:
                            ps = self.game.partner_system
                            msg += f"\nランク{ps.rank}({ps.rank_label})に昇格!"
                        self._show_message(msg)
                        # カーソルが範囲外にならないように調整
                        remaining = self.game.inventory.get_all_items()
                        if self.cursor >= len(remaining):
                            self.cursor = max(0, len(remaining) - 1)
                        if not remaining:
                            self.mode = "menu"

    def draw(self):
        t = self.game.text
        pyxel.cls(1)

        # === 全体レイアウト (12pxフォント, 行間14-16px) ===
        # y=4:   ショップ名 + 所持金
        # y=22:  サブタイトル
        # y=38~: アイテムリスト (16px間隔)
        # y=182: 説明文
        # y=198: メッセージ
        # y=218: パートナー情報
        # y=228: 操作ガイド/ランク

        # ショップ名
        shop_names = {
            "my_shop": "道具屋(自分の店)",
            "weapon_shop": "武器屋",
            "armor_shop": "防具屋",
        }
        name = shop_names.get(self.shop_id, "ショップ")
        t(8, 4, f"【{name}】", 10)
        t(168, 4, f"所持金:{self.game.player.gold}G", 7)

        if self.mode == "menu":
            pyxel.rect(88, 60, 80, 62, 1)
            pyxel.rectb(88, 60, 80, 62, 7)
            options = ["仕入れる", "売る", "やめる"]
            for i, opt in enumerate(options):
                color = 10 if i == self.menu_index else 7
                prefix = "> " if i == self.menu_index else "  "
                t(96, 66 + i * 18, prefix + opt, color)

        elif self.mode == "buy":
            t(8, 22, "何を仕入れる？ (Bで戻る)", 6)

            max_visible = 7
            self.scroll_offset = max(0, min(self.cursor - max_visible + 1, len(self.shop_items) - max_visible))
            visible_items = self.shop_items[self.scroll_offset:self.scroll_offset + max_visible]
            for i, item in enumerate(visible_items):
                actual_idx = i + self.scroll_offset
                y = 38 + i * 16
                color = 10 if actual_idx == self.cursor else 7
                prefix = "> " if actual_idx == self.cursor else "  "
                is_partner = item.get("shop") == "partner_shop"
                if is_partner:
                    label = "(P)"
                elif item.get("type") == "merchandise":
                    label = "(商)"
                else:
                    label = ""
                # 商品名を最大12文字に制限
                iname = item['name']
                if len(iname) > 12:
                    iname = iname[:11] + ".."
                t(8, y, f"{prefix}{iname}{label}", color)
                # 価格を右端に固定 (x=200)
                display_price = item["price"]
                if is_partner:
                    contract = self.game.partner_system.get_contract_for_shop(self.shop_id)
                    if contract and contract.contract_type == "referral":
                        display_price = 0
                t(200, y, f"{display_price}G", color)

            # 選択中アイテムの詳細表示
            if 0 <= self.cursor < len(self.shop_items):
                sel_item = self.shop_items[self.cursor]
                desc = sel_item.get("description", "")
                # 説明文を最大19文字に制限
                if len(desc) > 19:
                    desc = desc[:19]
                t(8, 182, desc, 6)
                # 装備比較表示
                inv = self.game.inventory
                if sel_item["type"] == "weapon":
                    current = inv.equipped_weapon
                    current_val = ITEMS[current]["value"] if current and current in ITEMS else 0
                    new_val = sel_item["value"]
                    diff = new_val - current_val
                    diff_text = f"+{diff}" if diff > 0 else str(diff)
                    color = 10 if diff > 0 else 8
                    t(8, 196, f"セ力: {current_val}→{new_val}({diff_text})", color)
                elif sel_item["type"] in ("armor", "shield"):
                    current = inv.equipped_armor if sel_item["type"] == "armor" else inv.equipped_shield
                    current_val = ITEMS[current]["value"] if current and current in ITEMS else 0
                    new_val = sel_item["value"]
                    diff = new_val - current_val
                    diff_text = f"+{diff}" if diff > 0 else str(diff)
                    color = 10 if diff > 0 else 8
                    t(8, 196, f"メンタル: {current_val}→{new_val}({diff_text})", color)

            # スクロールインジケータ
            if self.scroll_offset > 0:
                t(240, 36, "▲", 6)
            if self.scroll_offset + max_visible < len(self.shop_items):
                t(240, 38 + max_visible * 16 - 12, "▼", 6)

        elif self.mode == "sell":
            t(8, 22, "何を売る？ (Bで戻る)", 6)

            player_items = self.game.inventory.get_all_items()
            max_visible = 7
            sell_offset = max(0, min(self.cursor - max_visible + 1, len(player_items) - max_visible))
            visible_sell = player_items[sell_offset:sell_offset + max_visible]
            for i, item_info in enumerate(visible_sell):
                actual_idx = i + sell_offset
                y = 38 + i * 16
                color = 10 if actual_idx == self.cursor else 7
                prefix = "> " if actual_idx == self.cursor else "  "
                item = ITEMS.get(item_info["id"], {})
                sell_price = item.get("sell_price", 0)
                # 名前を最大12文字に制限
                iname = item_info['name']
                if len(iname) > 12:
                    iname = iname[:11] + ".."
                t(8, y, f"{prefix}{iname} x{item_info['quantity']}", color)
                t(200, y, f"{sell_price}G", color)

            # スクロールインジケータ
            if sell_offset > 0:
                t(240, 36, "▲", 6)
            if sell_offset + max_visible < len(player_items):
                t(240, 38 + max_visible * 16 - 12, "▼", 6)

        # メッセージ表示
        if self.message_timer > 0:
            pyxel.rect(16, 110, 224, 50, 1)
            pyxel.rectb(16, 110, 224, 50, 7)
            lines = self.message.split("\n")
            for i, line in enumerate(lines[:3]):
                # 最大18文字に制限
                if len(line) > 18:
                    line = line[:18]
                t(24, 116 + i * 14, line, 7)

        # パートナー情報
        contract = self._get_contract_for_shop()
        if contract:
            ptype = "紹介" if contract.contract_type == "referral" else "販売"
            ps = self.game.partner_system
            t(8, 218, f"契約:{ptype} フィー:{int(contract.fee_rate*100)}%", 10)
            t(8, 232, f"ランク:{ps.rank}({ps.rank_label}) 次:{ps.sales_to_next_rank}G", 10)
