from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *

import time
import traceback, sys
import wallet_api


class WorkerSignals(QObject):
    finished = pyqtSignal()
    error = pyqtSignal(tuple)
    result = pyqtSignal(object)
class Balance_Thread(QRunnable):
    def __init__(self, wallt_obj, *args, **kwargs):
        super(Balance_Thread, self).__init__()
        self.wallt_obj = wallt_obj
        self.args = args
        self.kwargs = kwargs
        self.signals = WorkerSignals()

    @pyqtSlot()
    def run(self):
        try:
            result = self.wallt_obj.get_balance()
        except:
            traceback.print_exc()
            exctype, value = sys.exc_info()[:2]
            self.signals.error.emit((exctype, value, traceback.format_exc()))
        else:
            self.signals.result.emit(result)
        finally:
            self.signals.finished.emit()
        print("Balance Thread")
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
        self.l = QLabel("Need load wallet")
        self.l.setAlignment(Qt.AlignCenter)

        b = QPushButton("Open Wallet file")
        b.pressed.connect(self.open_file)
        layout.addWidget(self.l)
        layout.addWidget(b)

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
    def open_file(self):
        file_name_selected = QFileDialog.getOpenFileName(self, "QFileDialog.getOpenFileName()", "","All Files (*);;CSV Files (*.csv)")
        file_name = file_name_selected[0]
        fileter   = file_name_selected[1]
        if(file_name == ''):
            print("User cancel file")
        else:
            print("User select file with %s" % file_name)
            self.l.setText("Select Wallet record")
            wallet_records = wallet_api.load_wallet_csv_file(file_name)
            wallet_list = QListWidget()
            for each_wallet in wallet_records:
                this_list_item = QListWidgetItem()
                this_list_item.setData(0x0100, each_wallet)
                this_list_item.setText(each_wallet.userid)
                wallet_list.addItem(this_list_item)
                wallet_list.itemClicked.connect(self.wallet_list_record_selected)
            select_wallet_btn = QPushButton("Load selected wallet")
            select_wallet_btn.pressed.connect(self.open_selected_wallet)
            wallet_record_and_select_layout = QVBoxLayout()
            wallet_record_and_select_layout.addWidget(wallet_list)
            wallet_record_and_select_layout.addWidget(select_wallet_btn)
            self.wallet_list_widget =  QWidget()
            self.wallet_list_widget.setLayout(wallet_record_and_select_layout)
            self.wallet_list_widget.show()
            #self.rootLayout.addWidget(wallet_list)

    def oh_no(self):
        worker = Balance_Thread(self.execute_this_fn)
        worker.signals.result.connect(self.print_output)
        worker.signals.finished.connect(self.thread_complete)
        self.threadPool.start(worker)
    def recurring_timer(self):
        self.counter += 1
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

    def balance_list_record_selected(self, itemSelect):
        self.asset_instance_in_item = itemSelect.data(0x0100)
        self.asset_balance_label.setText(self.asset_instance_in_item.balance)

    def wallet_list_record_selected(self, itemSelect):
        self.selected_wallet_record = itemSelect.data(0x0100)
        print(self.selected_wallet_record)
        print("%s selected"%self.selected_wallet_record.userid)



    def open_selected_wallet(self):
        if (hasattr(self, "selected_wallet_record")):
            self.balance_and_detail_layout = QHBoxLayout()
            self.Balance_detail_layout = QVBoxLayout()
            self.selected_asset_send = QPushButton("Send")
            self.selected_asset_manageasset = QPushButton("Manage address")

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

