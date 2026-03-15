"""メニュー画面（ステータス・装備・パートナー情報）"""
import pyxel

from data.items import ITEMS
from systems.economy import exp_for_level
from input_helper import btn_up, btn_down, btn_confirm, btn_cancel


class MenuScene:
    def __init__(self, game):
        self.game = game
        self.tab = 0  # 0=ステータス, 1=装備, 2=スキル, 3=パートナー
        self.equip_cursor = 0
        self.equip_mode = False
        self.equip_slot = None  # "weapon", "armor", "shield"
        self.equip_candidates = []
        self.equip_select = 0
        self.return_scene = "field"

    def on_enter(self, **kwargs):
        self.tab = 0
        self.equip_mode = False
        self.return_scene = kwargs.get("return_scene", "field")

    def update(self):
        if self.equip_mode:
            self._update_equip_select()
            return

        if btn_cancel():
            self.game.play_se("confirm")
            self.game.change_scene(self.return_scene)
            return

        # タブ切替
        if btn_left_tab():
            self.tab = max(0, self.tab - 1)
            self.game.play_se("cursor")
        elif btn_right_tab():
            self.tab = min(3, self.tab + 1)
            self.game.play_se("cursor")

        if self.tab == 1:
            # 装備タブ — UP/DOWNでスロット選択
            if btn_up():
                self.equip_cursor = max(0, self.equip_cursor - 1)
                self.game.play_se("cursor")
            if btn_down():
                self.equip_cursor = min(2, self.equip_cursor + 1)
                self.game.play_se("cursor")
            if btn_confirm():
                self._open_equip_select()

    def _open_equip_select(self):
        slots = ["weapon", "armor", "shield"]
        self.equip_slot = slots[self.equip_cursor]
        inv = self.game.inventory
        self.equip_candidates = []
        for item_id, qty in inv.items.items():
            item = ITEMS.get(item_id)
            if item and item["type"] == self.equip_slot:
                self.equip_candidates.append(item_id)
        # 「はずす」オプションを先頭に追加
        self.equip_candidates.insert(0, None)  # None = はずす
        self.equip_mode = True
        self.equip_select = 0
        self.game.play_se("confirm")

    def _update_equip_select(self):
        if btn_cancel():
            self.equip_mode = False
            return
        if btn_up():
            self.equip_select = max(0, self.equip_select - 1)
            self.game.play_se("cursor")
        if btn_down():
            self.equip_select = min(
                len(self.equip_candidates) - 1, self.equip_select
            )
            self.game.play_se("cursor")
        if btn_confirm():
            item_id = self.equip_candidates[self.equip_select]
            if item_id is None:
                # はずす
                inv = self.game.inventory
                if self.equip_slot == "weapon":
                    inv.equipped_weapon = None
                elif self.equip_slot == "armor":
                    inv.equipped_armor = None
                elif self.equip_slot == "shield":
                    inv.equipped_shield = None
            else:
                self.game.inventory.equip(item_id)
            self.game.play_se("confirm")
            self.equip_mode = False

    def draw(self):
        t = self.game.text
        pyxel.cls(1)

        # === タブ (y=4-20) ===
        tabs = ["ステータス", "装備", "スキル", "パートナー"]
        for i, name in enumerate(tabs):
            x = 4 + i * 62
            col = 10 if i == self.tab else 5
            pyxel.rect(x, 4, 60, 18, 1 if i != self.tab else 0)
            pyxel.rectb(x, 4, 60, 18, col)
            t(x + 6, 8, name, col)

        # 区切り線 (y=24)
        pyxel.line(0, 24, 256, 24, 5)

        if self.tab == 0:
            self._draw_status()
        elif self.tab == 1:
            self._draw_equip()
        elif self.tab == 2:
            self._draw_skills()
        elif self.tab == 3:
            self._draw_partner()

        # 操作ガイド (y=228)
        t(8, 228, "←→:タブ切替  B:閉じる", 5)

    def _draw_status(self):
        t = self.game.text
        p = self.game.player
        inv = self.game.inventory

        # y=30から14px間隔で配置
        t(16, 30, f"名前: {p.name}", 7)
        t(16, 44, f"レベル: {p.level}", 7)

        # EXPバー
        next_exp = exp_for_level(p.level + 1)
        current_exp = p.total_exp
        if next_exp > 0:
            prev_exp = exp_for_level(p.level)
            progress = current_exp - prev_exp
            needed = next_exp - prev_exp
            ratio = min(1.0, progress / needed) if needed > 0 else 1.0
        else:
            ratio = 1.0
        t(16, 58, f"経験値: {current_exp}/{next_exp}", 7)
        pyxel.rect(16, 72, 200, 6, 5)
        pyxel.rect(16, 72, int(200 * ratio), 6, 11)

        t(16, 82, f"やる気: {p.hp}/{p.max_hp}", 7)
        hp_ratio = p.hp / p.max_hp if p.max_hp > 0 else 0
        pyxel.rect(16, 96, 200, 6, 5)
        pyxel.rect(16, 96, int(200 * hp_ratio), 6, 8)

        total_atk = p.attack + inv.get_attack_bonus()
        total_def = p.defense + inv.get_defense_bonus()
        t(16, 106, f"セールス力: {total_atk} ({p.attack}+{inv.get_attack_bonus()})", 7)
        t(16, 120, f"メンタル: {total_def} ({p.defense}+{inv.get_defense_bonus()})", 7)
        t(16, 134, f"対応力: {p.speed}", 7)
        t(16, 152, f"所持金: {p.gold}G", 10)

    def _draw_equip(self):
        t = self.game.text
        inv = self.game.inventory

        slots = [
            ("資格", inv.equipped_weapon),
            ("研修", inv.equipped_armor),
            ("ケア", inv.equipped_shield),
        ]
        for i, (label, equipped_id) in enumerate(slots):
            y = 32 + i * 28
            color = 10 if i == self.equip_cursor else 7
            prefix = "> " if i == self.equip_cursor else "  "
            name = "---なし---"
            bonus = ""
            if equipped_id and equipped_id in ITEMS:
                item = ITEMS[equipped_id]
                name = item["name"]
                # 説明を最大12文字に
                desc = item['description']
                if len(desc) > 12:
                    desc = desc[:12]
                bonus = f" ({desc})"
            t(16, y, f"{prefix}{label}: {name}{bonus}", color)

        t(16, 120, "Aボタンで装備変更", 5)

        # 装備選択ウィンドウ
        if self.equip_mode:
            pyxel.rect(36, 60, 184, 100, 1)
            pyxel.rectb(36, 60, 184, 100, 7)
            slot_names = {"weapon": "資格", "armor": "研修", "shield": "ケア"}
            t(44, 66, f"{slot_names.get(self.equip_slot, '')}を選ぶ", 7)
            for i, item_id in enumerate(self.equip_candidates):
                y = 82 + i * 16
                if y > 150:
                    break
                color = 10 if i == self.equip_select else 7
                prefix = "> " if i == self.equip_select else "  "
                if item_id is None:
                    t(44, y, f"{prefix}---はずす---", color)
                else:
                    item = ITEMS[item_id]
                    desc = item['description']
                    if len(desc) > 10:
                        desc = desc[:10]
                    t(44, y, f"{prefix}{item['name']} ({desc})", color)

    def _draw_skills(self):
        t = self.game.text
        level = self.game.player.level

        t(16, 30, f"習得スキル (Lv.{level})", 10)

        from scenes.battle import SALES_SKILLS

        y = 48
        for skill in SALES_SKILLS:
            if skill["level"] <= level:
                cost_text = f" [{skill['cost']}]" if skill["cost"] > 0 else ""
                t(16, y, f"Lv{skill['level']}: {skill['name']}{cost_text}", 7)
                t(24, y + 14, skill["description"], 5)
                y += 30
            else:
                t(16, y, f"Lv{skill['level']}: ？？？", 5)
                y += 30
            if y > 214:
                break

    @property
    def partner_system(self):
        return self.game.partner_system

    def _draw_partner(self):
        t = self.game.text
        ps = self.partner_system

        if not ps.has_contract:
            t(16, 60, "パートナー契約はまだありません", 5)
            return

        t(16, 30, f"パートナーランク: {ps.rank} ({ps.rank_label})", 10)

        # ランクバー
        nr = ps.next_rank
        if nr:
            from systems.partner import PARTNER_RANKS
            current_min = PARTNER_RANKS[ps.rank]["min_sales"]
            next_min = PARTNER_RANKS[nr]["min_sales"]
            progress = ps.cumulative_sales - current_min
            needed = next_min - current_min
            ratio = min(1.0, progress / needed) if needed > 0 else 1.0
            t(16, 44, f"累計売上:{ps.cumulative_sales}G/次{nr}:{next_min}G", 7)
            pyxel.rect(16, 58, 200, 6, 5)
            pyxel.rect(16, 58, int(200 * ratio), 6, 11)
        else:
            t(16, 44, f"累計売上:{ps.cumulative_sales}G(最高ランク)", 10)

        # 契約一覧
        t(16, 72, "--- 契約一覧 ---", 6)
        for i, contract in enumerate(ps.active_contracts):
            y = 88 + i * 28
            ptype = "紹介" if contract.contract_type == "referral" else "販売"
            t(16, y, f"{contract.partner_name} ({ptype})", 7)
            t(24, y + 14, f"フィー:{int(contract.fee_rate*100)}% 売上:{contract.total_sales}G", 5)


def btn_left_tab():
    return pyxel.btnp(pyxel.KEY_LEFT) or pyxel.btnp(pyxel.GAMEPAD1_BUTTON_DPAD_LEFT)

def btn_right_tab():
    return pyxel.btnp(pyxel.KEY_RIGHT) or pyxel.btnp(pyxel.GAMEPAD1_BUTTON_DPAD_RIGHT)
