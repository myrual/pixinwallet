from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *

import time
import traceback, sys
import wallet_api
import mixin_asset_id_collection


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


class Balance_Thread(QRunnable):
    def __init__(self, wallet_obj, *args, **kwargs):
        super(Balance_Thread, self).__init__()
        self.wallet_obj = wallet_obj
        self.args = args
        self.kwargs = kwargs
        self.signals = WorkerSignals()

    @pyqtSlot()
    def run(self):
        try:
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
    def execute_this_fn(self):
        for i in range(0, 5):
            time.sleep(1)
        return "Done."
    def print_output(self, s):
        print(s)
    def thread_complete(self):
        print("THREAD COMPLETE")
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
           

    def open_file(self):
        file_name_selected = QFileDialog.getOpenFileName(self, "QFileDialog.getOpenFileName()", "","All Files (*);;CSV Files (*.csv)")
        file_name = file_name_selected[0]
        fileter   = file_name_selected[1]
        if(file_name == ''):
            print("User cancel file")
        else:
            print("User select file with %s" % file_name)
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
            print("Failed to create address ")

    def pop_create_withdraw_address_window_bitcoinstyle(self):


        account_tag_widget    = QLabel("Account alias:")
        self.account_tag_edit = QLineEdit()
        public_key_widget     = QLabel("Deposit address:")
        self.public_key_edit  = QLineEdit()
        asset_pin_widget     = QLabel("Asset pin:")
        self.asset_pin_edit  = QLineEdit()
        self.asset_pin_edit.setEchoMode(QLineEdit.PasswordEchoOnEdit)
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
        self.pin_selected_edit.setInputMask('999999')
        self.pin_selected_edit.setEchoMode(QLineEdit.PasswordEchoOnEdit)
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
    def received_asset_withdraw_addresses_result(self, withdraw_addresses_asset_result):
        if(withdraw_addresses_asset_result.is_success):
            withdraw_address_list = QListWidget()
            for eachAsset in withdraw_addresses_asset_result.data:
                this_list_item = QListWidgetItem()
                this_list_item.setData(0x0100, eachAsset)
                this_list_item.setText(eachAsset.label)
                withdraw_address_list.addItem(this_list_item)
            withdraw_address_list.itemClicked.connect(self.withdrawaddress_list_record_selected)
            withdraw_address_list.currentItemChanged.connect(self.withdraw_address_list_record_selection_actived)
            self.withdraw_addresses_list_widget = withdraw_address_list

            self.withdraw_addresses_list_and_new_layout.insertWidget(0, self.withdraw_addresses_list_widget)
            if(len(withdraw_addresses_asset_result.data) > 0):
                self.withdraw_addresses_list_widget.setCurrentRow(0)
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
            self.balance_list = balance_list
            if(len(balance_result.data) > 0):
                self.balance_list.setCurrentRow(0)
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
        self.withdraw_address_instance_in_item = itemCurr.data(0x0100)
        self.update_asset_address_detail(self.withdraw_address_instance_in_item)


    def balance_list_record_selected(self, itemSelect):
        self.asset_instance_in_item = itemSelect.data(0x0100)
        self.asset_balance_label.setText(self.asset_instance_in_item.balance)
    def update_asset_address_detail(self, this_withdraw_address):
        self.public_key_label_withdraw_address_asset.setText(this_withdraw_address.public_key)
        self.label_label_withdraw_address_asset.setText(this_withdraw_address.label)
        self.account_name_label_withdraw_address_asset.setText(this_withdraw_address.account_name)
        self.account_tag_label_withdraw_address_asset.setText(this_withdraw_address.account_tag)
        self.fee_label_withdraw_address_asset.setText(this_withdraw_address.fee)
        self.reserve_label_withdraw_address_asset.setText(this_withdraw_address.reserve)
        self.dust_label_withdraw_address_asset.setText(this_withdraw_address.dust)
        self.updated_at_label_withdraw_address_asset.setText(this_withdraw_address.updated_at) 

    def withdrawaddress_list_record_selected(self, itemSelect):
        self.withdraw_address_instance_in_item = itemSelect.data(0x0100)
        self.update_asset_address_detail(self.withdraw_address_instance_in_item)




    def open_widget_manage_asset(self):
        if (hasattr(self, "asset_instance_in_item")):
            
            add_withdraw_address_asset_btn = QPushButton("Add new address")
            add_withdraw_address_asset_btn.pressed.connect(self.pop_create_withdraw_address_window_bitcoinstyle)

            self.withdraw_addresses_list_and_new_layout = QVBoxLayout()
            self.withdraw_addresses_list_and_new_layout.addWidget(add_withdraw_address_asset_btn)

            withdraw_addresses_list_and_new_widget = QWidget()
            withdraw_addresses_list_and_new_widget.setLayout(self.withdraw_addresses_list_and_new_layout)

            self.public_key_label_withdraw_address_asset = QLabel("public key")
            self.label_label_withdraw_address_asset = QLabel("label")
            self.account_name_label_withdraw_address_asset = QLabel("account name:")
            self.account_tag_label_withdraw_address_asset = QLabel("account label:")
            self.fee_label_withdraw_address_asset = QLabel("fee")
            self.reserve_label_withdraw_address_asset = QLabel("reserve")
            self.dust_label_withdraw_address_asset = QLabel("dust")
            self.updated_at_label_withdraw_address_asset = QLabel("updated at")
            remove_address_btn = QPushButton("Delete")

            withdraw_addresses_detail_layout = QVBoxLayout()

            withdraw_addresses_detail_layout.addWidget(self.public_key_label_withdraw_address_asset)
            withdraw_addresses_detail_layout.addWidget(self.label_label_withdraw_address_asset )
            withdraw_addresses_detail_layout.addWidget(self.account_name_label_withdraw_address_asset )
            withdraw_addresses_detail_layout.addWidget(self.account_tag_label_withdraw_address_asset )
            withdraw_addresses_detail_layout.addWidget(self.fee_label_withdraw_address_asset )
            withdraw_addresses_detail_layout.addWidget(self.reserve_label_withdraw_address_asset )
            withdraw_addresses_detail_layout.addWidget(self.dust_label_withdraw_address_asset )
            withdraw_addresses_detail_layout.addWidget(self.updated_at_label_withdraw_address_asset )
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


    def open_selected_wallet(self):
        if (hasattr(self, "selected_wallet_record")):
            self.balance_and_detail_layout = QHBoxLayout()
            self.Balance_detail_layout = QVBoxLayout()
            self.selected_asset_send = QPushButton("Send")
            self.selected_asset_manageasset = QPushButton("Manage contact")
            self.selected_asset_manageasset.pressed.connect(self.open_widget_manage_asset)

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
            worker.signals.finished.connect(self.thread_complete)
            self.threadPool.start(worker)
        else:
            return


app = QApplication([])
window = MainWindow()
app.exec_()

