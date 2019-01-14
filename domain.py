from functools import reduce
from itertools import repeat

import numpy
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

        self.device_id = 0

        self.s21s = list()
        self.s11s = list()
        self.s22s = list()

        self._result_baseline = list()
        self._result_freqs = list()
        self._result_s11 = list()
        self._result_s22 = list()
        self._result_normalized_att = list()
        self._result_att_error_per_code = list()
        self._result_att = list()
        self._result_att_all = list()

    def _clear(self):
        self.s21s.clear()
        self.s11s.clear()
        self.s22s.clear()

        self._result_baseline.clear()
        self._result_freqs.clear()
        self._result_s11.clear()
        self._result_s22.clear()
        self._result_normalized_att.clear()
        self._result_att_error_per_code.clear()
        self._result_att.clear()
        self._result_att_all.clear()

    def connect(self):
        print('find instruments')
        return self._instruments.find()

    def check(self, threshold_level: float):
        print('check sample presence')

        points = 51
        data = self._instruments.test_sample(points=points).split(',')
        print(len(data))
        avg = reduce(lambda a, b: a + b, map(float, data), 0) / points

        print(f'>>> avg level: {avg}')

        return avg > threshold_level

    def measure(self, device_id):
        print(f'run measurement {device_id}')
        self._clear()
        self._threadPool.start(Task(self._measureFunc, self._processingFunc, device_id))

    def _measureFunc(self, device_id):
        print('start measurement task')
        self.device_id = device_id
        self.s21s, self.s11s, self.s22s, self._result_att_all = self._instruments.measure(device_id)
        print('end measurement task')

    def _processingFunc(self):
        print('processing stats')
        # gen freq data
        # TODO: read off PNA
        self._result_freqs = list(numpy.linspace(self._instruments.params[self.device_id]['f1'],
                                                 self._instruments.params[self.device_id]['f2'],
                                                 self._instruments.points))
        self._result_freqs = list(map(lambda x: x/1_000_000_000, self._result_freqs))

        # calc baseline
        self._result_baseline = self.s21s[0]

        # calc S11, S22
        self._result_s11 = self.s11s
        self._result_s22 = self.s22s

        # calc attenuation
        self._result_att = self.s21s

        # calc normalized attenuation
        self._result_normalized_att = list()
        for s21 in self.s21s:
            self._result_normalized_att.append([current - baseline for current, baseline in zip(s21, self._result_baseline)])

        # calc attenuation error per code
        for data, att in zip(self._result_normalized_att, self._instruments.codes[self.device_id].keys()):
            self._result_att_error_per_code.append([d + c for d, c in zip(data, repeat(att, len(data)))])

        # calc attenuation error per freq - ?
        # how to choose freqs?
        # interpolate data between setting points or simply connect points?

        # calc phase shift

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

    @property
    def calibrationFile(self):
        return self._instruments.calibration_file

    @calibrationFile.setter
    def calibrationFile(self, name):
        self._instruments.calibration_file = name

    @property
    def insLossXs(self):
        return self._result_freqs

    @property
    def insLossYs(self):
        return self._result_baseline

    @property
    def errorPerCodeXs(self):
        return [self._result_freqs] * 8

    @property
    def errorPerCodeYs(self):
        return self._result_att_error_per_code

    @property
    def inputInverseLossXs(self):
        return [self._result_freqs] * 8

    @property
    def inputInverseLossYs(self):
        return self._result_s11

    @property
    def outputInverseLossXs(self):
        return [self._result_freqs] * 8

    @property
    def outputInverseLossYs(self):
        return self._result_s22

    @property
    def normalizedAttXs(self):
        return [self._result_freqs] * 8

    @property
    def normalizedAttYs(self):
        return self._result_normalized_att

    @property
    def attenuationXs(self):
        return [self._result_freqs] * len(self._result_att_all)

    @property
    def attenuationYs(self):
        return self._result_att_all

