from functools import reduce
from PyQt5.QtCore import QObject, QRunnable, QThreadPool, pyqtSignal

from instrumentcontroller import InstrumentController


class MeasureContext:

    def __init__(self, model):
        self._model = model

    def __enter__(self):
        print('\nacquire analyzer context\n')
        self._model._analyzer.init_instrument()

    def __exit__(self, *args):
        print('\nexit analyzer context\n')
        self._model._analyzer.finish()


class Task(QRunnable):

    def __init__(self, fn, end, *args, **kwargs):
        super().__init__()
        self.fn = fn
        self.end = end
        self.args = args
        self.kwargs = kwargs

    def run(self):
        self.fn(*self.args, **self.kwargs)
        self.end()


class Domain(QObject):

    measureFinished = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)

        self._instruments = InstrumentController()
        self._threadPool = QThreadPool()

        self._baseline = list()

    def _clear(self):
        self._baseline.clear()

    def connect(self):
        print('find instruments')
        return self._instruments.find()

    def check(self):
        print('check sample presence')

        pass_threshold = -90
        points = 51
        avg = reduce(lambda a, b: a + b, map(float, self._instruments.test_sample(points=51).split(',')), 0) / points

        print(f'>>> avg level: {avg}')

        return avg > pass_threshold

    def measure(self):
        print(f'run measurement')
        self._clear()
        self._threadPool.start(Task(self._measureFunc, self._processingFunc))

    def _measureFunc(self):
        print('start measurement task')
        self._instruments.measure(1)
        print('end measurement task')

    def _processingFunc(self):
        self.measureFinished.emit()

    @property
    def analyzerAddress(self):
        return self._instruments.analyzer_addr

    @analyzerAddress.setter
    def analyzerAddress(self, addr):
        self._instruments.analyzer_addr = addr

    @property
    def programmerName(self):
        return str(self._instruments._programmer)

    @property
    def analyzerName(self):
        return str(self._instruments._analyzer)


