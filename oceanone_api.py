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
        return str(exin_order)
    except umsgpack.InsufficientDataException:
        return False
    except binascii.Error:
        return False

def memo_is_pay_to_ocean(input_snapshot):
    memo_at_snap = input_snapshot.memo
    if input_snapshot.opponent_id != OCEANONE_UUID:
        return False
    try:
        exin_order = umsgpack.unpackb(base64.b64decode(memo_at_snap), allow_invalid_utf8=True)

        if type(exin_order) == type({}) and "A"in exin_order:
            result = "exchange %s at price %s "%(str(uuid.UUID(bytes = exin_order.get("A"))), exin_order.get("P"))
            return result
        elif type(exin_order) == type({}) and (not "A"in exin_order)and ("O"in exin_order):
            result = "cancel order %s"%(str(uuid.UUID(bytes = exin_order.get("O"))))
            return result
        elif type(exin_order) == type({}) and (not "A"in exin_order)and ("U"in exin_order):
            result = "register public key %s"%(str(exin_order.get("O")))
            return result
        else:
            return "Failed to explain"

    except umsgpack.InsufficientDataException:
        return input_snapshot.memo
    except binascii.Error:
        return input_snapshot.memo
    except ValueError:
        return exin_order


def oceanone_can_explain_snapshot(input_snapshot):

    result = memo_is_pay_from_oceanone(input_snapshot)
    if result != False:
        return {"opponent_name":"OceanOne Exchange", "memo":str(memo_is_pay_from_oceanone(input_snapshot))}
    result = memo_is_pay_to_ocean(input_snapshot)
    if result != False:
        return {"opponent_name":"OceanOne Exchange", "memo":str(memo_is_pay_to_ocean(input_snapshot))}
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
    print(url)
    result_fetchPrice = requests.get(url)
    ocean_response = result_fetchPrice.json()
    print(ocean_response)
    this_ocean_pair = Ocean_pair_price(ocean_response)
    return this_ocean_pair
