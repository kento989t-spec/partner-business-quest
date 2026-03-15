"""画面遷移エフェクト"""
import pyxel


class TransitionEffect:
    """dither+palを使った画面遷移"""

    def __init__(self):
        self.active = False
        self.type = "none"  # fade_out, fade_in
        self.progress = 0.0  # 0.0〜1.0
        self.speed = 0.05  # 1フレームあたりの進行量
        self.on_complete = None

    def fade_out(self, speed=0.05, on_complete=None):
        """フェードアウト開始"""
        self.active = True
        self.type = "fade_out"
        self.progress = 0.0
        self.speed = speed
        self.on_complete = on_complete

    def fade_in(self, speed=0.05, on_complete=None):
        """フェードイン開始"""
        self.active = True
        self.type = "fade_in"
        self.progress = 1.0
        self.speed = speed
        self.on_complete = on_complete

    def update(self):
        if not self.active:
            return

        if self.type == "fade_out":
            self.progress += self.speed
            if self.progress >= 1.0:
                self.progress = 1.0
                self.active = False
                if self.on_complete:
                    self.on_complete()
        elif self.type == "fade_in":
            self.progress -= self.speed
            if self.progress <= 0.0:
                self.progress = 0.0
                self.active = False
                if self.on_complete:
                    self.on_complete()

    def draw(self):
        """遷移エフェクトを描画（全描画の後に呼ぶ）"""
        if not self.active and self.progress == 0.0:
            return

        if self.progress > 0:
            # ditherで画面を暗くする
            pyxel.dither(self.progress)
            pyxel.rect(0, 0, 256, 240, 0)
            pyxel.dither(1.0)  # リセット
