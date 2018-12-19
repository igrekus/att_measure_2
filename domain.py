import time
from collections import defaultdict

import serial
from PyQt5.QtCore import QObject, pyqtSignal, QRunnable, pyqtSlot, QThreadPool

# MOCK
def_mock = True


class MeasureContext:

    def __init__(self, model):
        self._model = model

    def __enter__(self):
        print('\nacquire analyzer context\n')
        self._model._analyzer.init_instrument()

    def __exit__(self, *args):
        print('\nexit analyzer context\n')
        self._model._analyzer.finish()


class InstrumentManager:

    def __init__(self):
        self._analyzer_addr = 'TCPIP::192.168.0.3::INSTR'

        self._programmer = None
        self._analyzer = None

        self._available_ports = list()

        self._harmonic = 1

    def _find_ports(self):
        for port in [f'COM{i+1}' for i in range(256)]:
            try:
                s = serial.Serial(port)
                s.close()
                self._available_ports.append(port)
            except (OSError, serial.SerialException):
                pass

    def _find_spi_port(self):
        for port in self._available_ports:
            s = serial.Serial(port=port, baudrate=9600, timeout=0.5)
            if s.is_open:
                s.write(b'<n>')
                ans = s.read(9)
                s.close()
                if b'SPI' in ans:
                    return port
        else:
            return ''

    def _find_parallel_port(self):
        for port in self._available_ports:
            s = serial.Serial(port=port, baudrate=9600, timeout=0.5)
            if s.is_open:
                s.write(b'#NAME')
                ans = s.read(9)
                s.close()
                if b'ARDUINO' in ans:
                    return port
        else:
            return ''

    def _find_programmer(self):
        if def_mock:
            from arduino.arduinospimock import ArduinoSpiMock
            self._programmer = ArduinoSpiMock()
            return

        port = self._find_parallel_port()
        if port:
            from arduino.arduinoparallel import ArduinoParallel
            self._programmer = ArduinoParallel(port=port, baudrate=9600, parity=serial.PARITY_NONE, bytesize=8,
                                               stopbits=serial.STOPBITS_ONE, timeout=0.5)
            return

        port = self._find_spi_port()
        if port:
            from arduino.arduinospi import ArduinoSpi
            self._programmer = ArduinoSpi(port=port, baudrate=115200, parity=serial.PARITY_NONE, bytesize=8,
                                          stopbits=serial.STOPBITS_ONE, timeout=1)

    def _find_analyzer(self):
        if def_mock:
            from instr.obzor304mock import Obzor304Mock
            self._analyzer = Obzor304Mock(self.analyzer_addr)
            return

        from instr.obzor304 import Obzor304
        try:
            self._analyzer = Obzor304(self._analyzer_addr)
        except Exception as ex:
            print(f'analyzer error: {ex}')

    def find(self):
        self._find_ports()
        print(f'available ports: {" ".join(self._available_ports)}')

        print('find programmer')
        self._find_programmer()
        print(f'programmer: {self._programmer}')

        print('find analyzer')
        try:
            self._find_analyzer()
        except Exception as ex:
            print(ex)
        print(f'analyzer: {self._analyzer}')

        return self._programmer and self._analyzer

    def measure(self, code):
        if not self._programmer.set_lpf_code(code):
            print(f'error setting code: {code}')
            return [], []
        time.sleep(0.7)
        return self._analyzer.measure(code)

    @property
    def harmonic(self):
        return self._harmonic

    @harmonic.setter
    def harmonic(self, value):
        # SENSe<Ch>:OFFSet[:STATe] <bool>

        # SENS:OFFS:PORT:DATA?
        # SENSe<Ch>:OFFSet:PORT<Pt>[:FREQuency]:DATA?
        # Считывает массив частот точек измерения порта Pt когда функция смещения частоты активна и тип смещения выбран "PORT" (только запрос)

        # SENS:OFFS:PORT:MULT
        # SENSe<Ch>:OFFSet:PORT<Pt>[:FREQuency]:MULTiplier <numeric>
        # SENSe<Ch>:OFFSet:PORT<Pt>[:FREQuency]:MULTiplier?
        # Описание
        # Устанавливает или считывает множитель базового частотного
        # диапазона для получения частоты порта Pt, когда функция
        # смещения частоты включена и тип смещения выбран "PORT".
        # (команда/запрос)

        # 1 - вкл
        # 2 - тип порт1 -> порт2
        # 3 - порт2: множитель x2, x3

        print('>>> IM set harmonic', value)

    @property
    def analyzer_addr(self):
        return self._analyzer_addr

    @analyzer_addr.setter
    def analyzer_addr(self, addr):
        self._analyzer_addr = addr


class Task(QRunnable):

    def __init__(self, end, fn, *args, **kwargs):
        super().__init__()
        self.end = end
        self.fn = fn
        self.args = args
        self.kwargs = kwargs

    @pyqtSlot()
    def run(self):
        self.fn(*self.args, **self.kwargs)
        self.end()


class Domain(QObject):

    MAXREG = 127

    codeMeasured = pyqtSignal()
    measurementFinished = pyqtSignal()
    statsReady = pyqtSignal()
    harmonicMeasured = pyqtSignal()
    harmonicPointMeasured = pyqtSignal()
    singleMeasured = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)

        self._instruments = InstrumentManager()
        self.pool = QThreadPool()

        self._code = 0

        self._lastMeasurement = tuple()
        self._lastFreqs = list()
        self._lastAmps = list()

        self.freqs = list()
        self.amps = list()
        self.codes = list()
        self.cutoff_freqs = list()
        self.loss_double_freq = list()
        self.loss_triple_freq = list()
        self.cutoff_freq_delta_x = list()
        self.cutoff_freq_delta_y = list()

        self.harms = defaultdict(list)
        self.harm_deltas = defaultdict(list)

        self._cutoffMag = -6
        self._cutoffAmp = 0

        self.measurementFinished.connect(self._processStats)
        self.harmonicPointMeasured.connect(self._processHarmonics)

    def _clear(self):
        self._lastFreqs.clear()
        self._lastAmps.clear()
        self.freqs.clear()
        self.amps.clear()
        self.codes.clear()
        self.cutoff_freqs.clear()
        self.loss_double_freq.clear()
        self.loss_triple_freq.clear()
        self.cutoff_freq_delta_x.clear()
        self.cutoff_freq_delta_y.clear()
        self.harms.clear()
        self.harm_deltas.clear()

    def findInstruments(self):
        print('find instruments')
        return self._instruments.find()

    def measure(self):
        print(f'run measurement, cutoff={self._cutoffMag}')
        self._clear()
        self.pool.start(Task(self.measurementFinished.emit, self._measureTask))

    def _measureCode(self, code=0):
        print(f'\nmeasure: code={code:03d}, bin={code:07b}')
        self._lastMeasurement = self._instruments.measure(code)

    def _measureTask(self):
        print('start measurement task')
        regs = self.MAXREG + 1

        # MOCK
        if def_mock:
            regs = 5

        with MeasureContext(self._instruments):
            for code in range(regs):
                self._measureCode(code=code)
                self._processCode()
                self.codeMeasured.emit()

        print('end measurement task')

    def _parseFreqStr(self, string):
        return [float(num) for num in string.split(',')]

    def _parseAmpStr(self, string):
        return [float(num) for idx, num in enumerate(string.split(',')) if idx % 2 == 0]

    def _processCode(self):
        print('processing code measurement')
        self._lastFreqs = self._parseFreqStr(self._lastMeasurement[0])
        self._lastAmps = self._parseAmpStr(self._lastMeasurement[1])

        self.freqs.append(self._lastFreqs)
        self.amps.append(self._lastAmps)

    def _processStats(self):
        print('process stats')
        max_amp = max(map(max, self.amps))

        cutoff_mag = max_amp + self._cutoffMag
        self._cutoffAmp = cutoff_mag

        for a, f in zip(self.amps, self.freqs):
            cutoff_freq = f[a.index(min(a, key=lambda x: abs(cutoff_mag - x)))]
            self.cutoff_freqs.append(cutoff_freq)

            amp_max = max(a)

            double_f = cutoff_freq * 2
            triple_f = cutoff_freq * 3
            double_f_index = f.index(min(f, key=lambda x: abs(double_f - x)))
            triple_f_index = f.index(min(f, key=lambda x: abs(triple_f - x)))

            self.loss_double_freq.append(amp_max - a[double_f_index])
            self.loss_triple_freq.append(amp_max - a[triple_f_index])

        self.cutoff_freqs = list(reversed(self.cutoff_freqs))
        # self.loss_double_freq = list(reversed(self.loss_double_freq))
        # self.loss_triple_freq = list(reversed(self.loss_triple_freq))
        self.codes = list(range(len(self.cutoff_freqs)))

        for i in range(len(self.cutoff_freqs[:-1])):
            d = abs(self.cutoff_freqs[i + 1] - self.cutoff_freqs[i])
            self.cutoff_freq_delta_y.append(d)

        self.cutoff_freq_delta_x = list(range(len(self.cutoff_freq_delta_y)))

        self.statsReady.emit()

    def measureSingle(self):
        print(f'measure harmonic={self._harmonic}, code={self._code}')
        with MeasureContext(self._instruments):
            self._measureCode(code=self._code)
            self._processCode()

        self.singleMeasured.emit()

    def measureHarmonics(self):
        print(f'run harmonic measurement, cutoff={self._cutoffMag}')

        self.harms.clear()
        self.harm_deltas.clear()
        self.pool.start(Task(self.harmonicPointMeasured.emit, self._measureHarmonicTask))

    def _measureHarmonicTask(self):
        print(f'start harmonic measurement task')
        regs = self.MAXREG + 1

        # MOCK
        if def_mock:
            regs = 5

        with MeasureContext(self._instruments):
            for harm in [2, 3]:
                self._instruments.harmonic = harm
                for code in range(regs):
                    self._measureCode(code=code)
                    self._processHarmonicCode(harm)

        self._processHarmonics()
        self.harmonicMeasured.emit()
        print('end harmonic measurement task')

    def _processHarmonicCode(self, n):
        print('processing code measurement')
        self.harms[n].append(self._parseAmpStr(self._lastMeasurement[1]))

    def _processHarmonics(self):
        print(f'processing harmonic stats')
        for key, harms in self.harms.items():
            for base, harm in zip(self.amps, harms):
                self.harm_deltas[key].append(max(base) - max(harm))

    @property
    def analyzerAddress(self):
        return self._instruments.analyzer_addr

    @analyzerAddress.setter
    def analyzerAddress(self, addr):
        print(f'set analyzer address {addr}')
        self._instruments.analyzer_addr = addr

    @property
    def programmerName(self):
        return str(self._instruments._programmer)

    @property
    def analyzerName(self):
        return str(self._instruments._analyzer)

    @property
    def cutoffMag(self):
        return self._cutoffMag

    @cutoffMag.setter
    def cutoffMag(self, value):
        self._cutoffMag = value

    @property
    def canMeasure(self):
        return self._instruments._analyzer and self._instruments._programmer

    @property
    def lastXs(self):
        return self._lastFreqs

    @property
    def lastYs(self):
        return self._lastAmps

    @property
    def cutoffXs(self):
        return self.codes

    @property
    def cutoffYs(self):
        return self.cutoff_freqs

    @property
    def deltaXs(self):
        return self.cutoff_freq_delta_x

    @property
    def deltaYs(self):
        return self.cutoff_freq_delta_y

    @property
    def lossDoubleXs(self):
        return self.codes

    @property
    def lossDoubleYs(self):
        return self.loss_double_freq

    @property
    def lossTripleXs(self):
        return self.codes

    @property
    def lossTripleYs(self):
        return self.loss_triple_freq

    @property
    def singleMeasureXs(self):
        return self._lastFreqs

    @property
    def singleMeasureYs(self):
        return self._lastAmps

    @property
    def harmonicN(self):
        return self._harmonic

    @harmonicN.setter
    def harmonicN(self, value):
        self._harmonic = value

    @property
    def code(self):
        return self._code

    @code.setter
    def code(self, value):
        self._code = value

    @property
    def cutoffAmp(self):
        return self._cutoffAmp

