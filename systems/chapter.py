"""チャプター進行管理システム（販売バトル版）"""


# チャプター定義
CHAPTERS = {
    1: {
        "title": "道具屋のあととり",
        "goal": "直販で累計売上500Gを達成する",
        "clear_condition": "sales_500",
        "intro": "アキトは道具屋の息子。\n親から店を継いだものの、\n客足は伸びない...\n\n外に出て、自分の力で\n商売を広げる決意をした。",
    },
    2: {
        "title": "パートナービジネスの始まり",
        "goal": "パートナー契約を結び、ランクCに上げる（累計売上500G）",
        "clear_condition": "rank_c",
        "intro": "直販で手応えを感じたアキト。\nしかし一人の力では限界がある。\n\n東の町に仲間がいると聞いた。\nパートナーと組めば、\nもっと大きな商売ができるかも。",
    },
    3: {
        "title": "商売の拡大",
        "goal": "クロスセルでランクBに上げる（累計売上2000G）",
        "clear_condition": "rank_b",
        "intro": "パートナーとの信頼が\n深まってきた。\n\nしかし北の商店街では\n独占商人ゴウヨクが暴れている\nという噂が...\n\n市場を自由にするため、\n商店街に乗り込もう。",
    },
    4: {
        "title": "独占商人との商談",
        "goal": "独占商人ゴウヨクとの最終商談に勝つ",
        "clear_condition": "boss_defeated",
        "intro": "ついにゴウヨクとの対決の時。\n\nこれまで培ったセールス力と\nパートナーの絆で、\n独占に立ち向かう！",
    },
}


class ChapterSystem:
    """チャプター進行管理"""

    def __init__(self):
        self.current_chapter = 1
        self.boss_defeated = False
        self.flags = set()  # イベントフラグ
        self.total_sales_gold = 0  # 直販での累計売上

    def set_flag(self, flag):
        self.flags.add(flag)

    def has_flag(self, flag):
        return flag in self.flags

    def add_sales(self, gold):
        """売上を加算"""
        self.total_sales_gold += gold

    @property
    def chapter_info(self):
        return CHAPTERS.get(self.current_chapter, {})

    @property
    def chapter_title(self):
        info = self.chapter_info
        return f"第{self.current_chapter}章: {info.get('title', '???')}"

    def check_chapter_clear(self, game):
        """チャプタークリア条件をチェック。クリアしたらTrue"""
        info = self.chapter_info
        condition = info.get("clear_condition")

        if condition == "sales_500":
            return self.total_sales_gold >= 500
        elif condition == "rank_c":
            return game.partner_system.rank in ("C", "B", "A")
        elif condition == "rank_b":
            return game.partner_system.rank in ("B", "A")
        elif condition == "boss_defeated":
            return self.boss_defeated
        return False

    def advance_chapter(self):
        """次のチャプターへ"""
        if self.current_chapter < len(CHAPTERS):
            self.current_chapter += 1
            return True
        return False
