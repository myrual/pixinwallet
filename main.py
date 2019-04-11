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


class MainWindow(QMainWindow):
    def __init__(self, *args, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)
        button_action = QAction("Open wallet file", self)
        button_action.setStatusTip("Open wallet file")
        button_action.triggered.connect(self.open_file)
 
        menu = self.menuBar()
        file_menu = menu.addMenu("File")
        file_menu.addAction(button_action)

        self.show_history_menu_action = QAction("Transaction history")
        self.show_history_menu_action.triggered.connect(self.open_transaction_history)
        file_menu.addAction(self.show_history_menu_action)


        pin_menu = menu.addMenu("Pin")
        self.verify_pin_action = QAction("verify pin", self)
        self.verify_pin_action.triggered.connect(self.pop_verify_pin_window)
        pin_menu.addAction(self.verify_pin_action)
        self.update_pin_action = QAction("update pin", self)
        self.update_pin_action.triggered.connect(self.pop_update_pin_window)
        pin_menu.addAction(self.update_pin_action)

        exchange_menu = menu.addMenu("Exchanges")
        self.exin_action = QAction("Instant change: Exin", self)
        self.exin_action.triggered.connect(self.open_exin_exchange)
        exchange_menu.addAction(self.exin_action)


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
    def show_transaction_history(self, all_transaction_history_list):
        transaction_history_list_widget = QListWidget()
        for each_sql_transaction in all_transaction_history_list:
            amount = each_sql_transaction.snap_amount
            if(float(amount) > 0):
                amount = "+" + amount
            itemN = QListWidgetItem()
            itemN.setData(0x0100, each_sql_transaction)
            itemN.setText(amount.ljust(15) + each_sql_transaction.snap_asset_symbol)
            transaction_history_list_widget.addItem(itemN)

        transaction_history_list_widget.itemClicked.connect(self.transaction_list_record_selected)
        transaction_history_list_widget.currentItemChanged.connect(self.transaction_list_record_actived)
        vlayer = QVBoxLayout()
        vlayer.addWidget(transaction_history_list_widget)
        self.transaction_history_list_widget = QWidget()
        self.transaction_history_list_widget.setLayout(vlayer)

        transaction_history_and_detail_layout = QHBoxLayout()
        transaction_history_and_detail_layout.addWidget(self.transaction_history_list_widget)

        self.transaction_record_detail = QLabel("history detail")
        transaction_history_and_detail_layout.addWidget(self.transaction_record_detail)

        self.widget_transaction_list_detail = QWidget()
        self.widget_transaction_list_detail.setLayout(transaction_history_and_detail_layout)
        self.widget_transaction_list_detail.show()
        if(len(all_transaction_history_list) > 0):
            transaction_history_list_widget.setCurrentRow(0)



    def open_asset_transaction_history(self):
        all_transaction_history_list = self.session.query(mixin_sqlalchemy_type.MySnapshot).filter_by(snap_asset_asset_id = self.asset_instance_in_item.asset_id).order_by(mixin_sqlalchemy_type.MySnapshot.id.desc()).all()
        self.show_transaction_history(all_transaction_history_list)

    def open_transaction_history(self):
        all_transaction_history_list = self.session.query(mixin_sqlalchemy_type.MySnapshot).order_by(mixin_sqlalchemy_type.MySnapshot.id.desc()).all()
        self.show_transaction_history(all_transaction_history_list)

    def execute_this_fn(self):
        for i in range(0, 5):
            time.sleep(1)
        return "Done."
    def print_output(self, s):
        print(s)
    def thread_complete(self):
        print("THREAD COMPLETE")

    def balance_load_thread_complete(self):
        print("THREAD COMPLETE")
        worker = Balance_Thread(self.selected_wallet_record, 10)
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
        file_name_selected = QFileDialog.getOpenFileName(self, "QFileDialog.getOpenFileName()", "","TXT Files (*.txt);;All Files (*)")
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
        file_name_selected = QFileDialog.getSaveFileName(self, "QFileDialog.getOpenFileName()", "","TXT Files (*.txt);;All Files (*)")
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
        file_name_selected = QFileDialog.getOpenFileName(self, "QFileDialog.getOpenFileName()", "","TXT Files (*.txt);;All Files (*)")
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
 
                    my_snapshot.snap_memo           = eachsnapshots.snapshot_id
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
        mysnapshots_worker.signals.finished.connect(self.thread_complete)
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
        print(exin_result)
        exin_price_list_widget = QListWidget()
        for eachPair in exin_result:
            this_list_item = QListWidgetItem()
            this_list_item.setData(0x0100, eachPair)
            this_list_item.setText(str(eachPair))
            exin_price_list_widget.addItem(this_list_item)
        #exin_price_list_widget.itemClicked.connect(self.balance_list_record_selected)
        if hasattr(self, "exin_trade_pair_list"):
            self.exin_tradelist_layout.removeWidget(self.exin_trade_pair_list)
        self.exin_trade_pair_list = exin_price_list_widget
        self.exin_tradelist_layout.addWidget(self.exin_trade_pair_list)
        return

    def received_balance_result(self, balance_result):
        if(balance_result.is_success):
            balance_list = QListWidget()
            for eachAsset in balance_result.data:
                this_list_item = QListWidgetItem()
                this_list_item.setData(0x0100, eachAsset)
                this_list_item.setText(eachAsset.name)
                balance_list.addItem(this_list_item)
            balance_list.itemClicked.connect(self.balance_list_record_selected)
            balance_list.currentItemChanged.connect(self.balance_list_record_selection_actived)
            current_select_row = 0
            if hasattr(self, "balance_list"):
                self.Balance_layout.removeWidget(self.balance_list)
                current_select_row = self.balance_list.currentRow()
            self.balance_list = balance_list
            if(len(balance_result.data) > 0):
                self.balance_list.setCurrentRow(current_select_row)
            self.Balance_layout.addWidget(self.balance_list)
        return
    def balance_list_record_selection_actived(self,itemCurr, itemPre):
        self.asset_instance_in_item = itemCurr.data(0x0100)
        self.asset_balance_label.setText(self.asset_instance_in_item.balance)
        deposit_address_title_value_segments = self.asset_instance_in_item.deposit_address()
        deposit_label_content = ""
        for each_seg in deposit_address_title_value_segments:
            deposit_label_content += each_seg["title"] + " : " + each_seg["value"] + "\n"
        self.asset_deposit_label.setText(deposit_label_content)
    def withdraw_address_list_record_selection_actived(self,itemCurr, itemPre):
        if itemCurr == None:
            self.clear_asset_address_detail()
            return
        self.withdraw_address_instance_in_item = itemCurr.data(0x0100)
        self.update_asset_address_detail(self.withdraw_address_instance_in_item, self.withdraw_address_of_asset_detail_label)
        self.remove_address_btn.setDisabled(False)

    def transaction_list_record_actived(self, itemCurr, itemPre):
        self.transaction_record_in_item = itemCurr.data(0x0100)
        totalString = ""
        totalString += ("UTC Timestamp: %s\n"%self.transaction_record_in_item.snap_created_at)
        totalString += ("opponent: %s\n"%self.transaction_record_in_item.snap_opponent_id)
        totalString += ("asset name: %s\n"%self.transaction_record_in_item.snap_asset_name)
        totalString += ("type: %s\n"%self.transaction_record_in_item.snap_type)
        totalString += ("memo: %s\n"%self.transaction_record_in_item.snap_memo)


        self.transaction_record_detail.setText(totalString)


    def transaction_list_record_selected(self, itemSelect):
        self.transaction_record_in_item = itemSelect.data(0x0100)
        totalString = ""
        totalString += ("UTC Timestamp: %s\n"%self.transaction_record_in_item.snap_created_at)
        totalString += ("opponent: %s\n"%self.transaction_record_in_item.snap_opponent_id)
        totalString += ("asset name: %s\n"%self.transaction_record_in_item.snap_asset_name)
        totalString += ("type: %s\n"%self.transaction_record_in_item.snap_type)
        totalString += ("memo: %s\n"%self.transaction_record_in_item.snap_memo)


        self.transaction_record_detail.setText(totalString)

    def balance_list_record_selected(self, itemSelect):
        self.asset_instance_in_item = itemSelect.data(0x0100)
        self.asset_balance_label.setText(self.asset_instance_in_item.balance)
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

    def send_asset_to_withdraw_address_pressed(self):
        self.selected_withdraw_address
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


    def open_exin_exchange(self):

        self.selected_trade_send = QPushButton("Send")
        self.selected_trade_send.pressed.connect(self.send_asset_to_address)

        self.selected_trade_manageasset = QPushButton("Manage contact")
        self.selected_trade_manageasset.pressed.connect(self.open_widget_manage_asset)

        self.trade_min_balance_label = QLabel("min")
        self.trade_max_balance_label = QLabel("max")

        exin_trade_detail_layout = QVBoxLayout()
        exin_trade_detail_layout.addWidget(self.trade_min_balance_label)
        exin_trade_detail_layout.addWidget(self.trade_max_balance_label)
        exin_trade_detail_layout.addWidget(self.selected_trade_send)
        exin_trade_detail_layout.addWidget(self.selected_trade_manageasset)
        self.exin_trade_detail_widget = QWidget()
        self.exin_trade_detail_widget.setLayout(exin_trade_detail_layout)

        self.exin_tradelist_layout = QVBoxLayout()
        self.exin_tradelist_widget = QWidget()
        self.exin_tradelist_widget.setLayout(self.exin_tradelist_layout)

        self.exin_tradelist_and_detail_layout = QHBoxLayout()
        self.exin_tradelist_and_detail_layout.addWidget(self.exin_tradelist_widget)
        self.exin_tradelist_and_detail_layout.addWidget(self.exin_trade_detail_widget)
        self.exin_tradelist_and_detail_widget = QWidget()
        self.exin_tradelist_and_detail_widget.setLayout(self.exin_tradelist_and_detail_layout)
        self.exin_tradelist_and_detail_widget.show()

        exin_worker = ExinPrice_Thread(mixin_asset_id_collection.USDT_ASSET_ID)
        exin_worker.signals.result.connect(self.received_exin_result)
        exin_worker.signals.finished.connect(self.thread_complete)

        self.threadPool.start(exin_worker)


    def open_selected_wallet(self):
        if (hasattr(self, "selected_wallet_record")):
            self.balance_and_detail_layout = QHBoxLayout()
            self.Balance_detail_layout = QVBoxLayout()
            self.selected_asset_send = QPushButton("Send")
            self.selected_asset_send.pressed.connect(self.send_asset_to_address)
            self.selected_asset_manageasset = QPushButton("Manage contact")
            self.selected_asset_manageasset.pressed.connect(self.open_widget_manage_asset)
            self.selected_asset_show_history = QPushButton("History")
            self.selected_asset_show_history.pressed.connect(self.open_asset_transaction_history)

            self.asset_balance_label = QLabel()
            balance_font = self.asset_balance_label.font()
            balance_font.setPointSize(40)
            self.asset_balance_label.setFont(balance_font)
            self.asset_balance_label.setAlignment(Qt.AlignCenter)

            self.asset_deposit_label = QLabel()
            self.asset_deposit_label.setTextInteractionFlags(Qt.TextSelectableByMouse)



            self.Balance_detail_layout.addWidget(self.asset_balance_label)
            self.Balance_detail_layout.addWidget(self.asset_deposit_label)

            self.Balance_detail_layout.addWidget(self.selected_asset_send)
            self.Balance_detail_layout.addWidget(self.selected_asset_manageasset)
            self.Balance_detail_layout.addWidget(self.selected_asset_show_history)

            self.Balance_layout = QVBoxLayout()
            self.widget_balance_list = QWidget()
            self.widget_balance_list.setLayout(self.Balance_layout)
            self.widget_balance_list.show()
            self.widget_balance_detail = QWidget()
            self.widget_balance_detail.setLayout(self.Balance_detail_layout)
            self.widget_balance_detail.show()
            self.balance_and_detail_layout.addWidget(self.widget_balance_list)
            self.balance_and_detail_layout.addWidget(self.widget_balance_detail)
            self.widget_balance = QWidget()
            self.widget_balance.setLayout(self.balance_and_detail_layout)
            self.widget_balance.show()

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
        else:
            return


app = QApplication([])
window = MainWindow()
app.exec_()

