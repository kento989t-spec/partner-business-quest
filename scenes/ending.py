"""エンディング画面（販売バトル版 - 充実版）"""
import pyxel
from input_helper import btn_confirm
from data.maps import TREASURE_CHESTS
from data.customers import ACHIEVEMENTS


class EndingScene:
    def __init__(self, game):
        self.game = game
        self.timer = 0
        self.phase = 0

    def on_enter(self, **kwargs):
        self.timer = 0
        self.phase = 0
        self.game.play_bgm("title")

    def _get_total_chests(self):
        """全宝箱数を返す"""
        return len(TREASURE_CHESTS)

    def _get_rank(self, rate, level):
        """総合評価ランクを判定"""
        if rate >= 90 and level >= 8:
            return "S", "伝説の商人"
        elif rate >= 70 and level >= 6:
            return "A", "一流の商人"
        elif rate >= 50:
            return "B", "腕利きの商人"
        else:
            return "C", "駆け出しの商人"

    def update(self):
        self.timer += 1
        if self.timer > 60 and btn_confirm():
            if self.phase < 3:
                self.phase += 1
                self.timer = 0
            else:
                # タイトルに戻る
                self.game.change_scene_with_transition("title")

    def draw(self):
        t = self.game.text
        pyxel.cls(0)

        if self.phase == 0:
            # Phase 0: ボス撃破メッセージ
            t(24, 20, "━━━━━━━━━━━━━━━━", 10)
            t(24, 38, "独占商人ゴウヨクとの", 10)
            t(24, 54, "  商談に勝利した！", 10)
            t(24, 70, "━━━━━━━━━━━━━━━━", 10)
            # フェードイン演出
            if self.timer > 20:
                t(24, 92, "この地域に自由な商売が戻った!", 7)
            if self.timer > 35:
                t(24, 110, "公正な取引が再び息づき始める..", 7)
            if self.timer > 50:
                p = self.game.player
                t(24, 134, f"{p.name}の名は広く知れ渡った。", 11)
                t(24, 152, "誠実なセールスと仲間との絆が", 11)
                t(24, 170, "市場の未来を切り拓いたのだ。", 11)

        elif self.phase == 1:
            # Phase 1: 冒険の記録（詳細統計）
            p = self.game.player
            ps = self.game.partner_system

            t(36, 8, "━━ 冒険の記録 ━━", 10)

            # 基本情報 (14px間隔)
            x = 36
            y = 28
            t(x, y, f"最終レベル: {p.level}", 7)
            t(x, y + 14, f"所持金:     {p.gold}G", 7)
            t(x, y + 28, f"パートナー: {ps.rank}({ps.rank_label})", 7)
            t(x, y + 42, f"累計売上:   {ps.cumulative_sales}G", 7)

            # 商談成績
            t(x, y + 60, f"商談成績: {p.wins}勝 {p.losses}敗", 7)
            total = p.wins + p.losses
            rate = int(p.wins / max(1, total) * 100)
            t(x, y + 74, f"成約率:   {rate}%", 7)
            t(x, y + 88, f"最大コンボ: {p.max_combo}連続", 7)

            # 探索
            total_chests = self._get_total_chests()
            opened = len(p.opened_chests)
            t(x, y + 102, f"宝箱: {opened}/{total_chests}個", 7)

            # 実績
            achv_count = len(p.achievements)
            achv_total = len(ACHIEVEMENTS)
            t(x, y + 116, f"実績: {achv_count}/{achv_total}個", 7)
            # 達成した実績名を表示（最大3個）
            achv_names = [ACHIEVEMENTS[a] for a in p.achievements if a in ACHIEVEMENTS]
            for i, aname in enumerate(achv_names[:3]):
                t(x + 16, y + 130 + i * 14, f"★ {aname}", 10)
            if len(achv_names) > 3:
                t(x + 16, y + 130 + 3 * 14, f"  ..他{len(achv_names)-3}個", 6)

            # 総合評価
            rank_letter, rank_title = self._get_rank(rate, p.level)
            eval_y = y + 130 + min(len(achv_names), 3) * 14 + (14 if len(achv_names) > 3 else 0) + 4
            if eval_y > 220:
                eval_y = 220
            pyxel.line(x, eval_y, x + 176, eval_y, 10)
            rank_color = {
                "S": 10, "A": 11, "B": 6, "C": 7,
            }.get(rank_letter, 7)
            t(x, eval_y + 6, f"総合評価: {rank_letter}ランク「{rank_title}」", rank_color)

        elif self.phase == 2:
            # Phase 2: パートナービジネスの教訓
            t(24, 14, "━━ パートナービジネスの教訓 ━━", 10)

            lessons = [
                ("信頼が資本", "パートナーとの信頼関係が", "ビジネスの土台になる。"),
                ("Win-Winの関係", "お互いに利益がある関係こそ", "長続きする。"),
                ("リスクとリターン", "紹介代理店は低リスク安定、", "販売代理店は高リターン。"),
                ("価値を伝える", "値引きは最後の手段。", "商品の価値を伝えよう。"),
            ]

            y = 36
            for i, (title, line1, line2) in enumerate(lessons):
                if self.timer > i * 12:
                    t(32, y, f"■ {title}", 10)
                    t(44, y + 14, line1, 7)
                    t(44, y + 28, line2, 7)
                y += 46

            if self.timer > 50:
                t(24, 224, "これが、パートナービジネスの力。", 11)

        elif self.phase == 3:
            # Phase 3: CoPASS宣伝 + クレジット
            t(44, 24, "Thank you for playing!", 10)

            t(24, 50, "PARTNER BUSINESS QUEST", 7)
            tw = self.game.text_width("パートナービジネスクエスト")
            t(128 - tw // 2, 68, "パートナービジネスクエスト", 7)

            t(24, 94, "このゲームを楽しめたなら、", 7)
            t(24, 110, "パートナービジネスの世界を", 7)
            t(24, 126, "もっと深く体験してみませんか？", 7)

            t(56, 156, "CoPASS をチェック！", 10)

            t(36, 200, "(C) 2026 Partner Business Quest", 5)

        if self.timer > 60 and pyxel.frame_count % 40 < 28:
            if self.phase < 3:
                t(160, 224, "- Aで続ける -", 6)
            else:
                t(140, 224, "- Aでタイトルへ -", 6)
