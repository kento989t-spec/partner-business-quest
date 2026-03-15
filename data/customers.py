"""顧客データ（販売バトル用）"""

# 実績定義
ACHIEVEMENTS = {
    "first_sale": "初めての成約",
    "combo_5": "5連続成約",
    "no_damage": "無傷の商談",
    "critical_finish": "会心の一撃で成約",
    "all_skills": "全スキル使用",
    "treasure_hunter": "宝箱5個以上発見",
    "rank_a": "ランクA到達",
    "boss_clear": "ゴウヨク撃破",
    "rich": "所持金1000G以上",
    "speed_kill": "1ターン成約",
}

CUSTOMERS = {
    # Chapter 1-2: 初心者向け
    "student": {
        "name": "熱心な学生",
        "hp": 18,
        "attack": 2,
        "defense": 3,
        "speed": 7,
        "exp": 3,
        "gold": 15,
        "weakness": "explain",
        "target": "general",
        "actions": [("hesitation", 0.4), ("impulse_buy", 0.4), ("haggle", 0.2)],
    },
    # Chapter 1: ホームタウン周辺
    "traveler": {
        "name": "通りすがりの旅人",
        "hp": 20,        # 購買意欲閾値（これを0から埋める）
        "attack": 4,     # 客の反応力（やる気ダメージ）
        "defense": 6,    # 警戒心（説得への耐性）
        "speed": 4,
        "exp": 5,
        "gold": 20,
        "weakness": "explain",
        "target": "general",
        "actions": [("hesitation", 0.6), ("haggle", 0.3), ("impulse_buy", 0.1)],
    },
    "housewife": {
        "name": "近所のおかみさん",
        "hp": 16,
        "attack": 3,
        "defense": 5,
        "speed": 5,
        "exp": 4,
        "gold": 18,
        "weakness": "discount",
        "target": "general",
        "actions": [("hesitation", 0.5), ("haggle", 0.3), ("impulse_buy", 0.2)],
    },
    # Chapter 2-3: 常連客
    "regular_customer": {
        "name": "常連のお客さん",
        "hp": 28,
        "attack": 3,
        "defense": 8,
        "speed": 5,
        "exp": 15,
        "gold": 40,
        "weakness": "smile",
        "target": "general",
        "actions": [("impulse_buy", 0.4), ("bulk_buy", 0.3), ("hesitation", 0.2), ("haggle", 0.1)],
    },
    # Chapter 2: フィールド
    "cautious_merchant": {
        "name": "慎重な商人",
        "hp": 35,
        "attack": 6,
        "defense": 14,
        "speed": 6,
        "exp": 18,
        "gold": 45,
        "weakness": "market_analysis",
        "target": "business",
        "actions": [("hesitation", 0.25), ("haggle", 0.25), ("comparison", 0.2), ("cold_visit", 0.1), ("charge", 0.2)],
    },
    "adventurer_party": {
        "name": "冒険者パーティ(3人)",
        "hp": 45,
        "attack": 5,
        "defense": 10,
        "speed": 8,
        "exp": 25,
        "gold": 55,
        "weakness": "presentation",
        "target": "general",
        "actions": [("hesitation", 0.3), ("haggle", 0.2), ("impulse_buy", 0.3), ("bulk_buy", 0.2)],
    },
    # Chapter 3+: 商店街
    "noble": {
        "name": "目の肥えた貴族",
        "hp": 60,
        "attack": 8,
        "defense": 22,
        "speed": 4,
        "exp": 60,
        "gold": 90,
        "weakness": "limited_offer",
        "target": "enterprise",
        "actions": [("hesitation", 0.15), ("haggle", 0.15), ("comparison", 0.25), ("cold_visit", 0.1), ("bulk_buy", 0.1), ("charge", 0.25)],
    },
    # Chapter 3+: クレーマー
    "complainer": {
        "name": "厳しいクレーマー",
        "hp": 50,
        "attack": 10,
        "defense": 16,
        "speed": 6,
        "exp": 45,
        "gold": 80,
        "weakness": "market_analysis",
        "target": "business",
        "actions": [("haggle", 0.3), ("comparison", 0.3), ("cold_visit", 0.2), ("hesitation", 0.2)],
    },
    # Chapter 2-3: 仕入れ担当バイヤー（field後半の中級敵）
    "buyer": {
        "name": "仕入れ担当バイヤー",
        "hp": 25,
        "attack": 6,
        "defense": 10,
        "speed": 8,
        "exp": 20,
        "gold": 35,
        "actions": [("hesitation", 0.2), ("haggle", 0.3), ("comparison", 0.3), ("impulse_buy", 0.2)],
        "weakness": "discount",
        "target": "business",
    },
    # Chapter 3+: 大口クライアント（dungeon後半の強敵）
    "big_client": {
        "name": "大口クライアント",
        "hp": 70,
        "attack": 8,
        "defense": 20,
        "speed": 4,
        "exp": 80,
        "gold": 100,
        "actions": [("hesitation", 0.15), ("haggle", 0.15), ("comparison", 0.2), ("bulk_buy", 0.2), ("charge", 0.3)],
        "weakness": "presentation",
        "target": "enterprise",
    },
    # レア顧客: VIPクライアント（2%出現）
    "vip_customer": {
        "name": "VIPクライアント",
        "hp": 50,
        "attack": 5,
        "defense": 15,
        "speed": 3,
        "exp": 100,
        "gold": 200,
        "actions": [("hesitation", 0.3), ("impulse_buy", 0.3), ("bulk_buy", 0.2), ("comparison", 0.2)],
        "weakness": "limited_offer",
        "target": "enterprise",
    },
    # ボス: 独占商人
    "boss_merchant": {
        "name": "独占商人ゴウヨク",
        "hp": 120,
        "attack": 10,
        "defense": 20,
        "speed": 12,
        "exp": 200,
        "gold": 500,
        "weakness": "closing",
        "target": "enterprise",
        "actions": [
            ("hesitation", 0.15),
            ("haggle", 0.15),
            ("comparison", 0.1),
            ("price_hike", 0.15),
            ("monopoly", 0.15),
            ("charge", 0.3),
        ],
    },
}

# 客のリアクション（特殊行動）
CUSTOMER_REACTIONS = {
    "hesitation": {"type": "attack", "multiplier": 1.0, "message": "{name}は 迷っている..."},
    "haggle": {"type": "attack", "multiplier": 1.3, "message": "{name}は 値切ってきた！"},
    "comparison": {"type": "debuff_attack", "amount": 3, "message": "{name}「他の店のほうが安い」\nセールス力がさがった！"},
    "cold_visit": {"type": "flee", "message": "{name}は 帰ってしまった..."},
    "impulse_buy": {"type": "boost", "amount": 3, "message": "{name}「これいいね！」\n購買意欲がアップ！"},
    "bulk_buy": {"type": "bulk", "multiplier": 2.0, "message": "{name}「まとめ買いしたい！」\n報酬2倍チャンス！"},
    "price_hike": {"type": "buff_attack", "amount": 5, "message": "{name}は 価格をつりあげた！\nやる気ダメージが増える！"},
    "monopoly": {"type": "buff_defense", "amount": 5, "message": "{name}は 独占を宣言した！\n警戒心があがった！"},
    "charge": {"type": "charge", "message": "{name}は 何か準備している..."},
}

# フィールドごとの出現テーブル
ENCOUNTER_TABLE = {
    "field": [
        ("student", 0.19),
        ("traveler", 0.19),
        ("housewife", 0.19),
        ("buyer", 0.15),
        ("regular_customer", 0.10),
        ("cautious_merchant", 0.10),
        ("adventurer_party", 0.06),
        ("vip_customer", 0.02),
    ],
    "dungeon": [
        ("cautious_merchant", 0.15),
        ("regular_customer", 0.14),
        ("adventurer_party", 0.14),
        ("complainer", 0.15),
        ("buyer", 0.10),
        ("big_client", 0.14),
        ("noble", 0.14),
        ("vip_customer", 0.04),
    ],
}
