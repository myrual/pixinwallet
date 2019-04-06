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
            self.wallet_list_widget = wallet_list
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
            balance_list.itemClicked.connect(self.wallet_list_record_selected)
            self.balance_list = balance_list
            self.Balance_layout.addWidget(self.balance_list)
        return
    def wallet_list_record_selected(self, itemSelect):
        wallet_instance_in_item = itemSelect.data(0x0100)
        print(wallet_instance_in_item)
        print("%s selected"%wallet_instance_in_item.userid)
        self.Balance_layout = QVBoxLayout()
        Title_Label = QLabel("Balance")
        Title_Label.setAlignment(Qt.AlignCenter)
        self.Balance_layout.addWidget(Title_Label)
        self.balance_widget = QWidget()
        self.balance_widget.setLayout(self.Balance_layout)
        self.balance_widget.show()

        worker = Balance_Thread(wallet_instance_in_item)
        worker.signals.result.connect(self.received_balance_result)
        worker.signals.finished.connect(self.thread_complete)
        self.threadPool.start(worker)


app = QApplication([])
window = MainWindow()
app.exec_()

