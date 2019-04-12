import requests
import uuid
import base64
import umsgpack
import binascii
EXINCORE_UUID   = "61103d28-3ac2-44a2-ae34-bd956070dab1"


class Asset_pair_price():
    def __init__(self, asset_price_in_exin):
        self.minimum_amount = asset_price_in_exin.get("minimum_amount")
        self.maximum_amount = asset_price_in_exin.get("maximum_amount")
        self.price       = asset_price_in_exin.get("price")
        self.base_asset_symbol               = asset_price_in_exin.get("base_asset_symbol")
        self.exchange_asset_symbol             = asset_price_in_exin.get("exchange_asset_symbol")
        self.base_asset               = asset_price_in_exin.get("base_asset")
        self.echange_asset             = asset_price_in_exin.get("exchange_asset")
        self.supported_by_exchanges = ""

        for eachExchange in asset_price_in_exin.get("exchanges"):
            self.supported_by_exchanges += eachExchange
            self.supported_by_exchanges += " "
    def __str__(self):
        result = "%s %s %s, exchange: %s"%(self.price.ljust(8), (self.base_asset_symbol)+"/"+self.exchange_asset_symbol.ljust(15), "min:"+self.minimum_amount.ljust(10)+" max:"+ self.maximum_amount.ljust(10)+ self.base_asset_symbol.ljust(20), self.supported_by_exchanges)
        return result
    def debug_str(self):
        result = "%s %s %s, exchange: %s base:%s target:%s"%(self.price.ljust(8), (self.base_asset_symbol)+"/"+self.exchange_asset_symbol.ljust(15), "min:"+self.minimum_amount+" max:"+ self.maximum_amount+ self.base_asset_symbol.ljust(20), self.supported_by_exchanges, self.base_asset, self.echange_asset)
        return result

def fetchExinPrice(source_asset_id , target_asset_id = ""):
    result_fetchPrice = requests.get('https://exinone.com/exincore/markets', params={'base_asset':source_asset_id, "exchange_asset":target_asset_id})
    exin_response = result_fetchPrice.json()

    datalist_in_response = []
    if (exin_response.get("code") == 0):
        for eachData in exin_response.get("data"):
            datalist_in_response.append(Asset_pair_price(eachData))
    return datalist_in_response

def gen_memo_ExinBuy(asset_id_string):
    return base64.b64encode(umsgpack.packb({"A": uuid.UUID("{" + asset_id_string + "}").bytes})).decode("utf-8")

def memo_is_pay_to_exin(input_snapshot):
    memo_at_snap = input_snapshot.memo
    try:
        exin_order = umsgpack.unpackb(base64.b64decode(memo_at_snap))

        if "A"in exin_order:
            target_asset_uuid_in_myorder = str(uuid.UUID(bytes = exin_order["A"]))

            my_request_to_exin = Exin_execute_request(input_snapshot, target_asset_uuid_in_myorder)
            return my_request_to_exin
        else:
            return False
    except umsgpack.InsufficientDataException:
        return False
    except binascii.Error:
        return False

EXIN_EXEC_TYPE_REQUEST = 0
EXIN_EXEC_TYPE_RESULT  = 1

class Exin_execute():
    def __init__(self, execute_type):
        self.execute_type = execute_type
    def is_request(self):
        return self.execute_type == EXIN_EXEC_TYPE_REQUEST
    def is_result(self):
        return self.execute_type == EXIN_EXEC_TYPE_RESULT


class Exin_execute_request(Exin_execute):
    def __init__(self, input_snapshot, target_asset_id):
        self.pay_amount     = abs(float(input_snapshot.amount))
        self.request_asset  = target_asset_id
        self.pay_asset      = input_snapshot.asset
        self.order          = input_snapshot.trace_id
        super().__init__(EXIN_EXEC_TYPE_REQUEST)
    def __str__(self):
        headString = "order: %s, pay %s %s to exin to buy %s "%(self.order, self.pay_amount, self.pay_asset.symbol, self.request_asset)
        return headString

class Exin_execute_result(Exin_execute):
    def __init__(self, exin_order):
        self.order_result   = exin_order["C"]
        self.price          = exin_order["P"]
        self.fee            = exin_order["F"]
        self.fee_asset_type = exin_order["FA"]
        self.type           = exin_order["T"]
        self.order          = exin_order["O"]
        super().__init__(EXIN_EXEC_TYPE_RESULT)
    def __str__(self):
        headString = "Status of your payment to exin is : "
        if(self.order_result == 1000):
            headString = headString + "Successful Exchange"
            headString = headString + ", your order is executed at price:" +  self.price
            headString = headString + ", Exin core fee is " + self.fee  + " with fee asset" + str(uuid.UUID(bytes = self.fee_asset_type))

        if(self.order_result == 1001):
            headString = headString + "The order not found or invalid"
        if(self.order_result == 1002):
            headString = headString + "The request data is invalid"
        if(self.order_result == 1003):
            headString = headString + "The market not supported"
        if(self.order_result == 1004):
            headString = headString + "Failed exchange"
        if(self.order_result == 1005):
            headString = headString + "Partial exchange"
        if(self.order_result == 1006):
            headString = headString + "Insufficient pool"
        if(self.order_result == 1007):
            headString = headString + "Below the minimum exchange amount"
        if(self.order_result == 1008):
            headString = headString + "Exceeding the maximum exchange amount"
        if (self.type == "F"):
            headString = headString +", your order is refund to you because your memo is not correct"
        if (self.type == "R"):
            headString = headString +", your order is executed successfully"
        if (self.type == "E"):
            headString = headString +", exin failed to execute your order"
        headString = headString +", trace id of your payment to exincore is " + str(uuid.UUID(bytes = self.order))
        return headString



def memo_is_pay_from_exin(input_snapshot):
    memo_at_snap = input_snapshot.memo
    try:
        exin_order = Exin_execute_result(umsgpack.unpackb(base64.b64decode(memo_at_snap)))
        return exin_order
    except umsgpack.InsufficientDataException:
        return False
    except binascii.Error:
        return False




def about_me(input_snapshot):
    exin_request = memo_is_pay_to_exin(input_snapshot)
    if exin_request != False:
        return exin_request
    exin_result = memo_is_pay_from_exin(input_snapshot)
    if exin_result != False:
        return exin_result
    return False
