"""入力ヘルパー - キーボード + ゲームパッド両対応"""
import pyxel

GP = pyxel.GAMEPAD1_BUTTON_A
GP_B = pyxel.GAMEPAD1_BUTTON_B
GP_UP = pyxel.GAMEPAD1_BUTTON_DPAD_UP
GP_DOWN = pyxel.GAMEPAD1_BUTTON_DPAD_DOWN
GP_LEFT = pyxel.GAMEPAD1_BUTTON_DPAD_LEFT
GP_RIGHT = pyxel.GAMEPAD1_BUTTON_DPAD_RIGHT


def btn_confirm():
    """決定ボタン（Enter/Space/A）"""
    return (
        pyxel.btnp(pyxel.KEY_RETURN)
        or pyxel.btnp(pyxel.KEY_SPACE)
        or pyxel.btnp(GP)
    )


def btn_cancel():
    """キャンセルボタン（ESC/B）"""
    return pyxel.btnp(pyxel.KEY_ESCAPE) or pyxel.btnp(GP_B)


def btn_up(hold_delay=0, hold_interval=0):
    """上ボタン"""
    return pyxel.btnp(pyxel.KEY_UP, hold_delay, hold_interval) or pyxel.btnp(
        GP_UP, hold_delay, hold_interval
    )


def btn_down(hold_delay=0, hold_interval=0):
    """下ボタン"""
    return pyxel.btnp(pyxel.KEY_DOWN, hold_delay, hold_interval) or pyxel.btnp(
        GP_DOWN, hold_delay, hold_interval
    )


def btn_left(hold_delay=0, hold_interval=0):
    """左ボタン"""
    return pyxel.btnp(pyxel.KEY_LEFT, hold_delay, hold_interval) or pyxel.btnp(
        GP_LEFT, hold_delay, hold_interval
    )


def btn_right(hold_delay=0, hold_interval=0):
    """右ボタン"""
    return pyxel.btnp(pyxel.KEY_RIGHT, hold_delay, hold_interval) or pyxel.btnp(
        GP_RIGHT, hold_delay, hold_interval
    )
