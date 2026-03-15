"""フィールド画面 - マップ移動（v2: トランジション・BGM対応）"""
import pyxel
import random

from data.maps import (
    MAPS,
    WALKABLE,
    TILE_BUILDING,
    TILE_GRASS,
    TILE_WALL,
    TILE_WATER,
    TILE_PATH,
    TILE_TREE,
    TILE_SHOP,
    BUILDING_EVENTS,
    MAP_TRANSITIONS,
    ENCOUNTER_RATE,
    MAP_NPCS,
    TREASURE_CHESTS,
)
from data.events import get_npc_dialogues, PARTNER_EVENTS
from data.customers import ENCOUNTER_TABLE
from input_helper import btn_up, btn_down, btn_left, btn_right, btn_confirm, btn_cancel


TILE_SIZE = 16

# タイルのスプライト位置（16x16スプライト、イメージバンク0の座標）
TILE_SPRITES = {
    TILE_GRASS: (32, 16),
    TILE_WALL: (80, 16),
    TILE_WATER: (48, 16),
    TILE_PATH: (64, 16),
    TILE_BUILDING: (0, 16),
    TILE_TREE: (16, 16),
    TILE_SHOP: (32, 32),
}


class FieldScene:
    def __init__(self, game):
        self.game = game
        self.current_map = "home"
        self.camera_x = 0
        self.camera_y = 0
        self.step_count = 0
        self.dialogue_queue = []
        self.current_dialogue_index = 0
        self.in_event = False
        self.walk_frame = 0  # 歩行アニメフレーム（0=静止, 1=歩行）
        self.player_direction = "down"  # プレイヤーの向き
        self.npcs = []  # 現在マップのNPCリスト
        self.npc_walk_timer = 0  # NPC歩行タイマー
        self._tutorial_done = False  # チュートリアルバトル済みフラグ
        self._intro_shown = False   # チャプター1イントロ表示済みフラグ
        self.current_talk_sprite = None  # NPC会話時のスプライト

    def on_enter(self, **kwargs):
        map_name = kwargs.get("map", self.current_map)
        self.current_map = map_name
        if "x" in kwargs:
            self.game.player.x = kwargs["x"]
        if "y" in kwargs:
            self.game.player.y = kwargs["y"]
        self._update_camera()

        # NPC初期化
        self.npcs = []
        for npc_data in MAP_NPCS.get(map_name, []):
            self.npcs.append({
                "id": npc_data["id"],
                "x": npc_data["x"],
                "y": npc_data["y"],
                "origin_x": npc_data["x"],
                "origin_y": npc_data["y"],
                "sprite": npc_data["sprite"],
                "walk": npc_data.get("walk", False),
                "walk_range": npc_data.get("walk_range", 1),
            })
        self.npc_walk_timer = 0

        # マップに応じたBGM
        bgm_map = {"home": "town", "field": "field", "dungeon": "boss"}
        bgm = bgm_map.get(map_name, "field")
        self.game.play_bgm(bgm)

        # 初回フィールド進入時のチュートリアルバトル
        if map_name == "field" and not self._tutorial_done:
            self._tutorial_done = True
            def start_tutorial(_):
                self.game.change_scene_with_transition("battle", enemy_id="student")
            self.game.message_window.show(
                "フィールドに出た！\nさっそくお客さんが来たようだ。\n\n初めての商談に挑もう！",
                on_close=start_tutorial
            )

        # 初回チャプター1イントロ＋長老の指示
        if self.game.chapter.current_chapter == 1 and self.step_count == 0 and not self._intro_shown:
            self._intro_shown = True
            intro = self.game.chapter.chapter_info.get("intro", "")
            if intro:
                def after_intro(_):
                    # 長老の会話を自動開始
                    self._start_dialogue("elder")
                self.game.message_window.show(intro, on_close=after_intro)

        # チャプタークリアチェック
        self._check_chapter_clear()

    def _update_camera(self):
        px = self.game.player.x * TILE_SIZE
        py = self.game.player.y * TILE_SIZE
        self.camera_x = max(0, px - 128 + TILE_SIZE // 2)
        self.camera_y = max(0, py - 120 + TILE_SIZE // 2)

    def _can_walk(self, x, y):
        map_data = MAPS.get(self.current_map)
        if not map_data:
            return False
        if y < 0 or y >= len(map_data) or x < 0 or x >= len(map_data[0]):
            return False
        if map_data[y][x] not in WALKABLE:
            return False
        # NPCの位置は通行不可
        for npc in self.npcs:
            if npc["x"] == x and npc["y"] == y:
                return False
        return True

    def _check_transition(self):
        key = (self.current_map, self.game.player.x, self.game.player.y)
        if key in MAP_TRANSITIONS:
            dest_map, dest_x, dest_y = MAP_TRANSITIONS[key]
            self.game.change_scene_with_transition(
                "field", map=dest_map, x=dest_x, y=dest_y
            )
            return True
        return False

    def _check_encounter(self):
        # repel（客足遠ざけ）チェック
        if self.game.player.repel_steps > 0:
            self.game.player.repel_steps -= 1
            return False
        rate = ENCOUNTER_RATE.get(self.current_map, 0)
        if rate > 0 and random.random() < rate:
            table = ENCOUNTER_TABLE.get(self.current_map, [])
            if table:
                r = random.random()
                cumulative = 0
                for enemy_id, prob in table:
                    cumulative += prob
                    if r <= cumulative:
                        self.game.change_scene_with_transition(
                            "battle", enemy_id=enemy_id
                        )
                        return True
        return False

    def _check_building_event(self):
        key = (self.current_map, self.game.player.x, self.game.player.y)
        event = BUILDING_EVENTS.get(key)
        if not event:
            return

        self.game.play_se("confirm")
        if event["type"] == "shop":
            self.game.change_scene_with_transition("shop", shop_id=event["shop_id"])
        elif event["type"] == "rest":
            p = self.game.player
            if p.hp < p.max_hp:
                old_hp = p.hp
                p.hp = p.max_hp
                self.game.play_se("heal")
                self.game.message_window.show(
                    f"自宅で休憩した！\nやる気が全回復！\n({old_hp} → {p.max_hp})"
                )
            else:
                self.game.message_window.show("やる気は十分だ！\n外に出て頑張ろう！")
        elif event["type"] == "talk":
            self.current_talk_sprite = None  # 建物イベントにはスプライトなし
            self._start_dialogue(event["npc_id"])
        elif event["type"] == "info":
            self.game.message_window.show(event["message"])

    def _check_npc_talk(self):
        """プレイヤーの隣接タイルにNPCがいたら会話開始"""
        px, py = self.game.player.x, self.game.player.y
        for npc in self.npcs:
            if (abs(npc["x"] - px) + abs(npc["y"] - py)) == 1:
                self.game.play_se("confirm")
                self.current_talk_sprite = npc["sprite"]
                self._start_dialogue(npc["id"])
                return True
        return False

    def _check_treasure(self):
        """宝箱チェック"""
        px, py = self.game.player.x, self.game.player.y
        for dx, dy in [(0, 0), (0, -1), (0, 1), (-1, 0), (1, 0)]:
            key = (self.current_map, px + dx, py + dy)
            chest = TREASURE_CHESTS.get(key)
            if chest and chest["id"] not in self.game.player.opened_chests:
                self.game.player.opened_chests.add(chest["id"])
                self.game.play_se("trade")
                if chest["type"] == "gold":
                    self.game.player.gold += chest["value"]
                elif chest["type"] == "item":
                    self.game.inventory.add_item(chest["item_id"])
                # 実績: 宝箱5個以上発見
                if len(self.game.player.opened_chests) >= 5:
                    self.game.player.achievements.add("treasure_hunter")
                self.game.message_window.show(f"宝箱を開けた！\n{chest['message']}")
                return True
        return False

    def _update_npc_walk(self):
        """歩くNPCをランダムに移動"""
        map_data = MAPS.get(self.current_map)
        if not map_data:
            return
        for npc in self.npcs:
            if not npc["walk"]:
                continue
            directions = [(0, -1), (0, 1), (-1, 0), (1, 0)]
            random.shuffle(directions)
            for dx, dy in directions:
                nx, ny = npc["x"] + dx, npc["y"] + dy
                # マップ範囲チェック
                if ny < 0 or ny >= len(map_data) or nx < 0 or nx >= len(map_data[0]):
                    continue
                # 通行可能タイルか
                if map_data[ny][nx] not in WALKABLE:
                    continue
                # 歩行範囲チェック
                if abs(nx - npc["origin_x"]) > npc["walk_range"]:
                    continue
                if abs(ny - npc["origin_y"]) > npc["walk_range"]:
                    continue
                # プレイヤーと重ならない
                if nx == self.game.player.x and ny == self.game.player.y:
                    continue
                # 他のNPCと重ならない
                occupied = False
                for other in self.npcs:
                    if other is not npc and other["x"] == nx and other["y"] == ny:
                        occupied = True
                        break
                if occupied:
                    continue
                npc["x"] = nx
                npc["y"] = ny
                break

    def _start_dialogue(self, npc_id):
        dialogues = get_npc_dialogues(npc_id, self.game)
        if not dialogues:
            return
        self.dialogue_queue = dialogues
        self.current_dialogue_index = 0
        self.in_event = True
        self._show_next_dialogue()

    def _show_next_dialogue(self):
        if self.current_dialogue_index >= len(self.dialogue_queue):
            self.in_event = False
            self.dialogue_queue = []
            return

        dialogue = self.dialogue_queue[self.current_dialogue_index]
        choices = dialogue.get("choices")

        def on_close(choice_index):
            if choice_index is not None and "choice_event" in dialogue:
                event_data = PARTNER_EVENTS.get(dialogue["choice_event"], {})
                choice_result = event_data.get(choice_index)
                if choice_result:
                    action = choice_result.get("action")
                    if action == "set_partner_type":
                        self.game.partner_system.sign_contract(
                            "武器屋", choice_result["value"]
                        )
                        self._check_chapter_clear()
                    elif action == "give_reward":
                        event_id = dialogue.get("choice_event", "")
                        if event_id not in self.game.player.quiz_completed:
                            self.game.player.quiz_completed.add(event_id)
                            self.game.player.gold += choice_result["value"]
                        else:
                            choice_result = {"text": "おっと、もう報酬は渡したよ！\nでもクイズの復習はいつでも歓迎さ。"}
                    elif action == "start_boss_battle":
                        self.game.message_window.show(
                            choice_result["text"],
                            on_close=lambda _: self.game.change_scene_with_transition(
                                "battle", enemy_id="boss_merchant"
                            ),
                        )
                        return
                    self.game.message_window.show(
                        choice_result["text"],
                        on_close=lambda _: self._advance_dialogue(),
                    )
                    return
            self._advance_dialogue()

        self.game.message_window.show(
            dialogue["text"], on_close=on_close, choices=choices,
            speaker_sprite=self.current_talk_sprite
        )

    def _advance_dialogue(self):
        self.current_dialogue_index += 1
        self._show_next_dialogue()

    def _check_random_event(self):
        """ランダムイベント（フィールドのみ）"""
        if self.current_map == "home":
            return False
        if random.random() < 0.03:  # 3%の確率
            events = [
                ("道端に落ちていた小銭を拾った！\n+10G", "gold", 10),
                ("通りすがりの人から\nアドバイスをもらった！\nやる気+5回復！", "heal", 5),
                ("珍しい商品のヒントを\n教えてもらった！\nEXP+3！", "exp", 3),
            ]
            event = random.choice(events)
            self.game.play_se("trade")
            if event[1] == "gold":
                self.game.player.gold += event[2]
            elif event[1] == "heal":
                p = self.game.player
                p.hp = min(p.max_hp, p.hp + event[2])
            elif event[1] == "exp":
                self.game.player.total_exp += event[2]
            self.game.message_window.show(event[0])
            return True
        return False

    def _check_chapter_clear(self):
        """チャプタークリア条件チェック"""
        ch = self.game.chapter
        if ch.check_chapter_clear(self.game):
            old_ch = ch.current_chapter
            if ch.advance_chapter():
                self.game.play_se("level_up")
                # クリアボーナス
                bonus_gold = {2: 100, 3: 200, 4: 300}.get(ch.current_chapter, 0)
                if bonus_gold > 0:
                    self.game.player.gold += bonus_gold
                intro = ch.chapter_info.get("intro", "")
                bonus_text = f"\nクリアボーナス: {bonus_gold}G！" if bonus_gold > 0 else ""
                def show_intro(_):
                    if intro:
                        self.game.message_window.show(intro)
                self.game.message_window.show(
                    f"━━━━━━━━━━━━━━\n"
                    f"  第{old_ch}章 クリア！{bonus_text}\n"
                    f"━━━━━━━━━━━━━━\n"
                    f"第{ch.current_chapter}章: {ch.chapter_info['title']}\n"
                    f"目標: {ch.chapter_info['goal']}",
                    on_close=show_intro
                )
            elif old_ch == 4 and ch.boss_defeated:
                # ゲームクリア！
                self.game.change_scene_with_transition("ending")

    def update(self):
        if self.game.message_window.active:
            self.game.message_window.update()
            return

        if self.in_event:
            return

        moved = False
        px, py = self.game.player.x, self.game.player.y

        if btn_up(8, 4):
            self.player_direction = "up"
            if self._can_walk(px, py - 1):
                self.game.player.y -= 1
                moved = True
        elif btn_down(8, 4):
            self.player_direction = "down"
            if self._can_walk(px, py + 1):
                self.game.player.y += 1
                moved = True
        elif btn_left(8, 4):
            self.player_direction = "left"
            if self._can_walk(px - 1, py):
                self.game.player.x -= 1
                moved = True
        elif btn_right(8, 4):
            self.player_direction = "right"
            if self._can_walk(px + 1, py):
                self.game.player.x += 1
                moved = True

        if moved:
            self._update_camera()
            self.step_count += 1
            self.walk_frame = 1 - self.walk_frame  # 歩行フレーム切り替え
            if self._check_transition():
                return
            if self._check_random_event():
                return
            if self._check_encounter():
                return

        # NPC歩行処理
        self.npc_walk_timer += 1
        if self.npc_walk_timer >= 30:
            self.npc_walk_timer = 0
            self._update_npc_walk()

        if btn_confirm():
            # NPC会話→宝箱→建物イベントの優先順
            if not self._check_npc_talk():
                if not self._check_treasure():
                    self._check_building_event()

        if btn_cancel():
            self.game.play_se("confirm")
            self.game.change_scene("menu")

    def draw(self):
        t = self.game.text
        map_data = MAPS.get(self.current_map, [])

        # マップ描画（16x16スプライト）
        for y, row in enumerate(map_data):
            for x, tile in enumerate(row):
                sx = x * TILE_SIZE - self.camera_x
                sy = y * TILE_SIZE - self.camera_y
                if -TILE_SIZE <= sx < 256 and -TILE_SIZE <= sy < 240:
                    sprite_pos = TILE_SPRITES.get(tile)
                    if sprite_pos:
                        pyxel.blt(sx, sy, 0, sprite_pos[0], sprite_pos[1], 16, 16, 0)
                    else:
                        pyxel.rect(sx, sy, TILE_SIZE, TILE_SIZE, 0)

        # NPC描画
        for npc in self.npcs:
            npc_sx = npc["x"] * TILE_SIZE - self.camera_x
            npc_sy = npc["y"] * TILE_SIZE - self.camera_y
            if -TILE_SIZE <= npc_sx < 256 and -TILE_SIZE <= npc_sy < 240:
                sp = npc["sprite"]
                pyxel.blt(npc_sx, npc_sy, 0, sp[0], sp[1], 16, 16, 0)

        # 宝箱描画（未開封のみ）
        for (map_name, cx, cy), chest in TREASURE_CHESTS.items():
            if map_name == self.current_map and chest["id"] not in self.game.player.opened_chests:
                sx = cx * TILE_SIZE - self.camera_x
                sy = cy * TILE_SIZE - self.camera_y
                if -TILE_SIZE <= sx < 256 and -TILE_SIZE <= sy < 240:
                    # 小さな宝箱アイコン（簡易描画）
                    pyxel.rect(sx + 3, sy + 6, 10, 8, 10)  # 箱本体（黄色）
                    pyxel.rect(sx + 3, sy + 4, 10, 3, 9)   # 蓋（橙色）
                    pyxel.rect(sx + 7, sy + 5, 2, 2, 7)     # 錠前（白）

        # プレイヤー描画（16x16, 歩行アニメ＋向き対応）
        player_sx = self.game.player.x * TILE_SIZE - self.camera_x
        player_sy = self.game.player.y * TILE_SIZE - self.camera_y
        # 左移動時はスプライトを左右反転（幅を-16にする）
        if self.player_direction == "left":
            w = -16
        else:
            w = 16
        if self.walk_frame == 1:
            pyxel.blt(player_sx, player_sy, 0, 96, 0, w, 16, 0)
        else:
            pyxel.blt(player_sx, player_sy, 0, 0, 0, w, 16, 0)

        # === ステータスバー (y=0-26, 2行×14px) ===
        pyxel.rect(0, 0, 256, 28, 1)
        pyxel.rectb(0, 0, 256, 28, 7)
        p = self.game.player
        # 1行目 (y=2): Lv+名前 + やる気バー
        t(8, 2, f"Lv:{p.level} {p.name}", 7)
        hp_ratio = p.hp / p.max_hp if p.max_hp > 0 else 0
        t(120, 2, "やる気", 7)
        pyxel.rect(164, 4, 48, 6, 5)
        if hp_ratio > 0.66:
            hp_bar_color = 11  # 緑
        elif hp_ratio > 0.33:
            hp_bar_color = 10  # 黄
        else:
            hp_bar_color = 8   # 赤
        pyxel.rect(164, 4, int(48 * hp_ratio), 6, hp_bar_color)
        t(216, 2, f"{p.hp}/{p.max_hp}", 7)
        # 2行目 (y=16): 所持金 + パートナー/コンボ
        t(8, 16, f"所持金:{p.gold}G", 10)
        # パートナー状態 or コンボ表示
        contract = self.game.partner_system.active_contract
        if contract:
            ps = self.game.partner_system
            ptype = "紹介" if contract.contract_type == "referral" else "販売"
            t(120, 16, f"[{ptype}]ランク:{ps.rank}", 10)
        if self.game.player.combo_count >= 2:
            t(210, 16, f"★{self.game.player.combo_count}連!", 10)

        # === 下部情報バー (y=212-240, 2行×14px) ===
        pyxel.rect(0, 212, 256, 28, 1)
        pyxel.rectb(0, 212, 256, 28, 5)
        ch = self.game.chapter
        map_names = {"home": "自分の町", "field": "フィールド", "dungeon": "商店街"}
        # 1行目 (y=214): チャプター+マップ + 操作ガイド
        t(8, 214, f"第{ch.current_chapter}章 {map_names.get(self.current_map, '')}", 7)
        t(130, 214, "十字:移動 A:調べる B:メニュー", 6)

        # 2行目 (y=228): チャプター進捗
        goal_text = ""
        if ch.current_chapter == 1:
            goal_text = f"売上:{ch.total_sales_gold}/500G"
        elif ch.current_chapter == 2:
            ps = self.game.partner_system
            goal_text = f"ランク:{ps.rank}(C目標)"
        elif ch.current_chapter == 3:
            ps = self.game.partner_system
            goal_text = f"ランク:{ps.rank}(B目標)"
        elif ch.current_chapter == 4:
            goal_text = "最終商談に挑め!"
        if goal_text:
            t(8, 228, f"目標: {goal_text}", 10)

        # ミニマップ描画
        self._draw_minimap()

    def _draw_minimap(self):
        """ミニマップ描画（右上）"""
        map_data = MAPS.get(self.current_map, [])
        if not map_data:
            return

        # ミニマップ位置とサイズ
        scale = 3  # 1タイル = 3x3ピクセル
        mw = len(map_data[0]) * scale
        mh = len(map_data) * scale
        mx = 256 - mw - 4  # 右上（右端から4px余白）
        my = 30  # ステータスバーの下

        # 背景と枠
        pyxel.rect(mx - 1, my - 1, mw + 2, mh + 2, 1)
        pyxel.rectb(mx - 1, my - 1, mw + 2, mh + 2, 5)

        # タイルの色マッピング
        tile_colors = {
            0: 3,   # 草→緑
            1: 5,   # 壁→灰
            2: 12,  # 水→青
            3: 4,   # 道→茶
            4: 9,   # 建物→橙
            5: 3,   # 木→緑
            6: 10,  # ショップ→黄
        }

        for y, row in enumerate(map_data):
            for x, tile in enumerate(row):
                color = tile_colors.get(tile, 0)
                pyxel.rect(mx + x * scale, my + y * scale, scale, scale, color)

        # 宝箱表示（未開封のみ、黄色ドット）
        for (map_name, cx, cy), chest in TREASURE_CHESTS.items():
            if map_name == self.current_map and chest["id"] not in self.game.player.opened_chests:
                tx = mx + cx * scale + 1
                ty = my + cy * scale + 1
                pyxel.rect(tx, ty, 1, 1, 10)

        # NPC表示（明緑ドット）
        for npc in self.npcs:
            nx = mx + npc["x"] * scale + 1
            ny = my + npc["y"] * scale + 1
            pyxel.rect(nx, ny, 1, 1, 11)

        # プレイヤー位置（点滅する白ドット）
        px = mx + self.game.player.x * scale + 1
        py_pos = my + self.game.player.y * scale + 1
        if pyxel.frame_count % 20 < 14:
            pyxel.rect(px, py_pos, 1, 1, 7)
