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

        chan = 1
        points = 51
        pass_threshold = -90
        # pass_threshold = -15

        # TODO move to instrumentcontroller

        self._instruments._programmer.set_lpf_code(0b100000)
        self._instruments._analyzer.reset()
        # TODO load calibration here
        _, meas_name = self._instruments._analyzer.calc_create_measurement(chan=chan, meas_name='check_s21', meas_type='S21')   # TODO add measurement parameter const
        self._instruments._analyzer.display_create_window(window=1)
        self._instruments._analyzer.display_measurement(window=1, trace=1, meas_name=meas_name)
        self._instruments._analyzer.trigger_source('MANual')
        print(self._instruments._analyzer.operation_complete)   # TODO wait for OPC
        self._instruments._analyzer.wait()
        self._instruments._analyzer.trigger_point_mode(chan=chan, mode='OFF')
        self._instruments._analyzer.source_power(chan=chan, port=1, value=-5)
        self._instruments._analyzer.sense_fom_sweep_type(chan=chan, range=1, type='linear')
        self._instruments._analyzer.sense_sweep_points(chan=chan, points=points)
        self._instruments._analyzer.sense_freq_start(chan=chan, value=10, unit='MHz')
        self._instruments._analyzer.sense_freq_stop(chan=chan, value=8, unit='GHz')
        self._instruments._analyzer.trigger_initiate()
        self._instruments._analyzer.wait()
        self._instruments._analyzer.calc_parameter_select(chan=chan, name=meas_name)
        self._instruments._analyzer.format('ASCII')

        res = self._instruments._analyzer.calc_formatted_data(chan=chan)

        avg = reduce(lambda a, b: a + b, map(float, res.split(',')), 0) / points

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

#     def measure_code(self, chan, name):
    #         print('measure param', name)
    #         self._analyzer.send(f'CALCulate{chan}:PARameter:SELect "{name}"')
    #         self._analyzer.send(f'FORMat ASCII')
    #         return self._analyzer.query(f'CALCulate{chan}:DATA? FDATA')
    #
    #     def parse_measure_string(self, string: str):
    #         return [float(point) for point in string.split(',')]
    #
    #     def measureTask(self, params):
    #         print(f'measurement task run {params}')
    #
    #         chan = 1
    #         port = 1
    #         s21_name = 'meas_s21'
    #         s11_name = 'meas_s11'
    #         s22_name = 'meas_s22'
    #
    #         meas_pow = self.measure_params[params]['pow']
    #         meas_f1 = self.measure_params[params]['f1']
    #         meas_f2 = self.measure_params[params]['f2']
    #         points = self.measure_params[params]['points']
    #
    #         if mock_enabled:
    #             points = 51
    #
    #         # self._analyzer.send(f'SYSTem:FPRESet')
    #
    #         self._analyzer.send(f'CALCulate{chan}:PARameter:DEFine:EXT "{s21_name}",S21')
    #         self._analyzer.send(f'CALCulate{chan}:PARameter:DEFine:EXT "{s11_name}",S11')
    #         self._analyzer.send(f'CALCulate{chan}:PARameter:DEFine:EXT "{s22_name}",S22')
    #         self._analyzer.send(f'DISPlay:WINDow1:TRACe1:DELete')
    #         self._analyzer.send(f'DISPlay:WINDow1:TRACe1:FEED "{s21_name}"')
    #         self._analyzer.send(f'DISPlay:WINDow1:TRACe2:FEED "{s11_name}"')
    #         self._analyzer.send(f'DISPlay:WINDow1:TRACe3:FEED "{s22_name}"')
    #
    #         self._analyzer.query(f'INITiate{chan}:CONTinuous ON;*OPC?')
    #
    #         self._analyzer.send(f'SOURce{chan}:POWer{port} {meas_pow} dbm')
    #         self._analyzer.send(f'SENSe{chan}:FOM:RANGe1:SWEep:TYPE linear')
    #         self._analyzer.send(f'SENSe{chan}:SWEep:POINts {points}')
    #         self._analyzer.send(f'SENSe{chan}:FREQuency:STARt {meas_f1}')
    #         self._analyzer.send(f'SENSe{chan}:FREQuency:STOP {meas_f2}')
    #
    #         s21s = list()
    #         s11s = list()
    #         s22s = list()
    #
    #         for label, code in list(self.level_codes[params].items()):
    #             print(f'setting value={label} code={code}')
    #             self._progr.set_lpf_code(code)
    #
    #             if not mock_enabled:
    #                 time.sleep(1)
    #
    #             self._analyzer.send(f'TRIG:SCOP CURRENT')
    #
    #             s21s.append(self.parse_measure_string(self.measure_code(chan, s21_name)))
    #             s11s.append(self.parse_measure_string(self.measure_code(chan, s11_name)))
    #             s22s.append(self.parse_measure_string(self.measure_code(chan, s22_name)))
    #
    #         # gen freq data
    #         # TODO: read off PNA
    #         self._res_freqs = list(numpy.linspace(meas_f1, meas_f2, points))
    #
    #         # calc baseline
    #         self._res_baseline = s21s[0]
    #
    #         # calc normalized attenuation
    #         self._res_normalized_att = list()
    #         for s21 in s21s:
    #             self._res_normalized_att.append([s - b for s, b in zip(s21, self._res_baseline)])
    #
    #         # calc S11, S22
    #         self._res_s11 = s11s
    #         self._res_s22 = s22s
    #
    #         # calc attenuation error per code
    #         for data, att in zip(self._res_normalized_att, self.level_codes[params].keys()):
    #             self._res_att_err_per_code.append([d + c for d, c in zip(data, repeat(att, len(data)))])
    #
    #         # calc attenuation error per freq - ?
    #         # how to chose freqs?
    #         # interpolate data between setting points or simply connect points?
    #
    #         # calc phase shift
    #
    #         # calc attenuation
    #         self._res_att = s21s

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


