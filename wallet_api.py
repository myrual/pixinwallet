import csv
from mixin_api import MIXIN_API
from Crypto.PublicKey import RSA
import iso8601
import time
import json
import requests
import base64
import random
import string

def randomString(stringLength=10):
    """Generate a random string of fixed length """
    letters = string.ascii_lowercase
    return ''.join(random.choice(letters) for i in range(stringLength))


def pubkeyContent(inputContent):
    contentWithoutHeader= inputContent[len("-----BEGIN PUBLIC KEY-----") + 1:]
    contentWithoutTail = contentWithoutHeader[:-1 * (len("-----END PUBLIC KEY-----") + 1)]
    contentWithoutReturn = contentWithoutTail[:64] + contentWithoutTail[65:129] + contentWithoutTail[130:194] + contentWithoutTail[195:]
    return contentWithoutReturn

class MIXIN_config():
    def __init__(self):
        self.private_key       = ""
        self.pin_token         = ""
        self.pay_session_id    = ""
        self.client_id         = ""
        self.client_secret     = ""
        self.pay_pin           = ""

def generateMixinAPI(private_key,pin_token,session_id,user_id,pin,client_secret):
    mixin_config = MIXIN_config()
    mixin_config.private_key       = private_key
    mixin_config.pin_token         = pin_token
    mixin_config.pay_session_id    = session_id
    mixin_config.client_id         = user_id
    mixin_config.client_secret     = client_secret
    mixin_config.pay_pin           = pin
    return  MIXIN_API(mixin_config)


class RSAKey4Mixin():
    def __init__(self):
        key = RSA.generate(1024)
        pubkey = key.publickey()
        private_key = key.exportKey()
        session_key = pubkeyContent(pubkey.exportKey())
        self.session_key = session_key.decode()
        self.private_key = private_key.decode()

class Mixin_Wallet_API_Result_Error():
    def __init__(self, dictInput):
        self.status      = dictInput.get("status")
        self.code        = dictInput.get("code")
        self.description = dictInput.get("description")
    def __str__(self):
        return "%s with status: %s, code: %s"%(self.description, self.status, self.code)

class Mixin_Wallet_HTTP_Result_Error():
    def __init__(self, dictInput):
        self.http_code        = dictInput
    def __str__(self):
        return "http visit failed with code %d "%(self.http_code)





class Mixin_Wallet_API_Result():
    def __init__(self, jsonInput, processFunc = None):
        if ("httpfailed" in jsonInput):
            self.is_success = False
            self.error      = Mixin_Wallet_HTTP_Result_Error(jsonInput.get("httpfailed"))
        elif ("error" in jsonInput):
            self.is_success = False
            self.error      = Mixin_Wallet_API_Result_Error(jsonInput.get("error"))
        else:
            self.is_success = True
            if processFunc != None:
                self.data = processFunc(jsonInput.get("data"))
    def __str__(self):
        if(self.is_success):
            if hasattr(self, 'data'):
                return  str(self.data)
            else:
                return "Success"
        else:
            return str(self.error)

class userInfo():
    def __init__(self, userInfojson):
        self.pin_token  = userInfojson.get("pin_token")
        self.session_id = userInfojson.get("session_id")
        self.user_id    = userInfojson.get("user_id")
    def fromcreateUserJson(self, userInfojson):
        self.pin_token  = userInfojson.get("pin_token")
        self.session_id = userInfojson.get("session_id")
        self.user_id    = userInfojson.get("user_id")

class Static_Asset():
    def __init__(self, jsonInput = ""):
        if jsonInput == "":
            return
        self.type     = jsonInput.get("type")
        self.name     = jsonInput.get("name")
        self.asset_id = jsonInput.get("asset_id")
        self.chain_id = jsonInput.get("chain_id")
        self.symbol   = jsonInput.get("symbol")
 
class Asset(Static_Asset):
    def __init__(self, jsonInput):
        self.type     = jsonInput.get("type")
        self.name     = jsonInput.get("name")
        self.asset_id = jsonInput.get("asset_id")
        self.chain_id = jsonInput.get("chain_id")
        self.balance  = jsonInput.get("balance")
        self.symbol   = jsonInput.get("symbol")
        self.public_key   = jsonInput.get("public_key")
        self.account_name = jsonInput.get("account_name")
        self.account_tag  = jsonInput.get("account_tag")
        self.asset_key = jsonInput.get("asset_key")
        self.price_usd = jsonInput.get("price_usd")
        self.confirmations = jsonInput.get("confirmations")
        self.capitalization = jsonInput.get("capitalization")

    def deposit_address(self):
        result_desposit = []
        if(self.public_key != ""):
            result_desposit.append({"title":"Deposit address", "value":self.public_key})
        if(self.account_name!= ""):
            result_desposit.append({"title":"Deposit account name", "value":self.account_name})
        if(self.account_tag!= ""):
            result_desposit.append({"title":"Deposit account tag", "value":self.account_tag})
        return result_desposit

class Withdrawal():
    def __init__(self, jsonInput):
        self.snapshot_id = jsonInput.get("snapshot_id")
        self.transaction_hash = jsonInput.get("transaction_hash")
        self.asset_id = jsonInput.get("asset_id")
        self.amount = jsonInput.get("amount")
        self.trace_id = jsonInput.get("trace_id")
        self.memo = jsonInput.get("memo")
        self.created_at = jsonInput.get("created_at")


class Snapshot():
    def __init__(self, jsonInput = ""):

        if jsonInput == "":
            return
        self.amount = jsonInput.get("amount")
        self.type = jsonInput.get("type")
        self.asset = Static_Asset(jsonInput.get("asset"))
        self.created_at = jsonInput.get("created_at")
        self.memo = jsonInput.get("data")
        self.snapshot_id = jsonInput.get("snapshot_id")
        self.source = jsonInput.get("source")
        self.user_id = jsonInput.get("user_id")
        self.trace_id = jsonInput.get("trace_id")
        self.opponent_id = jsonInput.get("opponent_id")
    def __str__(self):
        string_result = ""
        string_result += (self.amount.ljust(15))
        string_result += (" " + self.asset.symbol.ljust(10))
        string_result += " created at:" + self.created_at.ljust(30)
        if self.user_id != None:
            string_result += (" from " + self.user_id)
        if self.opponent_id != None:
            string_result += (" to " + self.opponent_id)
        if (self.trace_id != None):
            string_result += (" trace id:" + self.trace_id)
        if (self.memo != None):
            string_result += (" memo:" + self.memo)
        return string_result

    def is_sent(self):
        return float(self.amount) < 0
    def is_received(self):
        return float(self.amount) > 0
    def is_my_snap(self):
        return self.user_id != None

class Address():
    def __init__(self, jsonInput):
        self.address_id   = jsonInput.get("address_id")
        self.public_key   = jsonInput.get("public_key")
        self.asset_id     = jsonInput.get("asset_id")
        self.label        = jsonInput.get("label")
        self.account_name = jsonInput.get("account_name")
        self.account_tag  = jsonInput.get("account_tag")
        self.fee          = jsonInput.get("fee")
        self.reserve      = jsonInput.get("reserve")
        self.dust         = jsonInput.get("dust")
        self.updated_at   = jsonInput.get("updated_at")
    def __str__(self):
        result  = "\n"
        prefix = " "
        if self.label != "":
            result += prefix + "tag          : %s\n"%self.label

        if self.public_key != "":
            result += prefix + "Address : %s\n"%self.public_key

        if self.account_name!= "":
            result += prefix + "Account name : %s\n"%self.account_name

        if self.account_tag!= "":
            result += prefix + "Account memo : %s\n"%self.account_tag
        result += prefix + "fee          : %s\n"%self.fee
        result += prefix + "dust         : %s\n"%self.dust
        return result
def Address_list(jsonInputList):
    result = []
    for i in jsonInputList:
        result.append(Address(i))
    return result

def Asset_list(jsonInputList):
    result = []
    for i in jsonInputList:
        result.append(Asset(i))
    return result

def Snapshot_list(jsonInputList):
    result = []
    for i in jsonInputList:
        result.append(Snapshot(i))
    return result





class User_result():
    def __init__(self, data_dict):
        self.user_id    = data_dict.get("user_id")
        self.full_name  = data_dict.get("full_name")
        self.has_pin    = data_dict.get("has_pin")
        self.type       = data_dict.get("type")
        self.created_at = data_dict.get("created_at")
        self.session_id = data_dict.get("session_id")
            
    def __str__(self):
        """Format: Name on the first line
        and all grades on the second line,
        separated by spaces.
        """
        result = "" 
        result += self.full_name + " is created at " + self.created_at + " with user id:" + self.user_id
        if self.has_pin:
            result += ". Pin is created"
        else:
            result += ". wallet need to create pin"
        return result

class Transfer_result():
    def __init__(self, data_dict):

        self.amount       = data_dict.get("amount")
        self.memo         = data_dict.get("memo")
        self.snapshot_id  = data_dict.get("snapshot_id")
        self.asset_id     = data_dict.get("asset_id")
        self.type         = data_dict.get("type")
        self.trace_id     = data_dict.get("trace_id")
        self.opponent_id  = data_dict.get("opponent_id")
        self.created_at   = data_dict.get("created_at")
            
    def __str__(self):
        """Format: Name on the first line
        and all grades on the second line,
        separated by spaces.
        """
        result = "Successfully transfer %s %s to %s at %s with trace id:%s, snapshot id:%s"%(self.amount, self.asset_id, self.opponent_id, self.created_at, self.trace_id, self.snapshot_id)
        return result

class Transfer_Mainnet_result():
    def __init__(self, data_dict):

        self.amount       = data_dict.get("amount")
        self.memo         = data_dict.get("memo")
        self.snapshot_id  = data_dict.get("snapshot")
        self.asset_id     = data_dict.get("asset_id")
        self.type         = data_dict.get("type")
        self.trace_id     = data_dict.get("trace_id")
        self.opponent_key  = data_dict.get("opponent_key")
        self.created_at   = data_dict.get("created_at")
        self.state = data_dict.get("state")
        self.transaction_hash = data_dict.get("transaction_hash")
        self.snapshot_hash = data_dict.get("snapshot_hash")
        self.snapshot_at = data_dict.get("snapshot_at")
            
    def __str__(self):
        """Format: Name on the first line
        and all grades on the second line,
        separated by spaces.
        """
        result = "Successfully transfer %s %s to %s at %s with trace id:%s, snapshot id:%s, transaction hash %s, snapshot hash %s, snapshot_at %s"%(self.amount, self.asset_id, self.opponent_key, self.created_at, self.trace_id, self.snapshot_id, self.transaction_hash, self.snapshot_hash, self.snapshot_at)
        return result
def fetchTokenForCreateUser(body, url):
    body_in_json = json.dumps(body)
    headers = {
        'Content-Type'  : 'application/json',
    }
    r = requests.post(url, json=body, headers=headers)
    result_obj = r.json()
    return result_obj.get("token")

def top_asset_mixin_network():

    headers = {
        'Content-Type': 'application/json',
        'Content-length': '0',
    }
    response = requests.get('https://api.mixin.one/network/assets/top', headers=headers)
    result_obj = response.json()
    if "data" in result_obj:
        asset_array = result_obj.get("data")
        return Asset_list(asset_array)


def find_f_in_pbft(totalNodes):
    for f in range(totalNodes):
        if(((3*f+1) <= totalNodes) and ((3 * f + 4) > totalNodes)):
            return f
    return 0
    
def minimum_nodes_attack_mixin(totalNodes):
    return find_f_in_pbft(totalNodes) + 1

def minimum_nodes_control_mixin(totalNodes):
    return find_f_in_pbft(totalNodes) * 2 + 1

class WalletRecord():
    def __init__(self, pin, userid, session_id, pin_token, private_key):
       self.pin = pin
       self.userid = userid
       self.session_id = session_id
       self.pin_token = pin_token
       self.private_key = private_key
       self.mixinAPIInstance = generateMixinAPI(self.private_key,
                                                            self.pin_token,
                                                            self.session_id,
                                                            self.userid,
                                                            self.pin,"")

    def create_wallet(self, session_key, account_name, token_for_create_wallet):
        userInfoJson = self.mixinAPIInstance.createUser(session_key, account_name, token_for_create_wallet)
        created_user_result = Mixin_Wallet_API_Result(userInfoJson, userInfo)
        return created_user_result
    def get_balance(self):
        all_assets_json = self.mixinAPIInstance.getMyAssets()
        all_balance = Mixin_Wallet_API_Result(all_assets_json, Asset_list)
        return all_balance

    def get_singleasset_balance(self, input_asset_id):
        single_asset_json = self.mixinAPIInstance.getAsset(input_asset_id)
        return Mixin_Wallet_API_Result(single_asset_json, Asset)
    def get_asset_withdrawl_addresses(self, input_asset_id):
        asset_addresses_json = self.mixinAPIInstance.withdrawals_address(input_asset_id)
        asset_withdraw_addresses = Mixin_Wallet_API_Result(asset_addresses_json, Address_list)
        return asset_withdraw_addresses
    def create_address(self, asset_id, public_key = "", label = "", asset_pin = "", account_name = "", account_tag = ""):
        create_result_json = self.mixinAPIInstance.createAddress(asset_id, public_key , label , asset_pin , account_name , account_tag )
        createAddress_result = Mixin_Wallet_API_Result(create_result_json ,Address)
        return createAddress_result
    def remove_address(self, to_be_deleted_address_id, input_pin):
        remove_result_json = self.mixinAPIInstance.delAddress(to_be_deleted_address_id, input_pin)
        removeAddress_result = Mixin_Wallet_API_Result(remove_result_json)
        return removeAddress_result

    def transfer_to(self, destination_uuid, asset_id, amount_tosend, memo_input, this_uuid, asset_pin_input):
        transfer_result_json = self.mixinAPIInstance.transferTo(destination_uuid, asset_id, amount_tosend, memo_input, this_uuid, asset_pin_input)
        transfer_result = Mixin_Wallet_API_Result(transfer_result_json, Transfer_result)
        return transfer_result

    def transfer_to_mainnet(self, destination_key, asset_id, amount_tosend, memo_input, this_uuid, asset_pin_input):
        transfer_result_json = self.mixinAPIInstance.transferTo_MainNet(destination_key, asset_id, amount_tosend, memo_input, this_uuid, asset_pin_input)
        print(transfer_result_json)
        transfer_result = Mixin_Wallet_API_Result(transfer_result_json, Transfer_Mainnet_result)
        return transfer_result


    def withdraw_asset_to(self, address_id, withdraw_amount, withdraw_memo, withdraw_this_uuid, withdraw_asset_pin):
        asset_withdraw_result_json = self.mixinAPIInstance.withdrawals(address_id, withdraw_amount, withdraw_memo, withdraw_this_uuid, withdraw_asset_pin)
        withdraw_result = Mixin_Wallet_API_Result(asset_withdraw_result_json, Withdrawal)
        return withdraw_result
    def fetch_my_profile(self):
        my_profile_json = self.mixinAPIInstance.getMyProfile("")
        user_result = Mixin_Wallet_API_Result(my_profile_json, User_result)
        return user_result

    def verify_pin(self, input_pin):
        verify_pin_result_json = self.mixinAPIInstance.verifyPin(input_pin)
        user_result = Mixin_Wallet_API_Result(verify_pin_result_json, User_result)
        return user_result

    def update_pin(self, input_old_pin, input_new_pin):
        update_pin_result_json = self.mixinAPIInstance.updatePin(input_new_pin, input_old_pin)
        user_result = Mixin_Wallet_API_Result(update_pin_result_json, User_result)
        return user_result

    def account_snapshots_after(self, timestamp, asset_id, max_record_quantity):
        snapshots_json = self.mixinAPIInstance.account_snapshots_after(timestamp, asset_id, max_record_quantity)
        snapshots_list_result = Mixin_Wallet_API_Result(snapshots_json, Snapshot_list)
        return snapshots_list_result

    def my_snapshots_after(self, timestamp, asset_id = "", limit = 500, retry = 10):
        counter = 0
        mysnapshots_result = []
        last_time = timestamp
        while((len(mysnapshots_result) < limit )  and ((time.time() - iso8601.parse_date(last_time).timestamp()) > 2)):
            counter += 1
            snapshots_json = self.mixinAPIInstance.account_snapshots_after(last_time, asset_id, 500)
            snapshots_list_result = Mixin_Wallet_API_Result(snapshots_json, Snapshot_list)
            if(snapshots_list_result.is_success):
                snapshots_result = snapshots_list_result.data
                last_time = snapshots_result[-1].created_at
                for singleSnapShot in snapshots_result:
                    if (singleSnapShot.is_my_snap()):
                        mysnapshots_result.append(singleSnapShot)
            else:
                break
        return mysnapshots_result
    def find_snapshot(self, snapshot_id):
        snapshot_json = self.mixinAPIInstance.account_snapshot(snapshot_id)
        print(snapshot_json)
        return

def find_snapshot_of(client_id, in_snapshots):
    mysnapshots_result = []
    for singleSnapShot in in_snapshots:
        if (singleSnapShot.user_id == client_id):
            mysnapshots_result.append(singleSnapShot)
    return mysnapshots_result
def snapshot_time_difference_now(snap_shopt):
    diff = time.time() - iso8601.parse_date(snap_shopt.created_at).timestamp()
    remain = (", timestamp: %s"%snap_shopt.created_at)
    if int(diff) > 0:
        diff_in_day = int(diff/(60 * 60 * 24))
        if diff_in_day > 0:
            return "Receiving records happened %s day ago"%(diff_in_day) + remain
        diff_in_hour = int(diff/(60 * 60))
        if diff_in_hour > 0:
            return "Receiving records happened %s hour ago"%(diff_in_hour) + remain

        diff_in_minute = int(diff/(60))
        if diff_in_minute > 0:
            return "Receiving records happened %s minute ago"%(diff_in_minute) + remain
        return "Receiving records happened %s seconds ago"%(int(diff)) + remain
    else:
        return "synced " + remain
def append_wallet_into_csv_file(this_wallet, file_name):
    with open(file_name, 'a', newline='') as csvfile:
        csvwriter = csv.writer(csvfile)
        csvwriter.writerow([this_wallet.private_key,
                            this_wallet.pin_token,
                            this_wallet.session_id,
                            this_wallet.user_id,
                            ""])

def write_wallet_into_clear_base64_file(this_wallet, file_name):
    finalObj = {"uid":this_wallet.user_id, "sid":this_wallet.session_id, "pintoken":this_wallet.pin_token, "key":this_wallet.private_key}
    jsonstring_fromobj = json.dumps(finalObj)
    base64decoded_json = base64.b64encode(jsonstring_fromobj.encode('utf-8')).decode('utf-8')
    print(base64decoded_json)
    with open(file_name, 'w') as wallet_file:
        wallet_file.write(base64decoded_json)

def load_wallet_from_clear_base64_file(file_name):
    with open(file_name) as wallt_file:
        base64decoded_json = wallt_file.read()
        jsonstring = base64.b64decode(base64decoded_json)
        wallet_dict = json.loads(jsonstring)
        this_wallet_inst = WalletRecord("", wallet_dict.get("uid"), wallet_dict.get("sid"), wallet_dict.get("pintoken"), wallet_dict.get("key"))
        return this_wallet_inst


def load_wallet_csv_file(file_name):
    with open(file_name, newline='') as csvfile:
        reader  = csv.reader(csvfile)

        wallet_records = []
        for row in reader:

            pin         = row.pop()
            userid      = row.pop()
            session_id  = row.pop()
            pin_token   = row.pop()
            private_key = row.pop()
            wallet_records.append(WalletRecord(pin, userid, session_id, pin_token, private_key))
        return wallet_records
def create_wallet_csv_file(file_name):
    with open(file_name, newline='') as csvfile:
        reader  = csv.reader(csvfile)

        wallet_records = []
        for row in reader:

            pin         = row.pop()
            userid      = row.pop()
            session_id  = row.pop()
            pin_token   = row.pop()
            private_key = row.pop()
            wallet_records.append(WalletRecord(pin, userid, session_id, pin_token, private_key))
        return wallet_records
