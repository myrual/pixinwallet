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
                self.send_address_selection_widget.insertItem(i, eachAsset.label, userData = eachAsset)
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

    def balance_list_record_selected(self, itemSelect):
        self.asset_instance_in_item = itemSelect.data(0x0100)
        self.asset_balance_label.setText(self.asset_instance_in_item.balance)
    def update_asset_address_detail(self, this_withdraw_address, label_widget):
        stringForAddress = ""
        if this_withdraw_address.label != "":
            stringForAddress += this_withdraw_address.label
        if this_withdraw_address.public_key != "":
            stringForAddress +=  ("\n" + this_withdraw_address.public_key)
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


    def open_selected_wallet(self):
        if (hasattr(self, "selected_wallet_record")):
            self.balance_and_detail_layout = QHBoxLayout()
            self.Balance_detail_layout = QVBoxLayout()
            self.selected_asset_send = QPushButton("Send")
            self.selected_asset_send.pressed.connect(self.send_asset_to_address)
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
            worker.signals.finished.connect(self.balance_load_thread_complete)
            self.threadPool.start(worker)
        else:
            return


app = QApplication([])
window = MainWindow()
app.exec_()

