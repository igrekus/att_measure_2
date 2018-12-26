import time
import serial


is_mock = True


def invert_bits(value):
    return value ^ 0b111111


def parse_measure_string(string: str):
    return [float(point) for point in string.split(',')]


class InstrumentController:

    params = {
        0: {
            'f1': 10_000_000,
            'f2': 8_000_000_000,
            'pow': -5,
            'points': 1601 if not is_mock else 51
        },
        1: {
            'f1': 10_000_000,
            'f2': 15_000_000_000,
            'pow': -5,
            'points': 1601 if not is_mock else 51
        },
    }

    codes = {
        0: {
            0.0:    0b000000,
            0.25:   0b000001,
            0.5:    0b000010,
            1.0:    0b000100,
            2.0:    0b001000,
            4.0:    0b010000,
            8.0:    0b100000,
            15.75:  0b111111
        },
        1: {
            0.0:  0b000000,
            0.5:  0b000001,
            1.0:  0b000010,
            2.0:  0b000100,
            4.0:  0b001000,
            8.0:  0b010000,
            16.0: 0b100000,
            31.5: 0b111111
        }
    }

    def __init__(self):
        self._analyzer_addr = 'GPIB0::1::INSTR'

        self._calib_file_name = 'D:\\Vysotka29_ATT\\1324MP.csa'

        self._programmer = None
        self._analyzer = None

        self._available_ports = list()

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
            s = serial.Serial(port=port, baudrate=9600, timeout=1)
            if s.is_open:
                s.write(b'#NAME')
                time.sleep(2)
                ans = s.read_all()
                s.close()
                if b'ARDUINO' in ans:
                    return port
        else:
            return ''

    def _find_programmer(self):
        if is_mock:
            from arduino.arduinoparallelmock import ArduinoParallelMock
            self._programmer = ArduinoParallelMock()
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
        if is_mock:
            from instr.agilente8362bmock import AgilentE8362BMock
            self._analyzer = AgilentE8362BMock(AgilentE8362BMock.idn)
            return

        from instr.agilente8362b import AgilentE8362B

        if self._analyzer_addr:
            print(f'trying {self.analyzer_addr}')
            try:
                self._analyzer = AgilentE8362B.from_address_string(self._analyzer_addr)
                return
            except Exception as ex:
                print('analyzer find error:', ex)

        self._analyzer, self._analyzer_addr = AgilentE8362B.try_find()
        if not self._analyzer:
            print('analyzer not found, giving up')

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

    def test_sample(self, points=51):
        chan = 1
        window = 1
        trace = 1
        port = 1
        range_ = 1

        self._programmer.set_lpf_code(invert_bits(0b100000))
        self._analyzer.reset()
        self._analyzer.calib_import_device_state(f'MMEMory:LOAD:CSARchive "{self._calib_file_name}"')
        _, meas_name = self._analyzer.calc_create_measurement(chan=chan, meas_name='check_s21', meas_type='S21')
        # self._analyzer.display_create_window(window=window)
        self._analyzer.display_delete_trace(window=window, trace=trace)
        self._analyzer.display_create_trace(window=window, trace=trace, meas_name=meas_name)
        self._analyzer.trigger_source('MANual')
        self._analyzer.wait()
        self._analyzer.trigger_point_mode(chan=chan, mode='OFF')
        self._analyzer.source_power(chan=chan, port=port, value=-5)
        self._analyzer.sense_fom_sweep_type(chan=chan, range=range_, type='linear')
        self._analyzer.sense_sweep_points(chan=chan, points=points)
        self._analyzer.sense_freq_start(chan=chan, value=10, unit='MHz')
        self._analyzer.sense_freq_stop(chan=chan, value=8, unit='GHz')
        self._analyzer.trigger_initiate()
        self._analyzer.wait()
        self._analyzer.calc_parameter_select(chan=chan, name=meas_name)
        self._analyzer.format('ASCII')

        return self._analyzer.calc_formatted_data(chan=chan)

    def _measure_point(self, chan, name):
        print('measure param', name)
        self._analyzer.calc_parameter_select(chan=chan, name=name)
        return self._analyzer.calc_formatted_data(chan=1)

    def measure(self, device_id):
        time.sleep(1)

        chan = 1
        port = 1
        window = 1
        trace_s21 = 1
        trace_s11 = 2
        trace_s22 = 3
        range_ = 1
        s21_name = 'meas_s21'
        s11_name = 'meas_s11'
        s22_name = 'meas_s22'

        meas_pow = self.params[device_id]['pow']
        meas_f1 = self.params[device_id]['f1']
        meas_f2 = self.params[device_id]['f2']
        points = self.params[device_id]['points']

        # self._analyzer.reset()
        self._analyzer.calc_create_measurement(chan=chan, meas_name=s21_name, meas_type='S21')
        self._analyzer.calc_create_measurement(chan=chan, meas_name=s11_name, meas_type='S11')
        self._analyzer.calc_create_measurement(chan=chan, meas_name=s22_name, meas_type='S22')

        self._analyzer.display_delete_trace(window=window, trace=trace_s21)

        self._analyzer.display_create_trace(window=window, trace=trace_s21, meas_name=s21_name)
        self._analyzer.display_create_trace(window=window, trace=trace_s11, meas_name=s11_name)
        self._analyzer.display_create_trace(window=window, trace=trace_s22, meas_name=s22_name)

        self._analyzer.trigger_source('MANual')
        self._analyzer.wait()

        self._analyzer.source_power(chan=chan, port=port, value=meas_pow)
        self._analyzer.sense_fom_sweep_type(chan=chan, range=range_, type='linear')
        self._analyzer.sense_sweep_points(chan=chan, points=points)
        self._analyzer.sense_freq_start(chan=chan, value=meas_f1, unit='Hz')
        self._analyzer.sense_freq_stop(chan=chan, value=meas_f2, unit='Hz')

        self._analyzer.trigger_scope('CURRENT')
        self._analyzer.format('ASCII')

        s21s = list()
        s11s = list()
        s22s = list()
        s21s_all = list()

        cds = list(self.codes[device_id].values())
        for code in range(64):
            self._programmer.set_lpf_code(invert_bits(code))

            s21s_tmp = parse_measure_string(self._measure_point(chan, s21_name))
            s21s_all.append(s21s_tmp)

            if code in cds:
                self._analyzer.trigger_initiate()
                self._analyzer.wait()
                s21s.append(s21s_tmp)

                self._analyzer.trigger_initiate()
                self._analyzer.wait()
                s11s.append(parse_measure_string(self._measure_point(chan, s11_name)))

                self._analyzer.trigger_initiate()
                self._analyzer.wait()
                s22s.append(parse_measure_string(self._measure_point(chan, s22_name)))

        return s21s, s11s, s22s, s21s_all

    @property
    def analyzer_addr(self):
        return self._analyzer_addr

    @analyzer_addr.setter
    def analyzer_addr(self, addr):
        self._analyzer_addr = addr

    @property
    def calibration_file(self):
        return self._calib_file_name

    @calibration_file.setter
    def calibration_file(self, name):
        self._calib_file_name = name

