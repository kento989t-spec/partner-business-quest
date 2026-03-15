"""経済・バランス計算（販売バトル版）"""

# 経験値テーブル（累計）
EXP_TABLE = [0, 0, 15, 45, 90, 160, 260, 400, 600, 850, 1200]
# Lv1=0, Lv2=15, Lv3=45, ...

# レベルアップ時のステータス上昇
LEVEL_UP_STATS = {
    2: {"max_hp": 8, "attack": 1, "defense": 1, "speed": 1},
    3: {"max_hp": 10, "attack": 1, "defense": 2, "speed": 1},
    4: {"max_hp": 12, "attack": 2, "defense": 2, "speed": 2},
    5: {"max_hp": 15, "attack": 2, "defense": 3, "speed": 2},
    6: {"max_hp": 15, "attack": 2, "defense": 3, "speed": 3},
    7: {"max_hp": 18, "attack": 3, "defense": 4, "speed": 3},
    8: {"max_hp": 20, "attack": 3, "defense": 4, "speed": 4},
    9: {"max_hp": 22, "attack": 3, "defense": 5, "speed": 4},
    10: {"max_hp": 25, "attack": 4, "defense": 5, "speed": 5},
}


def calc_persuasion(attack, defense):
    """説得力計算（セールス力 vs 警戒心）
    説得量 = ((セールス力*2 - 警戒心) / 3) × 乱数(0.85〜1.15)
    最低1
    """
    import random
    base = (attack * 2 - defense) // 3
    if base <= 0:
        return max(1, random.randint(0, 1))
    variance = random.uniform(0.85, 1.15)
    return max(1, int(base * variance))


# 後方互換エイリアス（他モジュールからの参照用）
calc_damage = calc_persuasion


def calc_action_order(combatants):
    """行動順の決定
    行動優先値 = 対応力 × 乱数(0.5〜1.0)
    高い順に行動
    """
    import random
    order = []
    for c in combatants:
        priority = c["speed"] * random.uniform(0.5, 1.0)
        order.append((priority, c))
    order.sort(key=lambda x: x[0], reverse=True)
    return [c for _, c in order]


def exp_for_level(level):
    """指定レベルに必要な累計経験値"""
    if level < len(EXP_TABLE):
        return EXP_TABLE[level]
    last = EXP_TABLE[-1]
    for i in range(len(EXP_TABLE), level + 1):
        last = int(last * 1.5)
    return last


def check_level_up(current_level, total_exp):
    """レベルアップ判定。新レベルを返す"""
    new_level = current_level
    while new_level + 1 < len(EXP_TABLE) and total_exp >= EXP_TABLE[new_level + 1]:
        new_level += 1
    return new_level


def get_level_up_stats(level):
    """レベルアップ時のステータス上昇値"""
    return LEVEL_UP_STATS.get(level, {
        "max_hp": 10, "attack": 2, "defense": 2, "speed": 2
    })
