"""パートナー契約管理システム（v2: ランクシステム追加）"""


# パートナーランク定義
PARTNER_RANKS = {
    "D": {"min_sales": 0, "label": "見習い"},
    "C": {"min_sales": 500, "label": "一人前"},
    "B": {"min_sales": 2000, "label": "ベテラン"},
    "A": {"min_sales": 6000, "label": "マスター"},
}

RANK_ORDER = ["D", "C", "B", "A"]


class PartnerContract:
    """パートナー契約"""

    def __init__(self, partner_name, contract_type, shop_id="weapon_shop"):
        self.partner_name = partner_name
        self.contract_type = contract_type  # "referral" or "reseller"
        self.shop_id = shop_id
        self.active = True
        self.total_sales = 0
        self.total_fees = 0

    @property
    def fee_rate(self):
        if self.contract_type == "referral":
            return 0.15
        elif self.contract_type == "reseller":
            return 0.40
        return 0

    @property
    def has_inventory_risk(self):
        return self.contract_type == "reseller"

    def calculate_fee(self, sale_amount):
        """フィー計算"""
        fee = int(sale_amount * self.fee_rate)
        self.total_sales += sale_amount
        self.total_fees += fee
        return fee


class PartnerSystem:
    """パートナービジネスシステム（v2）"""

    def __init__(self):
        self.contracts = []
        self.partner_inventory = {}
        self._rank = "D"
        self._cumulative_sales = 0

    @property
    def has_contract(self):
        return len(self.contracts) > 0

    @property
    def active_contracts(self):
        return [c for c in self.contracts if c.active]

    @property
    def active_contract(self):
        """後方互換: 最初のアクティブ契約"""
        for c in self.contracts:
            if c.active:
                return c
        return None

    @property
    def rank(self):
        return self._rank

    @property
    def rank_label(self):
        return PARTNER_RANKS[self._rank]["label"]

    @property
    def cumulative_sales(self):
        return self._cumulative_sales

    @property
    def next_rank(self):
        idx = RANK_ORDER.index(self._rank)
        if idx < len(RANK_ORDER) - 1:
            return RANK_ORDER[idx + 1]
        return None

    @property
    def sales_to_next_rank(self):
        nr = self.next_rank
        if nr:
            return max(0, PARTNER_RANKS[nr]["min_sales"] - self._cumulative_sales)
        return 0

    def _update_rank(self):
        """累計売上に基づいてランクを更新"""
        old_rank = self._rank
        for rank in reversed(RANK_ORDER):
            if self._cumulative_sales >= PARTNER_RANKS[rank]["min_sales"]:
                self._rank = rank
                break
        return self._rank != old_rank  # ランクアップしたらTrue

    def sign_contract(self, partner_name, contract_type, shop_id="weapon_shop"):
        """パートナー契約を結ぶ"""
        contract = PartnerContract(partner_name, contract_type, shop_id)
        self.contracts.append(contract)
        return contract

    def add_partner_inventory(self, item_id, quantity):
        """販売代理店の在庫追加"""
        self.partner_inventory[item_id] = (
            self.partner_inventory.get(item_id, 0) + quantity
        )

    def sell_partner_item(self, item_id, price):
        """パートナー商品を販売。フィーを返す"""
        contract = self.active_contract
        if not contract:
            return 0, False

        if contract.contract_type == "reseller":
            if self.partner_inventory.get(item_id, 0) <= 0:
                return 0, False
            self.partner_inventory[item_id] -= 1

        fee = contract.calculate_fee(price)
        self._cumulative_sales += price
        rank_up = self._update_rank()
        return fee, rank_up

    def on_party_wipe(self):
        """全滅時の在庫損失処理"""
        contract = self.active_contract
        if not contract or not contract.has_inventory_risk:
            return {}

        lost_items = {}
        for item_id, qty in self.partner_inventory.items():
            lost = qty // 2
            if lost > 0:
                lost_items[item_id] = lost
                self.partner_inventory[item_id] -= lost

        return lost_items

    def get_contract_for_shop(self, shop_id):
        """指定ショップの契約を取得"""
        for c in self.contracts:
            if c.active and c.shop_id == shop_id:
                return c
        return None
