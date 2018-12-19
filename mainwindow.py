import time

from PyQt5 import uic
from PyQt5.QtWidgets import QMainWindow
from PyQt5.QtCore import Qt, pyqtSlot

from domain import Domain
from primaryplotwidget import PrimaryPlotWidget
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

        self._ui.tabWidget.addTab(self._ui.primaryPlots, 'Основные параметры')
        self._ui.tabWidget.addTab(self._ui.secondaryPlots, 'Второстепенные параметры')

        self.initDialog()

    def initDialog(self):
        self._setupSignals()
        self._setupUi()

        self.refreshView()

    def _setupSignals(self):
        pass

    def _setupUi(self):
        self._modeBeforeConnect()

    def refreshView(self):
        pass
        # self.resizeTable()

    def resizeTable(self):
        pass
        # self._ui.tableMeasure.resizeRowsToContents()
        # self._ui.tableMeasure.resizeColumnsToContents()

    def _modeBeforeConnect(self):
        self._ui.btnContinue.setVisible(False)
        self._ui.btnCheck.setEnabled(False)
        self._ui.comboDevice.setEnabled(False)
        self._ui.btnMeasure.setEnabled(False)
        self._ui.btnReport.setEnabled(False)

    def _modeBeforeSamplePresent(self):
        self._ui.btnCheck.setEnabled(True)
        self._ui.comboDevice.setEnabled(True)
        self._ui.btnMeasure.setEnabled(False)
        self._ui.btnMeasure.setVisible(True)
        self._ui.btnContinue.setVisible(False)
        self._ui.btnReport.setEnabled(False)

        self._ui.editAnalyzer.setText(self._domain.analyzerName)
        self._ui.editProgr.setText(self._domain.programmerName)

    def _modeBeforeMeasure(self):
        self._ui.btnCheck.setEnabled(False)
        self._ui.comboDevice.setEnabled(False)
        self._ui.btnMeasure.setEnabled(True)
        self._ui.btnContinue.setVisible(False)
        self._ui.btnReport.setEnabled(False)

    def _modeMeasureInProgress(self):
        self._ui.btnCheck.setEnabled(False)
        self._ui.comboDevice.setEnabled(False)
        self._ui.btnMeasure.setEnabled(False)
        self._ui.btnContinue.setVisible(False)
        self._ui.btnReport.setEnabled(False)

    def _modeAfterMeasure(self):
        self._ui.btnCheck.setEnabled(False)
        self._ui.comboDevice.setEnabled(True)
        self._ui.btnMeasure.setEnabled(False)
        self._ui.btnMeasure.setVisible(False)
        self._ui.btnContinue.setVisible(True)
        self._ui.btnReport.setEnabled(True)

    # event handlers
    def resizeEvent(self, event):
        self.refreshView()

    @pyqtSlot()
    def on_btnConnect_clicked(self):
        print('connect')
        time.sleep(1)
        self._modeBeforeSamplePresent()

    @pyqtSlot()
    def on_btnCheck_clicked(self):
        print('check')
        time.sleep(1)
        self._modeBeforeMeasure()

    @pyqtSlot()
    def on_btnMeasure_clicked(self):
        print('measure')
        time.sleep(1)
        self._modeMeasureInProgress()
        time.sleep(1)
        self._modeAfterMeasure()

    def on_btnContinue_clicked(self):
        print('continue')
        self._modeBeforeSamplePresent()
