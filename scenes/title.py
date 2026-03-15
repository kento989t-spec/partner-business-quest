"""タイトル画面"""
import pyxel
from input_helper import btn_confirm


class TitleScene:
    def __init__(self, game):
        self.game = game
        self.blink_timer = 0
        self.selected = 0  # 0=はじめから

    def on_enter(self, **kwargs):
        self.blink_timer = 0
        self.selected = 0
        self.game.play_bgm("title")

    def update(self):
        self.blink_timer += 1
        if btn_confirm():
            self.game.play_se("confirm")
            self.game.reset_game_state()
            self.game.change_scene_with_transition("field")

    def draw(self):
        t = self.game.text
        pyxel.cls(1)  # 暗い背景

        # タイトルロゴ（中央寄せ）
        tw1 = self.game.text_width("PARTNER")
        tw2 = self.game.text_width("BUSINESS")
        tw3 = self.game.text_width("QUEST")
        t(128 - tw1 // 2, 36, "PARTNER", 10)
        t(128 - tw2 // 2, 56, "BUSINESS", 10)
        t(128 - tw3 // 2, 76, "QUEST", 10)

        # サブタイトル
        subtitle = "〜パートナービジネスの冒険〜"
        tw = self.game.text_width(subtitle)
        t(128 - tw // 2, 100, subtitle, 7)

        # プレイヤースプライト表示（拡大）
        scale = 3
        sprite_w = 16 * scale  # 48px
        sprite_x = 128 - sprite_w // 2
        for dy in range(16):
            for dx in range(16):
                col = pyxel.images[0].pget(dx, dy)
                if col != 0:
                    pyxel.rect(sprite_x + dx * scale, 120 + dy * scale, scale, scale, col)

        # メニュー（点滅表示）
        if self.blink_timer % 40 < 28:
            start_text = "- Enter/Aボタンでスタート -"
            tw2 = self.game.text_width(start_text)
            t(128 - tw2 // 2, 192, start_text, 6)

        # クレジット
        credit = "Powered by Pyxel"
        tw3 = self.game.text_width(credit)
        t(128 - tw3 // 2, 222, credit, 5)
