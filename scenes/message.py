"""メッセージウィンドウ"""
import pyxel
from input_helper import btn_confirm, btn_up, btn_down


class MessageWindow:
    """画面下部に表示されるメッセージウィンドウ"""

    def __init__(self, game):
        self.game = game
        self.active = False
        self.text = ""
        self.displayed_chars = 0
        self.char_speed = 1
        self.frame_count = 0
        self.on_close = None
        self.choices = []
        self.selected_choice = 0
        self.speaker_sprite = None  # (sx, sy) or None

    def show(self, text, on_close=None, choices=None, speaker_sprite=None):
        self.active = True
        self.text = text
        self.displayed_chars = 0
        self.frame_count = 0
        self.on_close = on_close
        self.choices = choices or []
        self.selected_choice = 0
        self.speaker_sprite = speaker_sprite

    def update(self):
        if not self.active:
            return

        self.frame_count += 1

        if self.displayed_chars < len(self.text):
            if self.frame_count % self.char_speed == 0:
                self.displayed_chars += 1
            if btn_confirm():
                self.displayed_chars = len(self.text)
        else:
            if self.choices:
                if btn_up():
                    self.selected_choice = max(0, self.selected_choice - 1)
                if btn_down():
                    self.selected_choice = min(
                        len(self.choices) - 1, self.selected_choice + 1
                    )
                if btn_confirm():
                    self.active = False
                    if self.on_close:
                        self.on_close(self.selected_choice)
            else:
                if btn_confirm():
                    self.active = False
                    if self.on_close:
                        self.on_close(None)

    def draw(self):
        if not self.active:
            return

        t = self.game.text
        win_x = 4
        win_y = 140
        win_w = 248
        win_h = 96       # 6行×14px + padding = 96px

        # DQ風ウィンドウ
        pyxel.rect(win_x, win_y, win_w, win_h, 1)     # 背景
        pyxel.rectb(win_x, win_y, win_w, win_h, 7)     # 外枠白
        pyxel.rectb(win_x + 2, win_y + 2, win_w - 4, win_h - 4, 5)  # 内枠グレー

        # 話者スプライト表示
        if self.speaker_sprite:
            sx, sy = self.speaker_sprite
            scale = 2
            sp_x = win_x + 8
            sp_y = win_y + 8
            for dy in range(16):
                for dx in range(16):
                    col = pyxel.images[0].pget(sx + dx, sy + dy)
                    if col != 0:
                        pyxel.rect(sp_x + dx * scale, sp_y + dy * scale, scale, scale, col)
            # テキスト開始位置をスプライト分右にずらす
            text_x_offset = 40
        else:
            text_x_offset = 0

        display_text = self.text[: self.displayed_chars]
        lines = display_text.split("\n")
        # 枠内に収まる最大文字数: (win_w - 16 - text_x_offset) / 12 ≈ 19文字
        max_chars = (win_w - 16 - text_x_offset) // 12
        for i, line in enumerate(lines[:6]):
            # 長い行は切り詰め
            if len(line) > max_chars:
                line = line[:max_chars]
            t(win_x + 8 + text_x_offset, win_y + 8 + i * 14, line, 7)

        if self.choices and self.displayed_chars >= len(self.text):
            choice_x = win_x + win_w - 120
            choice_y = win_y - len(self.choices) * 18 - 8
            choice_w = 112
            choice_h = len(self.choices) * 18 + 12

            # DQ風選択肢ウィンドウ
            pyxel.rect(choice_x, choice_y, choice_w, choice_h, 1)
            pyxel.rectb(choice_x, choice_y, choice_w, choice_h, 7)
            pyxel.rectb(choice_x + 2, choice_y + 2, choice_w - 4, choice_h - 4, 5)

            for i, choice in enumerate(self.choices):
                cy = choice_y + 6 + i * 18
                color = 10 if i == self.selected_choice else 7
                prefix = "▶ " if i == self.selected_choice else "  "
                t(choice_x + 8, cy, prefix + choice, color)

        if (
            self.displayed_chars >= len(self.text)
            and not self.choices
            and self.frame_count % 40 < 25
        ):
            t(win_x + win_w - 20, win_y + win_h - 16, "▼", 7)
