import requests
import uuid
import base64
import umsgpack
import binascii
import hashlib
import datetime
import jwt



OCEANONE_UUID = "aaff5bef-42fb-4c9f-90e0-29f69176b7d4"

def memo_is_pay_from_oceanone(input_snapshot):
    memo_at_snap = input_snapshot.memo
    if input_snapshot.opponent_id != OCEANONE_UUID or float(input_snapshot.amount) < 0:
        return False
    try:
        exin_order = umsgpack.unpackb(base64.b64decode(memo_at_snap), allow_invalid_utf8=True)
        if type(exin_order) == type({}) and "S"in exin_order:
            result = Ocean_response(input_snapshot, exin_order)
            return result

        return False
    except umsgpack.InsufficientDataException:
        return False
    except binascii.Error:
        return False

class Ocean_execute_request_register_pubkey():
    def __init__(self, input_snapshot, msgpack_value):
        self.pay_amount      = abs(float(input_snapshot.amount))
        self.pay_asset       = input_snapshot.asset
        self.pubkey = msgpack_value.get("U")

    def explain(self):
        header = ["opponent", "action", "pubkey", "pay amount", "pay asset"]
        data   = ["OceanOne", "register key", self.pubkey, self.pay_amount, self.pay_asset.symbol]
        return (header, data)

    def __str__(self):
        headString = "register pubkey %s"%(self.pubkey)
        return headString


class Ocean_execute_request_cancel():
    def __init__(self, input_snapshot, msgpack_value):
        self.pay_amount      = abs(float(input_snapshot.amount))
        self.pay_asset       = input_snapshot.asset
        asset_uuid_raw       = msgpack_value.get("O")
        self.to_cancel_order = str(uuid.UUID(bytes = asset_uuid_raw))


    def explain(self):
        header = ["Opponent", "Action", "order be cancelled"]
        data   = ["OceanOne", "Cancel Order", self.to_cancel_order]
        return (header, data)

    def __str__(self):
        headString = "cancel order %s "%(self.to_cancel_order)
        return headString


class Ocean_execute_request_market():
    def __init__(self, input_snapshot, msgpack_value):
        self.pay_amount     = abs(float(input_snapshot.amount))

        asset_uuid_raw      = msgpack_value.get("A")
        self.request_asset  = str(uuid.UUID(bytes = asset_uuid_raw))
        self.pay_asset      = input_snapshot.asset
        self.order          = input_snapshot.trace_id
        self.side_type      = msgpack_value.get("S")
    def explain(self):
        header = ["opponent", "action", "order id", "pay amount", "pay asset", "to exchange asset id"]
        data   = ["OceanOne", "list market order", self.order, self.pay_amount, self.pay_asset.symbol, self.request_asset]
        return (header, data)

    def __str__(self):
        headString = "Market price order to OceanOne: %s, pay %s %s to ocean to exchange %s at price %"%(self.order, self.pay_amount, self.pay_asset.symbol, self.request_asset, self.price)
        return headString


class Ocean_response():
    def __init__(self, input_snapshot, msgpack_value):
        asset_uuid_raw      = msgpack_value.get("A")
        try:
            self.asset_id   = str(uuid.UUID(bytes = asset_uuid_raw))
        except:
            self.asset_id   = str(asset_uuid_raw)
        bid_uuid_raw        = msgpack_value.get("B")
        try:
            self.bid_id     = str(uuid.UUID(bytes = bid_uuid_raw))
        except:
            self.bid_id     = str(bid_uuid_raw)
        order_uuid_raw      = msgpack_value.get("O")
        try:
            self.order_id       = str(uuid.UUID(bytes = order_uuid_raw))
        except:
            self.order_id       = str(order_uuid_raw)
        self.status         = msgpack_value.get("S")
        self.pay_asset      = input_snapshot.asset
    def explain(self):
        header = ["Asset", "Bid", "Order", "Status"]
        data   = [self.asset_id, self.bid_id, self.order_id, self.status]
        return (header, data)

    def __str__(self):
        headString = "Ocean response asset %s, bid %s order %s status %s"%(self.pay_asset.symbol, self.bid_id, self.order_id, self.status)
        return headString


class Ocean_execute_request_limited():
    def __init__(self, input_snapshot, msgpack_value):
        self.pay_amount     = abs(float(input_snapshot.amount))

        asset_uuid_raw      = msgpack_value.get("A")
        self.request_asset  = str(uuid.UUID(bytes = asset_uuid_raw))
        self.pay_asset      = input_snapshot.asset
        self.order          = input_snapshot.trace_id
        self.side_type      = msgpack_value.get("S")
        self.price          = msgpack_value.get("P")
    def explain(self):
        header = ["opponent", "action", "order", "pay amount", "pay asset", "to exchange asset id", "price"]
        data   = ["OceanOne", "list limited price order", self.order, self.pay_amount, self.pay_asset.symbol, self.request_asset, self.price]
        return (header, data)

    def __str__(self):
        headString = "Limit price to OceanOne: %s, pay %s %s to ocean to exchange %s at price %s"%(self.order, self.pay_amount, self.pay_asset.symbol, self.request_asset, self.price)
        return headString


def memo_is_pay_to_ocean(input_snapshot):
    memo_at_snap = input_snapshot.memo
    if input_snapshot.opponent_id != OCEANONE_UUID:
        return False
    try:
        exin_order = umsgpack.unpackb(base64.b64decode(memo_at_snap), allow_invalid_utf8=True)
        if type(exin_order) == type({}) and "A"in exin_order:
            if "P" in exin_order:
                result = Ocean_execute_request_limited(input_snapshot, exin_order)
            else:
                result = Ocean_execute_request_market(input_snapshot, exin_order)
            return result
        elif type(exin_order) == type({}) and (not "A"in exin_order)and ("O"in exin_order):
            result = Ocean_execute_request_cancel(input_snapshot, exin_order)
            return result
        elif type(exin_order) == type({}) and (not "A"in exin_order)and ("U"in exin_order):
            result = Ocean_execute_request_register_pubkey(input_snapshot, exin_order)
            return result
        else:
            return False
    except umsgpack.InsufficientDataException:
        return False
    except binascii.Error:
        return False
    except ValueError:
        return False


def oceanone_can_explain_snapshot(input_snapshot):

    result = memo_is_pay_from_oceanone(input_snapshot)
    if result != False:
        return result
    result = memo_is_pay_to_ocean(input_snapshot)
    if result != False:
        return result
    return False




def gen_memo_ocean_reg_key(key_in_bytes):
    result = {"U":key_in_bytes}
    return base64.b64encode(umsgpack.packb(result)).decode("utf-8")


def gen_memo_ocean_cancel_order(order_uuid):
    result = {"O":uuid.UUID("{" + order_uuid+ "}").bytes}
    return base64.b64encode(umsgpack.packb(result)).decode("utf-8")

def gen_memo_ocean_create_order(asset_id_string, price_string, operation_type, side_operation):
    result = {"S":side_operation, "A":uuid.UUID("{" + asset_id_string + "}").bytes, "P":price_string, "T":operation_type}
    return base64.b64encode(umsgpack.packb(result)).decode("utf-8")

def gen_memo_ocean_bid(asset_id_string, price_string):
    return gen_memo_ocean_create_order(asset_id_string, price_string, "L", "B")
def gen_memo_ocean_ask(asset_id_string, price_string):
    return gen_memo_ocean_create_order(asset_id_string, price_string, "L", "A")


class ocean_order():
    def __init__(self, asset_order):
        self.amount = asset_order.get("amount")
        self.funds  = asset_order.get("funds")
        self.price  = asset_order.get("price")
        self.side   = asset_order.get("side")
class Ocean_pair_price():
    def __init__(self, asset_order_list_result):
        if 'error' in asset_order_list_result:
            return
        asset_order_list = asset_order_list_result.get("data")

        self.market                = asset_order_list.get("market")
        self.event                 = asset_order_list.get("event")
        self.sequence              = asset_order_list.get("sequence")
        self.timestamp             = asset_order_list.get("timestamp")
        self.ask_order_list = []
        self.bid_order_list = []

        data_group = asset_order_list.get("data")
        ask_group_in_data_groups = data_group.get("asks")
        for each in ask_group_in_data_groups:
            self.ask_order_list.append(ocean_order(each))
        bid_group_in_data_groups = data_group.get("bids")
        for each in bid_group_in_data_groups:
            self.bid_order_list.append(ocean_order(each))


def fetchTradePrice(quote_asset_id, target_asset_id):
    url = "https://events.ocean.one/markets/" + target_asset_id + "-" + quote_asset_id+ "/book"
    result_fetchPrice = requests.get(url)
    ocean_response = result_fetchPrice.json()
    this_ocean_pair = Ocean_pair_price(ocean_response)
    return this_ocean_pair
