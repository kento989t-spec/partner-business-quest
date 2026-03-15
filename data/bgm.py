"""BGM・SEデータ（MML形式 - Pyxel対応）

Partner Business Quest用のBGMとSE定義。
DQ3風の雰囲気を意識したオリジナル楽曲。

Pyxel MML仕様:
  音色 @0=Triangle, @1=Square, @2=Pulse, @3=Noise
  T=テンポ, O=オクターブ, V=音量(0-7), L=デフォルト音長
  CDEFGAB=音符, R=休符, #=シャープ, -=フラット
  .=付点, &=タイ, >/<=オクターブ上下
"""

import pyxel

# =============================================================================
# BGM定義（各3チャンネル: ch0=メロディ, ch1=ハーモニー, ch2=ベース）
# =============================================================================

# 1. タイトル画面BGM - 壮大で期待感のあるファンファーレ風
TITLE_BGM = [
    # ch0: メロディ（Square） - 荘厳なファンファーレ
    "T100 @1 V7 L8 O4 "
    "R4 C4 E G4. G "
    "A4 G E4. C "
    "D4 E F4. D "
    "E2. R4 "
    "C4 E G4. G "
    "A4 B >C4. <A "
    "G4 F E4. D "
    "C2. R4 "
    "E4 G >C4. <B "
    "A4 G F4. E "
    "D4 F A4. G "
    "F2. R4 "
    "E4 G >C4. <B "
    "A4 B >C4 D "
    "E4 D C4. <B "
    ">C1 ",

    # ch1: ハーモニー（Pulse） - 和音の3度/5度
    "T100 @2 V5 L8 O3 "
    "R4 E4 G >C4. C "
    "C4 <B G4. E "
    "F4 G A4. F "
    "G2. R4 "
    "E4 G >C4. C "
    "C4 D E4. C "
    "<B4 A G4. F "
    "E2. R4 "
    "G4 B >E4. D "
    "C4 <B A4. G "
    "F4 A >C4. <B "
    "A2. R4 "
    "G4 B >E4. D "
    "C4 D E4 F "
    "G4 F E4. D "
    "E1 ",

    # ch2: ベースライン（Triangle）
    "T100 @0 V6 L4 O2 "
    "R C G C "
    "F C E C "
    "D A D A "
    "C G2 R "
    "C G C G "
    "F G A F "
    "G D G D "
    "C G2 R "
    "C E G E "
    "F C F C "
    "D F A F "
    "F C2 R "
    "C E G E "
    "F G A B "
    ">C <G C G "
    "C1 ",
]

# 2. 町BGM - 穏やかで日常的な雰囲気
TOWN_BGM = [
    # ch0: メロディ（Square） - 穏やかなワルツ風
    "T120 @1 V6 L8 O4 "
    "E4 D C4 D "
    "E4. F G4 R "
    "A4 G F4 E "
    "D2. R4 "
    "E4 D C4 D "
    "E4. F G4 A "
    "G4 F E4 D "
    "C2. R4 "
    "G4 A B4 >C "
    "<A4. G F4 R "
    "E4 F G4 A "
    "F2. R4 "
    "G4 A B4 >C "
    "<B4. A G4 F "
    "E4 D C4 D "
    "C2. R4 ",

    # ch1: ハーモニー（Pulse）
    "T120 @2 V4 L8 O3 "
    "G4 F E4 F "
    "G4. A B4 R "
    ">C4 <B A4 G "
    "F2. R4 "
    "G4 F E4 F "
    "G4. A B4 >C "
    "<B4 A G4 F "
    "E2. R4 "
    "B4 >C D4 E "
    "C4. <B A4 R "
    "G4 A B4 >C "
    "<A2. R4 "
    "B4 >C D4 E "
    "D4. C <B4 A "
    "G4 F E4 F "
    "E2. R4 ",

    # ch2: ベースライン（Triangle） - ワルツのリズム
    "T120 @0 V5 L4 O2 "
    "C G G "
    "C G G "
    "F >C C "
    "<G D D "
    "C G G "
    "C G G "
    "G D D "
    "C G G "
    "E B B "
    "F >C C "
    "<C G G "
    "F >C C "
    "<E B B "
    "G D D "
    "C G G "
    "C G2 ",
]

# 3. フィールドBGM - 冒険感、前向きで勇壮
FIELD_BGM = [
    # ch0: メロディ（Square） - 力強い行進曲風
    "T130 @1 V7 L8 O4 "
    "C C D E E D C4 "
    "E E F G G F E4 "
    "G4 A G4 F "
    "E4 D C2 "
    "C C D E E D C4 "
    "E E F G A G F4 "
    "E4 F E4 D "
    "C2. R4 "
    "G4 >C <B4 A "
    "G4 F E4 D "
    "E4 F G4 A "
    "G2. R4 "
    "G4 >C <B4 A "
    "G4 A B4 >C "
    "<A4 G F4 E "
    "D2 C2 ",

    # ch1: ハーモニー（Pulse）
    "T130 @2 V5 L8 O3 "
    "E E F G G F E4 "
    "G G A B B A G4 "
    "B4 >C <B4 A "
    "G4 F E2 "
    "E E F G G F E4 "
    "G G A B >C <B A4 "
    "G4 A G4 F "
    "E2. R4 "
    "B4 >E D4 C "
    "<B4 A G4 F "
    "G4 A B4 >C "
    "<B2. R4 "
    "B4 >E D4 C "
    "<B4 >C D4 E "
    "C4 <B A4 G "
    "F2 E2 ",

    # ch2: ベースライン（Triangle） - 力強い行進ベース
    "T130 @0 V6 L8 O2 "
    "C4 G4 C4 G4 "
    "C4 G4 C4 G4 "
    "E4 A4 D4 F4 "
    "G4 G4 C4 G4 "
    "C4 G4 C4 G4 "
    "C4 G4 F4 A4 "
    "G4 A4 G4 D4 "
    "C4 G4 C4 R4 "
    "E4 G4 F4 A4 "
    "G4 D4 C4 G4 "
    "C4 F4 E4 A4 "
    "G4 D4 G4 R4 "
    "E4 G4 F4 A4 "
    "G4 A4 G4 >C4 "
    "<F4 G4 A4 C4 "
    "G4 G4 C4 C4 ",
]

# 4. 戦闘BGM - 緊張感、アップテンポ
BATTLE_BGM = [
    # ch0: メロディ（Square） - 激しい戦闘テーマ
    "T160 @1 V7 L16 O4 "
    "C8 C E8 E G8 G >C8 R "
    "<A8 A G8 G F8 F E8 R "
    "D8 D F8 F A8 A >C8 R "
    "<B8 B A8 A G8 G F8 R "
    "E8. R16 E8. R16 G8 A8 "
    "B8. R16 B8. R16 >C8 D8 "
    "E8 D C8 <B A8 G F8 E "
    "D4 R4 D4 R4 "
    "C8 E G8 >C <B8 A G8 F "
    "E8 G >C8 E D8 C <B8 A "
    "G8. R16 A8. R16 B8 >C8 "
    "D8 C <B8 A G4 R4 "
    "C8 E G8 >C <B8 A G8 F "
    "E8 G >C8 E D8 E F8 E "
    "D8 C <B8 A G8 F E8 D "
    "C4 R4 C4 R4 ",

    # ch1: ハーモニー（Pulse） - 裏メロディ
    "T160 @2 V5 L16 O3 "
    "E8 E G8 G B8 B >E8 R "
    "C8 C <B8 B A8 A G8 R "
    "F8 F A8 A >C8 C E8 R "
    "D8 D C8 C <B8 B A8 R "
    "G8. R16 G8. R16 B8 >C8 "
    "D8. R16 D8. R16 E8 F8 "
    "G8 F E8 D C8 <B A8 G "
    "F4 R4 F4 R4 "
    "E8 G B8 >E D8 C <B8 A "
    "G8 B >E8 G F8 E D8 C "
    "<B8. R16 >C8. R16 D8 E8 "
    "F8 E D8 C <B4 R4 "
    "E8 G B8 >E D8 C <B8 A "
    "G8 B >E8 G F8 G A8 G "
    "F8 E D8 C <B8 A G8 F "
    "E4 R4 E4 R4 ",

    # ch2: ベースライン（Triangle） - 疾走感のあるベース
    "T160 @0 V6 L8 O2 "
    "C C C C C C C C "
    "F F F F F F F F "
    "D D D D D D D D "
    "G G G G G G G G "
    "C C C C C C C C "
    "G G G G G G G G "
    "C C D D E E F F "
    "G4 G4 G4 G4 "
    "C C C C D D D D "
    "E E E E F F F F "
    "G G G G A A A A "
    "G G F F G4 G4 "
    "C C C C D D D D "
    "E E E E F F F F "
    "G G F F E E D D "
    "C4 C4 C4 C4 ",
]

# 5. ボス戦BGM - 重厚、緊迫
BOSS_BGM = [
    # ch0: メロディ（Square） - 重厚な主旋律
    "T140 @1 V7 L8 O4 "
    "R2 E-4 D "
    "C4 <B- A4 G "
    "A-4 B- >C4 D "
    "E-2. R4 "
    "R2 G4 F "
    "E-4 D C4 <B- "
    "A4 B- >C4 D "
    "C2. R4 "
    "E-4 F G4 A- "
    "B-4 A- G4 F "
    "E-4 D C4 <B- "
    ">C2 <B-2 "
    "A-4 B- >C4 D "
    "E-4 F G4 A- "
    "G4 F E-4 D "
    "C2. R4 ",

    # ch1: ハーモニー（Pulse） - 不穏な和音
    "T140 @2 V5 L8 O3 "
    "R2 G4 F "
    "E-4 D C4 <B- "
    ">C4 D E-4 F "
    "G2. R4 "
    "R2 B-4 A- "
    "G4 F E-4 D "
    "C4 D E-4 F "
    "E-2. R4 "
    "G4 A- B-4 >C "
    "D4 C <B-4 A- "
    "G4 F E-4 D "
    "E-2 D2 "
    "C4 D E-4 F "
    "G4 A- B-4 >C "
    "<B-4 A- G4 F "
    "E-2. R4 ",

    # ch2: ベースライン（Triangle） - 重低音の脈動
    "T140 @0 V7 L4 O2 "
    "C C C C "
    "A- A- A- A- "
    "F F F F "
    "G G G G "
    "C C C C "
    "A- A- A- A- "
    "F F F F "
    "C C C C "
    "E- E- E- E- "
    "B- B- B- B- "
    "G G G G "
    "A- A- G G "
    "F F F F "
    "E- E- E- E- "
    "G G G G "
    "C C C C ",
]

# 6. ショップBGM - 明るく軽快
SHOP_BGM = [
    # ch0: メロディ（Square） - 軽やかで楽しい
    "T140 @1 V6 L8 O4 "
    "C D E G F E D C "
    "D E F A G F E D "
    "E4 G4 >C4 <G4 "
    "A4 F4 D2 "
    "C D E G F E D C "
    "D E F A G A B >C "
    "<B4 A4 G4 F4 "
    "E2. R4 "
    "G4 E4 C4 E4 "
    "F4 D4 <B4 >D4 "
    "E4 C4 <A4 >C4 "
    "D4 <B4 G2 "
    ">C D E G F E D C "
    "D E F A G A B >C "
    "<A4 G4 F4 E4 "
    "C2. R4 ",

    # ch1: ハーモニー（Pulse） - 弾むリズム
    "T140 @2 V4 L8 O3 "
    "E R G R A R G R "
    "F R A R B R A R "
    "G4 B4 >E4 <B4 "
    ">C4 <A4 F2 "
    "E R G R A R G R "
    "F R A R B R >D R "
    "D4 C4 <B4 A4 "
    "G2. R4 "
    "B4 G4 E4 G4 "
    "A4 F4 D4 F4 "
    "G4 E4 C4 E4 "
    "F4 D4 <B2 "
    ">E R G R A R G R "
    "F R A R B R >D R "
    "C4 <B4 A4 G4 "
    "E2. R4 ",

    # ch2: ベースライン（Triangle） - 弾むベース
    "T140 @0 V5 L8 O2 "
    "C R G R C R G R "
    "D R A R D R A R "
    "E4 G4 >C4 <G4 "
    "F4 D4 G4 G4 "
    "C R G R C R G R "
    "D R A R D R G R "
    "G R D R G R D R "
    "C R G R C4 R4 "
    "C R G R C R G R "
    "D R A R D R A R "
    "E R B R E R B R "
    "G R D R G4 G4 "
    "C R G R C R G R "
    "D R A R D R G R "
    "F R C R G R G R "
    "C R G R C4 R4 ",
]


# =============================================================================
# SE定義（各1チャンネル: ch3で再生）
# =============================================================================

# 1. 決定音 - 短い確認音
SE_CONFIRM = "T180 @1 V6 L32 O5 C E G >C4"

# 2. カーソル音 - 軽い移動音
SE_CURSOR = "T200 @2 V4 L32 O5 E16 R16"

# 3. 攻撃ヒット - 打撃音
SE_ATTACK = "T200 @3 V7 L32 O3 C C C R C C R16"

# 4. ミス音 - 空振り
SE_MISS = "T160 @3 V4 L32 O5 C R C R C R R8"

# 5. 回復音 - 柔らかい上昇音
SE_HEAL = "T160 @0 V6 L16 O4 C E G >C E G8"

# 6. 敵撃破音 - 消滅音
SE_ENEMY_DEFEAT = "T200 @3 V7 L32 O4 C C C C <B B A A G G F F E E D D C8"

# 7. 売買成立音 - チャリン
SE_TRADE = "T200 @1 V6 L32 O6 E16 R16 E16 R16 G8"

# 8. レベルアップジングル - 達成感（3秒以内）
SE_LEVEL_UP = (
    "T150 @1 V7 L16 O4 "
    "C E G >C8 R16 <A >C E A8 R16 "
    "G B >D G4"
)

# 9. 勝利ファンファーレ - 短い勝利曲（3-5秒）
SE_VICTORY = (
    "T140 @1 V7 L8 O4 "
    "C C C C4 E-4 "
    "F F F F4 A-4 "
    "G4 A4 B4 >C2"
)

# 10. ゲームオーバー - 暗い下降音
SE_GAME_OVER = (
    "T100 @0 V6 L8 O4 "
    "E- D C <B- A- G F E-4"
)


# =============================================================================
# サウンドID割り当て（pyxel.sounds[n]へのマッピング用）
# =============================================================================
# BGM用: sounds[0]~[17] (各BGM 3ch x 6曲)
# SE用: sounds[30]~[39]

SOUND_MAP = {
    # BGM (sound_id: 曲名)
    "title": [0, 1, 2],
    "town": [3, 4, 5],
    "field": [6, 7, 8],
    "battle": [9, 10, 11],
    "boss": [12, 13, 14],
    "shop": [15, 16, 17],
    # SE (sound_id)
    "se_confirm": 30,
    "se_cursor": 31,
    "se_attack": 32,
    "se_miss": 33,
    "se_heal": 34,
    "se_enemy_defeat": 35,
    "se_trade": 36,
    "se_level_up": 37,
    "se_victory": 38,
    "se_game_over": 39,
}

# BGMデータの一覧（キー名: MMLリスト）
ALL_BGM = {
    "title": TITLE_BGM,
    "town": TOWN_BGM,
    "field": FIELD_BGM,
    "battle": BATTLE_BGM,
    "boss": BOSS_BGM,
    "shop": SHOP_BGM,
}

# SEデータの一覧（キー名: MML文字列）
ALL_SE = {
    "se_confirm": SE_CONFIRM,
    "se_cursor": SE_CURSOR,
    "se_attack": SE_ATTACK,
    "se_miss": SE_MISS,
    "se_heal": SE_HEAL,
    "se_enemy_defeat": SE_ENEMY_DEFEAT,
    "se_trade": SE_TRADE,
    "se_level_up": SE_LEVEL_UP,
    "se_victory": SE_VICTORY,
    "se_game_over": SE_GAME_OVER,
}


# =============================================================================
# Music定義（pyxel.musics[n]用のチャンネルマッピング）
# =============================================================================
# musics[0] = タイトル, musics[1] = 町, ... musics[5] = ショップ

MUSIC_MAP = {
    "title": 0,
    "town": 1,
    "field": 2,
    "battle": 3,
    "boss": 4,
    "shop": 5,
}


def init_sounds():
    """Pyxelサウンドシステムを初期化する。pyxel.init()の後に呼ぶ。"""

    # BGM用サウンドを登録
    for bgm_name, mml_list in ALL_BGM.items():
        sound_ids = SOUND_MAP[bgm_name]
        for ch_idx, mml in enumerate(mml_list):
            pyxel.sounds[sound_ids[ch_idx]].mml(mml)

    # SE用サウンドを登録
    for se_name, mml in ALL_SE.items():
        sound_id = SOUND_MAP[se_name]
        pyxel.sounds[sound_id].mml(mml)

    # Music定義（BGMのループ再生用）
    for bgm_name, music_id in MUSIC_MAP.items():
        sound_ids = SOUND_MAP[bgm_name]
        pyxel.musics[music_id].set(
            [sound_ids[0]],  # ch0
            [sound_ids[1]],  # ch1
            [sound_ids[2]],  # ch2
            [],               # ch3 (SE用に空けておく)
        )


def play_bgm(name):
    """BGMを再生する。name: 'title', 'town', 'field', 'battle', 'boss', 'shop'"""
    music_id = MUSIC_MAP.get(name)
    if music_id is not None:
        pyxel.playm(music_id, loop=True)


def stop_bgm():
    """BGMを停止する。"""
    pyxel.stop()


def play_se(name):
    """SEをch3で再生する。name: 'se_confirm', 'se_cursor', etc."""
    sound_id = SOUND_MAP.get(name)
    if sound_id is not None:
        pyxel.play(3, sound_id)


def play_jingle(name):
    """ジングル（勝利・レベルアップ等）を再生する。BGMを一時停止してch0で鳴らす。"""
    sound_id = SOUND_MAP.get(name)
    if sound_id is not None:
        pyxel.stop()
        pyxel.play(0, sound_id)
