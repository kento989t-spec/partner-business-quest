"""在庫・持ち物管理"""
from data.items import ITEMS


class InventorySystem:
    """プレイヤーの持ち物管理"""

    def __init__(self):
        self.items = {}  # {item_id: quantity}
        self.equipped_weapon = None
        self.equipped_armor = None
        self.equipped_shield = None

    def add_item(self, item_id, quantity=1):
        """アイテム追加"""
        self.items[item_id] = self.items.get(item_id, 0) + quantity

    def remove_item(self, item_id, quantity=1):
        """アイテム消費"""
        if self.items.get(item_id, 0) >= quantity:
            self.items[item_id] -= quantity
            if self.items[item_id] <= 0:
                del self.items[item_id]
            return True
        return False

    def has_item(self, item_id, quantity=1):
        return self.items.get(item_id, 0) >= quantity

    def get_count(self, item_id):
        return self.items.get(item_id, 0)

    def equip(self, item_id):
        """装備する"""
        item = ITEMS.get(item_id)
        if not item:
            return False

        if item["type"] == "weapon":
            self.equipped_weapon = item_id
        elif item["type"] == "armor":
            self.equipped_armor = item_id
        elif item["type"] == "shield":
            self.equipped_shield = item_id
        return True

    def get_attack_bonus(self):
        """装備によるセールス力ボーナス"""
        if self.equipped_weapon and self.equipped_weapon in ITEMS:
            return ITEMS[self.equipped_weapon]["value"]
        return 0

    def get_defense_bonus(self):
        """装備によるメンタルボーナス"""
        bonus = 0
        if self.equipped_armor and self.equipped_armor in ITEMS:
            bonus += ITEMS[self.equipped_armor]["value"]
        if self.equipped_shield and self.equipped_shield in ITEMS:
            bonus += ITEMS[self.equipped_shield]["value"]
        return bonus

    def get_all_items(self):
        """持ち物一覧"""
        result = []
        for item_id, qty in self.items.items():
            if item_id in ITEMS:
                result.append(
                    {"id": item_id, "name": ITEMS[item_id]["name"], "quantity": qty}
                )
        return result
