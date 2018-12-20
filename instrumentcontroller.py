import serial


is_mock = True


class InstrumentController:

    def __init__(self):
        self._analyzer_addr = 'GPIB0::1::INSTR'

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
        if is_mock:
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
                print(ex)

        self._analyzer = AgilentE8362B.try_find()
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

    def measure(self, code):
        if not self._programmer.set_lpf_code(code):
            print(f'error setting code: {code}')
            return [], []
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
