from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *

import time
import traceback, sys
import wallet_api
import mixin_asset_id_collection
import sqlalchemy
import mixin_sqlalchemy_type
import exincore_api


class WorkerSignals(QObject):
    finished = pyqtSignal()
    error = pyqtSignal(tuple)
    result = pyqtSignal(object)
    progress = pyqtSignal(object)
class Asset_addresses_Thread(QRunnable):
    def __init__(self, wallet_obj, asset_obj, *args, **kwargs):
        super(Asset_addresses_Thread, self).__init__()
        self.wallet_obj = wallet_obj
        self.asset_obj  = asset_obj
        self.args = args
        self.kwargs = kwargs
        self.signals = WorkerSignals()

    @pyqtSlot()
    def run(self):
        try:
            result = self.wallet_obj.get_asset_withdrawl_addresses(self.asset_obj.asset_id)
        except:
            traceback.print_exc()
            exctype, value = sys.exc_info()[:2]
            self.signals.error.emit((exctype, value, traceback.format_exc()))
        else:
            self.signals.result.emit(result)
        finally:
            self.signals.finished.emit()
        print("Withdraw address of asset Thread")


class AccountsSnapshots_Thread(QRunnable):
    def __init__(self, wallet_obj, starttime, delay_seconds = 0, *args, **kwargs):
        super(AccountsSnapshots_Thread, self).__init__()
        self.wallet_obj = wallet_obj
        self.starttime = starttime
        self.delay_seconds = delay_seconds
        self.args = args
        self.kwargs = kwargs
        self.signals = WorkerSignals()

    @pyqtSlot()
    def run(self):
        try:
            time.sleep(self.delay_seconds)
            result = self.wallet_obj.account_snapshots_after(self.starttime, "", 500)
        except:
            traceback.print_exc()
            exctype, value = sys.exc_info()[:2]
            self.signals.error.emit((exctype, value, traceback.format_exc()))
        else:
            self.signals.result.emit(result)
        finally:
            self.signals.finished.emit()
        print("Balance Thread")

class ExinPrice_Thread(QRunnable):
    def __init__(self, base_asset_id, target_asset_id = "", delay_seconds = 0,  *args, **kwargs):
        super(ExinPrice_Thread, self).__init__()
        self.target_asset_id = target_asset_id
        self.base_asset_id = base_asset_id
        self.delay_seconds = delay_seconds
        self.args = args
        self.kwargs = kwargs
        self.signals = WorkerSignals()

    @pyqtSlot()
    def run(self):
        try:
            time.sleep(self.delay_seconds)
            result = exincore_api.fetchExinPrice(self.base_asset_id, self.target_asset_id)
        except:
            traceback.print_exc()
            exctype, value = sys.exc_info()[:2]
            self.signals.error.emit((exctype, value, traceback.format_exc()))
        else:
            self.signals.result.emit(result)
        finally:
            self.signals.finished.emit()
        print("Balance Thread")

class Balance_Thread(QRunnable):
    def __init__(self, wallet_obj, delay_seconds = 0,  *args, **kwargs):
        super(Balance_Thread, self).__init__()
        self.wallet_obj = wallet_obj
        self.delay_seconds = delay_seconds
        self.args = args
        self.kwargs = kwargs
        self.signals = WorkerSignals()

    @pyqtSlot()
    def run(self):
        try:
            time.sleep(self.delay_seconds)
            result = self.wallet_obj.get_balance()
        except:
            traceback.print_exc()
            exctype, value = sys.exc_info()[:2]
            self.signals.error.emit((exctype, value, traceback.format_exc()))
        else:
            self.signals.result.emit(result)
        finally:
            self.signals.finished.emit()
        print("Balance Thread")
class UserProfile_Thread(QRunnable):
    def __init__(self, wallet_obj, *args, **kwargs):
        super(UserProfile_Thread, self).__init__()
        self.wallet_obj = wallet_obj
        self.args = args
        self.kwargs = kwargs
        self.signals = WorkerSignals()

    @pyqtSlot()
    def run(self):
        try:
            result = self.wallet_obj.fetch_my_profile()
        except:
            traceback.print_exc()
            exctype, value = sys.exc_info()[:2]
            self.signals.error.emit((exctype, value, traceback.format_exc()))
        else:
            self.signals.result.emit(result)
        finally:
            self.signals.finished.emit()
        print("Balance Thread")


class CreateAccount_Thread(QRunnable):
    def __init__(self, user_input_name, user_input_pin, user_input_file, *args, **kwargs):
        super(CreateAccount_Thread, self).__init__()
        self.user_input_name = user_input_name
        self.user_input_pin  = user_input_pin
        self.user_input_file = user_input_file
        self.args = args
        self.kwargs = kwargs
        self.signals = WorkerSignals()

    @pyqtSlot()
    def run(self):
        try:
            self.signals.progress.emit("Generating key file")
            thisAccountRSAKeyPair = wallet_api.RSAKey4Mixin()
            body = {
                "session_secret": thisAccountRSAKeyPair.session_key,
                "full_name": self.user_input_name
            }
            wallet_obj = wallet_api.WalletRecord("","","", "","")
            self.signals.progress.emit("Fetching authentication token to create wallet")
            token2create = wallet_api.fetchTokenForCreateUser(body, "http://freemixinapptoken.myrual.me/token")

            self.signals.progress.emit("Creating wallet")
            create_wallet_result = wallet_obj.create_wallet(thisAccountRSAKeyPair.session_key, self.user_input_name, token2create)
            if(create_wallet_result.is_success):
                self.signals.progress.emit("Writing wallet into file")

                create_wallet_result.data.private_key = thisAccountRSAKeyPair.private_key
                new_wallet = wallet_api.WalletRecord("",create_wallet_result.data.user_id, create_wallet_result.data.session_id, create_wallet_result.data.pin_token, create_wallet_result.data.private_key)
     
                wallet_api.write_wallet_into_clear_base64_file(create_wallet_result.data, self.user_input_file)
                create_pin_result = new_wallet.update_pin("", self.user_input_pin)
                if(create_pin_result.is_success):
                    self.signals.progress.emit("Pin is created")
                else:
 
                    self.signals.progress.emit("Failed to create pin. Update pin later")
                self.signals.progress.emit("Generating deposit address")
                for eachAssetID in mixin_asset_id_collection.MIXIN_DEFAULT_CHAIN_GROUP:
                    this_balance = new_wallet.get_singleasset_balance(eachAssetID)
                    if(this_balance.is_success):
                        self.signals.progress.emit("Generated deposit address for " + this_balance.data.name)
                self.signals.result.emit(True)
            else:
                self.signals.progress.emit("Failed to create wallet")
        except:
            traceback.print_exc()
            exctype, value = sys.exc_info()[:2]
            self.signals.error.emit((exctype, value, traceback.format_exc()))
        else:
            self.signals.result.emit(True)
        finally:
            self.signals.finished.emit()


class Balance_TableModel(QAbstractTableModel):
    """
    keep the method names
    they are an integral part of the model
    """
    def __init__(self, parent, balance_result_list, header, *args):
        QAbstractTableModel.__init__(self, parent, *args)
        finalData = []
        for eachAsset in balance_result_list:
            thisRecord = []
            thisRecord.append(eachAsset.name)
            thisRecord.append(eachAsset.balance)
            finalData.append(thisRecord)

        self.mylist = finalData
        self.header = header

    def rowCount(self, parent):
        return len(self.mylist)

    def columnCount(self, parent):
        if len(self.mylist) > 0:
            return len(self.mylist[0])
        return 0
        
    def data(self, index, role):
        if not index.isValid():
            return None
        value = self.mylist[index.row()][index.column()]
        if role == Qt.EditRole:
            return value
        elif role == Qt.DisplayRole:
            return value

    def headerData(self, col, orientation, role):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return self.header[col]
        return None

class ExinPrice_TableModel(QAbstractTableModel):
    """
    keep the method names
    they are an integral part of the model
    """
    def __init__(self, parent, exintrade_price_list, header, *args):
        QAbstractTableModel.__init__(self, parent, *args)
        finalData = []
        for eachAsset in exintrade_price_list:
            thisRecord = []
            thisRecord.append(eachAsset.price)
            thisRecord.append(eachAsset.base_asset_symbol + "/" + eachAsset.exchange_asset_symbol)
            thisRecord.append(eachAsset.minimum_amount)
            thisRecord.append(eachAsset.maximum_amount)

            finalData.append(thisRecord)

        self.mylist = finalData
        self.header = header

    def rowCount(self, parent):
        return len(self.mylist)

    def columnCount(self, parent):
        if len(self.mylist) > 0:
            return len(self.mylist[0])
        return 0
        
    def data(self, index, role):
        if not index.isValid():
            return None
        value = self.mylist[index.row()][index.column()]
        if role == Qt.EditRole:
            return value
        elif role == Qt.DisplayRole:
            return value

    def headerData(self, col, orientation, role):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return self.header[col]
        return None
plugins_func_list = [exincore_api.exincore_can_explain_snapshot]
def Snapshot_fromSql(transaction_record_in_item):
    singleSnapShot                  = wallet_api.Snapshot()
    singleSnapShot.snapshot_id      = transaction_record_in_item.snap_snapshot_id
    singleSnapShot.type             = transaction_record_in_item.snap_type
    singleSnapShot.amount           = transaction_record_in_item.snap_amount
    singleSnapShot.created_at       = transaction_record_in_item.snap_created_at
    singleSnapShot.asset            = wallet_api.Static_Asset()

    singleSnapShot.asset.asset_id   = transaction_record_in_item.snap_asset_asset_id
    singleSnapShot.asset.chain_id   = transaction_record_in_item.snap_asset_chain_id
    singleSnapShot.asset.name       = transaction_record_in_item.snap_asset_name
    singleSnapShot.asset.symbol     = transaction_record_in_item.snap_asset_symbol
    singleSnapShot.source           = transaction_record_in_item.snap_source
    singleSnapShot.user_id          = transaction_record_in_item.snap_user_id
    singleSnapShot.opponent_id      = transaction_record_in_item.snap_opponent_id
    singleSnapShot.trace_id         = transaction_record_in_item.snap_trace_id
    singleSnapShot.memo             = transaction_record_in_item.snap_memo
    return singleSnapShot


def plugin_can_explain_snapshot(input_snapshot):
    for eachFunc in plugins_func_list:
        result = eachFunc(input_snapshot)
        if result != False:
            return result
    return False


class TransactionHistoryTableModel(QAbstractTableModel):
    """
    keep the method names
    they are an integral part of the model
    """
    def __init__(self, parent, MySnapshot_list, header, *args):
        QAbstractTableModel.__init__(self, parent, *args)
        finalData = []
        for eachSqlRecord in MySnapshot_list:
            thisRecord = []
            thisRecord.append(eachSqlRecord.snap_created_at)
            thisRecord.append(eachSqlRecord.snap_type)
            thisRecord.append(eachSqlRecord.snap_amount)
            thisRecord.append(eachSqlRecord.snap_asset_symbol)

 
            thisSnapshot = Snapshot_fromSql(eachSqlRecord)
            result = plugin_can_explain_snapshot(thisSnapshot)
            if result != False:
                thisRecord.append(result.get("opponent_name"))
                thisRecord.append(result.get("memo"))
            else:
                thisRecord.append(eachSqlRecord.snap_opponent_id)
                thisRecord.append(eachSqlRecord.snap_memo)
            finalData.append(thisRecord)

        self.mylist = finalData
        self.header = ["Created at", "Type", "Amount", "Asset", "opponent", "memo"]

    def rowCount(self, parent):
        return len(self.mylist)

    def columnCount(self, parent):
        if len(self.mylist) > 0:
            return len(self.mylist[0])
        return 0
        
    def data(self, index, role):
        if not index.isValid():
            return None
        value = self.mylist[index.row()][index.column()]
        if role == Qt.EditRole:
            return value
        elif role == Qt.DisplayRole:
            return value

    def headerData(self, col, orientation, role):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return self.header[col]
        return None
class MainWindow(QMainWindow):
    def __init__(self, *args, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)
        button_action = QAction("Open wallet file", self)
        button_action.setStatusTip("Open wallet file")
        button_action.triggered.connect(self.open_file)
 
        menu = self.menuBar()
        file_menu = menu.addMenu("File")
        file_menu.addAction(button_action)

        pin_menu = menu.addMenu("Pin")
        self.verify_pin_action = QAction("verify pin", self)
        self.verify_pin_action.triggered.connect(self.pop_verify_pin_window)
        pin_menu.addAction(self.verify_pin_action)
        self.update_pin_action = QAction("update pin", self)
        self.update_pin_action.triggered.connect(self.pop_update_pin_window)
        pin_menu.addAction(self.update_pin_action)

        self.counter = 0
        layout = QVBoxLayout()
        self.rootLayout = layout

        b = QPushButton("Open Wallet file")
        b.pressed.connect(self.open_file)
        layout.addWidget(b)
        new_wallet_btn = QPushButton("Create Wallet file")
        new_wallet_btn.pressed.connect(self.pop_create_wallet_window)
        layout.addWidget(new_wallet_btn)


        w = QWidget()
        w.setLayout(layout)
        self.setCentralWidget(w)
        self.show()
        self.timer = QTimer()
        self.timer.setInterval(1000)

        self.timer.timeout.connect(self.recurring_timer)
        self.timer.start()

        self.threadPool = QThreadPool()
        print("Multithreading with maximum %d threads" % self.threadPool.maxThreadCount())
    def create_transaction_history(self, all_transaction_history_list):

        header = ["Amount", "Asset", "Created at", "opponent", "Type"]
        this_tableModel = TransactionHistoryTableModel(self, all_transaction_history_list, header)

        transaction_table_view = QTableView()
        transaction_table_view.setModel(this_tableModel)
        return transaction_table_view



    def open_asset_transaction_history(self):
        asset_transaction_history_list = self.session.query(mixin_sqlalchemy_type.MySnapshot).filter_by(snap_asset_asset_id = self.asset_instance_in_item.asset_id).order_by(mixin_sqlalchemy_type.MySnapshot.id.desc()).all()
        self.widget_transaction_list_detail = self.create_transaction_history(asset_transaction_history_list)
        self.widget_transaction_list_detail.show()

    def open_transaction_history(self):
            all_transaction_history_list = self.session.query(mixin_sqlalchemy_type.MySnapshot).order_by(mixin_sqlalchemy_type.MySnapshot.id.desc()).all()
            return self.create_transaction_history(all_transaction_history_list)

    def execute_this_fn(self):
        for i in range(0, 5):
            time.sleep(1)
        return "Done."
    def print_output(self, s):
        print(s)
    def snap_thread_complete(self):
        header = ["Amount", "Asset", "Created at", "opponent", "Type"]
        all_transaction_history_list = self.session.query(mixin_sqlalchemy_type.MySnapshot).order_by(mixin_sqlalchemy_type.MySnapshot.id.desc()).all()
        this_tableModel = TransactionHistoryTableModel(self, all_transaction_history_list, header)
        self.account_transaction_history_widget.setModel(this_tableModel)
        self.account_transaction_history_widget.update()

    def thread_complete(self):
        print("THREAD COMPLETE")
    def exin_thread_complete(self):
        print("EXIN THREAD COMPLETE")
        exin_worker = ExinPrice_Thread(mixin_asset_id_collection.USDT_ASSET_ID, "", 60)
        exin_worker.signals.result.connect(self.received_exin_result)
        exin_worker.signals.finished.connect(self.exin_thread_complete)
        self.threadPool.start(exin_worker)


    def balance_load_thread_complete(self):
        print("THREAD COMPLETE")
        worker = Balance_Thread(self.selected_wallet_record, 60)
        worker.signals.result.connect(self.received_balance_result)
        worker.signals.finished.connect(self.balance_load_thread_complete)
        self.threadPool.start(worker)

    def create_wallet_confirm_chosen_block(self,user_input_name, user_input_pin, user_input_file):

        thisAccountRSAKeyPair = wallet_api.RSAKey4Mixin()
        body = {
            "session_secret": thisAccountRSAKeyPair.session_key,
            "full_name": user_input_name
        }
        wallet_obj = wallet_api.WalletRecord("","","", "","")
        self.create_account_layout.addWidget(QLabel("Created key file"))
 
        token2create = wallet_api.fetchTokenForCreateUser(body, "http://freemixinapptoken.myrual.me/token")
 
        create_wallet_result = wallet_obj.create_wallet(thisAccountRSAKeyPair.session_key, user_input_name, token2create)
        if(create_wallet_result.is_success):
            self.create_account_layout.addWidget(QLabel("Created account"))

            create_wallet_result.data.private_key = thisAccountRSAKeyPair.private_key
            new_wallet = wallet_api.WalletRecord("",create_wallet_result.data.user_id, create_wallet_result.data.session_id, create_wallet_result.data.pin_token, create_wallet_result.data.private_key)
 
            wallet_api.write_wallet_into_clear_base64_file(create_wallet_result.data, user_input_file)
            self.create_account_layout.addWidget(QLabel("Wrote account info into "+user_input_file))

            create_pin_result = new_wallet.update_pin("", user_input_pin)
            for eachAssetID in mixin_asset_id_collection.MIXIN_DEFAULT_CHAIN_GROUP:
                print(eachAssetID)
                asset_result = new_wallet.get_singleasset_balance(eachAssetID)
                if(asset_result.is_success):
                    self.create_account_layout.addWidget(QLabel("Created deposit address for " + asset_result.data.name))
            if(create_pin_result.is_success):
                self.create_account_layout.addWidget(QLabel("Created pin"))

            else:
                self.create_account_layout.addWidget(QLabel("Failed to create pin"))
        else:
             self.create_account_layout.addWidget(QLabel("Failed to create account"))
           

    def open_verify_pin_window(self):
        print("verify pin")
    def open_update_pin_window(self):
        print("update pin")
    def open_file(self):
        file_name_selected = QFileDialog.getOpenFileName(self, "QFileDialog.getOpenFileName()", "","mixinkey Files (*.mixinkey);;All Files (*)")
        file_name = file_name_selected[0]
        fileter   = file_name_selected[1]
        if(file_name == ''):
            print("User cancel file")
        else:
            print("User select file with %s" % file_name)
            self.file_name = file_name
            self.selected_wallet_record = wallet_api.load_wallet_from_clear_base64_file(file_name)
            self.open_selected_wallet()
    def select_file_for_create_wallet(self):
        file_name_selected = QFileDialog.getSaveFileName(self, "QFileDialog.getOpenFileName()", "","mixinkey Files (*.mixinkey);;All Files (*)")
        file_name = file_name_selected[0]
        fileter   = file_name_selected[1]
        if(file_name == ''):
            print("User cancel file")
        else:
            print("User select file with %s" % file_name)
            self.file_selected_edit.setText(file_name)

    def create_wallet_progress_update(self, obj):
        print(obj)
        self.create_account_layout.addWidget(QLabel(obj))
    def create_account_button_pressed(self):
        self.create_account_widget.close()
    def create_account_finished_callback(self):
        Successful_created_account_button = QPushButton("Done")
        Successful_created_account_button.pressed.connect(self.create_account_button_pressed)
        self.create_account_layout.addWidget(Successful_created_account_button)

    def create_account_pressed(self):
        user_input_pin  = self.pin_selected_edit.text()
        user_input_file = self.file_selected_edit.text()
        #self.create_wallet_confirm_chosen_block(wallet_api.randomString(), user_input_pin, user_input_file)

        worker = CreateAccount_Thread(wallet_api.randomString(), user_input_pin, user_input_file)
        worker.signals.progress.connect(self.create_wallet_progress_update)
        worker.signals.finished.connect(self.create_account_finished_callback)
        self.threadPool.start(worker)
        self.go_create_accout_btn.setDisabled(True)
        

    def close_Create_Windows(self):
        self.create_withdraw_address_widget.close()
        worker = Asset_addresses_Thread(self.selected_wallet_record, self.asset_instance_in_item)
        worker.signals.result.connect(self.received_asset_withdraw_addresses_result)
        worker.signals.finished.connect(self.thread_complete)
        self.threadPool.start(worker)

        return
    def pressed_create_withdraw_address_bitcoin(self):
        print("Account tag %s, deposit address %s, pin %s"%(self.account_tag_edit.text(), self.public_key_edit.text(), self.asset_pin_edit.text()))
        self.Add_address_btn.setDisabled(True)
        create_address_result  = self.selected_wallet_record.create_address(self.asset_instance_in_item.asset_id, self.public_key_edit.text(), self.account_tag_edit.text(), asset_pin = self.asset_pin_edit.text())
        if create_address_result.is_success:
            print("Address is created with id %s"%create_address_result.data.address_id)
            OK_button = QPushButton("Done")
            OK_button.pressed.connect(self.close_Create_Windows)
            self.create_withdraw_address_layout.addWidget(OK_button)
        else:
            print("Failed to create address because "%str(create_address_result))
            failed_msg = QMessageBox()
            failed_msg.setText("Failed to create address %s"%str(create_address_result))
            failed_msg.exec_()
    def pressed_create_withdraw_address_eos(self):
        print("Account name %s, account memo %s, pin %s"%(self.account_name_edit.text(), self.account_memo_edit.text(), self.asset_pin_edit.text()))
        self.Add_address_btn.setDisabled(True)
        create_address_result  = self.selected_wallet_record.create_address(self.asset_instance_in_item.asset_id, "", "", self.asset_pin_edit.text(), self.account_name_edit.text(), self.account_memo_edit.text())
        if create_address_result.is_success:
            print("Address is created with id %s"%create_address_result.data.address_id)
            OK_button = QPushButton("Done")
            OK_button.pressed.connect(self.close_Create_Windows)
            self.create_withdraw_address_eos_layout.addWidget(OK_button)
        else:
            print("Failed to create address because "%str(create_address_result))
            failed_msg = QMessageBox()
            failed_msg.setText("Failed to create address %s"%str(create_address_result))
            failed_msg.exec_()


    def pressed_remove_withdraw_address_bitcoin(self):
        self.Remove_address_btn.setDisabled(True)
        remove_address_result  = self.selected_wallet_record.remove_address(self.withdraw_address_instance_in_item.address_id, self.asset_pin_edit.text())
        if remove_address_result.is_success:
            self.remove_withdraw_address__widget.close()
            worker = Asset_addresses_Thread(self.selected_wallet_record, self.asset_instance_in_item)
            worker.signals.result.connect(self.received_asset_withdraw_addresses_result)
            worker.signals.finished.connect(self.thread_complete)
            self.threadPool.start(worker)

        else:
            print("Failed to remove address %s"%str(remove_address_result))

            congratulations_msg = QMessageBox()
            congratulations_msg.setText("Failed to create address %s"%str(remove_address_result))
            congratulations_msg.exec_()

    def pressed_verify_pin(self):
        verify_pin_result  = self.selected_wallet_record.verify_pin(self.asset_pin_edit.text())
        if(verify_pin_result.is_success):
            self.verify_pin_widget.close()
            load_wallet_msg = QMessageBox()
            load_wallet_msg.setText("Pin is correct")
            load_wallet_msg.exec_()
        else:
            load_wallet_msg = QMessageBox()
            print(verify_pin_result.error.status)
            if verify_pin_result.error.status == 202 and verify_pin_result.error.code == 20119:
                print("pin incorrect")
                load_wallet_msg.setText(str(verify_pin_result.error.description))
            else:
                print("other error")
                load_wallet_msg.setText(str(verify_pin_result))
            load_wallet_msg.exec_()

    def pressed_update_pin(self):
        update_pin_result  = self.selected_wallet_record.update_pin(self.asset_pin_edit.text(), self.update_new_pin_edit.text())
        if(update_pin_result.is_success):
            print("success")
            self.update_pin_widget.close()
            load_wallet_msg = QMessageBox()
            load_wallet_msg.setText("Successfully updated pin")
            load_wallet_msg.exec_()
        else:
            load_wallet_msg = QMessageBox()
            load_wallet_msg.setText(str(update_pin_result))
            load_wallet_msg.exec_()


    def pop_verify_pin_window(self):


        if (not hasattr(self, "selected_wallet_record")):
            load_wallet_msg = QMessageBox()
            load_wallet_msg.setText("Please load wallet file")
            load_wallet_msg.exec_()
            return

        asset_pin_widget     = QLabel("Pin:")
        self.asset_pin_edit  = QLineEdit()
        self.asset_pin_edit.setEchoMode(QLineEdit.Password)
        self.asset_pin_edit.setMaxLength(6)
        Remove_address_btn       = QPushButton("Verify")
        Remove_address_btn.pressed.connect(self.pressed_verify_pin)
        self.Remove_address_btn = Remove_address_btn

        verify_pin_layout = QVBoxLayout()
        verify_pin_layout.addWidget(asset_pin_widget)
        verify_pin_layout.addWidget(self.asset_pin_edit)
        verify_pin_layout.addWidget(Remove_address_btn)

        self.verify_pin_widget = QWidget()
        self.verify_pin_widget.setLayout(verify_pin_layout)
        self.verify_pin_widget.show()

    def pop_update_pin_window(self):


        if (not hasattr(self, "selected_wallet_record")):
            load_wallet_msg = QMessageBox()
            load_wallet_msg.setText("Please load wallet file")
            load_wallet_msg.exec_()
            return

        asset_pin_widget     = QLabel("Old pin:")
        self.asset_pin_edit  = QLineEdit()
        self.asset_pin_edit.setEchoMode(QLineEdit.Password)
        self.asset_pin_edit.setMaxLength(6)
        asset_new_pin_widget     = QLabel("New pin:")
        self.update_new_pin_edit  = QLineEdit()
        self.update_new_pin_edit.setEchoMode(QLineEdit.Password)
        self.update_new_pin_edit.setMaxLength(6)

        update_pin_btn       = QPushButton("Update")
        update_pin_btn.pressed.connect(self.pressed_update_pin)

        update_pin_layout = QVBoxLayout()
        update_pin_layout.addWidget(asset_pin_widget)
        update_pin_layout.addWidget(self.asset_pin_edit)
        update_pin_layout.addWidget(asset_new_pin_widget)
        update_pin_layout.addWidget(self.update_new_pin_edit)
        update_pin_layout.addWidget(update_pin_btn)

        self.update_pin_widget = QWidget()
        self.update_pin_widget.setLayout(update_pin_layout)
        self.update_pin_widget.show()



    def pop_Remove_withdraw_address_window_bitcoinstyle(self):


        asset_pin_widget     = QLabel("Asset pin:")
        self.asset_pin_edit  = QLineEdit()
        self.asset_pin_edit.setEchoMode(QLineEdit.Password)
        self.asset_pin_edit.setMaxLength(6)
        Remove_address_btn       = QPushButton("Remove")
        Remove_address_btn.pressed.connect(self.pressed_remove_withdraw_address_bitcoin)
        self.Remove_address_btn = Remove_address_btn

        remove_withdraw_address_layout = QVBoxLayout()
        remove_withdraw_address_layout.addWidget(asset_pin_widget)
        remove_withdraw_address_layout.addWidget(self.asset_pin_edit)
        remove_withdraw_address_layout.addWidget(Remove_address_btn)

        self.remove_withdraw_address__widget = QWidget()
        self.remove_withdraw_address__widget.setLayout(remove_withdraw_address_layout)
        self.remove_withdraw_address__widget.show()


    def pop_create_withdraw_address_window_eosstyle(self):


        account_name_widget    = QLabel("Account name:")
        self.account_name_edit = QLineEdit()
        account_memo_widget      = QLabel("Account memo:")
        self.account_memo_edit = QLineEdit()
        asset_pin_widget       = QLabel("Asset pin:")
        self.asset_pin_edit    = QLineEdit()
        self.asset_pin_edit.setEchoMode(QLineEdit.Password)
        self.asset_pin_edit.setMaxLength(6)
        Add_address_btn       = QPushButton("Create")
        Add_address_btn.pressed.connect(self.pressed_create_withdraw_address_eos)
        self.Add_address_btn = Add_address_btn

        create_withdraw_address_layout = QVBoxLayout()
        create_withdraw_address_layout.addWidget(account_name_widget)
        create_withdraw_address_layout.addWidget(self.account_name_edit)
        create_withdraw_address_layout.addWidget(account_memo_widget)
        create_withdraw_address_layout.addWidget(self.account_memo_edit)
        create_withdraw_address_layout.addWidget(asset_pin_widget)
        create_withdraw_address_layout.addWidget(self.asset_pin_edit)
        create_withdraw_address_layout.addWidget(Add_address_btn)

        self.create_withdraw_address_eos_layout = create_withdraw_address_layout

        self.create_withdraw_address_widget = QWidget()
        self.create_withdraw_address_widget.setLayout(create_withdraw_address_layout)
        self.create_withdraw_address_widget.show()


    def pop_create_withdraw_address_window_bitcoinstyle(self):


        account_tag_widget    = QLabel("Account alias:")
        self.account_tag_edit = QLineEdit()
        public_key_widget     = QLabel("Deposit address:")
        self.public_key_edit  = QLineEdit()
        asset_pin_widget     = QLabel("Asset pin:")
        self.asset_pin_edit  = QLineEdit()
        self.asset_pin_edit.setEchoMode(QLineEdit.Password)
        self.asset_pin_edit.setMaxLength(6)
        Add_address_btn       = QPushButton("Create")
        Add_address_btn.pressed.connect(self.pressed_create_withdraw_address_bitcoin)
        self.Add_address_btn = Add_address_btn

        create_withdraw_address_layout = QVBoxLayout()
        create_withdraw_address_layout.addWidget(account_tag_widget)
        create_withdraw_address_layout.addWidget(self.account_tag_edit)
        create_withdraw_address_layout.addWidget(public_key_widget)
        create_withdraw_address_layout.addWidget(self.public_key_edit)
        create_withdraw_address_layout.addWidget(asset_pin_widget)
        create_withdraw_address_layout.addWidget(self.asset_pin_edit)
        create_withdraw_address_layout.addWidget(Add_address_btn)

        self.create_withdraw_address_layout = create_withdraw_address_layout

        self.create_withdraw_address_widget = QWidget()
        self.create_withdraw_address_widget.setLayout(create_withdraw_address_layout)
        self.create_withdraw_address_widget.show()


    def pop_create_wallet_window(self):

        file_selection_layout = QHBoxLayout()
        file_title_widget = QLabel("Wallet file name:")
        self.file_selected_edit     = QLineEdit()
        file_browser_btn  = QPushButton("Browse")
        file_browser_btn.pressed.connect(self.select_file_for_create_wallet)
        file_selection_layout.addWidget(file_title_widget)
        file_selection_layout.addWidget(self.file_selected_edit)
        file_selection_layout.addWidget(file_browser_btn)
        file_title_selection_widget = QWidget()
        file_title_selection_widget.setLayout(file_selection_layout)

        pin_selection_layout = QHBoxLayout()
        pin_title_widget = QLabel("Asset pin(6 numbers):")
        self.pin_selected_edit     = QLineEdit()
        self.pin_selected_edit.setText("")
        self.pin_selected_edit.setMaxLength(6)
        self.pin_selected_edit.setEchoMode(QLineEdit.Password)
        pin_selection_layout.addWidget(pin_title_widget)
        pin_selection_layout.addWidget(self.pin_selected_edit)
        pin_edit_widget = QWidget()
        pin_edit_widget.setLayout(pin_selection_layout)

        self.create_account_progress_widget = QLabel("Progress")
        self.create_account_progress_widget.setAlignment(Qt.AlignCenter)

        go_create_accout_btn  = QPushButton("Create wallet")
        go_create_accout_btn.pressed.connect(self.create_account_pressed)
        self.go_create_accout_btn = go_create_accout_btn

        create_account_layout = QVBoxLayout()
        create_account_layout.addWidget(file_title_selection_widget)
        create_account_layout.addWidget(pin_edit_widget)
        create_account_layout.addWidget(go_create_accout_btn)
        create_account_layout.addWidget(self.create_account_progress_widget)

        self.create_account_layout = create_account_layout



        self.create_account_widget = QWidget()
        self.create_account_widget.setLayout(create_account_layout)
        self.create_account_widget.show()

    def create_wallet_file(self):
        file_name_selected = QFileDialog.getOpenFileName(self, "QFileDialog.getOpenFileName()", "","mixinkey Files (*.mixinkey);;All Files (*)")
        file_name = file_name_selected[0]
        fileter   = file_name_selected[1]
        if(file_name == ''):
            print("User cancel file")
        else:
            print("User select file with %s" % file_name)
            self.selected_wallet_record = wallet_api.load_wallet_from_clear_base64_file(file_name)
            self.open_selected_wallet()


    def oh_no(self):
        worker = Balance_Thread(self.execute_this_fn)
        worker.signals.result.connect(self.print_output)
        worker.signals.finished.connect(self.thread_complete)
        self.threadPool.start(worker)
    def recurring_timer(self):
        self.counter += 1
    def received_send_withdraw_addresses_result(self, withdraw_addresses_asset_result):
        if(withdraw_addresses_asset_result.is_success):
            self.withdraw_address_of_asset_list = withdraw_addresses_asset_result.data
            i = 0
            for eachAsset in self.withdraw_address_of_asset_list:
                if(self.asset_instance_in_item.chain_id != mixin_asset_id_collection.EOS_ASSET_ID):
                    self.send_address_selection_widget.insertItem(i, eachAsset.label, userData = eachAsset)
                else:
                    self.send_address_selection_widget.insertItem(i, eachAsset.account_tag, userData = eachAsset)
                i += 0
        return


    def received_asset_withdraw_addresses_result(self, withdraw_addresses_asset_result):
        if(withdraw_addresses_asset_result.is_success):
            for i in self.withdraw_address_list:
                self.withdraw_addresses_list_widget.takeItem(0)
            self.withdraw_address_list = []

            for eachAsset in withdraw_addresses_asset_result.data:
                this_list_item = QListWidgetItem()
                this_list_item.setData(0x0100, eachAsset)
                this_list_item.setText(eachAsset.label)
                self.withdraw_addresses_list_widget.addItem(this_list_item)
                self.withdraw_address_list.append(this_list_item)

            if(len(withdraw_addresses_asset_result.data) > 0):
                self.withdraw_addresses_list_widget.setCurrentRow(0)
            else:
                self.remove_address_btn.setDisabled(True)

            self.withdraw_addresses_list_widget.update()
        return

    def received_snapshot(self, searched_snapshots_result):
        the_last_snapshots_time = searched_snapshots_result.data[-1].created_at
        print(the_last_snapshots_time)
        for eachsnapshots in searched_snapshots_result.data:
            if (eachsnapshots.is_my_snap()):
                found_snapshot_quantity = len(self.session.query(mixin_sqlalchemy_type.MySnapshot).filter_by(snap_snapshot_id = eachsnapshots.snapshot_id).all())
                if(found_snapshot_quantity == 0):
                    my_snapshot = mixin_sqlalchemy_type.MySnapshot()
                    my_snapshot.snap_amount         = eachsnapshots.amount
                    my_snapshot.snap_type           = eachsnapshots.type
                    my_snapshot.snap_created_at     = eachsnapshots.created_at
                    my_snapshot.snap_asset_name     = eachsnapshots.asset.name
                    my_snapshot.snap_asset_asset_id = eachsnapshots.asset.asset_id
                    my_snapshot.snap_asset_chain_id = eachsnapshots.asset.chain_id
                    my_snapshot.snap_asset_symbol   = eachsnapshots.asset.symbol
                    my_snapshot.snap_snapshot_id    = eachsnapshots.snapshot_id
 
                    my_snapshot.snap_memo           = eachsnapshots.memo
                    my_snapshot.snap_source         = eachsnapshots.source
                    my_snapshot.snap_user_id        = eachsnapshots.user_id
                    my_snapshot.snap_trace_id       = eachsnapshots.trace_id
                    my_snapshot.snap_opponent_id    = eachsnapshots.opponent_id
                    self.session.add(my_snapshot)

        if len(searched_snapshots_result.data) > 0:
            last_record_in_database = self.session.query(mixin_sqlalchemy_type.ScannedSnapshots).order_by(mixin_sqlalchemy_type.ScannedSnapshots.id.desc()).first()
            the_last_snapshot = searched_snapshots_result.data[-1]
            if last_record_in_database != None:
                last_record_in_database.snap_amount         = the_last_snapshot.amount
                last_record_in_database.snap_type           = the_last_snapshot.type
                last_record_in_database.snap_created_at     = the_last_snapshot.created_at
                last_record_in_database.snap_asset_name     = the_last_snapshot.asset.name
                last_record_in_database.snap_asset_asset_id = the_last_snapshot.asset.asset_id
                last_record_in_database.snap_asset_chain_id = the_last_snapshot.asset.chain_id
                last_record_in_database.snap_asset_symbol   = the_last_snapshot.asset.symbol
                last_record_in_database.snap_snapshot_id    = the_last_snapshot.snapshot_id
            else:
                the_last_record = mixin_sqlalchemy_type.ScannedSnapshots()
                the_last_record.snap_amount         = the_last_snapshot.amount
                the_last_record.snap_type           = the_last_snapshot.type
                the_last_record.snap_created_at     = the_last_snapshot.created_at
                the_last_record.snap_asset_name     = the_last_snapshot.asset.name
                the_last_record.snap_asset_asset_id = the_last_snapshot.asset.asset_id
                the_last_record.snap_asset_chain_id = the_last_snapshot.asset.chain_id
                the_last_record.snap_asset_symbol   = the_last_snapshot.asset.symbol
                the_last_record.snap_snapshot_id    = the_last_snapshot.snapshot_id
                self.session.add(the_last_record)
            self.session.commit()


        delay_seconds = 0
        if len(searched_snapshots_result.data) < 500:
            delay_seconds = 120
        mysnapshots_worker = AccountsSnapshots_Thread(self.selected_wallet_record, the_last_snapshots_time, delay_seconds)
        mysnapshots_worker.signals.result.connect(self.received_snapshot)
        mysnapshots_worker.signals.finished.connect(self.snap_thread_complete)
        self.threadPool.start(mysnapshots_worker)

    def received_user_profile_result(self, user_profile_result):
        self.loggedin_user_profile = user_profile_result
        print("user is created at %s"%self.loggedin_user_profile.data.created_at)
        lastRecord = self.session.query(mixin_sqlalchemy_type.ScannedSnapshots).order_by(mixin_sqlalchemy_type.ScannedSnapshots.id.desc()).first()
        print(lastRecord)
        created_at_string = ""
        if lastRecord != None: 
            created_at_string = lastRecord.snap_created_at
        else:
            created_at_string = self.loggedin_user_profile.data.created_at
        mysnapshots_worker = AccountsSnapshots_Thread(self.selected_wallet_record, created_at_string)
        mysnapshots_worker.signals.result.connect(self.received_snapshot)
        mysnapshots_worker.signals.finished.connect(self.thread_complete)
        self.threadPool.start(mysnapshots_worker)
 
    def received_exin_result(self, exin_result):
        self.exin_result = exin_result
        this_model = ExinPrice_TableModel(self, exin_result, ["price", "trade", "min pay", "max pay"])
        self.exin_tradelist_widget.setModel(this_model)
        self.exin_tradelist_widget.update()
        if hasattr(self, "exin_price_selected_row"):
            self.exin_tradelist_widget.selectRow(self.exin_price_selected_row)
        return

    def received_balance_result(self, balance_result):
        if(balance_result.is_success):
            final_balance_result = balance_result.data
            asset_id_from_server = []
            for eachAsset in balance_result.data:
                asset_id_from_server.append(eachAsset.asset_id)
            for default_id in mixin_asset_id_collection.MIXIN_DEFAULT_CHAIN_GROUP:
                if not (default_id in asset_id_from_server):
                    asset_balance_result = self.selected_wallet_record.get_singleasset_balance(default_id)
                    if asset_balance_result.is_success:
                        final_balance_result.append(asset_balance_result.data)
            this_balance_model = Balance_TableModel(self, final_balance_result, ["Asset name", "Amount"])
            self.balance_list_tableview.setModel(this_balance_model)
            self.balance_list_tableview.update()
            if hasattr(self, "balance_selected_row"):
                self.balance_list_tableview.selectRow(self.balance_selected_row)
            self.account_balance = balance_result.data
        return
    def withdraw_address_list_record_selection_actived(self,itemCurr, itemPre):
        if itemCurr == None:
            self.clear_asset_address_detail()
            return
        self.withdraw_address_instance_in_item = itemCurr.data(0x0100)
        self.update_asset_address_detail(self.withdraw_address_instance_in_item, self.withdraw_address_of_asset_detail_label)
        self.remove_address_btn.setDisabled(False)

    def update_transaction_list_record_detail(self):
        totalString = ""
        totalString += ("UTC Timestamp: %s\n"%self.transaction_record_in_item.snap_created_at)
        totalString += ("opponent: %s\n"%self.transaction_record_in_item.snap_opponent_id)
        totalString += ("asset name: %s\n"%self.transaction_record_in_item.snap_asset_name)
        totalString += ("type: %s\n"%self.transaction_record_in_item.snap_type)
        totalString += ("memo: %s\n"%self.transaction_record_in_item.snap_memo)
        singleSnapShot                  = wallet_api.Snapshot()
        singleSnapShot.snapshot_id      = self.transaction_record_in_item.snap_snapshot_id
        singleSnapShot.type             = self.transaction_record_in_item.snap_type
        singleSnapShot.amount           = self.transaction_record_in_item.snap_amount
        singleSnapShot.created_at       = self.transaction_record_in_item.snap_created_at
        singleSnapShot.asset            = wallet_api.Static_Asset()

        singleSnapShot.asset.asset_id   = self.transaction_record_in_item.snap_asset_asset_id
        singleSnapShot.asset.chain_id   = self.transaction_record_in_item.snap_asset_chain_id
        singleSnapShot.asset.name       = self.transaction_record_in_item.snap_asset_name
        singleSnapShot.asset.symbol     = self.transaction_record_in_item.snap_asset_symbol
        singleSnapShot.source           = self.transaction_record_in_item.snap_source
        singleSnapShot.user_id          = self.transaction_record_in_item.snap_user_id
        singleSnapShot.opponent_id      = self.transaction_record_in_item.snap_opponent_id
        singleSnapShot.trace_id         = self.transaction_record_in_item.snap_trace_id
        singleSnapShot.memo             = self.transaction_record_in_item.snap_memo


        is_exin = exincore_api.about_me(singleSnapShot)
        if(is_exin):
            totalString += ("ExinChange: %s\n"%str(is_exin))
        self.transaction_record_detail.setText(totalString)


    def transaction_list_record_actived(self, itemCurr, itemPre):
        self.transaction_record_in_item = itemCurr.data(0x0100)
        self.update_transaction_list_record_detail()

    def transaction_list_record_selected(self, itemSelect):
        self.transaction_record_in_item = itemSelect.data(0x0100)
        self.update_transaction_list_record_detail()

    def update_exin_detail(self):
        self.selected_trade_buy_btn.setText("Buy " + self.selected_exin_result.exchange_asset_symbol)
        self.selected_trade_buy_btn.setDisabled(False)
        self.selected_trade_sell_btn.setText("Sell " + self.selected_exin_result.exchange_asset_symbol)
        self.selected_trade_sell_btn.setDisabled(False)

    def exin_trade_list_record_selected(self, index):
        self.exin_price_selected_row = index.row()
        self.selected_exin_result = self.exin_result[self.exin_price_selected_row]
        self.update_exin_detail()
    def balance_list_record_selected(self, index):
        self.balance_selected_row = index.row()
        self.asset_instance_in_item = self.account_balance[self.balance_selected_row]
        self.selected_asset_send.setDisabled(False)
        self.selected_asset_send.setText("Send " + self.asset_instance_in_item.name)
        self.selected_asset_manageasset.setDisabled(False)
        self.selected_asset_show_history.setDisabled(False)
        self.selected_asset_show_history.setText("History of " + self.asset_instance_in_item.name)
        self.show_deposit_address_btn.setDisabled(False)
        self.show_deposit_address_btn.setText("Deposit address of " + self.asset_instance_in_item.name)

    def update_asset_address_detail(self, this_withdraw_address, label_widget):
        stringForAddress = ""
        if this_withdraw_address.public_key != "":
            stringForAddress +=  ("\n" + u'Address: ' + this_withdraw_address.public_key)
        if(this_withdraw_address.account_name!= ""):
            stringForAddress += ("\n" + u'Account name:'.ljust(20) + this_withdraw_address.account_name)
        if(this_withdraw_address.account_tag!= ""):
            stringForAddress += ("\n" + u'Account tag:'.ljust(20) + this_withdraw_address.account_tag)
        if(this_withdraw_address.fee!= ""):
            stringForAddress += ("\n" + this_withdraw_address.fee + u' fee')
        if(this_withdraw_address.reserve != ""):
            stringForAddress += ("\n" + this_withdraw_address.reserve + u' reserve')
        if(this_withdraw_address.dust!= ""):
            stringForAddress += ("\n" + this_withdraw_address.dust + u' dust')
        label_widget.setText(stringForAddress)

    def clear_asset_address_detail(self, label_widget):
        label_widget.setText("")

    def withdrawaddress_list_record_selected(self, itemSelect):
        if itemSelect == None:
            return

        self.withdraw_address_instance_in_item = itemSelect.data(0x0100)
        self.update_asset_address_detail(self.withdraw_address_instance_in_item)
        self.remove_address_btn.setDisabled(False)
    def send_withdrawaddress_list_record_indexChanged(self, indexActived):
        print("index changed %d"%indexActived)
        self.selected_withdraw_address = self.withdraw_address_of_asset_list[indexActived]
        self.update_asset_address_detail(self.selected_withdraw_address, self.send_address_title_widget)

    def pay_to_exin_pressed(self, base_asset, echange_asset):
        self.trade_exin_widget.close()
        memo_for_exin = exincore_api.gen_memo_ExinBuy(echange_asset)
        print("amount is %s"%self.pay_exin_amount_edit_Label_widget.text())
        print("base asset is %s"%base_asset)
        tranfer_result = self.selected_wallet_record.transfer_to(exincore_api.EXINCORE_UUID, base_asset, self.pay_exin_amount_edit_Label_widget.text(), memo_for_exin, "", self.pay_exin_pin_edit_Label_widget.text())
        if tranfer_result.is_success:
            congratulations_msg = QMessageBox()
            congratulations_msg.setText("Your payment to exin is successful, verify it on blockchain explorer on https://mixin.one/snapshots/%s" % tranfer_result.data.snapshot_id)
            congratulations_msg.setTextInteractionFlags(Qt.TextSelectableByMouse)
            congratulations_msg.exec_()
        else:
            congratulations_msg = QMessageBox()
            congratulations_msg.setText("Failed to pay, reason %s" % str(tranfer_result))
            congratulations_msg.exec_()

    def send_asset_to_withdraw_address_pressed(self):
        withdraw_asset_result = self.selected_wallet_record.withdraw_asset_to(self.selected_withdraw_address.address_id, self.send_amount_edit_Label_widget.text(), "", "", self.send_pin_edit_Label_widget.text())
        if withdraw_asset_result.is_success:
            self.send_asset_widget.close()
            congratulations_msg = QMessageBox()
            congratulations_msg.setText("Your withdraw operation is successful, verify it on blockchain explorer on https://mixin.one/snapshots/%s" % withdraw_asset_result.data.snapshot_id)
            congratulations_msg.setTextInteractionFlags(Qt.TextSelectableByMouse)
            congratulations_msg.exec_()
        else:
            congratulations_msg = QMessageBox()
            congratulations_msg.setText("Failed to send, reason %s" % str(withdraw_asset_result))
            congratulations_msg.exec_()


    def open_sell_trade_detail_for_exin(self):
        if (hasattr(self, "selected_exin_result")):
            self.open_trade_trade_detail_for_exin(self.selected_exin_result.echange_asset, self.selected_exin_result.base_asset)

    def open_buy_trade_detail_for_exin(self):
        if (hasattr(self, "selected_exin_result")):
            self.open_trade_trade_detail_for_exin(self.selected_exin_result.base_asset, self.selected_exin_result.echange_asset)
    def open_trade_trade_detail_for_exin(self, base_asset_id, target_asset_id):
        if (hasattr(self, "selected_exin_result")):
            asset_price_result = exincore_api.fetchExinPrice(base_asset_id, target_asset_id)
            #confirm price again
            this_trade_price = asset_price_result[0]
            minimum_pay_base_asset = this_trade_price.minimum_amount
            maximum_pay_base_asset = this_trade_price.maximum_amount
            price_base_asset       = this_trade_price.price
            base_sym               = this_trade_price.base_asset_symbol
            target_sym             = this_trade_price.exchange_asset_symbol

            tradepair_price_title_label_widget = QLabel("Price:  %s %s  ==> 1 %s"%(price_base_asset, base_sym, target_sym))
            send_amount_title_widget = QLabel("amount(%s -> %s) %s:"%(minimum_pay_base_asset, maximum_pay_base_asset, base_sym))
            self.pay_exin_amount_edit_Label_widget = QLineEdit()
            send_pin_title_widget = QLabel("Asset pin:")
            self.pay_exin_pin_edit_Label_widget = QLineEdit()
            self.pay_exin_pin_edit_Label_widget.setMaxLength(6)
            self.pay_exin_pin_edit_Label_widget.setEchoMode(QLineEdit.Password)

            send_payment_to_exin_btn = QPushButton("Go")
            send_payment_to_exin_btn.pressed.connect(lambda :self.pay_to_exin_pressed(base_asset_id, target_asset_id))

            send_payment_to_exin_layout = QVBoxLayout()
            send_payment_to_exin_layout.addWidget(tradepair_price_title_label_widget)
            send_payment_to_exin_layout.addWidget(send_amount_title_widget)
            send_payment_to_exin_layout.addWidget(self.pay_exin_amount_edit_Label_widget)
            send_payment_to_exin_layout.addWidget(send_pin_title_widget)
            send_payment_to_exin_layout.addWidget(self.pay_exin_pin_edit_Label_widget)
            send_payment_to_exin_layout.addWidget(send_payment_to_exin_btn)

            self.trade_exin_widget = QWidget()
            self.trade_exin_widget.setLayout(send_payment_to_exin_layout)
            self.trade_exin_widget.show()
        else:
            return


    def send_asset_to_address(self):
        if (hasattr(self, "asset_instance_in_item")):
            send_asset_title_label_widget = QLabel("Send " + self.asset_instance_in_item.name + " to:")
            send_amount_title_widget = QLabel("amount, %s %s available"%(self.asset_instance_in_item.balance, self.asset_instance_in_item.symbol))
            self.send_amount_edit_Label_widget = QLineEdit()
            send_pin_title_widget = QLabel("Asset pin:")
            self.send_pin_edit_Label_widget = QLineEdit()
            self.send_pin_edit_Label_widget.setMaxLength(6)
            self.send_pin_edit_Label_widget.setEchoMode(QLineEdit.Password)
            self.send_address_title_widget = QLabel("to ")

            self.send_address_selection_widget = QComboBox()
            self.send_address_selection_widget.currentIndexChanged.connect(self.send_withdrawaddress_list_record_indexChanged)
            send_asset_to_withdraw_address_btn = QPushButton("Send")
            send_asset_to_withdraw_address_btn.pressed.connect(self.send_asset_to_withdraw_address_pressed)

            send_asset_layout = QVBoxLayout()
            send_asset_layout.addWidget(send_asset_title_label_widget)
            send_asset_layout.addWidget(self.send_address_title_widget)
            send_asset_layout.addWidget(self.send_address_selection_widget)

            send_asset_layout.addWidget(send_amount_title_widget)

            send_asset_layout.addWidget(self.send_amount_edit_Label_widget)
            send_asset_layout.addWidget(send_pin_title_widget)
            send_asset_layout.addWidget(self.send_pin_edit_Label_widget)

            send_asset_layout.addWidget(send_asset_to_withdraw_address_btn)
            self.send_asset_widget = QWidget()
            self.send_asset_widget.setLayout(send_asset_layout)
            self.send_asset_widget.show()


            worker = Asset_addresses_Thread(self.selected_wallet_record, self.asset_instance_in_item)
            worker.signals.result.connect(self.received_send_withdraw_addresses_result)
            worker.signals.finished.connect(self.thread_complete)
            self.threadPool.start(worker)
        else:
            return



    def open_widget_manage_asset(self):
        if (hasattr(self, "asset_instance_in_item")):
            
            add_withdraw_address_asset_btn = QPushButton("Add new address")
            if(self.asset_instance_in_item.chain_id == mixin_asset_id_collection.EOS_ASSET_ID):
                add_withdraw_address_asset_btn.pressed.connect(self.pop_create_withdraw_address_window_eosstyle)
            else:
                add_withdraw_address_asset_btn.pressed.connect(self.pop_create_withdraw_address_window_bitcoinstyle)

            self.withdraw_addresses_list_and_new_layout = QVBoxLayout()
            self.withdraw_addresses_list_and_new_layout.addWidget(add_withdraw_address_asset_btn)
            self.withdraw_addresses_list_widget = QListWidget()
            self.withdraw_addresses_list_widget.itemClicked.connect(self.withdrawaddress_list_record_selected)
            self.withdraw_addresses_list_widget.currentItemChanged.connect(self.withdraw_address_list_record_selection_actived)
            self.withdraw_address_list = []


            self.withdraw_addresses_list_and_new_layout.addWidget(self.withdraw_addresses_list_widget)


            withdraw_addresses_list_and_new_widget = QWidget()
            withdraw_addresses_list_and_new_widget.setLayout(self.withdraw_addresses_list_and_new_layout)

            self.withdraw_address_of_asset_detail_label = QLabel()
            remove_address_btn = QPushButton("Delete")
            remove_address_btn.pressed.connect(self.pop_Remove_withdraw_address_window_bitcoinstyle)
            remove_address_btn.setDisabled(True)
            self.remove_address_btn = remove_address_btn

            withdraw_addresses_detail_layout = QVBoxLayout()


            withdraw_addresses_detail_layout.addWidget(self.withdraw_address_of_asset_detail_label)
            withdraw_addresses_detail_layout.addWidget(remove_address_btn)

            withdraw_addresses_detail_widget = QWidget()
            withdraw_addresses_detail_widget.setLayout(withdraw_addresses_detail_layout)
            withdraw_addresses_list_and_new_detail_layout = QHBoxLayout()
            withdraw_addresses_list_and_new_detail_layout.addWidget(withdraw_addresses_list_and_new_widget)
            withdraw_addresses_list_and_new_detail_layout.addWidget(withdraw_addresses_detail_widget)
            self.withdraw_addresses_list_and_new_detail_Widget = QWidget()
            self.withdraw_addresses_list_and_new_detail_Widget.setLayout(withdraw_addresses_list_and_new_detail_layout)
            self.withdraw_addresses_list_and_new_detail_Widget.show()

            worker = Asset_addresses_Thread(self.selected_wallet_record, self.asset_instance_in_item)
            worker.signals.result.connect(self.received_asset_withdraw_addresses_result)
            worker.signals.finished.connect(self.thread_complete)
            self.threadPool.start(worker)
        else:
            return


    def create_exin_exchange_widget(self):
        self.selected_trade_buy_btn = QPushButton("Buy")
        self.selected_trade_buy_btn.pressed.connect(self.open_buy_trade_detail_for_exin)
        self.selected_trade_buy_btn.setDisabled(True)

        self.selected_trade_sell_btn= QPushButton("Sell")
        self.selected_trade_sell_btn.pressed.connect(self.open_sell_trade_detail_for_exin)
        self.selected_trade_sell_btn.setDisabled(True)



        self.exin_tradelist_layout = QVBoxLayout()
        self.exin_tradelist_widget = QTableView()

        self.exin_tradelist_widget.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.exin_tradelist_widget.clicked.connect(self.exin_trade_list_record_selected)

        self.exin_tradelist_and_detail_layout = QVBoxLayout()
        self.exin_tradelist_and_detail_layout.addWidget(self.exin_tradelist_widget)
        self.exin_tradelist_and_detail_widget = QWidget()
        self.exin_tradelist_and_detail_widget.setLayout(self.exin_tradelist_and_detail_layout)
        button_layout = QHBoxLayout()
        button_layout.addWidget(self.selected_trade_buy_btn)
        button_layout.addWidget(self.selected_trade_sell_btn)
        button_group_widget = QWidget()
        button_group_widget.setLayout(button_layout)

        this_layout = QVBoxLayout()
        this_layout.addWidget(button_group_widget)
        this_layout.addWidget(self.exin_tradelist_and_detail_widget)
        exin_title_trade_list_detail = QWidget()
        exin_title_trade_list_detail.setLayout(this_layout)
        return exin_title_trade_list_detail


    def pop_deposit_addess_of_asset(self):
        if (hasattr(self, "asset_instance_in_item")):
            congratulations_msg = QMessageBox()
            deposit_address_title_value_segments = self.asset_instance_in_item.deposit_address()
            first_seg = deposit_address_title_value_segments[0]
            deposit_label_content = first_seg["title"] + " : " + first_seg["value"]

            if len(deposit_address_title_value_segments) > 1:
                second_seg = deposit_address_title_value_segments[1]
                deposit_label_content += "\n" + second_seg["title"] + " : " + second_seg["value"]
         
            congratulations_msg.setText(deposit_label_content)
            congratulations_msg.setTextInteractionFlags(Qt.TextSelectableByMouse)
            congratulations_msg.exec_()

    def create_balance_widget(self):
        self.balance_and_detail_layout = QVBoxLayout()
        self.Balance_detail_layout = QHBoxLayout()
        self.selected_asset_send = QPushButton("Send")
        self.selected_asset_send.setDisabled(True)
        self.selected_asset_send.pressed.connect(self.send_asset_to_address)
        self.selected_asset_manageasset = QPushButton("Manage contact")
        self.selected_asset_manageasset.setDisabled(True)
        self.selected_asset_manageasset.pressed.connect(self.open_widget_manage_asset)
        self.selected_asset_show_history = QPushButton("History")
        self.selected_asset_show_history.pressed.connect(self.open_asset_transaction_history)
        self.selected_asset_show_history.setDisabled(True)
        self.show_deposit_address_btn = QPushButton("Deposit address")
        self.show_deposit_address_btn.pressed.connect(self.pop_deposit_addess_of_asset)
        self.show_deposit_address_btn.setDisabled(True)

        self.Balance_detail_layout.addWidget(self.selected_asset_send)
        self.Balance_detail_layout.addWidget(self.selected_asset_show_history)
        self.Balance_detail_layout.addWidget(self.selected_asset_manageasset)
        self.Balance_detail_layout.addWidget(self.show_deposit_address_btn)

        self.balance_list_tableview = QTableView()
        self.balance_list_tableview.clicked.connect(self.balance_list_record_selected)
        self.balance_list_tableview.setSelectionBehavior(QAbstractItemView.SelectRows)

        self.widget_balance_detail = QWidget()
        self.widget_balance_detail.setLayout(self.Balance_detail_layout)
        self.widget_balance_detail.show()
        self.balance_and_detail_layout.addWidget(self.balance_list_tableview)
        self.balance_and_detail_layout.addWidget(self.widget_balance_detail)
        widget_balance = QWidget()
        widget_balance.setLayout(self.balance_and_detail_layout)
        return widget_balance


    def tab_is_selected(self, index):
        print("tab is changed" + str(index))
    def open_selected_wallet(self):
        if (hasattr(self, "selected_wallet_record")):
            worker = Balance_Thread(self.selected_wallet_record)
            worker.signals.result.connect(self.received_balance_result)
            worker.signals.finished.connect(self.balance_load_thread_complete)

            user_profile_worker = UserProfile_Thread(self.selected_wallet_record)
            engine = sqlalchemy.create_engine('sqlite:///' + self.file_name + '.snapshot.db')
            # Create all tables in the engine. This is equivalent to "Create Table"
            # statements in raw SQL.
            mixin_sqlalchemy_type.Base.metadata.create_all(engine)
            mixin_sqlalchemy_type.Base.metadata.bind = engine
 
            DBSession = sqlalchemy.orm.sessionmaker(bind=engine)
            self.session = DBSession()

            user_profile_worker.signals.result.connect(self.received_user_profile_result)
            user_profile_worker.signals.finished.connect(self.thread_complete)
            self.threadPool.start(worker)
            self.threadPool.start(user_profile_worker)

            self.widget_balance_widget = self.create_balance_widget()
            self.account_transaction_history_widget = self.open_transaction_history()
            header = self.account_transaction_history_widget.horizontalHeader()       
            header.setSectionResizeMode(0, QHeaderView.Stretch)
            header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
            header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
            header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
            header.setSectionResizeMode(4, QHeaderView.ResizeToContents)

            self.exin_title_trade_list_detail = self.create_exin_exchange_widget()
            self.account_tab_widget = QTabWidget()
            self.account_tab_widget.addTab(self.widget_balance_widget, "Balance")
            self.account_tab_widget.addTab(self.account_transaction_history_widget, "Transactions")
            self.account_tab_widget.addTab(self.exin_title_trade_list_detail, "Instant Exin Exchange")
            self.account_tab_widget.show()
            self.account_tab_widget.currentChanged.connect(self.tab_is_selected)

            exin_worker = ExinPrice_Thread(mixin_asset_id_collection.USDT_ASSET_ID, "")
            exin_worker.signals.result.connect(self.received_exin_result)
            exin_worker.signals.finished.connect(self.exin_thread_complete)

            self.threadPool.start(exin_worker)
        else:
            return


app = QApplication([])
window = MainWindow()
app.exec_()

