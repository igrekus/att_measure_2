import time

from PyQt5 import uic
from PyQt5.QtWidgets import QMainWindow, QMessageBox, QButtonGroup
from PyQt5.QtCore import Qt, pyqtSlot

from domain import Domain
from mytools.mapmodel import MapModel
from primaryplotwidget import PrimaryPlotWidget
from resultmodel import ResultModel
from secondaryplotwidget import SecondaryPlotWidget


class MainWindow(QMainWindow):

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setAttribute(Qt.WA_QuitOnClose)
        self.setAttribute(Qt.WA_DeleteOnClose)

        # create instance variables
        self._domain = Domain(parent=self)

        self._ui = uic.loadUi('mainwindow.ui', self)
        self._ui.primaryPlots = PrimaryPlotWidget(parent=self, domain=self._domain)
        self._ui.secondaryPlots = SecondaryPlotWidget(parent=self, domain=self._domain)

        self._ui.tabWidget.addTab(self._ui.primaryPlots, 'Параметры 1')
        self._ui.tabWidget.addTab(self._ui.secondaryPlots, 'Параметры 2')

        self._ui.bgrpDevice = QButtonGroup(parent=self)
        self._ui.bgrpDevice.addButton(self._ui.radioPm1u, id=0)
        self._ui.bgrpDevice.addButton(self._ui.radioPm2u, id=1)
        self._ui.bgrpDevice.addButton(self._ui.radioAmp, id=2)   # TODO change to the device name

        self._init()

    def _init(self):
        self._setupSignals()
        self._setupUi()

        self._refreshView()

    def _setupSignals(self):
        self._domain.measureFinished.connect(self.on_measurementFinished)
        self._ui.bgrpDevice.buttonToggled[int, bool].connect(self.on_bgrpDevice_buttonToggled)

    def _setupUi(self):
        # self._ui.comboDevice.setModel(MapModel(parent=self, data={0: '1324ПМ1У (0,25 дБ)', 1: '1324ПМ2У (0,5 дБ)'}))
        self._ui.tableResult.setModel(ResultModel(parent=self, domain=self._domain))

        self._modeBeforeConnect()
        self._refreshView()

    def _refreshView(self):
        self._resizeTable()

    def _resizeTable(self):
        self._ui.tableResult.resizeRowsToContents()
        self._ui.tableResult.resizeColumnsToContents()

    def _setBgrpDeviceEnabled(self, state: bool):
        self._ui.radioPm1u.setEnabled(state)
        self._ui.radioPm2u.setEnabled(state)
        self._ui.radioAmp.setEnabled(state)

    def _modeBeforeConnect(self):
        self._ui.btnContinue.setVisible(False)
        self._ui.btnCheck.setEnabled(False)
        self._ui.btnMeasure.setEnabled(False)
        self._ui.btnReport.setEnabled(False)
        self._setBgrpDeviceEnabled(False)

    def _modeBeforeSamplePresent(self):
        self._ui.btnCheck.setEnabled(True)
        self._ui.btnMeasure.setEnabled(False)
        self._ui.btnMeasure.setVisible(True)
        self._ui.btnContinue.setVisible(False)
        self._ui.btnReport.setEnabled(False)
        self._setBgrpDeviceEnabled(True)

        self._ui.editAnalyzer.setText(f'{self._domain.analyzerName} at {self._domain.analyzerAddress}')
        self._ui.editProgr.setText(self._domain.programmerName)

    def _modeBeforeMeasure(self):
        self._ui.btnCheck.setEnabled(False)
        self._ui.btnMeasure.setEnabled(True)
        self._ui.btnContinue.setVisible(False)
        self._ui.btnReport.setEnabled(False)
        self._setBgrpDeviceEnabled(False)

    def _modeMeasureInProgress(self):
        self._ui.btnCheck.setEnabled(False)
        self._ui.btnMeasure.setEnabled(False)
        self._ui.btnContinue.setVisible(False)
        self._ui.btnReport.setEnabled(False)
        self._setBgrpDeviceEnabled(False)

    def _modeAfterMeasure(self):
        self._ui.btnCheck.setEnabled(False)
        self._ui.btnMeasure.setEnabled(False)
        self._ui.btnMeasure.setVisible(False)
        self._ui.btnContinue.setVisible(True)
        self._ui.btnReport.setEnabled(True)
        self._setBgrpDeviceEnabled(True)

    # event handlers
    # GUI
    def resizeEvent(self, event):
        self._refreshView()

    @pyqtSlot(int, bool)
    def on_bgrpDevice_buttonToggled(self, index, state):
        if state:
            model = self._ui.tableResult.model()
            if model:
                self._ui.tableResult.model().init(index)

    @pyqtSlot()
    def on_btnConnect_clicked(self):
        if not self._domain.connect():
            QMessageBox.information(self, 'Ошибка',
                                    'Не удалось найти инструменты, проверьте подключение.\nПодробности в логах.')
        self._modeBeforeSamplePresent()

    @pyqtSlot()
    def on_btnCheck_clicked(self):
        if not self._domain.check():
            QMessageBox.information(self, 'Ошибка',
                                    'Образец не найден, проверьте стенд.')
            return False
        self._modeBeforeMeasure()

    @pyqtSlot()
    def on_btnMeasure_clicked(self):
        self._modeMeasureInProgress()
        self._domain.measure(self._ui.bgrpDevice.checkedId())

    @pyqtSlot()
    def on_btnContinue_clicked(self):
        print('continue')
        self._modeBeforeSamplePresent()

    @pyqtSlot()
    def on_btnReport_clicked(self):
        print('report')

    @pyqtSlot(str)
    def on_editAnalyzerAddr_textChanged(self, text):
        self._domain.analyzerAddress = text

    @pyqtSlot(str)
    def on_editCalibFile_textChanged(self, text):
        self._domain.calibrationFile = text

    # measurement events
    @pyqtSlot()
    def on_measurementFinished(self):
        print('plotting stats')
        try:
            self._ui.primaryPlots.plot(self._ui.bgrpDevice.checkedId())   # TODO 11,12 -- 12GHz limit
            self._ui.secondaryPlots.plot(self._ui.bgrpDevice.checkedId())   # TODO 11, 12 -- 12GHZ limit
        except Exception as ex:
            print(ex)
        self._modeAfterMeasure()
