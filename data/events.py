"""イベント・会話データ（v3: 販売バトル版）"""


def get_npc_dialogues(npc_id, game):
    """チャプターやフラグに応じた会話を返す"""
    chapter = game.chapter.current_chapter
    has_contract = game.partner_system.has_contract

    if npc_id == "elder":
        if chapter == 1:
            return ELDER_CH1
        elif chapter == 2 and not has_contract:
            return ELDER_CH2_PRE
        elif chapter == 2:
            return ELDER_CH2
        elif chapter >= 3:
            return ELDER_CH3
        else:
            return ELDER_DEFAULT

    elif npc_id == "villager":
        if chapter == 1:
            return VILLAGER_CH1
        elif chapter >= 3:
            return VILLAGER_CH3
        elif has_contract:
            return VILLAGER_WITH_CONTRACT
        else:
            return VILLAGER_DEFAULT

    elif npc_id == "weapon_shop_owner":
        if has_contract:
            return WEAPON_SHOP_AFTER
        else:
            return WEAPON_SHOP_FIRST

    elif npc_id == "armor_shop_owner":
        return ARMOR_SHOP_DIALOGUE

    elif npc_id == "quiz_npc":
        if chapter == 1:
            return QUIZ_CH1
        elif chapter == 2:
            return QUIZ_CH2
        elif chapter >= 3:
            return QUIZ_CH3
        else:
            return QUIZ_NPC

    elif npc_id == "dungeon_merchant1":
        if game.chapter.boss_defeated:
            return [{"text": "ゴウヨクがいなくなって\n商売がしやすくなったよ！\nありがとう！"}]
        elif chapter >= 4:
            return [{"text": "ゴウヨクが奥にいるぞ。\n気をつけてくれ..."},
                    {"text": "ヤツは価格をつり上げたり\n独占を宣言してくる。\n市場分析で対抗だ！"}]
        else:
            return [{"text": "ここは商店街だ。\n最近は独占商人ゴウヨクのせいで\n客が減ってしまった..."}]

    elif npc_id == "dungeon_merchant2":
        return [{"text": "商店街には強い客が多い。\n装備を整えてから来るんだぞ。"},
                {"text": "ランクが上がれば\n強い資格や研修が買えるようになる。"}]

    elif npc_id == "boss_room":
        if game.chapter.boss_defeated:
            return [
                {"text": "...参ったな。\nお前のセールスには負けたよ。"},
                {"text": "オレも昔はお前みたいに\nまっすぐ商売してたんだ。\nいつの間にか独占に走ってた..."},
                {"text": "パートナーか。\nそういうやり方もあるんだな。\n...悪くないかもしれん。"},
            ]
        elif chapter >= 4:
            return BOSS_ROOM_CH4
        else:
            return [{"text": "奥に何かの気配がする...\nまだ準備が足りないだろう。"}]

    return NPC_DIALOGUES.get(npc_id, [{"text": "..."}])


# === 長老の会話 ===
ELDER_CH1 = [
    {"text": "おお、ナオトか。\nお前の親父は立派な商人じゃった。\nわしも昔は商売をしておったんじゃ。"},
    {"text": "最初はな、誰でもうまくいかん。\nじゃが諦めずに続ければ\n道は開けるもんじゃ。"},
    {"text": "まずはフィールドに出て\nお客さんと商談してみるんじゃ。\n「特技」を使い分けるのがコツじゃぞ。"},
    {"text": "あ、それとな...\n道具屋で装備を整えてから\n出発するんじゃぞ。\n裸一貫では商売にならんからのう。"},
]

ELDER_CH2_PRE = [
    {"text": "ほう、腕を上げたのう！\nお前を見ていると\n昔の自分を思い出すわい。"},
    {"text": "じゃがな、一人の力には限界がある。\nわしもそれで苦労したんじゃ..."},
    {"text": "東のフィールドに\nタケシという男がおる。\nヤツと手を組めば\n商売の幅が広がるぞ。"},
    {"text": "「紹介代理店」か「販売代理店」か...\nどちらにもリスクとリターンがある。\nよく考えて選ぶんじゃぞ。"},
]

ELDER_CH2 = [
    {"text": "おお、パートナー契約を\n結んだようじゃな！\n大したもんじゃ。"},
    {
        "text": "商売のコツを教えてやろう。\n何が知りたい？",
        "choices": ["攻めのコツ", "守りのコツ"],
        "choice_event": "elder_advice",
    },
    {"text": "パートナービジネスには\n二つの形態がある。"},
    {"text": "「紹介代理店」はフィー15%じゃが\n在庫リスクがない。\n安定した収入が見込めるぞ。"},
    {"text": "「販売代理店」はフィー40%と\n高リターンじゃが、\n仕入れコストがかかる。"},
    {"text": "どちらが正解ということはない。\nどんどん売上を伸ばして\nランクCを目指すんじゃ！"},
]

ELDER_CH3 = [
    {"text": "大変じゃ！\n独占商人ゴウヨクのせいで\n仕入れ値が上がっておる！"},
    {"text": "ヤツが市場を支配して\n価格をつり上げとるんじゃ。\nこのままでは皆が困る..."},
    {"text": "お前のセールス力で\nヤツとの商談に勝ってくれ！\n北の商店街にヤツはおる。"},
    {"text": "じゃが気をつけるんじゃ。\nヤツは溜め攻撃で\n一気に叩いてくるぞ。\n準備を見たら笑顔で凌ぐんじゃ！"},
    {"text": "クロスセルというのはな、\n自社の道具とパートナーの研修を\nセットで提案することじゃ。"},
    {"text": "セット販売すると\n利益が1.3倍になるし、\n客の警戒心も下がるぞ。\nパートナーの力を活かすんじゃ！"},
]

ELDER_DEFAULT = [
    {"text": "お客さんとの商談は順調かの？\nコツコツ売上を積み上げるんじゃぞ。"},
]

# === 村人の会話 ===
VILLAGER_CH1 = [
    {"text": "あ、ナオト！\n商売始めたんだって？\n頑張ってね！"},
    {"text": "あのね、知ってた？\n自宅で休めば\nやる気が全回復するんだよ！\n疲れたら無理しないでね。"},
    {"text": "あと、フィールドには\n宝箱が落ちてることがあるらしいよ。\n隅々まで探してみたら？"},
]

VILLAGER_DEFAULT = [
    {"text": "道具屋さん、いつもお世話になってます！"},
    {"text": "外に出ればお客さんが来るはず。\nセールストークで頑張ってね！"},
    {"text": "メニューからステータスや\n持ち物を確認できるよ。\n便利だから使ってみて！"},
]

VILLAGER_WITH_CONTRACT = [
    {"text": "パートナー契約を結んだんですか！\nそれは頼もしいですね！"},
    {"text": "品揃えが充実すれば\nお客さんも喜びますよ。"},
    {"text": "ランクが上がると\n仕入れられる商品も増えるって\n聞いたことがあるよ。"},
]

VILLAGER_CH3 = [
    {"text": "ねえ聞いた？\n北の商店街で独占商人ってやつが\n暴れてるんだって..."},
    {"text": "ゴウヨクって名前らしいよ。\n元は普通の商人だったけど\n欲に目がくらんだんだとか..."},
    {"text": "あの人、溜め攻撃してくるらしいよ。\n「準備している」って表示が出たら\n次のターンは防御的にいった方がいいかも！"},
    {"text": "あ、あと商品説明を使うと\n相手の弱点がわかるって噂だよ！\nぜひ試してみて！"},
]

# === 防具屋の会話 ===
ARMOR_SHOP_DIALOGUE = [
    {"text": "いらっしゃい！\nここはメンタル研修所だよ。"},
    {"text": "ストレスケアやレジリエンスなど\nメンタルを鍛える研修を\n取り揃えているよ。"},
    {"text": "ランクが上がれば\nもっと上級の研修も受けられるぞ。\n中の看板から見てくれ！"},
]

# === 武器屋→パートナー候補の会話 ===
WEAPON_SHOP_FIRST = [
    {"text": "よう！隣町から来たのか！\nオレはタケシ。\nセールス用品を扱ってるんだ。"},
    {"text": "お前さん、なかなか\n見どころがあるじゃねぇか。\nオレと組まないか？"},
    {
        "text": "一緒にやれば\nお互いの商品を紹介し合えるし\n客の幅も広がるってもんだ！",
        "choices": ["紹介代理店として契約する", "販売代理店として契約する", "もう少し考える"],
        "choice_event": "partner_contract",
    },
]

WEAPON_SHOP_AFTER = [
    {"text": "おう、パートナー！\n調子はどうだ？"},
    {"text": "コツコツ売上を\n積み上げていけば\nランクも上がるぜ。\nそうすりゃ仕入れの幅も広がる！"},
    {"text": "困った時は特技を使い分けろ。\n相手によって効く技が違うからな。\n商品説明で弱点を探るのも手だぜ！"},
]

# === ボス部屋 ===
BOSS_ROOM_CH4 = [
    {"text": "...ほう、ここまで来たか。\n道具屋の小僧が。"},
    {"text": "この市場はオレのものだ。\n価格も客も、すべてオレが決める。\nそれが効率ってもんだろう？"},
    {
        "text": "最後の商談だ。\n覚悟はいいか？",
        "choices": ["挑む！", "準備してから来る"],
        "choice_event": "boss_challenge",
    },
]

# === クイズNPC（チャプター別） ===
QUIZ_CH1 = [
    {"text": "やあ！ビジネスクイズの時間だ！\n正解すると50Gもらえるよ。"},
    {
        "text": "問題！\n商談で「やる気」が0になったら\nどうなる？",
        "choices": ["所持金が半分になる", "何もペナルティはない"],
        "choice_event": "quiz_ch1",
    },
]

QUIZ_CH2 = [
    {"text": "おっ、パートナー契約したんだね！\nじゃあちょっと難しい問題！"},
    {
        "text": "問題！\n紹介代理店と販売代理店、\nフィー率が高いのはどっち？",
        "choices": ["紹介代理店（15%）", "販売代理店（40%）"],
        "choice_event": "quiz_fee_rate",
    },
]

QUIZ_CH3 = [
    {"text": "ここまで来たか！\n最後の問題だ！"},
    {
        "text": "問題！\nパートナービジネスで\n最も重要なのは？",
        "choices": ["自分だけ儲かること", "お互いにWin-Winであること", "とにかく安く売ること"],
        "choice_event": "quiz_ch3",
    },
]

# レガシー互換用（デフォルト）
QUIZ_NPC = [
    {"text": "やあ！パートナービジネス\n検定を受けてみないかい？"},
    {
        "text": "問題！\n紹介代理店と販売代理店、\nフィー率が高いのはどっち？",
        "choices": ["紹介代理店（15%）", "販売代理店（40%）"],
        "choice_event": "quiz_fee_rate",
    },
]


# === レガシー互換用 ===
NPC_DIALOGUES = {
    "elder": ELDER_CH1,
    "villager": VILLAGER_DEFAULT,
    "weapon_shop_owner": WEAPON_SHOP_FIRST,
    "armor_shop_owner": ARMOR_SHOP_DIALOGUE,
}

# パートナー契約イベント
PARTNER_EVENTS = {
    "partner_contract": {
        0: {
            "text": "紹介代理店か！\nお客を紹介してくれたら\nフィー（売上の15%）を払うよ。\n在庫リスクはないから安心だ！",
            "action": "set_partner_type",
            "value": "referral",
        },
        1: {
            "text": "販売代理店か！\nウチの商品を仕入れて売ってくれ。\nフィー（売上の40%）は高いが、\n在庫を持つリスクがあるぞ。",
            "action": "set_partner_type",
            "value": "reseller",
        },
        2: {
            "text": "そうか、じゃあまた来てくれ。\nいつでも待ってるぜ！",
        },
    },
    "elder_advice": {
        0: {
            "text": "攻めじゃな。\n商品説明で弱点を探り、\n弱点スキルで畳みかけるんじゃ。\n\nそうすれば1.5倍の効果じゃぞ！",
            "action": "give_reward",
            "value": 30,
        },
        1: {
            "text": "守りじゃな。\n笑顔で対応で回復しつつ、\n敵の溜め攻撃に備えるんじゃ。\n\n装備を整えれば被ダメも減るぞ。",
            "action": "give_reward",
            "value": 30,
        },
    },
    "boss_challenge": {
        0: {
            "text": "いざ、最終商談！",
            "action": "start_boss_battle",
        },
        1: {
            "text": "そうだな、準備は大事だ。\n万全の状態で挑もう。",
        },
    },
    "quiz_ch1": {
        0: {
            "text": "残念！ 失注してもペナルティはないんだ。\n気軽に挑戦できるのが\nこの世界のいいところ！",
        },
        1: {
            "text": "正解！ さすがだね！\n失敗を恐れず挑戦しよう！",
            "action": "give_reward",
            "value": 50,
        },
    },
    "quiz_fee_rate": {
        0: {
            "text": "残念！\n紹介代理店は15%、\n販売代理店は40%だよ。\n販売代理店の方が高リターンだが、\n在庫リスクもあるんだ。",
        },
        1: {
            "text": "正解！\n販売代理店は40%と高フィーだが、\n在庫を持つリスクもある。\nリスクとリターンのバランスが\nビジネスの基本だね！",
            "action": "give_reward",
            "value": 50,
        },
    },
    "quiz_ch3": {
        0: {
            "text": "残念... 自分だけ儲かっても\n長続きしないよ。",
        },
        1: {
            "text": "大正解！ Win-Winの関係が\nパートナービジネスの核心だ！\nさすが上級者！",
            "action": "give_reward",
            "value": 100,
        },
        2: {
            "text": "安売りは利益を圧迫する。\n価値を伝えることが大事だよ。",
        },
    },
}
