from PyQt5 import uic
from PyQt5.QtWidgets import QMainWindow
from PyQt5.QtCore import Qt

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
        self._ui.btnContinue.setVisible(False)

    def refreshView(self):
        pass
        # self.resizeTable()

    def resizeTable(self):
        pass
        # self._ui.tableMeasure.resizeRowsToContents()
        # self._ui.tableMeasure.resizeColumnsToContents()

    def modeSearchInstruments(self):
        self._ui.btnMeasureStop.hide()
        self._ui.btnCheckSample.setEnabled(False)
        self._ui.comboChip.setEnabled(False)
        self._ui.btnMeasureStart.setEnabled(False)

    def modeCheckSample(self):
        self._ui.btnCheckSample.setEnabled(True)
        self._ui.comboChip.setEnabled(True)
        self._ui.btnMeasureStart.show()
        self._ui.btnMeasureStart.setEnabled(False)
        self._ui.btnMeasureStop.hide()
        analyzer, progr = self._instrumentManager.getInstrumentNames()
        self._ui.editAnalyzer.setText(analyzer)
        self._ui.editProg.setText(progr)

    def modeReadyToMeasure(self):
        self._ui.btnCheckSample.setEnabled(False)
        self._ui.comboChip.setEnabled(False)
        self._ui.btnMeasureStart.setEnabled(True)

    def modeMeasureInProgress(self):
        self._ui.btnCheckSample.setEnabled(False)
        self._ui.comboChip.setEnabled(False)
        self._ui.btnMeasureStart.setVisible(False)
        self._ui.btnMeasureStop.setVisible(True)

    def modeMeasureFinished(self):
        self._ui.btnCheckSample.setEnabled(False)
        self._ui.comboChip.setEnabled(False)
        self._ui.btnMeasureStart.setVisible(False)
        self._ui.btnMeasureStop.setVisible(True)

    # event handlers
    def resizeEvent(self, event):
        self.refreshView()
