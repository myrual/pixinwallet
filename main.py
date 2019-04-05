from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *

import time
import traceback, sys


class WorkerSignals(QObject):
    finished = pyqtSignal()
    error = pyqtSignal(tuple)
    result = pyqtSignal(object)
class Worker(QRunnable):
    def __init__(self, fn, *args, **kwargs):
        super(Worker, self).__init__()
        self.fn = fn
        self.args = args
        self.kwargs = kwargs
        self.signals = WorkerSignals()

    @pyqtSlot()
    def run(self):
        try:
            result = self.fn(*self.args, **self.kwargs, status = self.signals.status,
                    progress=self.signals.progress,)
        except:
            traceback.print_exc()
            exctype, value = sys.exc_info()[:2]
            self.signals.error.emit((exctype, value, traceback.format_exc()))
        else:
            self.signals.result.emit(result)
        finally:
            self.signals.finished.emit()
        time.sleep(5)
        print("Thread complete")
class MainWindow(QMainWindow):
    def __init__(self, *args, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)

        self.counter = 0
        layout = QVBoxLayout()
        self.l = QLabel("Start")

        b = QPushButton("DANGER!")
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
        file_name = QFileDialog.getOpenFileName(self, "QFileDialog.getOpenFileName()", "","All Files (*);;CSV Files (*.csv)")
        print("selected_file:")
        print(file_name)
    def oh_no(self):
        worker = Worker(self.execute_this_fn)
        worker.signals.result.connect(self.print_output)
        worker.signals.finished.connect(self.thread_complete)
        self.threadPool.start(worker)
    def recurring_timer(self):
        self.counter += 1
        self.l.setText("Counter %d" % self.counter)

app = QApplication([])
window = MainWindow()
app.exec_()

