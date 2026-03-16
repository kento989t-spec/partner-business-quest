"""ゲーム本体 - Pyxelアプリケーション"""
import pyxel

from scenes.title import TitleScene
from scenes.field import FieldScene
from scenes.battle import BattleScene
from scenes.shop import ShopScene
from scenes.menu import MenuScene
from scenes.ending import EndingScene
from scenes.message import MessageWindow
from scenes.transition import TransitionEffect
from systems.partner import PartnerSystem
from systems.inventory import InventorySystem
from systems.chapter import ChapterSystem
from systems.economy import check_level_up, get_level_up_stats, exp_for_level
from data.items import ITEMS


# 画面サイズ
SCREEN_W = 256
SCREEN_H = 240

# シーン定数
SCENE_TITLE = "title"
SCENE_FIELD = "field"
SCENE_BATTLE = "battle"
SCENE_SHOP = "shop"
SCENE_MENU = "menu"
SCENE_ENDING = "ending"


class PlayerState:
    """プレイヤーの状態管理"""

    def __init__(self):
        self.name = "ナオト"
        self.hp = 50
        self.max_hp = 50
        self.attack = 12
        self.defense = 6
        self.speed = 5
        self.gold = 150
        self.level = 1
        self.exp = 0
        self.total_exp = 0
        self.x = 5  # フィールド上のタイル座標
        self.y = 5
        self.chapter = 1  # 現在のチャプター
        self.repel_steps = 0
        self.combo_count = 0  # 連続成約数
        self.max_combo = 0   # 最大コンボ記録
        self.wins = 0    # 勝利数
        self.losses = 0  # 敗北数
        self.opened_chests = set()  # 開封済み宝箱のIDセット
        self.quiz_completed = set()  # クリア済みクイズのIDセット
        self.achievements = set()   # 達成した実績のIDセット
        self.used_skills = set()    # 使用したスキルのIDセット


class Game:
    """メインゲームクラス"""

    def __init__(self):
        pyxel.init(SCREEN_W, SCREEN_H, title="Partner Business Quest", fps=30)

        # 日本語フォント読み込み
        self.font = pyxel.Font("assets/umplus_j12r.bdf")

        self._init_resources()

        # ゲーム状態
        self.player = PlayerState()
        self.partner_system = PartnerSystem()
        self.inventory = InventorySystem()
        self.chapter = ChapterSystem()
        self.message_window = MessageWindow(self)
        self.transition = TransitionEffect()
        self.shake_timer = 0
        self.shake_intensity = 0

        # サウンド初期化
        self._init_sounds()
        self._current_bgm = None  # 現在再生中のBGM名

        # シーン管理
        self.scenes = {
            SCENE_TITLE: TitleScene(self),
            SCENE_FIELD: FieldScene(self),
            SCENE_BATTLE: BattleScene(self),
            SCENE_SHOP: ShopScene(self),
            SCENE_MENU: MenuScene(self),
            SCENE_ENDING: EndingScene(self),
        }
        self.current_scene = SCENE_TITLE

    def text(self, x, y, s, col):
        """日本語対応テキスト描画"""
        pyxel.text(x, y, s, col, self.font)

    def text_width(self, s):
        """テキスト幅を取得"""
        return self.font.text_width(s)

    def _init_resources(self):
        """リソース初期化（16x16スプライト、FC DQ3品質準拠）"""
        # === プレイヤーキャラ ナオト（16x16, 下向き静止）===
        # 色0=透過, F=肌, 5=青服, A=黄ベルト, 4=茶髪/靴, 1=目
        player_sprite = [
            "0000004440000000",
            "0000044444000000",
            "0000444444400000",
            "0000441F14400000",
            "000041FFF1400000",
            "0000044F44000000",
            "00000A555A000000",
            "0000555A55500000",
            "0005555A55550000",
            "0005555555550000",
            "0000555555000000",
            "0000055550000000",
            "0000055550000000",
            "0000050050000000",
            "0000440044000000",
            "0000440044000000",
        ]
        self._draw_sprite(self._add_outline(player_sprite), 0, 0)

        # === プレイヤー歩行フレーム（16x16, 下向き歩行）===
        player_walk = [
            "0000004440000000",
            "0000044444000000",
            "0000444444400000",
            "0000441F14400000",
            "000041FFF1400000",
            "0000044F44000000",
            "00000A555A000000",
            "0000555A55500000",
            "0005555A55550000",
            "0005555555550000",
            "0000555555000000",
            "0000055550000000",
            "0000055550000000",
            "0000500050000000",
            "0004400044000000",
            "0004400004400000",
        ]
        self._draw_sprite(self._add_outline(player_walk), 96, 0)

        # === NPCキャラ 長老（16x16）===
        # 色7=白髪, F=肌, 2=紫ローブ, 4=茶靴, 1=目, 左に杖(7)
        npc_sprite = [
            "0000007770000000",
            "0000077777000000",
            "0000777777700000",
            "000077F1F7700000",
            "000071FFF1700000",
            "000007FFF7000000",
            "0000022222000000",
            "0700222722200000",
            "0700222222200000",
            "0702222222220000",
            "0000222222000000",
            "0000022220000000",
            "0000022220000000",
            "0000020020000000",
            "0000440044000000",
            "0000440044000000",
        ]
        self._draw_sprite(self._add_outline(npc_sprite), 16, 0)

        # === 通りすがりの旅人（16x16）===
        # つば広帽子(9=橙,10px幅), マント(4=茶)で体を覆う, リュック(7), F=肌, 1=目
        traveler_sprite = [
            "0009999999900000",
            "0099999999990000",
            "0009999999900000",
            "000099F1F9900000",
            "0000099FF9000000",
            "0000044444000000",
            "0004444744400000",
            "0044444474440000",
            "0044444444440000",
            "0004444444400000",
            "0000444444000000",
            "0000044440000000",
            "0000044440000000",
            "0000040040000000",
            "0000440044000000",
            "0000000000000000",
        ]
        self._draw_sprite(self._add_outline(traveler_sprite), 32, 0)

        # === 近所のおかみさん（16x16）===
        # 色0=透過, 4=茶髪(お団子), F=肌, 8=赤エプロン, 6=模様, A=かご, 1=目
        housewife_sprite = [
            "0000044400000000",
            "0000444440000000",
            "0000044444000000",
            "000044F1F4400000",
            "000041FFF1400000",
            "0000044F44000000",
            "0000088888000000",
            "0008888688800000",
            "0088888688880000",
            "0088888888880000",
            "0008888888800000",
            "0000888888000000",
            "0000088880000000",
            "000008AA80000000",
            "0000880088000000",
            "0000880088000000",
        ]
        self._draw_sprite(self._add_outline(housewife_sprite), 48, 0)

        # === 慎重な商人（16x16）===
        # 色0=透過, 3=緑服, F=肌, A=金アクセ, 4=茶, 1=目, ずんぐり体型
        cautious_merchant_sprite = [
            "0000004440000000",
            "0000044444000000",
            "0000444444400000",
            "000044F1F4400000",
            "000041FFF1400000",
            "000004FFF4000000",
            "000A033333A00000",
            "00A3333333300000",
            "0A33333333330000",
            "0A33333A3333A000",
            "00A3333333A00000",
            "000A333333000000",
            "0000033330000000",
            "0000030030000000",
            "0000440044000000",
            "0000440044000000",
        ]
        self._draw_sprite(self._add_outline(cautious_merchant_sprite), 64, 0)

        # === 冒険者パーティ(3人)（16x16）===
        # 色0=透過, 5=青, 8=赤, B=黄緑, F=肌, 1=目(各キャラに追加)
        adventurer_sprite = [
            "0040000800003000",
            "0444008880033300",
            "04F1088F1033F100",
            "04FF088FF033FF00",
            "0044008800033000",
            "0555088880BBB300",
            "0555088880BBB300",
            "0555088880BBB300",
            "0050008000030000",
            "0050008000030000",
            "0440088000330000",
            "0000000000000000",
            "0000000000000000",
            "0000000000000000",
            "0000000000000000",
            "0000000000000000",
        ]
        self._draw_sprite(self._add_outline(adventurer_sprite), 80, 0)

        # === 目の肥えた貴族（16x16）===
        # 色0=透過, A=金冠, 2=紫ローブ, F=肌, 7=白髪, 1=目, 長身
        noble_sprite = [
            "00000AAAAA000000",
            "0000A0A0A0A00000",
            "0000077777000000",
            "0000777777700000",
            "000077F1F7700000",
            "000071FFF1700000",
            "0000077F77000000",
            "0000022222000000",
            "0000222222200000",
            "0002222222220000",
            "0002222222220000",
            "0000222222000000",
            "0000022220000000",
            "0000020020000000",
            "0000220022000000",
            "0000220022000000",
        ]
        self._draw_sprite(self._add_outline(noble_sprite), 0, 32)

        # === 独占商人ゴウヨク ボス（16x16, 専用スプライト）===
        # 巨大・威圧的, A=金の冠/ベルト, 9=橙服, 2=紫マント, F=肌, 1=目, 幅広体型
        boss_sprite = [
            "00AAAAAAAAA00000",
            "0AAAAAAAAAA00000",
            "0AAAAAAAAAA00000",
            "00009F1F19000000",
            "000091FFF1900000",
            "0000099F99000000",
            "0002999999920000",
            "0029999999992000",
            "029999AAA9992000",
            "0299999999992000",
            "0029999999920000",
            "0002999999200000",
            "0000999999000000",
            "0000090090000000",
            "0000990099000000",
            "0000990099000000",
        ]
        self._draw_sprite(self._add_outline(boss_sprite), 16, 32)

        # === 熱心な学生（16x16）===
        # 細身シルエット, 5=黒髪, 7=白シャツ(制服), C=青ネクタイ, F=肌, 1=目, A=黄カバン
        student_sprite = [
            "0000005550000000",
            "0000055555000000",
            "0000555555500000",
            "0000551F15500000",
            "000051FFF1500000",
            "0000055F55000000",
            "00000C777C000000",
            "0000777C77700000",
            "0000777777700000",
            "0000777777700000",
            "000077777A700000",
            "000007777AA00000",
            "0000077770000000",
            "0000070070000000",
            "0000550055000000",
            "0000000000000000",
        ]
        self._draw_sprite(self._add_outline(student_sprite), 48, 32)

        # === 常連のお客さん（16x16）===
        # ふくよか体型, 9=橙服(暖色), 4=茶髪, F=肌, 1=目, A=黄色い買い物袋(右側に膨らみ)
        regular_sprite = [
            "0000004440000000",
            "0000044444000000",
            "0000444444400000",
            "0000441F14400000",
            "000041FFF1400000",
            "000004FFF4000000",
            "0000099999000000",
            "0009999999900000",
            "0099999999990000",
            "009999999999A000",
            "000999999999A000",
            "0000999999AA0000",
            "0000099990000000",
            "0000090090000000",
            "0000440044000000",
            "0000000000000000",
        ]
        self._draw_sprite(self._add_outline(regular_sprite), 64, 32)

        # === 厳しいクレーマー（16x16）===
        # 角張った体型, 怒り眉(太い1), 8=赤服, 5=暗髪, F=肌, 1=目, 腕組みポーズ
        complainer_sprite = [
            "0000005550000000",
            "0000055555000000",
            "0000555555500000",
            "0000151F15100000",
            "000051FFF1500000",
            "0000055155000000",
            "0000088888000000",
            "0008888888800000",
            "0088888888880000",
            "0088858858880000",
            "0008855558800000",
            "0000888888000000",
            "0000088880000000",
            "0000080080000000",
            "0000550055000000",
            "0000000000000000",
        ]
        self._draw_sprite(self._add_outline(complainer_sprite), 80, 32)

        # === 大口クライアント（16x16）===
        # 色1=暗紺スーツ, A=金ネクタイ, F=肌, 5=暗髪, 大きめ体格
        big_client_sprite = [
            "0000005550000000",
            "0000055555000000",
            "0000555555500000",
            "0000551F15500000",
            "000051FFF1500000",
            "0000055F55000000",
            "0001111111100000",
            "0011111111110000",
            "0111111111111000",
            "0111111A11111000",
            "0011111111110000",
            "0001111111100000",
            "0000111111000000",
            "0000010010000000",
            "0000110011000000",
            "0000000000000000",
        ]
        self._draw_sprite(self._add_outline(big_client_sprite), 96, 32)

        # === 仕入れ担当バイヤー（16x16）===
        # 色6=水色メガネ, 3=緑服, 7=白クリップボード, 4=茶髪, F=肌, 1=目
        buyer_sprite = [
            "0000004440000000",
            "0000044444000000",
            "0000444444400000",
            "0000461F16400000",
            "000041FFF1400000",
            "0000044F44000000",
            "0000033333000000",
            "0000333333300000",
            "0003333333370000",
            "0003333333370000",
            "0000333333370000",
            "0000033330770000",
            "0000033330000000",
            "0000030030000000",
            "0000440044000000",
            "0000000000000000",
        ]
        self._draw_sprite(self._add_outline(buyer_sprite), 112, 32)

        # === VIPクライアント（16x16）===
        # 金色ベースの豪華なキャラ, A=金冠/装飾, 10=黄服, F=肌, 1=目, 2=紫マント
        vip_sprite = [
            "00000AAAAA000000",
            "0000A0AAA0A00000",
            "0000AAAAAAA00000",
            "000044F1F4400000",
            "000041FFF1400000",
            "0000044F44000000",
            "000A0AAAAA0A0000",
            "00A2AAAAAAA2A000",
            "0A22AAAAAAA22A00",
            "0A22AAA2AAA22A00",
            "00A2AAAAAAA2A000",
            "000AAAAAAAAA0000",
            "0000AAAAAAA00000",
            "00000A00A0000000",
            "0000AA00AA000000",
            "0000AA00AA000000",
        ]
        self._draw_sprite(self._add_outline(vip_sprite), 128, 32)

        # === 建物タイル（16x16）===
        # 色9=屋根, 0=アウトライン, F=壁, 4=ドア, 6=窓
        building_tile = [
            "0000009990000000",
            "0000099999000000",
            "0000999999900000",
            "0009999999990000",
            "0099999999999000",
            "9999999999999900",
            "00FFFFFFFFFFFF00",
            "00FFFFFFFFFFFF00",
            "00FF066FF066FF00",
            "00FF066FF066FF00",
            "00FFFFFFFFFFFF00",
            "00FFFFFFFFFFFF00",
            "00FFFF0440FFFF00",
            "00FFFF0440FFFF00",
            "00FFFF0440FFFF00",
            "0044444444444400",
        ]
        self._draw_sprite(building_tile, 0, 16)

        # === 木タイル（16x16）===
        # 色0=アウトライン, 3=緑葉, B=明緑, 4=茶幹
        tree_tile = [
            "0000003300000000",
            "0000033B30000000",
            "00003B3B33000000",
            "0003333B33300000",
            "00333B33B3300000",
            "033333333B300000",
            "03B333333B330000",
            "0333B33333300000",
            "003333B333000000",
            "0003333330000000",
            "0000033300000000",
            "0000044000000000",
            "0000044000000000",
            "0000044000000000",
            "0000044000000000",
            "0000044000000000",
        ]
        self._draw_sprite(tree_tile, 16, 16)

        # === 草タイル（16x16）===
        # 色3=緑ベース, B=明緑アクセント
        grass_tile = [
            "33333333B3333333",
            "3333333333333333",
            "33B33333333B3333",
            "333333333333B333",
            "3333333333333333",
            "3333B33333333333",
            "33333333B3333333",
            "3333333333333333",
            "333333333333B333",
            "3333333333333333",
            "33333B3333333333",
            "3333333333333B33",
            "3333333333333333",
            "3B33333333333333",
            "33333333B3333333",
            "3333333333333333",
        ]
        self._draw_sprite(grass_tile, 32, 16)

        # === 水タイル（16x16）===
        # 色5=青ベース, 6=明青波, 1=暗部
        water_tile = [
            "5555555555555555",
            "5566555556655555",
            "5556655555665555",
            "5555555555555555",
            "5555555555555555",
            "5555566555556655",
            "5555556655555665",
            "5555555555555555",
            "5555555555555555",
            "5566555555665555",
            "5556655555565555",
            "5555555555555555",
            "5555555555555555",
            "5555566555556655",
            "5555556655555665",
            "5555555555555555",
        ]
        self._draw_sprite(water_tile, 48, 16)

        # === 道タイル（16x16）===
        # 色4=茶ベース, F=明部, D=小石
        path_tile = [
            "4444444444444444",
            "4444F44444444444",
            "44444444F4444444",
            "4444444444444444",
            "44444444444F4444",
            "44F4444444444444",
            "44444444444444D4",
            "4444D44444444444",
            "4444444F44444444",
            "4444444444444444",
            "4444444444DF4444",
            "4444F44444444444",
            "4444444444444444",
            "44D4444444444444",
            "44444444F4444444",
            "4444444444444444",
        ]
        self._draw_sprite(path_tile, 64, 16)

        # === 看板付き建物タイル（16x16）===
        # 色A=黄屋根, 0=アウトライン, F=壁, 4=ドア開, 6=窓
        shop_building_tile = [
            "000000AAA0000000",
            "00000AAAAA000000",
            "0000AAAAAAA00000",
            "000AAAAAAAAA0000",
            "00AAAAAAAAAAA000",
            "AAAAAAAAAAAAAAAA",
            "00FFFFFFFFFFFF00",
            "00FFFFFFFFFFFF00",
            "00FF066FF066FF00",
            "00FF066FF066FF00",
            "00FFFFFFFFFFFF00",
            "00FFFFA44AFFFF00",
            "00FFFF4004FFFF00",
            "00FFFF0000FFFF00",
            "00FFFF0000FFFF00",
            "0044444444444400",
        ]
        self._draw_sprite(shop_building_tile, 32, 32)

        # === 壁タイル（16x16）===
        # 色1=暗部, D=灰ベース, 5=目地
        wall_tile = [
            "5555555555555555",
            "DDDDDDD5DDDDDDD5",
            "DDDDDDD5DDDDDDD5",
            "5555555555555555",
            "DDD5DDDDDDD5DDDD",
            "DDD5DDDDDDD5DDDD",
            "5555555555555555",
            "DDDDDDD5DDDDDDD5",
            "DDDDDDD5DDDDDDD5",
            "5555555555555555",
            "DDD5DDDDDDD5DDDD",
            "DDD5DDDDDDD5DDDD",
            "5555555555555555",
            "DDDDDDD5DDDDDDD5",
            "DDDDDDD5DDDDDDD5",
            "5555555555555555",
        ]
        self._draw_sprite(wall_tile, 80, 16)

    def _add_outline(self, data, outline_color="1"):
        """スプライトデータに自動アウトラインを追加（FC DQ3品質）"""
        rows = [row.ljust(16, "0")[:16] for row in data]
        height = len(rows)
        result = []
        for y in range(height):
            new_row = list(rows[y])
            for x in range(16):
                if new_row[x] == "0":
                    for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                        nx, ny = x + dx, y + dy
                        if 0 <= nx < 16 and 0 <= ny < height:
                            if rows[ny][nx] != "0":
                                new_row[x] = outline_color
                                break
            result.append("".join(new_row))
        return result

    def _draw_sprite(self, data, ox, oy):
        """スプライトデータをイメージバンクに描画"""
        for y, row in enumerate(data):
            for x, ch in enumerate(row.rstrip()):
                if ch != "0":
                    col = int(ch, 16)
                    pyxel.images[0].pset(ox + x, oy + y, col)

    def _init_sounds(self):
        """サウンド初期化（BGM/SE全登録）"""
        try:
            from data.bgm import init_sounds
            init_sounds()
            self.sound_enabled = True
        except Exception:
            self.sound_enabled = False

    def play_se(self, name):
        """SE再生"""
        if not self.sound_enabled:
            return
        from data.bgm import play_se
        play_se(f"se_{name}")

    def play_bgm(self, name, force=False):
        """BGM再生（同じBGMが再生中ならスキップ）"""
        if not self.sound_enabled:
            return
        if not force and self._current_bgm == name:
            return
        from data.bgm import play_bgm
        play_bgm(name)
        self._current_bgm = name

    def stop_bgm(self):
        """BGM停止"""
        if not self.sound_enabled:
            return
        from data.bgm import stop_bgm
        stop_bgm()
        self._current_bgm = None

    def reset_game_state(self):
        """ゲーム状態を初期化（ニューゲーム時）"""
        self.player = PlayerState()
        self.partner_system = PartnerSystem()
        self.inventory = InventorySystem()
        self.chapter = ChapterSystem()
        # 初期商材
        self.inventory.add_item("basic_tool", 3)
        # シーン固有の状態もリセット
        field = self.scenes.get(SCENE_FIELD)
        if field:
            field._tutorial_done = False
            field._intro_shown = False
            field.step_count = 0
            field.current_map = "home"
            field.npcs = []
            field.dialogue_queue = []
            field.in_event = False

    @property
    def scene(self):
        return self.scenes[self.current_scene]

    def change_scene(self, scene_name, **kwargs):
        """シーン切り替え（トランジション付き）"""
        self.current_scene = scene_name
        self.scene.on_enter(**kwargs)

    def change_scene_with_transition(self, scene_name, **kwargs):
        """フェードアウト→シーン切替→フェードインの遷移"""
        def on_fade_out():
            self.current_scene = scene_name
            self.scene.on_enter(**kwargs)
            self.transition.fade_in(speed=0.08)
        self.transition.fade_out(speed=0.08, on_complete=on_fade_out)

    def screen_shake(self, intensity=3, duration=10):
        """画面シェイク開始"""
        self.shake_timer = duration
        self.shake_intensity = intensity

    def run(self):
        """ゲーム開始"""
        self.scene.on_enter()
        pyxel.run(self.update, self.draw)

    def update(self):
        """毎フレーム更新"""
        self.transition.update()
        if not self.transition.active:
            self.scene.update()
        # 画面シェイク処理
        if self.shake_timer > 0:
            self.shake_timer -= 1
            import random
            dx = random.randint(-self.shake_intensity, self.shake_intensity)
            dy = random.randint(-self.shake_intensity, self.shake_intensity)
            pyxel.camera(dx, dy)
        else:
            pyxel.camera(0, 0)

    def draw(self):
        """毎フレーム描画"""
        pyxel.cls(0)
        self.scene.draw()

        # メッセージウィンドウは常に最前面
        if self.message_window.active:
            self.message_window.draw()

        # トランジションエフェクトは最前面
        self.transition.draw()
