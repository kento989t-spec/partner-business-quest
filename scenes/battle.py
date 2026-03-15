"""販売バトルシーン（v3: 販売メタファー全面刷新）"""
import pyxel
import random

from data.customers import CUSTOMERS, CUSTOMER_REACTIONS, ACHIEVEMENTS
from data.items import ITEMS
from systems.economy import calc_damage, calc_action_order, check_level_up, get_level_up_stats
from input_helper import btn_up, btn_down, btn_confirm, btn_cancel

BUSINESS_TIPS = [
    "Tip: パートナービジネスは信頼が資本",
    "Tip: 値引きは最後の手段。価値を伝えよう",
    "Tip: 紹介は最も低コストな集客方法",
    "Tip: Win-Winの関係が長期的な成功の鍵",
    "Tip: 顧客の声をよく聞くことが成約への近道",
    "Tip: クロスセルで顧客単価を上げよう",
    "Tip: 失敗は学び。次に活かせばOK",
    "Tip: 在庫リスクとリターンのバランスが大事",
    "Tip: ランクが上がると仕入れの幅が広がる",
    "Tip: 連続成約でコンボボーナスを狙おう",
]

# 顧客スプライト位置（16x16）
CUSTOMER_SPRITES = {
    "traveler": (32, 0),
    "housewife": (48, 0),
    "cautious_merchant": (64, 0),
    "adventurer_party": (80, 0),
    "noble": (0, 32),
    "boss_merchant": (16, 32),
    "student": (48, 32),
    "regular_customer": (64, 32),
    "complainer": (80, 32),
    "big_client": (96, 32),
    "buyer": (112, 32),
    "vip_customer": (128, 32),
}

SALES_SKILLS = [
    {"id": "discount", "name": "値引き提案", "cost": 0, "level": 1, "description": "説得力1.8倍 利益半減"},
    {"id": "explain", "name": "商品説明", "cost": 0, "level": 1, "description": "警戒心↓ やる気+5 (1回)"},
    {"id": "smile", "name": "笑顔で対応", "cost": 0, "level": 1, "description": "やる気+12回復"},
    {"id": "market_analysis", "name": "市場分析", "cost": 8, "level": 3, "description": "警戒心50%↓"},
    {"id": "presentation", "name": "プレゼン", "cost": 10, "level": 1, "description": "説得力1.8倍 やる気-10"},
    {"id": "closing", "name": "クロージング", "cost": 12, "level": 5, "description": "購買意欲+15"},
    {"id": "limited_offer", "name": "限定オファー", "cost": 15, "level": 7, "description": "次の攻撃力3倍"},
    {"id": "ultimate_pitch", "name": "究極プレゼン", "cost": 25, "level": 9, "description": "説得力3倍 やる気-25"},
]


class BattleScene:
    def __init__(self, game):
        self.game = game
        self.customer = None
        self.customer_id = "traveler"
        self.purchase_gauge = 0       # 購買意欲（0→閾値で成約）
        self.purchase_threshold = 0   # 閾値
        self.menu_index = 0
        self.phase = "menu"
        self.log = []
        self.result_timer = 0
        self.item_select_index = 0
        self.customer_attack_bonus = 0   # やる気ダメージ追加
        self.customer_defense_bonus = 0  # 警戒心追加
        self.player_attack_debuff = 0    # セールス力デバフ
        self.bulk_buy_active = False     # まとめ買い報酬2倍
        self.explained = False           # 商品説明済みフラグ
        self.skill_select_index = 0
        self.skill_scroll_offset = 0
        self.next_attack_multiplier = 1.0
        self.result_gold = 0   # 成約時の最終利益（表示用）
        self.result_exp = 0    # 成約時の獲得EXP（表示用）
        self.damage_flash = 0  # 被ダメージ時の点滅タイマー
        self.smile_cooldown = 0  # 笑顔クールダウン
        self.customer_charging = False  # 顧客チャージ状態
        self.last_critical = False       # 直前の攻撃が会心だったか
        self.turn_count = 0              # ターンカウント
        self.selected_product = None     # 選択した商材
        self.product_select_index = 0    # 商品選択カーソル
        self.cross_sell_bonus = False    # クロスセルボーナスフラグ

    def on_enter(self, **kwargs):
        self.customer_id = kwargs.get("enemy_id", "traveler")
        self.customer = CUSTOMERS[self.customer_id].copy()
        self.purchase_gauge = 0
        self.purchase_threshold = self.customer["hp"]
        self.menu_index = 0
        self.phase = "menu"
        # エンカウントメッセージ（顧客タイプ別）
        encounter_msgs = {
            "traveler": [f"{self.customer['name']}が\n通りかかった！"],
            "housewife": [f"{self.customer['name']}が\n買い物にやってきた！"],
            "cautious_merchant": [f"{self.customer['name']}が\nじっくりと品定めしている..."],
            "adventurer_party": [f"{self.customer['name']}が\nにぎやかにやってきた！"],
            "noble": [f"{self.customer['name']}が\nゆったりと入店した。"],
            "boss_merchant": [f"{self.customer['name']}が\n立ちはだかった！"],
            "student": [f"{self.customer['name']}が\n興味津々でやってきた！"],
            "regular_customer": [f"{self.customer['name']}が\nまた来てくれた！"],
            "complainer": [f"{self.customer['name']}が\n厳しい目つきでやってきた..."],
            "big_client": [f"{self.customer['name']}が\n堂々と入店した！"],
            "buyer": [f"{self.customer['name']}が\nチェックリスト片手にやってきた！"],
            "vip_customer": [f"★ {self.customer['name']}が", "特別にやってきた！ ★"],
        }
        # \nを含むメッセージは行ごとに分割してログに入れる
        msgs = encounter_msgs.get(self.customer_id, [f"{self.customer['name']}が やってきた！"])
        self.log = []
        for msg in msgs:
            for line in msg.split("\n"):
                if line:
                    self.log.append(line)
        # VIP出現時に特別なSE
        if self.customer_id == "vip_customer":
            self.game.play_se("level_up")
        self.result_timer = 0
        self.customer_attack_bonus = 0
        self.customer_defense_bonus = 0
        self.player_attack_debuff = 0
        self.bulk_buy_active = False
        self.explained = False
        self.skill_select_index = 0
        self.skill_scroll_offset = 0
        self.next_attack_multiplier = 1.0
        self.result_gold = 0
        self.result_exp = 0
        self.damage_flash = 0
        self.smile_cooldown = 0
        self.customer_charging = False
        self.last_critical = False
        self.turn_count = 0
        self.selected_product = None
        self.product_select_index = 0
        self.cross_sell_bonus = False
        self.game.play_bgm("battle" if self.customer_id != "boss_merchant" else "boss", force=True)
        # パートナー契約後の初バトルメッセージ
        if self.game.partner_system.has_contract:
            contract = self.game.partner_system.active_contract
            if contract:
                ptype = "紹介" if contract.contract_type == "referral" else "販売"
                if not hasattr(self.game, '_partner_battle_shown'):
                    self.game._partner_battle_shown = True
                    self.log.append(f"({ptype}パートナーの力が加わった！)")
        self.phase = "encounter"
        self.result_timer = 45  # 1.5秒間メッセージ表示

    def _get_merchandise(self):
        """在庫の商材一覧を取得（クロスセルオプション含む）"""
        items = self.game.inventory.get_all_items()
        merchandise = [i for i in items if ITEMS.get(i["id"], {}).get("type") == "merchandise"]

        # クロスセルオプションを生成
        my_products = [m for m in merchandise if ITEMS.get(m["id"], {}).get("shop") == "my_shop"]
        partner_products = [m for m in merchandise if ITEMS.get(m["id"], {}).get("shop") == "partner_shop"]

        cross_sell_options = []
        if my_products and partner_products:
            # 最も利益の高い組み合わせを1つ提案
            best_my = max(my_products, key=lambda m: ITEMS[m["id"]].get("sell_value", 0) - ITEMS[m["id"]].get("price", 0))
            best_partner = max(partner_products, key=lambda m: ITEMS[m["id"]].get("sell_value", 0) - ITEMS[m["id"]].get("price", 0))
            cross_sell_options.append({
                "id": "__cross_sell__",
                "name": f"セット: {ITEMS[best_my['id']]['name']}+{ITEMS[best_partner['id']]['name']}",
                "my_product": best_my,
                "partner_product": best_partner,
                "quantity": 1,
            })

        return merchandise + cross_sell_options

    def _apply_product_bonus(self):
        """商品とターゲットの相性を適用"""
        if not self.selected_product:
            return

        # クロスセルの場合
        if self.selected_product.get("id") == "__cross_sell__":
            self.cross_sell_bonus = True
            my_item = ITEMS.get(self.selected_product["my_product"]["id"])
            partner_item = ITEMS.get(self.selected_product["partner_product"]["id"])
            if my_item and partner_item:
                # 難易度は高い方を適用（ただし少し緩和）
                difficulty = max(my_item.get("difficulty", 0), partner_item.get("difficulty", 0))
                self.customer_defense_bonus += max(0, difficulty - 1)
                # クロスセルボーナス: 警戒心ダウン
                self.customer["defense"] = max(1, self.customer["defense"] - 5)
                self.log.append("★ クロスセル提案！ ★")
                self.log.append("セット販売で顧客の安心感UP！ 警戒心ダウン！")
            return

        item = ITEMS.get(self.selected_product["id"])
        if not item:
            return
        customer_target = self.customer.get("target", "general")
        product_target = item.get("target", "general")

        # 難易度補正を顧客のdefenseに加算
        self.customer_defense_bonus += item.get("difficulty", 0)

        # ターゲット相性
        if product_target == customer_target:
            self.log.append("★ 商品がニーズにマッチ！ 警戒心ダウン！")
            self.customer["defense"] = max(1, self.customer["defense"] - 3)
        elif product_target == "enterprise" and customer_target == "general":
            self.log.append("高額商品にたじろいでいる...")
            self.customer_defense_bonus += 5
        elif product_target == "general" and customer_target == "enterprise":
            self.log.append("物足りなさそうだ...")

    def _get_player_attack(self):
        base = self.game.player.attack + self.game.inventory.get_attack_bonus()
        return max(1, base - self.player_attack_debuff)

    def _get_player_defense(self):
        return self.game.player.defense + self.game.inventory.get_defense_bonus()

    def _check_weakness(self, skill_id):
        """弱点チェック — 弱点スキルなら1.5倍ボーナスを返す"""
        weakness = self.customer.get("weakness")
        if weakness == skill_id:
            self.log.append("★ 効果抜群！ ★")
            self.game.play_se("heal")
            return 1.5
        return 1.0

    def _sales_talk(self):
        """セールストーク — メインの説得行動"""
        p = self.game.player
        # セールストークのやる気消費（小）
        p.hp -= 2
        if p.hp <= 0:
            p.hp = 0
            self._on_sale_lost()
            return
        attack = self._get_player_attack()
        defense = self.customer["defense"] + self.customer_defense_bonus
        persuasion = calc_damage(attack, defense)
        # バフ適用
        if self.next_attack_multiplier > 1.0:
            persuasion = int(persuasion * self.next_attack_multiplier)
            self.log.append("限定オファーの効果！")
            self.next_attack_multiplier = 1.0
        # 会心の一撃判定（10%）
        self.last_critical = False
        if random.random() < 0.10:
            persuasion *= 2
            self.last_critical = True
            self.game.play_se("level_up")
            self.game.screen_shake(4, 12)
            self.log.append(f"★ 会心のセールストーク！ ★")
        self.purchase_gauge += persuasion
        self.game.play_se("attack")
        self.log.append(f"{p.name}のセールストーク！ 説得力{persuasion}！")

        if self.purchase_gauge >= self.purchase_threshold:
            self.purchase_gauge = self.purchase_threshold
            self._on_sale_closed()
        else:
            self.phase = "customer_turn"
            self.result_timer = 30

    def _discount(self):
        """値引き — 利益減だが大幅説得＋警戒心20%ダウン"""
        p = self.game.player
        attack = self._get_player_attack()
        # 値引きは1.8倍の説得力だが、報酬が半減
        persuasion = int(attack * 1.8)
        # 弱点ボーナス
        bonus = self._check_weakness("discount")
        if bonus > 1.0:
            persuasion = int(persuasion * bonus)
        self.purchase_gauge += persuasion
        self.game.play_se("attack")
        self.log.append(f"{p.name}は 値引きを提案！ 説得力{persuasion}！")
        self.log.append("（成約時の利益が半減する）")
        # 値引きに弱い顧客タイプ
        if self.customer_id in ("housewife", "student"):
            self.purchase_gauge += 5
            self.log.append("値引きが刺さった！ 購買意欲+5！")
        # 報酬半減フラグはgoldを直接減らす
        self.customer["gold"] = max(1, self.customer["gold"] // 2)
        # 値引き効果: 警戒心も20%ダウン
        reduction = max(1, self.customer["defense"] // 5)
        self.customer["defense"] = max(0, self.customer["defense"] - reduction)
        self.log.append(f"客の警戒心もさがった！")

        if self.purchase_gauge >= self.purchase_threshold:
            self.purchase_gauge = self.purchase_threshold
            self._on_sale_closed()
        else:
            self.phase = "customer_turn"
            self.result_timer = 30

    def _explain_product(self):
        """商品説明 — 警戒心を下げ、やる気小回復（1戦闘1回）"""
        if self.explained:
            self.log.append("もう説明済みだ！")
            return

        self.explained = True
        p = self.game.player
        # 弱点ボーナス
        bonus = self._check_weakness("explain")
        # 警戒心を30%ダウン（弱点なら50%）
        if bonus > 1.0:
            reduction = max(1, self.customer["defense"] // 2)
        else:
            reduction = max(1, self.customer["defense"] // 3)
        self.customer["defense"] = max(0, self.customer["defense"] - reduction)
        # やる気小回復
        heal = 5
        p.hp = min(p.max_hp, p.hp + heal)
        self.game.play_se("heal")
        self.log.append(f"{p.name}は 商品を丁寧に説明した！")
        self.log.append(f"客の警戒心ダウン！ やる気+{heal}回復！")
        # 弱点ヒント
        weakness = self.customer.get("weakness")
        if weakness:
            skill_names = {s["id"]: s["name"] for s in SALES_SKILLS}
            wname = skill_names.get(weakness, "？？？")
            self.log.append(f"(ヒント: {wname}が効きそうだ)")
        # 顧客の行動傾向を表示
        actions = self.customer.get("actions", [])
        if actions:
            top_action = max(actions, key=lambda a: a[1])
            action_names = {
                "hesitation": "迷いやすい",
                "haggle": "値切り好き",
                "comparison": "比較検討型",
                "cold_visit": "帰りやすい",
                "impulse_buy": "衝動買い型",
                "bulk_buy": "まとめ買い好き",
                "charge": "溜め攻撃あり",
            }
            tendency = action_names.get(top_action[0], "読めない")
            self.log.append(f"(傾向: {tendency})")

        self.phase = "customer_turn"
        self.result_timer = 30

    def _get_available_skills(self):
        level = self.game.player.level
        return [s for s in SALES_SKILLS if s["level"] <= level]

    def _use_skill(self, skill_id):
        # スキル使用を記録（実績用）
        self.game.player.used_skills.add(skill_id)
        all_skill_ids = {s["id"] for s in SALES_SKILLS}
        if self.game.player.used_skills >= all_skill_ids:
            self.game.player.achievements.add("all_skills")
        if skill_id == "discount":
            order = self._determine_action_order()
            if order[0]["id"] == "player":
                self._discount()
            else:
                self.phase = "customer_first_discount"
                self.result_timer = 20
        elif skill_id == "explain":
            if self.explained:
                self.log.append("もう説明済みだ！")
                return
            self._explain_product()
        elif skill_id == "presentation":
            if self.game.player.hp < 10:
                self.log.append("やる気が足りない！")
                return
            self._presentation()
        elif skill_id == "smile":
            self._smile_response()
        elif skill_id == "market_analysis":
            if self.game.player.hp < 8:
                self.log.append("やる気が足りない！")
                return
            self._market_analysis()
        elif skill_id == "closing":
            if self.game.player.hp < 12:
                self.log.append("やる気が足りない！")
                return
            self._closing()
        elif skill_id == "limited_offer":
            if self.game.player.hp < 15:
                self.log.append("やる気が足りない！")
                return
            self._limited_offer()
        elif skill_id == "ultimate_pitch":
            if self.game.player.hp < 25:
                self.log.append("やる気が足りない！")
                return
            self._ultimate_pitch()

    def _presentation(self):
        """プレゼン — やる気10消費して大説得"""
        p = self.game.player
        p.hp -= 10
        attack = self._get_player_attack()
        persuasion = int(attack * 1.8)
        # 弱点ボーナス
        bonus = self._check_weakness("presentation")
        if bonus > 1.0:
            persuasion = int(persuasion * bonus)
        self.purchase_gauge += persuasion
        self.game.play_se("attack")
        self.game.screen_shake(3, 10)
        self.log.append(f"{p.name}の熱血プレゼン！ やる気-10！")
        self.log.append(f"説得力{persuasion}！")

        if self.purchase_gauge >= self.purchase_threshold:
            self.purchase_gauge = self.purchase_threshold
            self._on_sale_closed()
        else:
            self.phase = "customer_turn"
            self.result_timer = 30

    def _smile_response(self):
        """笑顔で対応 — やる気12回復（3ターンクールダウン）"""
        if self.smile_cooldown > 0:
            self.log.append(f"まだ笑顔の効果が残っている！ (あと{self.smile_cooldown}ターン)")
            return
        p = self.game.player
        heal = 12
        p.hp = min(p.max_hp, p.hp + heal)
        self.game.play_se("heal")
        self.log.append(f"{p.name}は 笑顔で対応した！")
        self.log.append(f"やる気が {heal} 回復した！")
        self.smile_cooldown = 3
        # 弱点チェック（笑顔は回復なので購買意欲には影響しないが演出）
        bonus = self._check_weakness("smile")
        if bonus > 1.0:
            extra = 5
            self.purchase_gauge += extra
            self.log.append(f"好感度アップ！ 購買意欲+{extra}！")
        self.phase = "customer_turn"
        self.result_timer = 30

    def _market_analysis(self):
        """市場分析 — 客の警戒心を50%ダウン"""
        p = self.game.player
        p.hp -= 8
        # 弱点ボーナス: 弱点なら75%ダウン
        bonus = self._check_weakness("market_analysis")
        total_def = self.customer["defense"] + self.customer_defense_bonus
        if bonus > 1.0:
            reduction = max(1, int(total_def * 0.75))
        else:
            reduction = max(1, total_def // 2)
        # bonusから先に引く
        if self.customer_defense_bonus >= reduction:
            self.customer_defense_bonus -= reduction
        else:
            remaining = reduction - self.customer_defense_bonus
            self.customer_defense_bonus = 0
            self.customer["defense"] = max(0, self.customer["defense"] - remaining)
        self.game.play_se("heal")
        self.log.append(f"{p.name}は 市場を分析した！")
        self.log.append(f"客の警戒心が 大幅にさがった！")
        self.phase = "customer_turn"
        self.result_timer = 30

    def _closing(self):
        """クロージング — 購買意欲を固定値加算"""
        p = self.game.player
        p.hp -= 12
        amount = 15
        # 弱点ボーナス
        bonus = self._check_weakness("closing")
        if bonus > 1.0:
            amount = int(amount * bonus)
        self.purchase_gauge += amount
        self.game.play_se("attack")
        self.log.append(f"{p.name}の クロージングトーク！")
        self.log.append(f"購買意欲が {amount} アップ！")
        if self.purchase_gauge >= self.purchase_threshold:
            self.purchase_gauge = self.purchase_threshold
            self._on_sale_closed()
        else:
            self.phase = "customer_turn"
            self.result_timer = 30

    def _limited_offer(self):
        """限定オファー — 次のセールストークの説得力3倍バフ"""
        p = self.game.player
        p.hp -= 15
        # 弱点ボーナス: 弱点なら4倍
        bonus = self._check_weakness("limited_offer")
        if bonus > 1.0:
            self.next_attack_multiplier = 4.0
            self.game.play_se("heal")
            self.log.append(f"{p.name}は 限定オファーを準備した！")
            self.log.append("次のセールストークが 4倍の説得力に！")
        else:
            self.next_attack_multiplier = 3.0
            self.game.play_se("heal")
            self.log.append(f"{p.name}は 限定オファーを準備した！")
            self.log.append("次のセールストークが 3倍の説得力に！")
        self.phase = "customer_turn"
        self.result_timer = 30

    def _ultimate_pitch(self):
        """究極プレゼン — 説得力4倍"""
        p = self.game.player
        p.hp -= 25
        attack = self._get_player_attack()
        persuasion = int(attack * 3.0)
        # 弱点ボーナス
        bonus = self._check_weakness("ultimate_pitch")
        if bonus > 1.0:
            persuasion = int(persuasion * bonus)
        self.purchase_gauge += persuasion
        self.game.play_se("attack")
        self.game.screen_shake(4, 12)
        self.log.append(f"{p.name}の 究極プレゼンテーション！")
        self.log.append(f"圧倒的な説得力 {persuasion}！")
        if self.purchase_gauge >= self.purchase_threshold:
            self.purchase_gauge = self.purchase_threshold
            self._on_sale_closed()
        else:
            self.phase = "customer_turn"
            self.result_timer = 30

    def _give_up(self):
        """見送る — 確率で失敗、成功してもコンボリセット"""
        # 見送り成功判定（80%成功、ボスは50%）
        success_rate = 0.5 if self.customer_id == "boss_merchant" else 0.8
        if random.random() < success_rate:
            self.log.append("商談を見送った。")
            self.game.player.combo_count = 0
            self.phase = "result"
            self.result_timer = 30
            self.result_gold = 0
            self.result_exp = 0
        else:
            self.log.append("見送ろうとしたが、引き止められた！")
            self.game.play_se("miss")
            self.phase = "customer_turn"
            self.result_timer = 30

    def _customer_turn(self):
        """客のリアクションを選択・実行"""
        if self.customer_charging:
            self.customer_charging = False
            # 強攻撃（haggleの1.5倍）
            attack = int((self.customer["attack"] + self.customer_attack_bonus) * 1.5)
            defense = self._get_player_defense()
            damage = calc_damage(attack, defense)
            p = self.game.player
            p.hp -= damage
            self.game.play_se("attack")
            self.game.screen_shake(4, 12)
            self.damage_flash = 15
            self.log.append(f"{self.customer['name']}の 強烈な値切り交渉！")
            self.log.append(f"やる気が {damage} さがった！")
            self._check_player_exhausted()
            return
        actions = self.customer.get("actions", [("hesitation", 1.0)])

        # 購買意欲が50%以上になると行動が変化
        gauge_ratio = self.purchase_gauge / self.purchase_threshold if self.purchase_threshold > 0 else 0
        if gauge_ratio >= 0.5:
            # 成約が近い: 衝動買いが増える、迷いが減る
            modified_actions = []
            for action, prob in actions:
                if action == "impulse_buy":
                    modified_actions.append((action, prob * 1.5))
                elif action == "hesitation":
                    modified_actions.append((action, prob * 0.5))
                elif action in ("haggle", "comparison"):
                    modified_actions.append((action, prob * 1.3))
                else:
                    modified_actions.append((action, prob))
            # 確率を正規化
            total = sum(p for _, p in modified_actions)
            if total > 0:
                actions = [(a, p / total) for a, p in modified_actions]

        r = random.random()
        cumulative = 0
        chosen = "hesitation"
        for action, prob in actions:
            cumulative += prob
            if r <= cumulative:
                chosen = action
                break

        self._customer_reaction(chosen)

    def _customer_reaction(self, reaction_id):
        """客のリアクション処理"""
        p = self.game.player
        spec = CUSTOMER_REACTIONS.get(reaction_id)
        if not spec:
            # フォールバック
            self._customer_hesitation()
            return

        msg = spec["message"].format(name=self.customer["name"])

        if spec["type"] == "attack":
            # 迷い/値切り: やる気ダメージ
            attack = self.customer["attack"] + self.customer_attack_bonus
            if spec.get("multiplier", 1.0) != 1.0:
                attack = int(attack * spec["multiplier"])
            defense = self._get_player_defense()
            damage = calc_damage(attack, defense)
            p.hp -= damage
            self.game.play_se("attack")
            self.game.screen_shake(2, 8)
            self.damage_flash = 15
            self.log.append(msg)
            self.log.append(f"やる気が {damage} さがった！")

        elif spec["type"] == "debuff_attack":
            # 比較検討: セールス力デバフ
            self.player_attack_debuff += spec["amount"]
            self.log.append(msg)

        elif spec["type"] == "flee":
            # 冷やかし: 客が帰る
            self.log.append(msg)
            self.game.play_se("enemy_defeat")
            self.phase = "result"
            self.result_timer = 30
            return

        elif spec["type"] == "boost":
            # 衝動買い: 購買意欲UP（ポジティブ）
            self.purchase_gauge += spec["amount"]
            self.game.play_se("heal")
            self.log.append(msg)
            if self.purchase_gauge >= self.purchase_threshold:
                self.purchase_gauge = self.purchase_threshold
                self._on_sale_closed()
                return

        elif spec["type"] == "bulk":
            # まとめ買い交渉: 報酬2倍チャンス
            self.bulk_buy_active = True
            self.log.append(msg)

        elif spec["type"] == "buff_attack":
            self.customer_attack_bonus = min(self.customer_attack_bonus + spec["amount"], 15)  # 上限15
            self.game.screen_shake(4, 12)
            self.log.append(msg)

        elif spec["type"] == "buff_defense":
            self.customer_defense_bonus = min(self.customer_defense_bonus + spec["amount"], 15)  # 上限15
            self.game.screen_shake(4, 12)
            self.log.append(msg)

        elif spec["type"] == "charge":
            self.customer_charging = True
            self.log.append(msg)
            # chargeターンは攻撃なし
            self._append_customer_quote(reaction_id)
            self._check_player_exhausted()
            return

        # 顧客の台詞（ランダム）
        self._append_customer_quote(reaction_id)
        self._check_player_exhausted()

    def _append_customer_quote(self, reaction_id):
        """顧客の台詞をランダムでログに追加（30%の確率）"""
        if random.random() < 0.3:
            quotes = {
                "hesitation": ["「うーん、どうしようかな...」", "「もう少し考えさせて」"],
                "haggle": ["「もうちょっと安くならない？」", "「他の店はもっと安いよ？」"],
                "comparison": ["「ネットの方が安いんだよね」", "「友達に聞いてみるよ」"],
                "impulse_buy": ["「あ、これいいかも！」", "「買っちゃおうかな！」"],
                "bulk_buy": ["「まとめて買うから割引してよ」"],
                "charge": ["「...（何か考えているようだ）」"],
            }
            if reaction_id in quotes:
                quote = random.choice(quotes[reaction_id])
                self.log.append(quote)

    def _customer_hesitation(self):
        """フォールバック: 迷い"""
        p = self.game.player
        damage = max(1, calc_damage(self.customer["attack"], self._get_player_defense()))
        p.hp -= damage
        self.game.screen_shake(2, 8)
        self.damage_flash = 15
        self.log.append(f"{self.customer['name']}は 迷っている...")
        self.log.append(f"やる気が {damage} さがった！")
        self._check_player_exhausted()

    def _check_player_exhausted(self):
        """やる気が0になったら失注"""
        # ターン経過
        self.turn_count += 1
        if self.smile_cooldown > 0:
            self.smile_cooldown -= 1

        # ターン制限チェック（ボス戦は20、通常は15）
        max_turns = 20 if self.customer_id == "boss_merchant" else 15
        if self.turn_count >= max_turns and self.phase != "result":
            self.log.append(f"{self.customer['name']}は 待ちくたびれて帰ってしまった...")
            self.game.play_se("enemy_defeat")
            self.game.player.combo_count = 0
            self.phase = "result"
            self.result_timer = 60
            self.result_gold = 0
            self.result_exp = 0
            return

        if self.game.player.hp <= 0:
            self.game.player.hp = 0
            self._on_sale_lost()
        else:
            self.phase = "menu"

    def _determine_action_order(self):
        """行動順決定"""
        p = self.game.player
        combatants = [
            {"id": "player", "speed": p.speed},
            {"id": "customer", "speed": self.customer.get("speed", 5)},
        ]
        return calc_action_order(combatants)

    def _on_sale_closed(self):
        """成約（勝利）"""
        self.game.play_se("enemy_defeat")

        if self.selected_product and self.selected_product.get("id") == "__cross_sell__":
            # クロスセル成約: 両方消費してボーナス付き利益
            my_item = ITEMS[self.selected_product["my_product"]["id"]]
            partner_item = ITEMS[self.selected_product["partner_product"]["id"]]
            self.game.inventory.remove_item(self.selected_product["my_product"]["id"])
            self.game.inventory.remove_item(self.selected_product["partner_product"]["id"])

            my_profit = my_item["sell_value"] - my_item["price"]
            # 紹介代理店の場合はreferral_feeを使う
            contract = self.game.partner_system.active_contract
            if contract and contract.contract_type == "referral":
                partner_profit = partner_item.get("referral_fee", 0)
            else:
                partner_profit = partner_item["sell_value"] - partner_item["price"]

            gold = int((my_profit + partner_profit) * 1.3)  # クロスセルボーナス1.3倍
            exp = self.customer["exp"] * 2  # クロスセルはEXP2倍
            self.log.append("★ クロスセル成約！ ★")
            self.log.append(f"{my_item['name']}+{partner_item['name']}をセット販売！")
        elif self.selected_product:
            # 商品販売: 売値 - 仕入れ値 = 粗利
            item = ITEMS.get(self.selected_product["id"])
            sell_value = item.get("sell_value", 0)
            buy_price = item.get("price", 0)
            # パートナー商品で紹介代理店の場合はreferral_feeを使う
            if item.get("shop") == "partner_shop":
                contract = self.game.partner_system.active_contract
                if contract and contract.contract_type == "referral":
                    gold = item.get("referral_fee", 0)
                else:
                    gold = sell_value - buy_price
            else:
                gold = sell_value - buy_price  # 粗利
            exp = self.customer["exp"]
            # 商品を在庫から消費
            self.game.inventory.remove_item(self.selected_product["id"])
            self.log.append(f"{item['name']}を売った！")
        else:
            # 商品なし: 基本報酬（低い）
            gold = max(5, self.customer["gold"] // 3)
            exp = self.customer["exp"] // 2
            self.log.append("商品なしの商談... 紹介料のみ。")

        # まとめ買い2倍
        if self.bulk_buy_active:
            gold *= 2
            self.log.append("まとめ買い成立！ 利益2倍！")

        # パートナーフィー計算
        contract = self.game.partner_system.active_contract
        fee_bonus = 0
        rank_up = False
        if contract:
            fee_bonus = contract.calculate_fee(gold)
            self.game.partner_system._cumulative_sales += gold
            rank_up = self.game.partner_system._update_rank()
            gold += fee_bonus

        # 連戦コンボ
        self.game.player.combo_count += 1
        self.game.player.max_combo = max(self.game.player.max_combo, self.game.player.combo_count)
        combo = self.game.player.combo_count
        if combo >= 2:
            combo_bonus = min(combo * 0.1, 0.5)  # 最大50%ボーナス
            combo_gold = int(gold * combo_bonus)
            gold += combo_gold

        # ボス撃破フラグ
        if self.customer_id == "boss_merchant":
            self.game.chapter.boss_defeated = True

        p = self.game.player
        p.total_exp += exp
        p.gold += gold
        # 売上を累計に加算（チャプター条件用）
        self.game.chapter.add_sales(gold)

        # 表示用に記録
        self.result_gold = gold
        self.result_exp = exp

        self.log.append(f"{self.customer['name']}との商談 成約！")
        self.log.append(f"EXP +{exp}  利益 +{gold}G")
        if fee_bonus > 0:
            self.log.append(f"(パートナーフィー +{fee_bonus}G)")
        if combo >= 2:
            self.log.append(f"★ {combo}連続成約！ ボーナス +{combo_gold}G！")

        # ランクアップ通知
        if rank_up:
            ps = self.game.partner_system
            self.log.append(f"パートナーランクが {ps.rank}({ps.rank_label})に上がった！")

        self.game.player.wins += 1

        # === 実績チェック ===
        p = self.game.player
        if p.wins == 1:
            p.achievements.add("first_sale")
        if p.combo_count >= 5:
            p.achievements.add("combo_5")
        if self.customer_id == "boss_merchant":
            p.achievements.add("boss_clear")
        # 会心の一撃で成約
        if self.last_critical:
            p.achievements.add("critical_finish")
        # 無傷（被ダメージ0で成約）
        if p.hp == p.max_hp:
            p.achievements.add("no_damage")
        # 1ターン成約（攻撃行動が1回だけ）
        attack_actions = [l for l in self.log if "セールストーク" in l or "プレゼン" in l or "究極" in l]
        if len(attack_actions) == 1:
            p.achievements.add("speed_kill")
        # ランクA到達
        if self.game.partner_system.rank == "A":
            p.achievements.add("rank_a")
        # 所持金1000G以上
        if p.gold >= 1000:
            p.achievements.add("rich")

        self._check_level_up()
        self.phase = "result"
        self.result_timer = 90
        self.game.play_se("victory")

    def _on_sale_lost(self):
        """失注（敗北）— 軽いペナルティ"""
        self.game.player.losses += 1
        self.game.player.combo_count = 0
        self.game.play_se("game_over")

        # ゴールドペナルティ（10%、最低5G）
        p = self.game.player
        penalty = max(5, p.gold // 10)
        penalty = min(penalty, p.gold)  # 0未満にならない
        p.gold -= penalty

        self.log.append("やる気が尽きた... 商談失敗。")
        if penalty > 0:
            self.log.append(f"動揺して {penalty}G 落としてしまった...")
        self.log.append("気を取り直して次に行こう！")
        p.hp = p.max_hp
        self.phase = "result"
        self.result_timer = 60
        self.result_gold = 0
        self.result_exp = 0

    def _check_level_up(self):
        p = self.game.player
        new_level = check_level_up(p.level, p.total_exp)
        while p.level < new_level:
            p.level += 1
            stats = get_level_up_stats(p.level)
            p.max_hp += stats["max_hp"]
            p.hp = p.max_hp
            p.attack += stats["attack"]
            p.defense += stats["defense"]
            p.speed += stats["speed"]
            self.game.play_se("level_up")
            self.log.append(f"レベルが {p.level} にあがった！")
            self.log.append(
                f"やる気+{stats['max_hp']} セ+{stats['attack']} "
                f"メ+{stats['defense']} 対+{stats['speed']}"
            )
            # スキル習得通知
            for skill in SALES_SKILLS:
                if skill["level"] == p.level:
                    self.log.append(f"★ {skill['name']}を覚えた！")

    def _use_item(self, item_id):
        item = ITEMS.get(item_id)
        if not item or item["type"] != "consumable":
            return
        if not self.game.inventory.remove_item(item_id):
            return
        if item["effect"] == "hp_heal":
            heal = item["value"]
            self.game.player.hp = min(
                self.game.player.max_hp, self.game.player.hp + heal
            )
            self.game.play_se("heal")
            self.log.append(f"{item['name']}を使った！ やる気 {heal}回復！")
        elif item["effect"] == "cure_debuff":
            self.player_attack_debuff = 0
            self.customer_attack_bonus = 0
            self.game.play_se("heal")
            self.log.append(f"{item['name']}を使った！ 緊張がほぐれた！")
        elif item["effect"] == "reveal_weakness":
            weakness = self.customer.get("weakness")
            if weakness:
                skill_names = {s["id"]: s["name"] for s in SALES_SKILLS}
                wname = skill_names.get(weakness, "？？？")
                self.log.append(f"{item['name']}を使った！")
                self.log.append(f"弱点判明: {wname}が効く！")
            else:
                self.log.append(f"{item['name']}を使った！")
                self.log.append("弱点は見つからなかった...")
            self.game.play_se("heal")
        elif item["effect"] == "repel":
            self.game.player.repel_steps = item["value"]
            self.log.append(f"{item['name']}を配った！ 客足が遠のいた。")
            self.phase = "result"
            self.result_timer = 30
            return

        self.phase = "customer_turn"
        self.result_timer = 30

    def update(self):
        if self.game.message_window.active:
            self.game.message_window.update()
            return

        if self.phase == "encounter":
            self.result_timer -= 1
            if self.result_timer <= 0 or btn_confirm():
                # 商材を持っているか確認
                merchandise = self._get_merchandise()
                if merchandise:
                    self.phase = "select_product"
                    self.product_select_index = 0
                else:
                    # 商材なし → 素手の商談（利益は固定で低い）
                    self.selected_product = None
                    self.phase = "menu"

        elif self.phase == "select_product":
            merchandise = self._get_merchandise()
            total_options = len(merchandise[:5]) + 1  # 商品 + 「商品なしで商談」
            if btn_up():
                self.product_select_index = max(0, self.product_select_index - 1)
                self.game.play_se("cursor")
            if btn_down():
                self.product_select_index = min(total_options - 1, self.product_select_index + 1)
                self.game.play_se("cursor")
            if btn_confirm():
                if self.product_select_index < len(merchandise[:5]):
                    self.selected_product = merchandise[self.product_select_index]
                    # 商品とターゲットの相性チェック
                    self._apply_product_bonus()
                else:
                    # 「商品なしで商談」オプション
                    self.selected_product = None
                self.game.play_se("confirm")
                self.phase = "menu"

        elif self.phase == "menu":
            if btn_up():
                self.menu_index = max(0, self.menu_index - 1)
                self.game.play_se("cursor")
            if btn_down():
                self.menu_index = min(3, self.menu_index + 1)
                self.game.play_se("cursor")

            if btn_confirm():
                self.game.play_se("confirm")

                if self.menu_index == 0:
                    # セールストーク
                    order = self._determine_action_order()
                    if order[0]["id"] == "player":
                        self._sales_talk()
                    else:
                        self.phase = "customer_first"
                        self.result_timer = 20
                elif self.menu_index == 1:
                    # 特技サブメニュー
                    self.phase = "skill_select"
                    self.skill_select_index = 0
                elif self.menu_index == 2:
                    # 道具サブメニュー
                    items = self.game.inventory.get_all_items()
                    consumables = [
                        i for i in items if ITEMS.get(i["id"], {}).get("type") == "consumable"
                    ]
                    if consumables:
                        self.phase = "item_select"
                        self.item_select_index = 0
                    else:
                        self.log.append("道具を持っていない！")
                elif self.menu_index == 3:
                    # 見送る
                    self._give_up()

        elif self.phase == "skill_select":
            skills = self._get_available_skills()
            max_visible = 4
            if btn_up():
                self.skill_select_index = max(0, self.skill_select_index - 1)
                if self.skill_select_index < self.skill_scroll_offset:
                    self.skill_scroll_offset = self.skill_select_index
                self.game.play_se("cursor")
            if btn_down():
                self.skill_select_index = min(len(skills) - 1, self.skill_select_index + 1)
                if self.skill_select_index >= self.skill_scroll_offset + max_visible:
                    self.skill_scroll_offset = self.skill_select_index - max_visible + 1
                self.game.play_se("cursor")
            if btn_confirm():
                self.game.play_se("confirm")
                self._use_skill(skills[self.skill_select_index]["id"])
            if btn_cancel():
                self.phase = "menu"

        elif self.phase == "item_select":
            items = self.game.inventory.get_all_items()
            consumables = [
                i for i in items if ITEMS.get(i["id"], {}).get("type") == "consumable"
            ]
            total_options = len(consumables)
            if total_options == 0:
                self.log.append("道具を持っていない！")
                self.phase = "menu"
                return

            if btn_up():
                self.item_select_index = max(0, self.item_select_index - 1)
                self.game.play_se("cursor")
            if btn_down():
                self.item_select_index = min(total_options - 1, self.item_select_index + 1)
                self.game.play_se("cursor")
            if btn_confirm():
                self.game.play_se("confirm")
                self._use_item(consumables[self.item_select_index]["id"])
            if btn_cancel():
                self.phase = "menu"

        elif self.phase == "customer_first":
            self.result_timer -= 1
            if self.result_timer <= 0:
                self._customer_turn()
                if self.phase not in ("result",) and self.game.player.hp > 0:
                    self._sales_talk()

        elif self.phase == "customer_first_discount":
            self.result_timer -= 1
            if self.result_timer <= 0:
                self._customer_turn()
                if self.phase not in ("result",) and self.game.player.hp > 0:
                    self._discount()

        elif self.phase == "customer_turn":
            self.result_timer -= 1
            if self.result_timer <= 0:
                self._customer_turn()

        elif self.phase == "result":
            self.result_timer -= 1
            if self.result_timer <= 0:
                if btn_confirm():
                    if self.game.player.hp > 0:
                        # ボス撃破後はエンディングへ直行
                        if self.customer_id == "boss_merchant" and self.purchase_gauge >= self.purchase_threshold:
                            self.game.change_scene_with_transition("ending")
                        else:
                            self.game.change_scene_with_transition("field")
                    else:
                        self.game.change_scene_with_transition(
                            "field", map="home", x=7, y=7
                        )
            elif btn_confirm():
                # タイマースキップ
                self.result_timer = 0

    def draw(self):
        t = self.game.text
        pyxel.cls(1)

        # === 全体レイアウト（12pxフォント, 行間14px） ===
        # y=0-14:    顧客名
        # y=16-96:   顧客スプライト（5倍=80px）
        # y=98-106:  購買意欲ゲージ
        # y=108-172: コマンド(左) + ステータス(右)
        # y=174-240: ログエリア

        # 顧客表示（拡大描画 16x16 -> 5倍）
        sprite = CUSTOMER_SPRITES.get(self.customer_id, (32, 0))
        ex, ey = 80, 16
        scale = 5
        for dy in range(16):
            for dx in range(16):
                col = pyxel.images[0].pget(sprite[0] + dx, sprite[1] + dy)
                if col != 0:
                    pyxel.rect(
                        ex + dx * scale, ey + dy * scale, scale, scale, col
                    )

        # 顧客名 (y=0-14)
        t(ex, 2, self.customer["name"], 7)

        # 購買意欲ゲージ (y=98-106)
        gauge_ratio = self.purchase_gauge / self.purchase_threshold if self.purchase_threshold > 0 else 0
        bar_x = ex
        bar_y = 100
        t(bar_x - 72, bar_y - 2, "購買意欲", 6)
        pyxel.rect(bar_x, bar_y, 80, 6, 5)
        # 段階色
        if gauge_ratio < 0.34:
            bar_color = 8  # 赤
        elif gauge_ratio < 0.67:
            bar_color = 10  # 黄
        else:
            bar_color = 11  # 緑
        pyxel.rect(bar_x, bar_y, int(80 * gauge_ratio), 6, bar_color)
        t(bar_x + 82, bar_y - 2, f"{self.purchase_gauge}/{self.purchase_threshold}", 6)

        # === プレイヤーステータス（右半分 x=140-255, y=108-172） ===
        p = self.game.player
        if self.damage_flash > 0:
            self.damage_flash -= 1
            bg_color = 8 if self.damage_flash % 4 < 2 else 1  # 赤点滅
        else:
            bg_color = 1
        pyxel.rect(140, 108, 112, 64, bg_color)
        pyxel.rectb(140, 108, 112, 64, 7)
        t(148, 110, p.name, 7)
        # やる気バー (y=122)
        hp_ratio = p.hp / p.max_hp if p.max_hp > 0 else 0
        t(148, 124, f"やる気{p.hp}/{p.max_hp}", 7)
        pyxel.rect(148, 136, 96, 4, 5)
        if hp_ratio > 0.66:
            hp_bar_color = 11  # 緑
        elif hp_ratio > 0.33:
            hp_bar_color = 10  # 黄
        else:
            hp_bar_color = 8   # 赤
        pyxel.rect(148, 136, int(96 * hp_ratio), 4, hp_bar_color)
        t(148, 142, f"Lv:{p.level} セ力:{self._get_player_attack()}", 7)
        # 残りターン + バフ (y=156)
        max_turns = 20 if self.customer_id == "boss_merchant" else 15
        remaining_turns = max(0, max_turns - self.turn_count)
        turn_color = 7 if remaining_turns > 5 else 10 if remaining_turns > 2 else 8
        turn_text = f"残り{remaining_turns}T"
        if self.next_attack_multiplier > 1.0:
            turn_text += f" ★x{self.next_attack_multiplier:.0f}"
        t(148, 156, turn_text, turn_color)

        # === コマンドメニュー（左半分 x=4-135, y=108-172） ===
        if self.phase == "menu":
            pyxel.rect(4, 108, 132, 64, 1)
            pyxel.rectb(4, 108, 132, 64, 7)
            commands = ["セールストーク", "特技", "道具", "見送る"]
            for i, cmd in enumerate(commands):
                color = 10 if i == self.menu_index else 7
                prefix = "> " if i == self.menu_index else "  "
                t(12, 112 + i * 14, prefix + cmd, color)

        elif self.phase == "skill_select":
            skills = self._get_available_skills()
            max_visible = 4
            pyxel.rect(4, 108, 132, 64, 1)
            pyxel.rectb(4, 108, 132, 64, 7)
            visible_skills = skills[self.skill_scroll_offset:self.skill_scroll_offset + max_visible]
            for i, skill in enumerate(visible_skills):
                actual_index = i + self.skill_scroll_offset
                is_selected = actual_index == self.skill_select_index
                # 商品説明済み or 笑顔クールダウン中ならグレー表示
                if skill["id"] == "explain" and self.explained:
                    color = 13  # グレー
                elif skill["id"] == "smile" and self.smile_cooldown > 0:
                    color = 13  # グレー
                elif is_selected:
                    color = 10
                else:
                    color = 7
                prefix = "> " if is_selected else "  "
                cost_str = f"[{skill['cost']}]" if skill["cost"] > 0 else ""
                t(12, 112 + i * 14, f"{prefix}{skill['name']}{cost_str}", color)
            # スクロールインジケータ
            if self.skill_scroll_offset > 0:
                t(124, 110, "▲", 6)
            if self.skill_scroll_offset + max_visible < len(skills):
                t(124, 160, "▼", 6)
            # 選択中スキルの説明（スキルウィンドウ下部に表示）
            if self.skill_select_index < len(skills):
                selected_skill = skills[self.skill_select_index]
                desc = selected_skill["description"]
                pyxel.rect(4, 164, 136, 14, 1)
                t(8, 166, desc, 10)

        elif self.phase == "item_select":
            items = self.game.inventory.get_all_items()
            consumables = [
                i for i in items if ITEMS.get(i["id"], {}).get("type") == "consumable"
            ]
            max_visible_items = 4
            item_scroll = max(0, self.item_select_index - max_visible_items + 1)
            pyxel.rect(4, 108, 132, 64, 1)
            pyxel.rectb(4, 108, 132, 64, 7)
            visible_items = consumables[item_scroll:item_scroll + max_visible_items]
            for i, item in enumerate(visible_items):
                actual_idx = i + item_scroll
                color = 10 if actual_idx == self.item_select_index else 7
                prefix = "> " if actual_idx == self.item_select_index else "  "
                t(12, 112 + i * 14, f"{prefix}{item['name']} x{item['quantity']}", color)

        elif self.phase == "select_product":
            # 商品選択ウィンドウ (y=80-172)
            pyxel.rect(4, 80, 248, 92, 1)
            pyxel.rectb(4, 80, 248, 92, 7)
            pyxel.rectb(6, 82, 244, 88, 5)
            t(12, 86, "どの商品を提案する？", 10)
            merchandise = self._get_merchandise()
            for i, item in enumerate(merchandise[:5]):
                y = 102 + i * 14
                color = 10 if i == self.product_select_index else 7
                prefix = "> " if i == self.product_select_index else "  "

                if item.get("id") == "__cross_sell__":
                    # クロスセルオプション
                    my_item = ITEMS.get(item["my_product"]["id"], {})
                    partner_item = ITEMS.get(item["partner_product"]["id"], {})
                    my_profit = my_item.get("sell_value", 0) - my_item.get("price", 0)
                    contract = self.game.partner_system.active_contract
                    if contract and contract.contract_type == "referral":
                        p_profit = partner_item.get("referral_fee", 0)
                    else:
                        p_profit = partner_item.get("sell_value", 0) - partner_item.get("price", 0)
                    total = int((my_profit + p_profit) * 1.3)
                    t(12, y, f"{prefix}★セット販売 ◎", color)
                    t(192, y, f"+{total}G", 10)
                else:
                    product = ITEMS.get(item["id"], {})
                    # ターゲット相性表示
                    customer_target = self.customer.get("target", "general")
                    product_target = product.get("target", "general")
                    if product_target == customer_target:
                        match = "◎"
                    elif product_target == "general":
                        match = "○"
                    else:
                        match = "△"
                    # パートナー商品かどうかの表記
                    partner_mark = "P" if product.get("shop") == "partner_shop" else ""
                    # 商品名を最大10文字に制限
                    pname = product['name']
                    if len(pname) > 10:
                        pname = pname[:9] + ".."
                    t(12, y, f"{prefix}{pname}{partner_mark} {match}", color)
                    if product.get("shop") == "partner_shop":
                        contract = self.game.partner_system.active_contract
                        if contract and contract.contract_type == "referral":
                            profit = product.get("referral_fee", 0)
                        else:
                            profit = product.get("sell_value", 0) - product.get("price", 0)
                    else:
                        profit = product.get("sell_value", 0) - product.get("price", 0)
                    t(192, y, f"+{profit}G", 6)
            # 「商品なしで商談」オプション
            ni = len(merchandise[:5])
            color = 10 if self.product_select_index == ni else 7
            prefix = "> " if self.product_select_index == ni else "  "
            t(12, 102 + ni * 14, f"{prefix}商品なしで商談", color)
            # 操作ガイド
            t(12, 160, "↑↓:選択 A:決定", 6)

        # === ログエリア (y=174-240, 4行×14px) ===
        log_y = 178
        pyxel.rect(4, 174, 248, 66, 1)
        pyxel.rectb(4, 174, 248, 66, 13)
        visible_log = self.log[-4:]
        # ログテキストを最大19文字に制限
        for i, msg in enumerate(visible_log):
            if len(msg) > 19:
                msg = msg[:19]
            t(12, log_y + i * 14, msg, 7)

        # === 成約結果表示（勝利時の強調表示） ===
        if self.phase == "result" and self.purchase_gauge >= self.purchase_threshold:
            rx, ry, rw, rh = 12, 30, 232, 140
            pyxel.rect(rx, ry, rw, rh, 0)
            pyxel.rect(rx + 2, ry + 2, rw - 4, rh - 4, 1)
            pyxel.rectb(rx, ry, rw, rh, 10)
            pyxel.rectb(rx + 2, ry + 2, rw - 4, rh - 4, 10)
            # タイトル行 (ry+8)
            t(rx + 56, ry + 8, "★ 商談成約！ ★", 10)
            # 区切り線 (ry+24)
            pyxel.line(rx + 8, ry + 24, rx + rw - 8, ry + 24, 10)
            # 結果情報 (14px間隔)
            t(rx + 16, ry + 30, f"利益:   {self.result_gold}G", 7)
            t(rx + 16, ry + 44, f"経験値: {self.result_exp}EXP", 7)
            p = self.game.player
            t(rx + 16, ry + 58, f"Lv:{p.level} やる気:{p.hp}/{p.max_hp}", 7)
            combo = self.game.player.combo_count
            if self.cross_sell_bonus:
                t(rx + 16, ry + 72, "★クロスセル! (x1.3)", 10)
            elif combo >= 2:
                t(rx + 16, ry + 72, f"★{combo}連続成約ボーナス!", 10)
            elif self.bulk_buy_active:
                t(rx + 16, ry + 72, "まとめ買いボーナス!", 10)
            # 区切り線
            pyxel.line(rx + 8, ry + 88, rx + rw - 8, ry + 88, 5)
            # Tips表示
            tip_index = (self.game.player.wins - 1) % len(BUSINESS_TIPS)
            tip = BUSINESS_TIPS[tip_index]
            # Tipを枠内に収める（最大18文字）
            if len(tip) > 18:
                tip = tip[:18]
            t(rx + 8, ry + 94, tip, 6)
            # Aで続ける
            if self.result_timer <= 0 and pyxel.frame_count % 40 < 28:
                t(rx + 56, ry + 110, "- Aで続ける -", 6)
        elif self.phase == "result" and self.game.player.hp <= 0:
            # 失注時パネル
            rx, ry, rw, rh = 12, 60, 232, 80
            pyxel.rect(rx, ry, rw, rh, 0)
            pyxel.rect(rx + 2, ry + 2, rw - 4, rh - 4, 1)
            pyxel.rectb(rx, ry, rw, rh, 8)
            pyxel.rectb(rx + 2, ry + 2, rw - 4, rh - 4, 8)
            t(rx + 56, ry + 8, "商談失敗...", 8)
            pyxel.line(rx + 8, ry + 24, rx + rw - 8, ry + 24, 8)
            t(rx + 16, ry + 30, "やる気が尽きてしまった。", 7)
            t(rx + 16, ry + 44, "気を取り直して次に行こう!", 7)
            if self.result_timer <= 0 and pyxel.frame_count % 40 < 28:
                t(rx + 56, ry + 60, "- Aで続ける -", 6)

        # 結果画面の入力プロンプト（パネル外のフォールバック）
        if self.phase == "result" and self.result_timer <= 0:
            if self.purchase_gauge < self.purchase_threshold and self.game.player.hp > 0:
                # 見送り時のみここに表示
                if pyxel.frame_count % 40 < 28:
                    t(160, 224, "- Aで続ける -", 6)
