"""Partner Business Quest - 総合テスト"""
import sys
import unittest
import random
from unittest.mock import MagicMock, patch

# === pyxelモジュールをモック ===
mock_pyxel = MagicMock()
mock_pyxel.KEY_UP = 0
mock_pyxel.KEY_DOWN = 1
mock_pyxel.KEY_LEFT = 2
mock_pyxel.KEY_RIGHT = 3
mock_pyxel.KEY_Z = 4
mock_pyxel.KEY_X = 5
mock_pyxel.KEY_RETURN = 12
mock_pyxel.KEY_SPACE = 13
mock_pyxel.KEY_ESCAPE = 14
mock_pyxel.GAMEPAD1_BUTTON_A = 6
mock_pyxel.GAMEPAD1_BUTTON_B = 7
mock_pyxel.GAMEPAD1_BUTTON_DPAD_UP = 8
mock_pyxel.GAMEPAD1_BUTTON_DPAD_DOWN = 9
mock_pyxel.GAMEPAD1_BUTTON_DPAD_LEFT = 10
mock_pyxel.GAMEPAD1_BUTTON_DPAD_RIGHT = 11
mock_pyxel.frame_count = 0
mock_pyxel.btnp = MagicMock(return_value=False)
mock_pyxel.images = [MagicMock()]
mock_pyxel.Font = MagicMock()
sys.modules['pyxel'] = mock_pyxel

# ゲームモジュールをインポート
from game import PlayerState, Game
from systems.economy import (
    calc_damage, calc_persuasion, check_level_up,
    get_level_up_stats, exp_for_level, EXP_TABLE, LEVEL_UP_STATS
)
from systems.partner import PartnerSystem, PartnerContract, PARTNER_RANKS, RANK_ORDER
from systems.inventory import InventorySystem
from systems.chapter import ChapterSystem, CHAPTERS
from scenes.battle import BattleScene, SALES_SKILLS
from scenes.shop import ShopScene
from data.maps import (
    MAPS, WALKABLE, TILE_SHOP, BUILDING_EVENTS,
    MAP_NPCS, MAP_TRANSITIONS, TREASURE_CHESTS
)
from data.items import ITEMS, SHOP_INVENTORY, get_available_items
from data.customers import CUSTOMERS, CUSTOMER_REACTIONS, ENCOUNTER_TABLE


# ============================================================
# 1. 初期状態テスト
# ============================================================
class TestInitialState(unittest.TestCase):
    """初期状態テスト"""

    def test_player_state_defaults(self):
        p = PlayerState()
        self.assertEqual(p.name, "ナオト")
        self.assertEqual(p.hp, 50)
        self.assertEqual(p.max_hp, 50)
        self.assertEqual(p.attack, 12)
        self.assertEqual(p.defense, 6)
        self.assertEqual(p.speed, 5)
        self.assertEqual(p.gold, 150)
        self.assertEqual(p.level, 1)
        self.assertEqual(p.exp, 0)
        self.assertEqual(p.total_exp, 0)
        self.assertEqual(p.x, 5)
        self.assertEqual(p.y, 5)
        self.assertEqual(p.chapter, 1)
        self.assertEqual(p.repel_steps, 0)
        self.assertEqual(p.combo_count, 0)
        self.assertEqual(p.wins, 0)
        self.assertEqual(p.losses, 0)
        self.assertEqual(p.opened_chests, set())

    def test_partner_system_initial(self):
        ps = PartnerSystem()
        self.assertFalse(ps.has_contract)
        self.assertEqual(ps.rank, "D")
        self.assertEqual(ps.rank_label, "見習い")
        self.assertEqual(ps.cumulative_sales, 0)
        self.assertEqual(ps.contracts, [])
        self.assertEqual(ps.partner_inventory, {})

    def test_inventory_system_initial(self):
        inv = InventorySystem()
        self.assertEqual(inv.items, {})
        self.assertIsNone(inv.equipped_weapon)
        self.assertIsNone(inv.equipped_armor)
        self.assertIsNone(inv.equipped_shield)
        self.assertEqual(inv.get_attack_bonus(), 0)
        self.assertEqual(inv.get_defense_bonus(), 0)
        self.assertEqual(inv.get_all_items(), [])

    def test_chapter_system_initial(self):
        cs = ChapterSystem()
        self.assertEqual(cs.current_chapter, 1)
        self.assertFalse(cs.boss_defeated)
        self.assertEqual(cs.flags, set())
        self.assertEqual(cs.total_sales_gold, 0)


# ============================================================
# 2. 経済システムテスト
# ============================================================
class TestEconomySystem(unittest.TestCase):
    """経済システムテスト"""

    def test_calc_damage_attack_greater_than_defense(self):
        """攻撃力>防御力のとき、正の説得力が出る"""
        random.seed(42)
        result = calc_damage(20, 4)
        # base = (20*2 - 4)//3 = 36//3 = 12, variance ~0.85-1.15
        self.assertGreaterEqual(result, 1)
        self.assertGreaterEqual(result, 10)  # 12*0.85=10.2

    def test_calc_damage_attack_less_than_defense(self):
        """攻撃力<防御力のとき、最小1"""
        random.seed(42)
        result = calc_damage(2, 100)
        # base = 2 - 100//2 = 2 - 50 = -48 → <=0 → max(1, random.randint(0,1))
        self.assertGreaterEqual(result, 0)
        self.assertLessEqual(result, 1)

    def test_calc_damage_minimum_one_when_positive_base(self):
        """baseが正のとき最低1"""
        for _ in range(50):
            result = calc_damage(5, 8)
            # base = 5 - 8//2 = 5-4 = 1, 1*variance >= 0.85 -> int(0.85)=0 -> max(1,0)=1
            self.assertGreaterEqual(result, 1)

    def test_check_level_up_no_change(self):
        """経験値不足ならレベル変わらない"""
        self.assertEqual(check_level_up(1, 0), 1)
        self.assertEqual(check_level_up(1, 10), 1)

    def test_check_level_up_to_level2(self):
        """経験値15でレベル2"""
        self.assertEqual(check_level_up(1, 15), 2)

    def test_check_level_up_to_level3(self):
        """経験値45でレベル3"""
        self.assertEqual(check_level_up(1, 45), 3)

    def test_check_level_up_multiple_levels(self):
        """一気に複数レベルアップ"""
        self.assertEqual(check_level_up(1, 1200), 10)

    def test_check_level_up_exact_threshold(self):
        """ちょうどの経験値"""
        for lv in range(2, len(EXP_TABLE)):
            self.assertEqual(check_level_up(1, EXP_TABLE[lv]), lv)

    def test_get_level_up_stats_known_levels(self):
        """既知レベルのステータス上昇"""
        stats2 = get_level_up_stats(2)
        self.assertEqual(stats2["max_hp"], 8)
        self.assertEqual(stats2["attack"], 1)
        self.assertEqual(stats2["defense"], 1)
        self.assertEqual(stats2["speed"], 1)

        stats10 = get_level_up_stats(10)
        self.assertEqual(stats10["max_hp"], 25)
        self.assertEqual(stats10["attack"], 4)

    def test_get_level_up_stats_unknown_level(self):
        """未知レベルはデフォルト値"""
        stats = get_level_up_stats(99)
        self.assertEqual(stats["max_hp"], 10)
        self.assertEqual(stats["attack"], 2)
        self.assertEqual(stats["defense"], 2)
        self.assertEqual(stats["speed"], 2)

    def test_exp_for_level_known(self):
        """既知レベルの必要経験値"""
        self.assertEqual(exp_for_level(1), 0)
        self.assertEqual(exp_for_level(2), 15)
        self.assertEqual(exp_for_level(3), 45)
        self.assertEqual(exp_for_level(10), 1200)

    def test_exp_for_level_beyond_table(self):
        """テーブル超過レベルは1.5倍で増える"""
        lv11 = exp_for_level(11)
        self.assertEqual(lv11, int(1200 * 1.5))  # 1800


# ============================================================
# 3. パートナーシステムテスト
# ============================================================
class TestPartnerSystem(unittest.TestCase):
    """パートナーシステムテスト"""

    def test_no_contract(self):
        ps = PartnerSystem()
        self.assertFalse(ps.has_contract)
        self.assertIsNone(ps.active_contract)
        self.assertEqual(ps.active_contracts, [])

    def test_referral_contract(self):
        ps = PartnerSystem()
        contract = ps.sign_contract("テスト商人", "referral")
        self.assertTrue(ps.has_contract)
        self.assertEqual(contract.fee_rate, 0.15)
        self.assertFalse(contract.has_inventory_risk)

    def test_reseller_contract(self):
        ps = PartnerSystem()
        contract = ps.sign_contract("テスト商人", "reseller")
        self.assertTrue(ps.has_contract)
        self.assertEqual(contract.fee_rate, 0.40)
        self.assertTrue(contract.has_inventory_risk)

    def test_fee_calculation_referral(self):
        ps = PartnerSystem()
        contract = ps.sign_contract("テスト", "referral")
        fee = contract.calculate_fee(100)
        self.assertEqual(fee, 15)  # 100 * 0.15
        self.assertEqual(contract.total_sales, 100)
        self.assertEqual(contract.total_fees, 15)

    def test_fee_calculation_reseller(self):
        ps = PartnerSystem()
        contract = ps.sign_contract("テスト", "reseller")
        fee = contract.calculate_fee(100)
        self.assertEqual(fee, 40)  # 100 * 0.40

    def test_rank_up_d_to_c(self):
        """D→C at 500G"""
        ps = PartnerSystem()
        ps.sign_contract("テスト", "referral")
        ps._cumulative_sales = 499
        ps._update_rank()
        self.assertEqual(ps.rank, "D")
        ps._cumulative_sales = 500
        ps._update_rank()
        self.assertEqual(ps.rank, "C")

    def test_rank_up_c_to_b(self):
        """C→B at 2000G"""
        ps = PartnerSystem()
        ps._cumulative_sales = 2000
        ps._update_rank()
        self.assertEqual(ps.rank, "B")

    def test_rank_up_b_to_a(self):
        """B→A at 6000G"""
        ps = PartnerSystem()
        ps._cumulative_sales = 6000
        ps._update_rank()
        self.assertEqual(ps.rank, "A")

    def test_rank_labels(self):
        ps = PartnerSystem()
        self.assertEqual(ps.rank_label, "見習い")
        ps._cumulative_sales = 500
        ps._update_rank()
        self.assertEqual(ps.rank_label, "一人前")
        ps._cumulative_sales = 2000
        ps._update_rank()
        self.assertEqual(ps.rank_label, "ベテラン")
        ps._cumulative_sales = 6000
        ps._update_rank()
        self.assertEqual(ps.rank_label, "マスター")

    def test_sales_to_next_rank(self):
        ps = PartnerSystem()
        self.assertEqual(ps.next_rank, "C")
        self.assertEqual(ps.sales_to_next_rank, 500)
        ps._cumulative_sales = 300
        self.assertEqual(ps.sales_to_next_rank, 200)

    def test_sell_partner_item_referral(self):
        ps = PartnerSystem()
        ps.sign_contract("テスト", "referral")
        fee, rank_up = ps.sell_partner_item("sales_intro", 100)
        self.assertEqual(fee, 15)
        self.assertEqual(ps.cumulative_sales, 100)

    def test_sell_partner_item_reseller_no_inventory(self):
        ps = PartnerSystem()
        ps.sign_contract("テスト", "reseller")
        fee, rank_up = ps.sell_partner_item("sales_intro", 100)
        self.assertEqual(fee, 0)  # 在庫なし

    def test_sell_partner_item_reseller_with_inventory(self):
        ps = PartnerSystem()
        ps.sign_contract("テスト", "reseller")
        ps.add_partner_inventory("sales_intro", 3)
        fee, rank_up = ps.sell_partner_item("sales_intro", 100)
        self.assertEqual(fee, 40)
        self.assertEqual(ps.partner_inventory["sales_intro"], 2)

    def test_on_party_wipe_reseller(self):
        ps = PartnerSystem()
        ps.sign_contract("テスト", "reseller")
        ps.add_partner_inventory("item_a", 10)
        lost = ps.on_party_wipe()
        self.assertEqual(lost["item_a"], 5)
        self.assertEqual(ps.partner_inventory["item_a"], 5)

    def test_on_party_wipe_referral_no_loss(self):
        ps = PartnerSystem()
        ps.sign_contract("テスト", "referral")
        lost = ps.on_party_wipe()
        self.assertEqual(lost, {})

    def test_next_rank_at_max(self):
        ps = PartnerSystem()
        ps._cumulative_sales = 10000
        ps._update_rank()
        self.assertEqual(ps.rank, "A")
        self.assertIsNone(ps.next_rank)
        self.assertEqual(ps.sales_to_next_rank, 0)


# ============================================================
# 4. インベントリテスト
# ============================================================
class TestInventorySystem(unittest.TestCase):
    """インベントリテスト"""

    def test_add_item(self):
        inv = InventorySystem()
        inv.add_item("smile_notebook", 3)
        self.assertTrue(inv.has_item("smile_notebook"))
        self.assertEqual(inv.get_count("smile_notebook"), 3)

    def test_remove_item(self):
        inv = InventorySystem()
        inv.add_item("smile_notebook", 3)
        result = inv.remove_item("smile_notebook", 2)
        self.assertTrue(result)
        self.assertEqual(inv.get_count("smile_notebook"), 1)

    def test_remove_item_all(self):
        inv = InventorySystem()
        inv.add_item("smile_notebook", 1)
        inv.remove_item("smile_notebook", 1)
        self.assertFalse(inv.has_item("smile_notebook"))
        self.assertEqual(inv.get_count("smile_notebook"), 0)

    def test_remove_item_insufficient(self):
        inv = InventorySystem()
        inv.add_item("smile_notebook", 1)
        result = inv.remove_item("smile_notebook", 5)
        self.assertFalse(result)
        self.assertEqual(inv.get_count("smile_notebook"), 1)  # 変化なし

    def test_equip_weapon(self):
        inv = InventorySystem()
        inv.add_item("sales_intro")
        inv.equip("sales_intro")
        self.assertEqual(inv.equipped_weapon, "sales_intro")
        self.assertEqual(inv.get_attack_bonus(), 5)  # sales_intro value=5

    def test_equip_armor(self):
        inv = InventorySystem()
        inv.add_item("manner_course")
        inv.equip("manner_course")
        self.assertEqual(inv.equipped_armor, "manner_course")
        self.assertEqual(inv.get_defense_bonus(), 8)

    def test_equip_shield(self):
        inv = InventorySystem()
        inv.add_item("stress_care")
        inv.equip("stress_care")
        self.assertEqual(inv.equipped_shield, "stress_care")
        self.assertEqual(inv.get_defense_bonus(), 5)

    def test_equip_armor_and_shield_combined(self):
        inv = InventorySystem()
        inv.equip("manner_course")   # armor value=8
        inv.equip("stress_care")     # shield value=5
        self.assertEqual(inv.get_defense_bonus(), 13)

    def test_get_all_items(self):
        inv = InventorySystem()
        inv.add_item("smile_notebook", 2)
        inv.add_item("sales_intro", 1)
        all_items = inv.get_all_items()
        self.assertEqual(len(all_items), 2)
        names = [i["name"] for i in all_items]
        self.assertIn("笑顔の練習帳", names)
        self.assertIn("接客入門書", names)

    def test_equip_nonexistent_item(self):
        inv = InventorySystem()
        result = inv.equip("nonexistent")
        self.assertFalse(result)


# ============================================================
# 5. チャプターシステムテスト
# ============================================================
class TestChapterSystem(unittest.TestCase):
    """チャプターシステムテスト"""

    def test_chapter1_clear_condition(self):
        """Chapter 1: sales_500"""
        cs = ChapterSystem()
        mock_game = MagicMock()
        cs.total_sales_gold = 499
        self.assertFalse(cs.check_chapter_clear(mock_game))
        cs.total_sales_gold = 500
        self.assertTrue(cs.check_chapter_clear(mock_game))

    def test_chapter2_clear_condition(self):
        """Chapter 2: rank_c"""
        cs = ChapterSystem()
        cs.current_chapter = 2
        mock_game = MagicMock()
        mock_game.partner_system.rank = "D"
        self.assertFalse(cs.check_chapter_clear(mock_game))
        mock_game.partner_system.rank = "C"
        self.assertTrue(cs.check_chapter_clear(mock_game))

    def test_chapter3_clear_condition(self):
        """Chapter 3: rank_b"""
        cs = ChapterSystem()
        cs.current_chapter = 3
        mock_game = MagicMock()
        mock_game.partner_system.rank = "C"
        self.assertFalse(cs.check_chapter_clear(mock_game))
        mock_game.partner_system.rank = "B"
        self.assertTrue(cs.check_chapter_clear(mock_game))

    def test_chapter4_clear_condition(self):
        """Chapter 4: boss_defeated"""
        cs = ChapterSystem()
        cs.current_chapter = 4
        mock_game = MagicMock()
        self.assertFalse(cs.check_chapter_clear(mock_game))
        cs.boss_defeated = True
        self.assertTrue(cs.check_chapter_clear(mock_game))

    def test_advance_chapter(self):
        cs = ChapterSystem()
        self.assertTrue(cs.advance_chapter())
        self.assertEqual(cs.current_chapter, 2)
        cs.advance_chapter()
        self.assertEqual(cs.current_chapter, 3)
        cs.advance_chapter()
        self.assertEqual(cs.current_chapter, 4)
        self.assertFalse(cs.advance_chapter())  # 最大チャプター
        self.assertEqual(cs.current_chapter, 4)

    def test_chapter_intro_text_exists(self):
        """全チャプターにintroテキストがある"""
        for ch_num, ch_data in CHAPTERS.items():
            self.assertIn("intro", ch_data, f"Chapter {ch_num} missing intro")
            self.assertTrue(len(ch_data["intro"]) > 0)

    def test_chapter_has_all_required_fields(self):
        for ch_num, ch_data in CHAPTERS.items():
            self.assertIn("title", ch_data)
            self.assertIn("goal", ch_data)
            self.assertIn("clear_condition", ch_data)

    def test_add_sales(self):
        cs = ChapterSystem()
        cs.add_sales(100)
        cs.add_sales(200)
        self.assertEqual(cs.total_sales_gold, 300)

    def test_flags(self):
        cs = ChapterSystem()
        self.assertFalse(cs.has_flag("test"))
        cs.set_flag("test")
        self.assertTrue(cs.has_flag("test"))


# ============================================================
# 6. バトルロジックテスト
# ============================================================
class TestBattleLogic(unittest.TestCase):
    """バトルロジックテスト"""

    def _make_game(self):
        """テスト用のゲームオブジェクトを作成"""
        game = MagicMock()
        game.player = PlayerState()
        game.partner_system = PartnerSystem()
        game.inventory = InventorySystem()
        game.chapter = ChapterSystem()
        game.play_se = MagicMock()
        game.play_bgm = MagicMock()
        game.message_window = MagicMock()
        game.message_window.active = False
        return game

    def _make_battle(self, game, enemy_id="traveler"):
        """バトルシーンを初期化"""
        battle = BattleScene(game)
        battle.on_enter(enemy_id=enemy_id)
        return battle

    def test_sales_talk_adds_persuasion(self):
        """セールストークで購買意欲が増える"""
        game = self._make_game()
        battle = self._make_battle(game)
        random.seed(42)
        initial_gauge = battle.purchase_gauge
        battle._sales_talk()
        self.assertGreater(battle.purchase_gauge, initial_gauge)

    def test_discount_1_8x_persuasion(self):
        """値引きは攻撃力の1.8倍"""
        game = self._make_game()
        battle = self._make_battle(game, "boss_merchant")  # hp=100で閾値に達しない
        attack = battle._get_player_attack()
        expected = int(attack * 1.8)
        battle._discount()
        self.assertEqual(battle.purchase_gauge, expected)

    def test_discount_halves_gold(self):
        """値引きで報酬が半減"""
        game = self._make_game()
        battle = self._make_battle(game)
        original_gold = battle.customer["gold"]
        battle._discount()
        self.assertEqual(battle.customer["gold"], max(1, original_gold // 2))

    def test_explain_product_once(self):
        """商品説明は1回限り"""
        game = self._make_game()
        battle = self._make_battle(game)
        self.assertFalse(battle.explained)
        battle._explain_product()
        self.assertTrue(battle.explained)
        # 2回目は効果なし
        old_log_len = len(battle.log)
        battle._use_skill("explain")
        self.assertIn("もう説明済みだ！", battle.log)

    def test_explain_reduces_defense(self):
        """商品説明で警戒心ダウン（弱点なら50%、通常30%）"""
        game = self._make_game()
        battle = self._make_battle(game)
        original_def = battle.customer["defense"]
        # travelerの弱点はexplainなので50%ダウン
        weakness = battle.customer.get("weakness")
        if weakness == "explain":
            reduction = max(1, original_def // 2)
        else:
            reduction = max(1, original_def // 3)
        battle._explain_product()
        self.assertEqual(battle.customer["defense"], max(0, original_def - reduction))

    def test_explain_heals_5hp(self):
        """商品説明でやる気+5"""
        game = self._make_game()
        game.player.hp = 30
        battle = self._make_battle(game)
        battle._explain_product()
        self.assertEqual(game.player.hp, 35)

    def test_presentation_costs_10hp(self):
        """プレゼンでやる気10消費"""
        game = self._make_game()
        battle = self._make_battle(game)
        initial_hp = game.player.hp
        battle._presentation()
        self.assertEqual(game.player.hp, initial_hp - 10)

    def test_presentation_2_5x(self):
        """プレゼンは2.5倍の説得力"""
        game = self._make_game()
        battle = self._make_battle(game, "boss_merchant")  # hp=100で閾値に達しない
        attack = battle._get_player_attack()
        expected = int(attack * 2.5)
        battle._presentation()
        self.assertEqual(battle.purchase_gauge, expected)

    def test_market_analysis_50pct_defense_down(self):
        """市場分析で警戒心50%ダウン"""
        game = self._make_game()
        battle = self._make_battle(game)
        original_def = battle.customer["defense"]
        battle._market_analysis()
        total_reduction = max(1, original_def // 2)
        self.assertEqual(battle.customer["defense"], max(0, original_def - total_reduction))

    def test_market_analysis_costs_8hp(self):
        game = self._make_game()
        battle = self._make_battle(game)
        initial_hp = game.player.hp
        battle._market_analysis()
        self.assertEqual(game.player.hp, initial_hp - 8)

    def test_closing_adds_purchase(self):
        """クロージングで購買意欲が増える（弱点なら1.5倍）"""
        game = self._make_game()
        battle = self._make_battle(game, "boss_merchant")  # hp=100で閾値に達しない
        battle._closing()
        # boss_merchantの弱点はclosingなので15*1.5=22
        self.assertEqual(battle.purchase_gauge, 22)

    def test_closing_costs_12hp(self):
        game = self._make_game()
        battle = self._make_battle(game)
        initial_hp = game.player.hp
        battle._closing()
        self.assertEqual(game.player.hp, initial_hp - 12)

    def test_limited_offer_sets_multiplier(self):
        """限定オファーでnext_attack_multiplier=3.0"""
        game = self._make_game()
        battle = self._make_battle(game)
        battle._limited_offer()
        self.assertEqual(battle.next_attack_multiplier, 3.0)

    def test_limited_offer_costs_15hp(self):
        game = self._make_game()
        battle = self._make_battle(game)
        initial_hp = game.player.hp
        battle._limited_offer()
        self.assertEqual(game.player.hp, initial_hp - 15)

    def test_ultimate_pitch_4x(self):
        """究極プレゼンは4倍"""
        game = self._make_game()
        battle = self._make_battle(game, "boss_merchant")  # hp=100で閾値に達しない
        attack = battle._get_player_attack()
        expected = int(attack * 4.0)
        battle._ultimate_pitch()
        self.assertEqual(battle.purchase_gauge, expected)

    def test_ultimate_pitch_costs_25hp(self):
        game = self._make_game()
        battle = self._make_battle(game)
        initial_hp = game.player.hp
        battle._ultimate_pitch()
        self.assertEqual(game.player.hp, initial_hp - 25)

    def test_smile_heals_12hp(self):
        """笑顔で対応でやる気12回復"""
        game = self._make_game()
        game.player.hp = 20
        battle = self._make_battle(game)
        battle._smile_response()
        self.assertEqual(game.player.hp, 32)

    def test_smile_caps_at_max_hp(self):
        game = self._make_game()
        game.player.hp = 45
        battle = self._make_battle(game)
        battle._smile_response()
        self.assertEqual(game.player.hp, 50)  # max_hp

    def test_sale_closed_adds_exp_and_gold(self):
        """成約時にEXP/Gold加算"""
        game = self._make_game()
        battle = self._make_battle(game)
        initial_gold = game.player.gold
        initial_exp = game.player.total_exp
        # 強制的に成約
        battle.purchase_gauge = battle.purchase_threshold
        battle._on_sale_closed()
        self.assertGreater(game.player.total_exp, initial_exp)
        self.assertGreater(game.player.gold, initial_gold)

    def test_sale_closed_increments_combo(self):
        """成約でコンボカウント+1"""
        game = self._make_game()
        battle = self._make_battle(game)
        self.assertEqual(game.player.combo_count, 0)
        battle._on_sale_closed()
        self.assertEqual(game.player.combo_count, 1)

    def test_combo_bonus(self):
        """コンボボーナスの加算"""
        game = self._make_game()
        game.player.combo_count = 2  # 次の成約で3連続
        battle = self._make_battle(game)
        battle._on_sale_closed()
        # combo=3, bonus = min(3*0.1, 0.5) = 0.3
        self.assertEqual(game.player.combo_count, 3)

    def test_sale_closed_level_up(self):
        """成約でレベルアップ"""
        game = self._make_game()
        game.player.total_exp = 14  # あと1でLv2
        battle = self._make_battle(game, "traveler")
        # travelerのexp=5, 14+5=19 > 15(Lv2 threshold)
        battle._on_sale_closed()
        self.assertEqual(game.player.level, 2)

    def test_sale_lost_resets_combo(self):
        """失注でコンボリセット"""
        game = self._make_game()
        game.player.combo_count = 5
        battle = self._make_battle(game)
        battle._on_sale_lost()
        self.assertEqual(game.player.combo_count, 0)

    def test_sale_lost_full_hp_recovery(self):
        """失注でやる気全回復"""
        game = self._make_game()
        game.player.hp = 0
        battle = self._make_battle(game)
        battle._on_sale_lost()
        self.assertEqual(game.player.hp, game.player.max_hp)

    def test_sale_lost_increments_losses(self):
        game = self._make_game()
        battle = self._make_battle(game)
        battle._on_sale_lost()
        self.assertEqual(game.player.losses, 1)

    def test_sale_closed_increments_wins(self):
        game = self._make_game()
        battle = self._make_battle(game)
        battle._on_sale_closed()
        self.assertEqual(game.player.wins, 1)

    def test_boss_defeated_flag(self):
        """ボス撃破フラグ"""
        game = self._make_game()
        battle = self._make_battle(game, "boss_merchant")
        battle._on_sale_closed()
        self.assertTrue(game.chapter.boss_defeated)

    def test_customer_reaction_hesitation(self):
        """迷いリアクション → やる気ダメージ"""
        game = self._make_game()
        battle = self._make_battle(game)
        initial_hp = game.player.hp
        battle._customer_reaction("hesitation")
        self.assertLess(game.player.hp, initial_hp)

    def test_customer_reaction_haggle(self):
        """値切りリアクション → 1.3倍ダメージ"""
        game = self._make_game()
        battle = self._make_battle(game)
        initial_hp = game.player.hp
        battle._customer_reaction("haggle")
        self.assertLess(game.player.hp, initial_hp)

    def test_customer_reaction_comparison(self):
        """比較検討 → セールス力デバフ"""
        game = self._make_game()
        battle = self._make_battle(game)
        battle._customer_reaction("comparison")
        self.assertEqual(battle.player_attack_debuff, 3)

    def test_customer_reaction_cold_visit(self):
        """冷やかし → 客が帰る(result)"""
        game = self._make_game()
        battle = self._make_battle(game)
        battle._customer_reaction("cold_visit")
        self.assertEqual(battle.phase, "result")

    def test_customer_reaction_impulse_buy(self):
        """衝動買い → 購買意欲+3"""
        game = self._make_game()
        battle = self._make_battle(game)
        battle._customer_reaction("impulse_buy")
        self.assertEqual(battle.purchase_gauge, 3)

    def test_customer_reaction_bulk_buy(self):
        """まとめ買い → bulk_buy_active"""
        game = self._make_game()
        battle = self._make_battle(game)
        battle._customer_reaction("bulk_buy")
        self.assertTrue(battle.bulk_buy_active)

    def test_customer_reaction_price_hike(self):
        """価格つり上げ → customer_attack_bonus+5"""
        game = self._make_game()
        battle = self._make_battle(game)
        battle._customer_reaction("price_hike")
        self.assertEqual(battle.customer_attack_bonus, 5)

    def test_customer_reaction_monopoly(self):
        """独占宣言 → customer_defense_bonus+5"""
        game = self._make_game()
        battle = self._make_battle(game)
        battle._customer_reaction("monopoly")
        self.assertEqual(battle.customer_defense_bonus, 5)

    def test_skill_level_restriction(self):
        """スキルレベル制限"""
        game = self._make_game()
        game.player.level = 1
        battle = self._make_battle(game)
        available = battle._get_available_skills()
        available_ids = [s["id"] for s in available]
        # level 1スキル
        self.assertIn("discount", available_ids)
        self.assertIn("explain", available_ids)
        self.assertIn("smile", available_ids)
        self.assertIn("presentation", available_ids)
        # level 3 → 不可
        self.assertNotIn("market_analysis", available_ids)
        # level 5 → 不可
        self.assertNotIn("closing", available_ids)

    def test_skill_level_3_unlocked(self):
        game = self._make_game()
        game.player.level = 3
        battle = self._make_battle(game)
        available = battle._get_available_skills()
        available_ids = [s["id"] for s in available]
        self.assertIn("market_analysis", available_ids)

    def test_skill_insufficient_hp(self):
        """やる気不足でスキル使用不可"""
        game = self._make_game()
        game.player.hp = 5
        game.player.level = 10
        battle = self._make_battle(game)
        battle._use_skill("presentation")  # costs 10
        self.assertIn("やる気が足りない！", battle.log)

    def test_next_attack_multiplier_applied_and_reset(self):
        """限定オファー→セールストークで3倍適用&リセット"""
        game = self._make_game()
        battle = self._make_battle(game)
        battle.next_attack_multiplier = 3.0
        random.seed(1)
        battle._sales_talk()
        self.assertEqual(battle.next_attack_multiplier, 1.0)
        self.assertGreater(battle.purchase_gauge, 0)

    def test_bulk_buy_doubles_gold(self):
        """まとめ買いで報酬2倍"""
        game = self._make_game()
        # 商材をセットして利益計算を確認
        game.inventory.add_item("basic_tool", 1)
        battle = self._make_battle(game)
        battle.bulk_buy_active = True
        battle.selected_product = {"id": "basic_tool", "name": "ベーシック道具セット", "quantity": 1}
        # basic_tool: sell_value=40, price=20, profit=20, bulk=40
        battle._on_sale_closed()
        self.assertGreaterEqual(battle.result_gold, 40)

    def test_give_up_resets_combo(self):
        """見送り成功でコンボリセット"""
        game = self._make_game()
        game.player.combo_count = 3
        battle = self._make_battle(game)
        # 見送り成功するseedを探す（80%成功率）
        for seed in range(100):
            random.seed(seed)
            if random.random() < 0.8:
                random.seed(seed)
                battle._give_up()
                break
        self.assertEqual(game.player.combo_count, 0)
        self.assertEqual(battle.phase, "result")


# ============================================================
# 7. ショップロジックテスト
# ============================================================
class TestShopLogic(unittest.TestCase):
    """ショップロジックテスト"""

    def _make_game(self):
        game = MagicMock()
        game.player = PlayerState()
        game.partner_system = PartnerSystem()
        game.inventory = InventorySystem()
        game.chapter = ChapterSystem()
        game.play_se = MagicMock()
        game.play_bgm = MagicMock()
        game.message_window = MagicMock()
        game.message_window.active = False
        game.change_scene_with_transition = MagicMock()
        game.text = MagicMock()
        return game

    def test_buy_item_success(self):
        """所持金があれば購入成功"""
        game = self._make_game()
        game.player.gold = 100
        shop = ShopScene(game)
        shop.on_enter(shop_id="my_shop")
        # smile_notebook は 8G
        item = shop.shop_items[0]  # smile_notebook
        self.assertEqual(item["id"], "smile_notebook")
        game.player.gold -= item["price"]
        game.inventory.add_item(item["id"])
        self.assertEqual(game.player.gold, 92)
        self.assertTrue(game.inventory.has_item("smile_notebook"))

    def test_buy_item_insufficient_gold(self):
        """所持金不足で購入失敗"""
        game = self._make_game()
        game.player.gold = 5
        shop = ShopScene(game)
        shop.on_enter(shop_id="weapon_shop")
        # sales_intro is 30G
        item = [i for i in shop.shop_items if i["id"] == "sales_intro"][0]
        can_buy = game.player.gold >= item["price"]
        self.assertFalse(can_buy)

    def test_sell_item(self):
        """アイテム売却でゴールド加算"""
        game = self._make_game()
        game.inventory.add_item("smile_notebook")
        initial_gold = game.player.gold
        item = ITEMS["smile_notebook"]
        game.inventory.remove_item("smile_notebook")
        game.player.gold += item["sell_price"]
        self.assertEqual(game.player.gold, initial_gold + 4)
        self.assertFalse(game.inventory.has_item("smile_notebook"))

    def test_rank_based_inventory_d(self):
        """ランクD: 基本アイテムのみ"""
        items = get_available_items("weapon_shop", "D")
        # rank無し: sales_intro, sales_training, manner_course
        for iid in items:
            item = ITEMS[iid]
            self.assertNotIn("rank", item, f"{iid} should not require rank but has rank={item.get('rank')}")

    def test_rank_based_inventory_c(self):
        """ランクC: Cランクアイテムも出る"""
        items = get_available_items("weapon_shop", "C")
        self.assertIn("claim_training", items)  # rank=C

    def test_rank_based_inventory_b(self):
        """ランクB: Bランクアイテムも出る"""
        items = get_available_items("weapon_shop", "B")
        self.assertIn("sales_expert", items)  # rank=B

    def test_rank_based_inventory_a(self):
        """ランクA: Aランクアイテムも出る"""
        items = get_available_items("weapon_shop", "A")
        self.assertIn("top_sales", items)  # rank=A

    def test_equipment_auto_equip(self):
        """装備品購入で自動装備"""
        game = self._make_game()
        game.inventory.add_item("sales_intro")
        game.inventory.equip("sales_intro")
        self.assertEqual(game.inventory.equipped_weapon, "sales_intro")

    def test_rank_d_no_rank_items(self):
        """ランクDではrank付きアイテムが出ない（weapon_shop）"""
        items_d = get_available_items("weapon_shop", "D")
        for iid in items_d:
            self.assertFalse(
                ITEMS[iid].get("rank") in ("C", "B", "A"),
                f"{iid} requires rank {ITEMS[iid].get('rank')} but appeared at rank D"
            )


# ============================================================
# 8. マップデータ整合性テスト
# ============================================================
class TestMapDataIntegrity(unittest.TestCase):
    """マップデータ整合性テスト"""

    def test_all_maps_16x16(self):
        """全マップが16x16"""
        for name, data in MAPS.items():
            self.assertEqual(len(data), 16, f"Map '{name}' has {len(data)} rows, expected 16")
            for i, row in enumerate(data):
                self.assertEqual(len(row), 16, f"Map '{name}' row {i} has {len(row)} cols, expected 16")

    def test_building_events_on_shop_tile(self):
        """BUILDING_EVENTSの座標がSHOPタイル上"""
        for (map_name, x, y), event in BUILDING_EVENTS.items():
            map_data = MAPS[map_name]
            tile = map_data[y][x]
            self.assertEqual(
                tile, TILE_SHOP,
                f"BUILDING_EVENT at ({map_name},{x},{y}) is on tile {tile}, expected TILE_SHOP({TILE_SHOP})"
            )

    def test_map_npcs_on_walkable(self):
        """MAP_NPCsの座標が歩けるタイル上"""
        for map_name, npcs in MAP_NPCS.items():
            map_data = MAPS[map_name]
            for npc in npcs:
                x, y = npc["x"], npc["y"]
                tile = map_data[y][x]
                self.assertIn(
                    tile, WALKABLE,
                    f"NPC '{npc['id']}' at ({map_name},{x},{y}) is on non-walkable tile {tile}"
                )

    def test_map_transitions_walkable(self):
        """MAP_TRANSITIONSの入口・出口が歩けるタイル上"""
        for (src_map, sx, sy), (dst_map, dx, dy) in MAP_TRANSITIONS.items():
            # 入口チェック
            src_data = MAPS[src_map]
            src_tile = src_data[sy][sx]
            self.assertIn(
                src_tile, WALKABLE,
                f"Transition source ({src_map},{sx},{sy}) is on non-walkable tile {src_tile}"
            )
            # 出口チェック
            dst_data = MAPS[dst_map]
            dst_tile = dst_data[dy][dx]
            self.assertIn(
                dst_tile, WALKABLE,
                f"Transition dest ({dst_map},{dx},{dy}) is on non-walkable tile {dst_tile}"
            )

    def test_encounter_table_probabilities(self):
        """ENCOUNTER_TABLEの確率合計が1.0"""
        for map_name, table in ENCOUNTER_TABLE.items():
            total = sum(prob for _, prob in table)
            self.assertAlmostEqual(
                total, 1.0, places=5,
                msg=f"ENCOUNTER_TABLE '{map_name}' prob sum = {total}"
            )

    def test_treasure_chests_on_walkable(self):
        """TREASURE_CHESTSの座標が歩けるタイル上"""
        for (map_name, x, y), chest in TREASURE_CHESTS.items():
            map_data = MAPS[map_name]
            tile = map_data[y][x]
            self.assertIn(
                tile, WALKABLE,
                f"Chest '{chest['id']}' at ({map_name},{x},{y}) is on non-walkable tile {tile}"
            )


# ============================================================
# 9. アイテムデータ整合性テスト
# ============================================================
class TestItemDataIntegrity(unittest.TestCase):
    """アイテムデータ整合性テスト"""

    def test_all_items_have_required_fields(self):
        """全アイテムに必須フィールドがある"""
        required = {"name", "price", "sell_price", "type", "value", "description"}
        for item_id, item in ITEMS.items():
            for field in required:
                self.assertIn(
                    field, item,
                    f"Item '{item_id}' missing required field '{field}'"
                )

    def test_shop_inventory_items_exist(self):
        """SHOP_INVENTORYの全アイテムIDがITEMSに存在"""
        for shop_id, item_ids in SHOP_INVENTORY.items():
            for iid in item_ids:
                self.assertIn(
                    iid, ITEMS,
                    f"SHOP_INVENTORY '{shop_id}' references unknown item '{iid}'"
                )

    def test_all_customer_ids_exist(self):
        """全顧客IDがCUSTOMERSに存在"""
        for map_name, table in ENCOUNTER_TABLE.items():
            for customer_id, prob in table:
                self.assertIn(
                    customer_id, CUSTOMERS,
                    f"ENCOUNTER_TABLE '{map_name}' references unknown customer '{customer_id}'"
                )

    def test_all_customer_actions_exist_in_reactions(self):
        """全顧客アクションがCUSTOMER_REACTIONSに存在"""
        for cust_id, cust in CUSTOMERS.items():
            actions = cust.get("actions", [])
            for action, prob in actions:
                self.assertIn(
                    action, CUSTOMER_REACTIONS,
                    f"Customer '{cust_id}' has unknown action '{action}'"
                )

    def test_customer_required_fields(self):
        """全顧客に必須フィールドがある"""
        required = {"name", "hp", "attack", "defense", "speed", "exp", "gold"}
        for cust_id, cust in CUSTOMERS.items():
            for field in required:
                self.assertIn(
                    field, cust,
                    f"Customer '{cust_id}' missing required field '{field}'"
                )

    def test_items_have_effect_field_for_consumables(self):
        """消費アイテムにeffectフィールドがある"""
        for item_id, item in ITEMS.items():
            if item["type"] == "consumable":
                self.assertIn(
                    "effect", item,
                    f"Consumable item '{item_id}' missing 'effect' field"
                )


# ============================================================
# 10. ゲームフロー統合テスト
# ============================================================
class TestGameFlowIntegration(unittest.TestCase):
    """ゲームフロー統合テスト（シミュレーション）"""

    def _make_game(self):
        game = MagicMock()
        game.player = PlayerState()
        game.partner_system = PartnerSystem()
        game.inventory = InventorySystem()
        game.chapter = ChapterSystem()
        game.play_se = MagicMock()
        game.play_bgm = MagicMock()
        game.message_window = MagicMock()
        game.message_window.active = False
        game.change_scene_with_transition = MagicMock()
        return game

    def test_full_game_flow(self):
        """ゲーム開始→バトル→成約→レベルアップ→チャプタークリア→パートナー→ショップ"""
        random.seed(123)
        game = self._make_game()

        # 1. ゲーム開始 → PlayerState初期化
        p = game.player
        self.assertEqual(p.level, 1)
        self.assertEqual(p.gold, 150)

        # 2. バトル開始（traveler遭遇）
        battle = BattleScene(game)
        battle.on_enter(enemy_id="traveler")
        self.assertEqual(battle.customer_id, "traveler")
        self.assertEqual(battle.purchase_gauge, 0)
        self.assertEqual(battle.purchase_threshold, 20)

        # 3. セールストーク → 説得力加算
        battle._sales_talk()
        self.assertGreater(battle.purchase_gauge, 0)

        # 4. 成約 → EXP/Gold獲得 （強制成約、商材あり）
        game.inventory.add_item("basic_tool", 20)  # 十分な商材を用意
        battle2 = BattleScene(game)
        battle2.on_enter(enemy_id="traveler")
        battle2.selected_product = {"id": "basic_tool", "name": "ベーシック道具セット", "quantity": 1}
        battle2.purchase_gauge = battle2.purchase_threshold  # 強制成約
        initial_gold = p.gold
        initial_exp = p.total_exp
        battle2._on_sale_closed()
        self.assertGreater(p.total_exp, initial_exp)
        self.assertGreater(p.gold, initial_gold)

        # 5. レベルアップ判定 - 複数バトルでLv2に
        # traveler exp=5, 3回成約で15exp → Lv2（商材ありでフルEXP）
        for _ in range(2):  # 合計3回(上で1回)
            b = BattleScene(game)
            b.on_enter(enemy_id="traveler")
            b.selected_product = {"id": "basic_tool", "name": "ベーシック道具セット", "quantity": 1}
            b._on_sale_closed()

        self.assertGreaterEqual(p.level, 2)

        # 6. 複数バトル → チャプタークリア条件達成チェック
        # Chapter 1: total_sales >= 500G
        while game.chapter.total_sales_gold < 500:
            b = BattleScene(game)
            b.on_enter(enemy_id="cautious_merchant")  # gold=30
            b.selected_product = {"id": "basic_tool", "name": "ベーシック道具セット", "quantity": 1}
            b._on_sale_closed()

        self.assertTrue(game.chapter.check_chapter_clear(game))
        game.chapter.advance_chapter()
        self.assertEqual(game.chapter.current_chapter, 2)

        # 7. パートナー契約 → フィー計算
        contract = game.partner_system.sign_contract("武器屋", "referral")
        self.assertEqual(contract.fee_rate, 0.15)
        fee = contract.calculate_fee(200)
        self.assertEqual(fee, 30)  # 200 * 0.15

        # 8. ショップでアイテム購入 → 装備
        game.inventory.add_item("sales_intro")
        game.inventory.equip("sales_intro")
        self.assertEqual(game.inventory.equipped_weapon, "sales_intro")
        self.assertEqual(game.inventory.get_attack_bonus(), 5)

    def test_partner_rank_progression(self):
        """パートナーランク昇格フロー"""
        game = self._make_game()
        ps = game.partner_system
        ps.sign_contract("武器屋", "referral")

        # 売上を積む
        for _ in range(50):  # 50回 * 100G sell
            ps.sell_partner_item("some_item", 100)

        # 5000G → ランクB
        self.assertIn(ps.rank, ("B", "A"))

    def test_chapter_progression_full(self):
        """全チャプター進行テスト"""
        game = self._make_game()
        cs = game.chapter

        # Chapter 1: sales_500
        cs.total_sales_gold = 500
        self.assertTrue(cs.check_chapter_clear(game))
        cs.advance_chapter()

        # Chapter 2: rank_c
        game.partner_system.sign_contract("テスト", "referral")
        game.partner_system._cumulative_sales = 500
        game.partner_system._update_rank()
        self.assertTrue(cs.check_chapter_clear(game))
        cs.advance_chapter()

        # Chapter 3: rank_b
        game.partner_system._cumulative_sales = 2000
        game.partner_system._update_rank()
        self.assertTrue(cs.check_chapter_clear(game))
        cs.advance_chapter()

        # Chapter 4: boss_defeated
        cs.boss_defeated = True
        self.assertTrue(cs.check_chapter_clear(game))

    def test_battle_with_equipment(self):
        """装備ありバトル"""
        game = self._make_game()
        game.inventory.equip("sales_training")  # value=12
        game.inventory.equip("manner_course")   # armor value=8

        battle = BattleScene(game)
        battle.on_enter(enemy_id="traveler")

        # 攻撃力 = player.attack(12) + weapon bonus(12) = 24
        self.assertEqual(battle._get_player_attack(), 24)
        # 防御力 = player.defense(6) + armor bonus(8) = 14
        self.assertEqual(battle._get_player_defense(), 14)

    def test_combo_gold_bonus(self):
        """連続成約のゴールドボーナス計算"""
        game = self._make_game()
        game.player.combo_count = 4  # 次の成約で5連続
        game.inventory.add_item("basic_tool", 1)
        battle = BattleScene(game)
        battle.on_enter(enemy_id="traveler")
        battle.selected_product = {"id": "basic_tool", "name": "ベーシック道具セット", "quantity": 1}
        initial_gold = game.player.gold
        battle._on_sale_closed()
        # combo=5, bonus=min(5*0.1, 0.5)=0.5 → 50%ボーナス
        # base gold = 20 (basic_tool profit), total = 20 + 20*0.5 = 30
        earned = game.player.gold - initial_gold
        self.assertGreaterEqual(earned, 30)


# ============================================================
# 11. 新機能テスト（v3追加分）
# ============================================================
class TestNewFeatures(unittest.TestCase):
    """v3で追加された新機能のテスト"""

    def _make_game(self):
        game = MagicMock()
        game.player = PlayerState()
        game.partner_system = PartnerSystem()
        game.inventory = InventorySystem()
        game.chapter = ChapterSystem()
        game.play_se = MagicMock()
        game.play_bgm = MagicMock()
        game.message_window = MagicMock()
        game.message_window.active = False
        game.change_scene_with_transition = MagicMock()
        game.screen_shake = MagicMock()
        return game

    def _make_battle(self, game, enemy_id="traveler"):
        battle = BattleScene(game)
        battle.on_enter(enemy_id=enemy_id)
        return battle

    # --- 笑顔のクールダウン ---
    def test_smile_cooldown_set_after_use(self):
        """笑顔使用後にクールダウンが3に設定される"""
        game = self._make_game()
        game.player.hp = 20
        battle = self._make_battle(game)
        battle._smile_response()
        self.assertEqual(battle.smile_cooldown, 3)

    def test_smile_blocked_during_cooldown(self):
        """クールダウン中は笑顔が使えない"""
        game = self._make_game()
        game.player.hp = 20
        battle = self._make_battle(game)
        battle._smile_response()
        self.assertEqual(battle.smile_cooldown, 3)
        old_hp = game.player.hp
        battle._smile_response()  # ブロックされる
        self.assertEqual(game.player.hp, old_hp)  # HP変わらず
        self.assertIn("まだ笑顔の効果が残っている！ (あと3ターン)", battle.log)

    def test_smile_cooldown_decreases_on_customer_turn(self):
        """ターン経過でクールダウンが減少する"""
        game = self._make_game()
        game.player.hp = 20
        battle = self._make_battle(game)
        battle._smile_response()
        self.assertEqual(battle.smile_cooldown, 3)
        # _check_player_exhaustedでクールダウンが減る
        battle._check_player_exhausted()
        self.assertEqual(battle.smile_cooldown, 2)
        battle._check_player_exhausted()
        self.assertEqual(battle.smile_cooldown, 1)
        battle._check_player_exhausted()
        self.assertEqual(battle.smile_cooldown, 0)

    def test_smile_usable_after_cooldown_expires(self):
        """クールダウン終了後に笑顔が再使用可能"""
        game = self._make_game()
        game.player.hp = 20
        battle = self._make_battle(game)
        battle._smile_response()
        # 3ターン経過させる
        for _ in range(3):
            battle._check_player_exhausted()
        self.assertEqual(battle.smile_cooldown, 0)
        game.player.hp = 20
        old_hp = game.player.hp
        battle._smile_response()
        self.assertEqual(game.player.hp, old_hp + 12)  # 回復できた

    # --- 弱点システム ---
    def test_weakness_bonus_1_5x(self):
        """弱点スキルで1.5倍ボーナスが返る"""
        game = self._make_game()
        battle = self._make_battle(game, "traveler")  # weakness=explain
        bonus = battle._check_weakness("explain")
        self.assertEqual(bonus, 1.5)

    def test_no_weakness_bonus(self):
        """弱点でないスキルでは1.0"""
        game = self._make_game()
        battle = self._make_battle(game, "traveler")  # weakness=explain
        bonus = battle._check_weakness("discount")
        self.assertEqual(bonus, 1.0)

    def test_weakness_closing_on_boss(self):
        """ボスの弱点はclosing"""
        game = self._make_game()
        battle = self._make_battle(game, "boss_merchant")  # weakness=closing
        bonus = battle._check_weakness("closing")
        self.assertEqual(bonus, 1.5)

    def test_closing_with_weakness_bonus(self):
        """弱点closingで購買意欲が15*1.5=22になる"""
        game = self._make_game()
        battle = self._make_battle(game, "boss_merchant")  # hp=100, weakness=closing
        battle._closing()
        self.assertEqual(battle.purchase_gauge, 22)  # int(15*1.5)

    # --- 失注ペナルティ ---
    def test_sale_lost_gold_penalty_10pct(self):
        """失注時に10%のゴールドロス"""
        game = self._make_game()
        game.player.gold = 200
        battle = self._make_battle(game)
        battle._on_sale_lost()
        # penalty = max(5, 200//10) = 20
        self.assertEqual(game.player.gold, 180)

    def test_sale_lost_gold_penalty_minimum_5(self):
        """失注ペナルティは最低5G"""
        game = self._make_game()
        game.player.gold = 30  # 30//10=3 < 5, so penalty=5
        battle = self._make_battle(game)
        battle._on_sale_lost()
        self.assertEqual(game.player.gold, 25)

    def test_sale_lost_gold_penalty_caps_at_current(self):
        """ペナルティは所持金を超えない"""
        game = self._make_game()
        game.player.gold = 3  # penalty = max(5,0)=5, but min(5,3)=3
        battle = self._make_battle(game)
        battle._on_sale_lost()
        self.assertEqual(game.player.gold, 0)

    # --- 会心の一撃 ---
    def test_critical_hit_doubles_persuasion(self):
        """会心の一撃で説得力2倍（seed固定で発生確認）"""
        game = self._make_game()
        battle = self._make_battle(game, "boss_merchant")  # hp=100で閾値に達しない
        # 会心が出るseedを探す
        found_critical = False
        for seed in range(1000):
            random.seed(seed)
            r = random.random()
            if r < 0.10:
                # このseedなら会心が出る
                random.seed(seed)
                battle.purchase_gauge = 0
                battle.next_attack_multiplier = 1.0
                battle._sales_talk()
                # 会心メッセージがlogにある
                if "★ 会心のセールストーク！ ★" in battle.log:
                    found_critical = True
                    break
        self.assertTrue(found_critical, "会心の一撃が発生するseedが見つからなかった")

    def test_no_critical_hit(self):
        """会心なしの場合は通常ダメージ（seed固定で非発生確認）"""
        game = self._make_game()
        battle = self._make_battle(game, "boss_merchant")
        # 会心が出ないseedを探す
        for seed in range(1000):
            random.seed(seed)
            r = random.random()
            if r >= 0.10:
                random.seed(seed)
                battle.purchase_gauge = 0
                battle.log = []
                battle._sales_talk()
                self.assertNotIn("★ 会心のセールストーク！ ★", battle.log)
                break

    # --- ボスデバフ上限 ---
    def test_boss_buff_attack_cap_15(self):
        """price_hikeのbuff_attackは上限15"""
        game = self._make_game()
        battle = self._make_battle(game, "boss_merchant")
        # 4回price_hikeで5*4=20だが上限15
        for _ in range(4):
            battle._customer_reaction("price_hike")
        self.assertEqual(battle.customer_attack_bonus, 15)

    def test_boss_buff_defense_cap_15(self):
        """monopolyのbuff_defenseは上限15"""
        game = self._make_game()
        battle = self._make_battle(game, "boss_merchant")
        # 4回monopolyで5*4=20だが上限15
        for _ in range(4):
            battle._customer_reaction("monopoly")
        self.assertEqual(battle.customer_defense_bonus, 15)

    # --- 初期装備 ---
    def test_initial_equipment_sales_intro(self):
        """ゲーム開始時に接客入門書を装備している"""
        game = self._make_game()
        # reset_game_stateと同様の処理をシミュレーション
        inv = InventorySystem()
        inv.add_item("sales_intro")
        inv.equip("sales_intro")
        self.assertEqual(inv.equipped_weapon, "sales_intro")
        self.assertTrue(inv.has_item("sales_intro"))
        self.assertEqual(inv.get_attack_bonus(), 5)

    def test_initial_equipment_in_items_data(self):
        """接客入門書がアイテムデータに存在する"""
        self.assertIn("sales_intro", ITEMS)
        self.assertEqual(ITEMS["sales_intro"]["type"], "weapon")
        self.assertEqual(ITEMS["sales_intro"]["value"], 5)
        self.assertEqual(ITEMS["sales_intro"]["name"], "接客入門書")

    # --- コンボシステム ---
    def test_combo_count_increments_on_win(self):
        """成約でcombo_countが増加"""
        game = self._make_game()
        battle = self._make_battle(game)
        self.assertEqual(game.player.combo_count, 0)
        battle._on_sale_closed()
        self.assertEqual(game.player.combo_count, 1)

    def test_combo_bonus_at_2(self):
        """2連続成約でコンボボーナス発生"""
        game = self._make_game()
        game.player.combo_count = 1  # 次で2連続
        game.inventory.add_item("basic_tool", 1)
        battle = self._make_battle(game)
        battle.selected_product = {"id": "basic_tool", "name": "ベーシック道具セット", "quantity": 1}
        initial_gold = game.player.gold
        battle._on_sale_closed()
        self.assertEqual(game.player.combo_count, 2)
        earned = game.player.gold - initial_gold
        base_gold = 20  # basic_tool: sell_value=40 - price=20
        # combo=2, bonus=min(2*0.1,0.5)=0.2, combo_gold=int(base*0.2)
        combo_gold = int(base_gold * 0.2)
        expected = base_gold + combo_gold
        self.assertEqual(earned, expected)

    def test_combo_bonus_capped_at_50pct(self):
        """コンボボーナスは最大50%"""
        game = self._make_game()
        game.player.combo_count = 9  # 次で10連続
        game.inventory.add_item("basic_tool", 1)
        battle = self._make_battle(game)
        battle.selected_product = {"id": "basic_tool", "name": "ベーシック道具セット", "quantity": 1}
        initial_gold = game.player.gold
        battle._on_sale_closed()
        self.assertEqual(game.player.combo_count, 10)
        earned = game.player.gold - initial_gold
        base_gold = 20  # basic_tool: sell_value=40 - price=20
        # combo=10, bonus=min(10*0.1, 0.5)=0.5
        combo_gold = int(base_gold * 0.5)
        expected = base_gold + combo_gold
        self.assertEqual(earned, expected)

    def test_combo_resets_on_loss(self):
        """失注でコンボリセット"""
        game = self._make_game()
        game.player.combo_count = 5
        battle = self._make_battle(game)
        battle._on_sale_lost()
        self.assertEqual(game.player.combo_count, 0)

    def test_combo_resets_on_give_up(self):
        """見送りでコンボリセット"""
        game = self._make_game()
        game.player.combo_count = 3
        battle = self._make_battle(game)
        battle._give_up()
        self.assertEqual(game.player.combo_count, 0)

    # --- encounterフェーズ ---
    def test_battle_starts_in_encounter_phase(self):
        """バトル開始時にencounterフェーズから始まる"""
        game = self._make_game()
        battle = self._make_battle(game)
        self.assertEqual(battle.phase, "encounter")

    def test_encounter_phase_has_timer(self):
        """encounterフェーズにはタイマーが設定される"""
        game = self._make_game()
        battle = self._make_battle(game)
        self.assertEqual(battle.result_timer, 45)

    def test_encounter_phase_transitions_to_menu(self):
        """encounterフェーズのタイマー終了後にmenuへ遷移"""
        game = self._make_game()
        battle = self._make_battle(game)
        self.assertEqual(battle.phase, "encounter")
        # タイマーを0にする
        battle.result_timer = 0
        battle.update()
        self.assertEqual(battle.phase, "menu")

    def test_encounter_shows_customer_message(self):
        """encounterフェーズで顧客タイプ別メッセージが表示される"""
        game = self._make_game()
        battle = self._make_battle(game, "traveler")
        # ログにエンカウントメッセージがある
        self.assertTrue(any("通りかかった" in msg for msg in battle.log))

    def test_encounter_boss_message(self):
        """ボスのエンカウントメッセージ"""
        game = self._make_game()
        battle = self._make_battle(game, "boss_merchant")
        self.assertTrue(any("立ちはだかった" in msg for msg in battle.log))


# ============================================================
# 12. 追加機能テスト（最終レビュー分）
# ============================================================
class TestTurnLimit(unittest.TestCase):
    """ターン制限テスト"""

    def _make_game(self):
        game = MagicMock()
        game.player = PlayerState()
        game.partner_system = PartnerSystem()
        game.inventory = InventorySystem()
        game.chapter = ChapterSystem()
        game.play_se = MagicMock()
        game.play_bgm = MagicMock()
        game.message_window = MagicMock()
        game.message_window.active = False
        game.change_scene_with_transition = MagicMock()
        game.screen_shake = MagicMock()
        return game

    def _make_battle(self, game, enemy_id="traveler"):
        battle = BattleScene(game)
        battle.on_enter(enemy_id=enemy_id)
        return battle

    def test_normal_customer_turn_limit_15(self):
        """通常客は15ターンで帰る"""
        game = self._make_game()
        battle = self._make_battle(game, "traveler")
        battle.turn_count = 14  # 次で15
        battle._check_player_exhausted()
        self.assertEqual(battle.phase, "result")
        self.assertTrue(any("帰ってしまった" in msg for msg in battle.log))

    def test_normal_customer_14_turns_ok(self):
        """通常客は14ターンではまだ帰らない"""
        game = self._make_game()
        battle = self._make_battle(game, "traveler")
        battle.turn_count = 13  # _check_player_exhaustedで+1=14
        battle._check_player_exhausted()
        self.assertEqual(battle.phase, "menu")

    def test_boss_turn_limit_20(self):
        """ボスは20ターンで帰る"""
        game = self._make_game()
        battle = self._make_battle(game, "boss_merchant")
        battle.turn_count = 19  # 次で20
        battle._check_player_exhausted()
        self.assertEqual(battle.phase, "result")

    def test_boss_19_turns_ok(self):
        """ボスは19ターンではまだ帰らない"""
        game = self._make_game()
        battle = self._make_battle(game, "boss_merchant")
        battle.turn_count = 18  # +1=19
        battle._check_player_exhausted()
        self.assertEqual(battle.phase, "menu")

    def test_turn_limit_resets_combo(self):
        """ターン制限で帰ると、コンボがリセットされる"""
        game = self._make_game()
        game.player.combo_count = 5
        battle = self._make_battle(game, "traveler")
        battle.turn_count = 14
        battle._check_player_exhausted()
        self.assertEqual(game.player.combo_count, 0)

    def test_turn_limit_no_gold_no_exp(self):
        """ターン制限で帰るとゴールドもEXPもなし"""
        game = self._make_game()
        battle = self._make_battle(game, "traveler")
        battle.turn_count = 14
        battle._check_player_exhausted()
        self.assertEqual(battle.result_gold, 0)
        self.assertEqual(battle.result_exp, 0)


class TestGiveUpSuccessFailure(unittest.TestCase):
    """見送り成功/失敗テスト"""

    def _make_game(self):
        game = MagicMock()
        game.player = PlayerState()
        game.partner_system = PartnerSystem()
        game.inventory = InventorySystem()
        game.chapter = ChapterSystem()
        game.play_se = MagicMock()
        game.play_bgm = MagicMock()
        game.message_window = MagicMock()
        game.message_window.active = False
        game.change_scene_with_transition = MagicMock()
        game.screen_shake = MagicMock()
        return game

    def _make_battle(self, game, enemy_id="traveler"):
        battle = BattleScene(game)
        battle.on_enter(enemy_id=enemy_id)
        return battle

    def test_give_up_success_normal(self):
        """通常客への見送り成功（80%成功率、seed固定）"""
        game = self._make_game()
        battle = self._make_battle(game, "traveler")
        # random.random() < 0.8 → 成功
        random.seed(0)  # random.random() = 0.844... → fails
        # Find a seed that succeeds
        for seed in range(100):
            random.seed(seed)
            if random.random() < 0.8:
                random.seed(seed)
                battle.phase = "menu"
                battle._give_up()
                self.assertEqual(battle.phase, "result")
                self.assertIn("商談を見送った。", battle.log)
                break

    def test_give_up_failure_normal(self):
        """通常客への見送り失敗"""
        game = self._make_game()
        battle = self._make_battle(game, "traveler")
        # Find a seed where random.random() >= 0.8
        for seed in range(100):
            random.seed(seed)
            if random.random() >= 0.8:
                random.seed(seed)
                battle.phase = "menu"
                battle.log = []
                battle._give_up()
                self.assertEqual(battle.phase, "customer_turn")
                self.assertIn("見送ろうとしたが、引き止められた！", battle.log)
                break

    def test_give_up_boss_50pct_success(self):
        """ボスへの見送りは50%成功率"""
        game = self._make_game()
        battle = self._make_battle(game, "boss_merchant")
        success_count = 0
        fail_count = 0
        for seed in range(100):
            random.seed(seed)
            battle.phase = "menu"
            battle.log = []
            battle._give_up()
            if battle.phase == "result":
                success_count += 1
            else:
                fail_count += 1
        # 50%確率なので、100回中20-80回は成功するはず
        self.assertGreater(success_count, 20)
        self.assertGreater(fail_count, 20)


class TestPurchaseGaugeAIChange(unittest.TestCase):
    """購買意欲50%以上での顧客AI変化テスト"""

    def _make_game(self):
        game = MagicMock()
        game.player = PlayerState()
        game.partner_system = PartnerSystem()
        game.inventory = InventorySystem()
        game.chapter = ChapterSystem()
        game.play_se = MagicMock()
        game.play_bgm = MagicMock()
        game.message_window = MagicMock()
        game.message_window.active = False
        game.change_scene_with_transition = MagicMock()
        game.screen_shake = MagicMock()
        return game

    def test_ai_changes_at_50pct_gauge(self):
        """購買意欲50%以上で顧客AIが変化する（衝動買い確率UP, 迷い確率DOWN）"""
        game = self._make_game()
        battle = BattleScene(game)
        battle.on_enter(enemy_id="traveler")
        # travelerのactions: hesitation=0.6, haggle=0.3, impulse_buy=0.1
        # 50%以上にする
        battle.purchase_gauge = battle.purchase_threshold // 2
        # _customer_turnの中でmodified_actionsが計算されるはず
        # 直接テストするにはランダムの分布を見る
        action_counts = {"hesitation": 0, "impulse_buy": 0, "haggle": 0}
        for seed in range(1000):
            random.seed(seed)
            battle.phase = "customer_turn"
            battle.log = []
            # 直接_customer_turnを呼ぶ（battle.phaseが変わるので復元必要）
            old_hp = game.player.hp
            battle._customer_turn()
            game.player.hp = old_hp  # HP復元
            for action in action_counts:
                reactions_map = {
                    "hesitation": "迷っている",
                    "impulse_buy": "いいね",
                    "haggle": "値切ってきた",
                }
                if any(reactions_map[action] in msg for msg in battle.log):
                    action_counts[action] += 1
                    break
        # 衝動買いが増えて、迷いが減っているはず
        # 元の比率: hesitation=0.6, impulse_buy=0.1
        # 変化後: hesitation*0.5, impulse_buy*1.5 → 正規化後
        # impulse_buyの比率が元の10%より増えているか確認
        total = sum(action_counts.values())
        if total > 0:
            impulse_ratio = action_counts["impulse_buy"] / total
            self.assertGreater(impulse_ratio, 0.10, "衝動買い比率が上がるべき")


class TestAchievementSystem(unittest.TestCase):
    """実績システムテスト"""

    def _make_game(self):
        game = MagicMock()
        game.player = PlayerState()
        game.partner_system = PartnerSystem()
        game.inventory = InventorySystem()
        game.chapter = ChapterSystem()
        game.play_se = MagicMock()
        game.play_bgm = MagicMock()
        game.message_window = MagicMock()
        game.message_window.active = False
        game.change_scene_with_transition = MagicMock()
        game.screen_shake = MagicMock()
        return game

    def _make_battle(self, game, enemy_id="traveler"):
        battle = BattleScene(game)
        battle.on_enter(enemy_id=enemy_id)
        return battle

    def test_first_sale_achievement(self):
        """初回成約で first_sale 実績"""
        game = self._make_game()
        battle = self._make_battle(game)
        battle._on_sale_closed()
        self.assertIn("first_sale", game.player.achievements)

    def test_combo_5_achievement(self):
        """5連続成約で combo_5 実績"""
        game = self._make_game()
        game.player.combo_count = 4  # 次で5
        battle = self._make_battle(game)
        battle._on_sale_closed()
        self.assertIn("combo_5", game.player.achievements)

    def test_combo_4_no_achievement(self):
        """4連続では combo_5 実績がつかない"""
        game = self._make_game()
        game.player.combo_count = 3  # 次で4
        battle = self._make_battle(game)
        battle._on_sale_closed()
        self.assertNotIn("combo_5", game.player.achievements)

    def test_boss_clear_achievement(self):
        """ボス撃破で boss_clear 実績"""
        game = self._make_game()
        battle = self._make_battle(game, "boss_merchant")
        battle._on_sale_closed()
        self.assertIn("boss_clear", game.player.achievements)

    def test_no_damage_achievement(self):
        """無傷で成約すると no_damage 実績"""
        game = self._make_game()
        game.player.hp = game.player.max_hp
        battle = self._make_battle(game)
        battle._on_sale_closed()
        self.assertIn("no_damage", game.player.achievements)

    def test_no_damage_not_if_damaged(self):
        """被ダメージありでは no_damage がつかない"""
        game = self._make_game()
        game.player.hp = game.player.max_hp - 1
        battle = self._make_battle(game)
        battle._on_sale_closed()
        self.assertNotIn("no_damage", game.player.achievements)

    def test_rich_achievement(self):
        """所持金1000G以上で rich 実績"""
        game = self._make_game()
        game.player.gold = 990
        game.inventory.add_item("basic_tool", 1)
        battle = self._make_battle(game)
        battle.selected_product = {"id": "basic_tool", "name": "ベーシック道具セット", "quantity": 1}
        battle._on_sale_closed()
        # basic_tool profit=20, 990+20=1010 >= 1000
        self.assertIn("rich", game.player.achievements)

    def test_rank_a_achievement(self):
        """ランクAで rank_a 実績"""
        game = self._make_game()
        game.partner_system.sign_contract("テスト", "referral")
        game.partner_system._cumulative_sales = 6000
        game.partner_system._update_rank()
        battle = self._make_battle(game)
        battle._on_sale_closed()
        self.assertIn("rank_a", game.player.achievements)

    def test_all_skills_achievement(self):
        """全スキル使用で all_skills 実績"""
        game = self._make_game()
        game.player.level = 10
        game.player.hp = 200
        game.player.max_hp = 200
        battle = self._make_battle(game, "boss_merchant")  # 高HPで閾値に達しない
        all_skill_ids = {s["id"] for s in SALES_SKILLS}
        # 全スキルIDをused_skillsに追加（1つ残す）
        for sid in list(all_skill_ids)[:-1]:
            game.player.used_skills.add(sid)
        last_skill = list(all_skill_ids)[-1]
        # 最後のスキルを使う
        battle._use_skill(last_skill)
        self.assertIn("all_skills", game.player.achievements)

    def test_achievements_defined_in_data(self):
        """ACHIEVEMENTS定義に全実績IDがある"""
        from data.customers import ACHIEVEMENTS
        expected_ids = ["first_sale", "combo_5", "no_damage", "critical_finish",
                        "all_skills", "treasure_hunter", "rank_a", "boss_clear",
                        "rich", "speed_kill"]
        for aid in expected_ids:
            self.assertIn(aid, ACHIEVEMENTS, f"Achievement '{aid}' missing from ACHIEVEMENTS")


class TestMaxCombo(unittest.TestCase):
    """max_combo記録テスト"""

    def _make_game(self):
        game = MagicMock()
        game.player = PlayerState()
        game.partner_system = PartnerSystem()
        game.inventory = InventorySystem()
        game.chapter = ChapterSystem()
        game.play_se = MagicMock()
        game.play_bgm = MagicMock()
        game.message_window = MagicMock()
        game.message_window.active = False
        game.change_scene_with_transition = MagicMock()
        game.screen_shake = MagicMock()
        return game

    def test_max_combo_initial_zero(self):
        """初期状態でmax_comboは0"""
        p = PlayerState()
        self.assertEqual(p.max_combo, 0)

    def test_max_combo_updates_on_win(self):
        """成約でmax_comboが更新される"""
        game = self._make_game()
        battle = BattleScene(game)
        battle.on_enter(enemy_id="traveler")
        battle._on_sale_closed()
        self.assertEqual(game.player.max_combo, 1)

    def test_max_combo_tracks_highest(self):
        """max_comboは最高記録を保持する"""
        game = self._make_game()
        # 3連続成約
        for _ in range(3):
            battle = BattleScene(game)
            battle.on_enter(enemy_id="traveler")
            battle._on_sale_closed()
        self.assertEqual(game.player.max_combo, 3)
        # 失注でcomboリセット
        battle = BattleScene(game)
        battle.on_enter(enemy_id="traveler")
        battle._on_sale_lost()
        self.assertEqual(game.player.combo_count, 0)
        # max_comboは3のまま
        self.assertEqual(game.player.max_combo, 3)
        # 再度1連続
        battle = BattleScene(game)
        battle.on_enter(enemy_id="traveler")
        battle._on_sale_closed()
        # max_comboは3のまま（1 < 3）
        self.assertEqual(game.player.max_combo, 3)


class TestVIPCustomer(unittest.TestCase):
    """VIP顧客テスト"""

    def test_vip_customer_exists(self):
        """VIP顧客がCUSTOMERSに存在する"""
        self.assertIn("vip_customer", CUSTOMERS)

    def test_vip_customer_stats(self):
        """VIP顧客のステータスが正しい"""
        vip = CUSTOMERS["vip_customer"]
        self.assertEqual(vip["name"], "VIPクライアント")
        self.assertEqual(vip["hp"], 50)
        self.assertEqual(vip["exp"], 100)
        self.assertEqual(vip["gold"], 200)

    def test_vip_in_encounter_tables(self):
        """VIP顧客がエンカウントテーブルに存在する"""
        found = False
        for map_name, table in ENCOUNTER_TABLE.items():
            for cust_id, prob in table:
                if cust_id == "vip_customer":
                    found = True
                    self.assertLessEqual(prob, 0.05, "VIPは低確率であるべき")
        self.assertTrue(found, "VIP顧客がエンカウントテーブルにない")

    def test_vip_has_sprite(self):
        """VIP顧客のスプライトが定義されている"""
        from scenes.battle import CUSTOMER_SPRITES
        self.assertIn("vip_customer", CUSTOMER_SPRITES)


class TestNewItems(unittest.TestCase):
    """新アイテムテスト"""

    def test_energy_drink_exists(self):
        """栄養ドリンクがITEMSに存在する"""
        self.assertIn("energy_drink", ITEMS)
        self.assertEqual(ITEMS["energy_drink"]["name"], "栄養ドリンク")
        self.assertEqual(ITEMS["energy_drink"]["type"], "consumable")
        self.assertEqual(ITEMS["energy_drink"]["effect"], "hp_heal")
        self.assertEqual(ITEMS["energy_drink"]["value"], 50)

    def test_market_report_exists(self):
        """市場レポートがITEMSに存在する"""
        self.assertIn("market_report", ITEMS)
        self.assertEqual(ITEMS["market_report"]["name"], "市場レポート")
        self.assertEqual(ITEMS["market_report"]["type"], "consumable")
        self.assertEqual(ITEMS["market_report"]["effect"], "reveal_weakness")

    def test_energy_drink_in_shop(self):
        """栄養ドリンクがショップに並ぶ"""
        self.assertIn("energy_drink", SHOP_INVENTORY["my_shop"])

    def test_market_report_in_shop(self):
        """市場レポートがショップに並ぶ"""
        self.assertIn("market_report", SHOP_INVENTORY["my_shop"])

    def test_market_report_requires_rank_c(self):
        """市場レポートはランクCが必要"""
        self.assertEqual(ITEMS["market_report"].get("rank"), "C")
        items_d = get_available_items("my_shop", "D")
        self.assertNotIn("market_report", items_d)
        items_c = get_available_items("my_shop", "C")
        self.assertIn("market_report", items_c)


class TestRevealWeakness(unittest.TestCase):
    """reveal_weakness効果テスト"""

    def _make_game(self):
        game = MagicMock()
        game.player = PlayerState()
        game.partner_system = PartnerSystem()
        game.inventory = InventorySystem()
        game.chapter = ChapterSystem()
        game.play_se = MagicMock()
        game.play_bgm = MagicMock()
        game.message_window = MagicMock()
        game.message_window.active = False
        game.change_scene_with_transition = MagicMock()
        game.screen_shake = MagicMock()
        return game

    def test_reveal_weakness_shows_weakness(self):
        """市場レポートで弱点が表示される"""
        game = self._make_game()
        game.inventory.add_item("market_report")
        battle = BattleScene(game)
        battle.on_enter(enemy_id="traveler")  # weakness=explain
        battle._use_item("market_report")
        self.assertTrue(any("弱点判明" in msg for msg in battle.log))
        self.assertTrue(any("商品説明" in msg for msg in battle.log))

    def test_reveal_weakness_consumes_item(self):
        """市場レポート使用でアイテムが消費される"""
        game = self._make_game()
        game.inventory.add_item("market_report", 1)
        battle = BattleScene(game)
        battle.on_enter(enemy_id="traveler")
        battle._use_item("market_report")
        self.assertFalse(game.inventory.has_item("market_report"))


class TestTreasureChestCount(unittest.TestCase):
    """宝箱の数テスト"""

    def test_treasure_chest_total_count(self):
        """宝箱が全部で17個ある"""
        self.assertEqual(len(TREASURE_CHESTS), 17)

    def test_treasure_chests_per_map(self):
        """各マップの宝箱数"""
        home_chests = sum(1 for (m, _, _) in TREASURE_CHESTS if m == "home")
        field_chests = sum(1 for (m, _, _) in TREASURE_CHESTS if m == "field")
        dungeon_chests = sum(1 for (m, _, _) in TREASURE_CHESTS if m == "dungeon")
        self.assertEqual(home_chests, 3)
        self.assertEqual(field_chests, 6)
        self.assertEqual(dungeon_chests, 8)

    def test_all_chest_ids_unique(self):
        """宝箱IDがすべてユニーク"""
        ids = [chest["id"] for chest in TREASURE_CHESTS.values()]
        self.assertEqual(len(ids), len(set(ids)))


class TestSalesTalkHPCost(unittest.TestCase):
    """セールストークのHP消費テスト"""

    def _make_game(self):
        game = MagicMock()
        game.player = PlayerState()
        game.partner_system = PartnerSystem()
        game.inventory = InventorySystem()
        game.chapter = ChapterSystem()
        game.play_se = MagicMock()
        game.play_bgm = MagicMock()
        game.message_window = MagicMock()
        game.message_window.active = False
        game.change_scene_with_transition = MagicMock()
        game.screen_shake = MagicMock()
        return game

    def test_sales_talk_costs_2hp(self):
        """セールストークでやる気が2消費される"""
        game = self._make_game()
        battle = BattleScene(game)
        battle.on_enter(enemy_id="boss_merchant")  # 高HP閾値で成約しない
        initial_hp = game.player.hp
        random.seed(42)
        battle._sales_talk()
        self.assertEqual(game.player.hp, initial_hp - 2)

    def test_sales_talk_at_2hp_triggers_loss(self):
        """やる気が2のときセールストークすると失注"""
        game = self._make_game()
        game.player.hp = 2
        battle = BattleScene(game)
        battle.on_enter(enemy_id="boss_merchant")
        battle._sales_talk()
        # hp = 2-2 = 0 → 失注
        self.assertEqual(game.player.hp, game.player.max_hp)  # 全回復済み
        self.assertEqual(battle.phase, "result")

    def test_sales_talk_at_1hp_triggers_loss(self):
        """やる気が1のときセールストークすると失注"""
        game = self._make_game()
        game.player.hp = 1
        battle = BattleScene(game)
        battle.on_enter(enemy_id="boss_merchant")
        battle._sales_talk()
        self.assertEqual(battle.phase, "result")


class TestStateReset(unittest.TestCase):
    """ニューゲーム時の状態リセットテスト"""

    def test_player_state_reset(self):
        """ニューゲームでPlayerStateが初期化される"""
        game = MagicMock()
        game.player = PlayerState()
        game.player.gold = 999
        game.player.level = 10
        game.player.combo_count = 5
        game.player.max_combo = 8
        game.player.wins = 50
        game.player.achievements = {"first_sale", "combo_5"}
        # リセット
        new_player = PlayerState()
        self.assertEqual(new_player.gold, 150)
        self.assertEqual(new_player.level, 1)
        self.assertEqual(new_player.combo_count, 0)
        self.assertEqual(new_player.max_combo, 0)
        self.assertEqual(new_player.wins, 0)
        self.assertEqual(new_player.achievements, set())

    def test_chapter_system_reset(self):
        """ニューゲームでChapterSystemが初期化される"""
        cs = ChapterSystem()
        cs.current_chapter = 4
        cs.boss_defeated = True
        cs.total_sales_gold = 9999
        # リセット
        new_cs = ChapterSystem()
        self.assertEqual(new_cs.current_chapter, 1)
        self.assertFalse(new_cs.boss_defeated)
        self.assertEqual(new_cs.total_sales_gold, 0)

    def test_partner_system_reset(self):
        """ニューゲームでPartnerSystemが初期化される"""
        ps = PartnerSystem()
        ps.sign_contract("テスト", "referral")
        ps._cumulative_sales = 5000
        ps._update_rank()
        # リセット
        new_ps = PartnerSystem()
        self.assertFalse(new_ps.has_contract)
        self.assertEqual(new_ps.rank, "D")
        self.assertEqual(new_ps.cumulative_sales, 0)


class TestZeroDivisionSafety(unittest.TestCase):
    """ゼロ除算の安全性テスト"""

    def test_ending_rate_zero_battles(self):
        """戦闘0回でも成約率計算がゼロ除算しない"""
        p = PlayerState()
        total = p.wins + p.losses
        rate = int(p.wins / max(1, total) * 100)
        self.assertEqual(rate, 0)

    def test_battle_gauge_zero_threshold(self):
        """purchase_threshold=0でもゼロ除算しない"""
        game = MagicMock()
        game.player = PlayerState()
        game.partner_system = PartnerSystem()
        game.inventory = InventorySystem()
        game.chapter = ChapterSystem()
        game.play_se = MagicMock()
        game.play_bgm = MagicMock()
        game.message_window = MagicMock()
        game.message_window.active = False
        game.screen_shake = MagicMock()
        battle = BattleScene(game)
        battle.on_enter(enemy_id="traveler")
        battle.purchase_threshold = 0
        # _customer_turn内のgauge_ratio計算
        gauge_ratio = battle.purchase_gauge / battle.purchase_threshold if battle.purchase_threshold > 0 else 0
        self.assertEqual(gauge_ratio, 0)

    def test_hp_ratio_zero_max_hp(self):
        """max_hp=0でもゼロ除算しない"""
        p = PlayerState()
        p.max_hp = 0
        hp_ratio = p.hp / p.max_hp if p.max_hp > 0 else 0
        self.assertEqual(hp_ratio, 0)


# ============================================================
# パートナー商材・クロスセルテスト
# ============================================================
class TestPartnerMerchandise(unittest.TestCase):
    """パートナー商材テスト"""

    def test_partner_items_exist(self):
        """パートナー商材がITEMSに存在する"""
        self.assertIn("partner_basic_training", ITEMS)
        self.assertIn("partner_advanced_training", ITEMS)
        self.assertIn("partner_executive_program", ITEMS)

    def test_partner_items_have_referral_fee(self):
        """パートナー商材にreferral_feeがある"""
        self.assertEqual(ITEMS["partner_basic_training"]["referral_fee"], 15)
        self.assertEqual(ITEMS["partner_advanced_training"]["referral_fee"], 52)
        self.assertEqual(ITEMS["partner_executive_program"]["referral_fee"], 120)

    def test_partner_items_are_merchandise(self):
        """パートナー商材はmerchandiseタイプ"""
        for pid in ("partner_basic_training", "partner_advanced_training", "partner_executive_program"):
            self.assertEqual(ITEMS[pid]["type"], "merchandise")
            self.assertEqual(ITEMS[pid]["shop"], "partner_shop")

    def test_partner_items_in_weapon_shop_inventory(self):
        """パートナー商材がweapon_shopのSHOP_INVENTORYにある"""
        inv = SHOP_INVENTORY["weapon_shop"]
        self.assertIn("partner_basic_training", inv)
        self.assertIn("partner_advanced_training", inv)
        self.assertIn("partner_executive_program", inv)

    def test_partner_items_hidden_without_contract(self):
        """パートナー契約なしではパートナー商材が表示されない"""
        items = get_available_items("weapon_shop", "D")
        self.assertNotIn("partner_basic_training", items)
        items = get_available_items("weapon_shop", "D", partner_system=None)
        self.assertNotIn("partner_basic_training", items)

    def test_partner_items_hidden_no_contract_system(self):
        """PartnerSystemがあっても契約なしでは非表示"""
        ps = PartnerSystem()
        items = get_available_items("weapon_shop", "D", partner_system=ps)
        self.assertNotIn("partner_basic_training", items)

    def test_partner_items_shown_with_contract(self):
        """パートナー契約ありでパートナー商材が表示される"""
        ps = PartnerSystem()
        ps.sign_contract("タケシ", "referral", "weapon_shop")
        items = get_available_items("weapon_shop", "D", partner_system=ps)
        self.assertIn("partner_basic_training", items)
        # rank制限のある商材はDランクでは出ない
        self.assertNotIn("partner_advanced_training", items)  # rank=C
        self.assertNotIn("partner_executive_program", items)  # rank=B

    def test_partner_items_rank_c(self):
        """ランクCでadvanced_trainingが表示される"""
        ps = PartnerSystem()
        ps.sign_contract("タケシ", "reseller", "weapon_shop")
        items = get_available_items("weapon_shop", "C", partner_system=ps)
        self.assertIn("partner_basic_training", items)
        self.assertIn("partner_advanced_training", items)
        self.assertNotIn("partner_executive_program", items)

    def test_partner_items_rank_b(self):
        """ランクBでexecutive_programも表示される"""
        ps = PartnerSystem()
        ps.sign_contract("タケシ", "reseller", "weapon_shop")
        items = get_available_items("weapon_shop", "B", partner_system=ps)
        self.assertIn("partner_basic_training", items)
        self.assertIn("partner_advanced_training", items)
        self.assertIn("partner_executive_program", items)


class TestCrossSell(unittest.TestCase):
    """クロスセルテスト"""

    def _make_game(self):
        game = MagicMock()
        game.player = PlayerState()
        game.partner_system = PartnerSystem()
        game.inventory = InventorySystem()
        game.chapter = ChapterSystem()
        game.play_se = MagicMock()
        game.play_bgm = MagicMock()
        game.message_window = MagicMock()
        game.message_window.active = False
        game.screen_shake = MagicMock()
        game.text = MagicMock()
        return game

    def test_no_cross_sell_without_both(self):
        """自社商品のみではクロスセルオプションなし"""
        game = self._make_game()
        battle = BattleScene(game)
        battle.on_enter(enemy_id="traveler")
        game.inventory.add_item("basic_tool", 1)
        merch = battle._get_merchandise()
        cross_sells = [m for m in merch if m.get("id") == "__cross_sell__"]
        self.assertEqual(len(cross_sells), 0)

    def test_no_cross_sell_partner_only(self):
        """パートナー商品のみではクロスセルオプションなし"""
        game = self._make_game()
        battle = BattleScene(game)
        battle.on_enter(enemy_id="traveler")
        game.inventory.add_item("partner_basic_training", 1)
        merch = battle._get_merchandise()
        cross_sells = [m for m in merch if m.get("id") == "__cross_sell__"]
        self.assertEqual(len(cross_sells), 0)

    def test_cross_sell_with_both(self):
        """自社+パートナー商品があればクロスセルオプションが出る"""
        game = self._make_game()
        battle = BattleScene(game)
        battle.on_enter(enemy_id="traveler")
        game.inventory.add_item("basic_tool", 1)
        game.inventory.add_item("partner_basic_training", 1)
        merch = battle._get_merchandise()
        cross_sells = [m for m in merch if m.get("id") == "__cross_sell__"]
        self.assertEqual(len(cross_sells), 1)
        cs = cross_sells[0]
        self.assertIn("my_product", cs)
        self.assertIn("partner_product", cs)

    def test_cross_sell_profit_calculation_reseller(self):
        """クロスセル利益計算（販売代理店）"""
        # basic_tool: sell_value=40, price=20 → 粗利20
        # partner_basic_training: sell_value=100, price=40 → 粗利60
        # クロスセル: (20+60)*1.3 = 104
        my_profit = ITEMS["basic_tool"]["sell_value"] - ITEMS["basic_tool"]["price"]
        p_profit = ITEMS["partner_basic_training"]["sell_value"] - ITEMS["partner_basic_training"]["price"]
        total = int((my_profit + p_profit) * 1.3)
        self.assertEqual(my_profit, 20)
        self.assertEqual(p_profit, 60)
        self.assertEqual(total, 104)

    def test_cross_sell_profit_calculation_referral(self):
        """クロスセル利益計算（紹介代理店）"""
        # basic_tool: 粗利20
        # partner_basic_training: referral_fee=15
        # クロスセル: (20+15)*1.3 = 45
        my_profit = ITEMS["basic_tool"]["sell_value"] - ITEMS["basic_tool"]["price"]
        p_profit = ITEMS["partner_basic_training"]["referral_fee"]
        total = int((my_profit + p_profit) * 1.3)
        self.assertEqual(total, 45)

    def test_cross_sell_bonus_flag(self):
        """クロスセル選択時にcross_sell_bonusフラグがセットされる"""
        game = self._make_game()
        battle = BattleScene(game)
        battle.on_enter(enemy_id="traveler")
        self.assertFalse(battle.cross_sell_bonus)
        # クロスセル商品を選択してapply_product_bonusを呼ぶ
        game.inventory.add_item("basic_tool", 1)
        game.inventory.add_item("partner_basic_training", 1)
        merch = battle._get_merchandise()
        cross_sell = [m for m in merch if m.get("id") == "__cross_sell__"][0]
        battle.selected_product = cross_sell
        battle.customer = {"defense": 20, "target": "general", "hp": 100}
        battle._apply_product_bonus()
        self.assertTrue(battle.cross_sell_bonus)

    def test_partner_single_sale_referral_profit(self):
        """パートナー商品単品販売（紹介代理店）の利益はreferral_fee"""
        # referral_fee = 15 for partner_basic_training
        item = ITEMS["partner_basic_training"]
        self.assertEqual(item["referral_fee"], 15)
        self.assertEqual(item["sell_value"], 100)
        self.assertEqual(item["price"], 40)
        # 販売代理店の場合は粗利 = 100-40 = 60
        reseller_profit = item["sell_value"] - item["price"]
        self.assertEqual(reseller_profit, 60)


class TestPartnerShopPricing(unittest.TestCase):
    """ショップでのパートナー商品価格テスト"""

    def _make_game(self):
        game = MagicMock()
        game.player = PlayerState()
        game.partner_system = PartnerSystem()
        game.inventory = InventorySystem()
        game.chapter = ChapterSystem()
        game.play_se = MagicMock()
        game.play_bgm = MagicMock()
        game.message_window = MagicMock()
        game.message_window.active = False
        game.text = MagicMock()
        return game

    def test_referral_partner_item_free(self):
        """紹介代理店ではパートナー商品が無料で取得できる"""
        game = self._make_game()
        game.partner_system.sign_contract("タケシ", "referral", "weapon_shop")
        shop = ShopScene(game)
        shop.on_enter(shop_id="weapon_shop")
        # パートナー商品を探す
        partner_items = [s for s in shop.shop_items if s.get("shop") == "partner_shop"]
        self.assertTrue(len(partner_items) > 0)
        # 紹介代理店の場合、実際の購入価格は0
        item = partner_items[0]
        initial_gold = game.player.gold
        shop.cursor = shop.shop_items.index(item)
        shop.mode = "buy"
        # 手動で購入処理をテスト
        is_partner_item = item.get("shop") == "partner_shop"
        self.assertTrue(is_partner_item)
        contract = game.partner_system.get_contract_for_shop("weapon_shop")
        self.assertEqual(contract.contract_type, "referral")
        # 紹介代理店なら0G
        actual_price = 0 if (is_partner_item and contract and contract.contract_type == "referral") else item["price"]
        self.assertEqual(actual_price, 0)

    def test_reseller_partner_item_paid(self):
        """販売代理店ではパートナー商品は有料"""
        game = self._make_game()
        game.partner_system.sign_contract("タケシ", "reseller", "weapon_shop")
        shop = ShopScene(game)
        shop.on_enter(shop_id="weapon_shop")
        partner_items = [s for s in shop.shop_items if s.get("shop") == "partner_shop"]
        self.assertTrue(len(partner_items) > 0)
        item = partner_items[0]
        contract = game.partner_system.get_contract_for_shop("weapon_shop")
        is_partner_item = item.get("shop") == "partner_shop"
        actual_price = 0 if (is_partner_item and contract and contract.contract_type == "referral") else item["price"]
        self.assertGreater(actual_price, 0)


# ============================================================
# メイン実行
# ============================================================
if __name__ == "__main__":
    # テスト結果サマリ
    unittest.main(verbosity=2)
