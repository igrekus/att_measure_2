import errno
import os

from PyQt5.QtWidgets import QGridLayout, QWidget
from mytools.plotwidget import PlotWidget


class PrimaryPlotWidget(QWidget):

    def __init__(self, parent=None, domain=None):
        super().__init__(parent)

        self._domain = domain

        self._grid = QGridLayout()

        self._plot11 = PlotWidget(parent=None, toolbar=True)
        self._plot12 = PlotWidget(parent=None, toolbar=True)
        self._plot21 = PlotWidget(parent=None, toolbar=True)
        self._plot22 = PlotWidget(parent=None, toolbar=True)

        self._grid.addWidget(self._plot11, 0, 0)
        self._grid.addWidget(self._plot12, 0, 1)
        self._grid.addWidget(self._plot21, 1, 0)
        self._grid.addWidget(self._plot22, 1, 1)

        self.setLayout(self._grid)

        self._init()

    def _init(self):
        # self._plot11.set_tight_layout(True)
        self._plot11.subplots_adjust(bottom=0.150)
        self._plot11.set_title('Вносимые потери')
        self._plot11.set_xlabel('F, ГГц', labelpad=-2)
        self._plot11.set_ylabel('Loss, дБ', labelpad=-2)
        self._plot11.grid(b=True, which='major', color='0.5', linestyle='-')

        # self._plot22.set_tight_layout(True)
        self._plot12.subplots_adjust(bottom=0.150)
        self._plot12.set_title('Ошибка для состояния')
        self._plot12.set_xlabel('F, ГГц', labelpad=-2)
        self._plot12.set_ylabel('Bit error', labelpad=-2)
        self._plot12.grid(b=True, which='major', color='0.5', linestyle='-')

        # self._plot21.set_tight_layout(True)
        self._plot21.subplots_adjust(bottom=0.150)
        self._plot21.set_title(f'Входные обратные потери')
        self._plot21.set_xlabel('F, ГГц', labelpad=-2)
        self._plot21.set_ylabel('S11, дБ', labelpad=-2)
        self._plot21.grid(b=True, which='major', color='0.5', linestyle='-')

        # self._plot22.set_tight_layout(True)
        self._plot22.subplots_adjust(bottom=0.150)
        self._plot22.set_title('Выходные обратные потери')
        self._plot22.set_xlabel('F, ГГц', labelpad=-2)
        self._plot22.set_ylabel('S22, дБ', labelpad=-2)
        self._plot22.grid(b=True, which='major', color='0.5', linestyle='-')

    def clear(self):
        self._plot11.clear()
        self._plot12.clear()
        self._plot21.clear()
        self._plot22.clear()
        self._init()

    def plotCode(self):
        print('plotting code')
        self._plot11.plot(self._domain.lastXs, self._domain.lastYs, color='0.4')

    def plotStats(self):
        print('plotting stats')
        self._plot12.plot(self._domain.cutoffXs, self._domain.cutoffYs, color='0.4')
        self._plot21.plot(self._domain.deltaXs, self._domain.deltaYs, color='0.4')
        self._plot22.plot(self._domain.lossDoubleXs, self._domain.lossDoubleYs, color='0.4')
        self._plot22.plot(self._domain.lossTripleXs, self._domain.lossTripleYs, color='0.4')

        self._plot11.axhline(self._domain.cutoffAmp, 0, 1, linewidth=0.8, color='0.3', linestyle='--')
        self._plot11.set_yticks(sorted(set(list(self._plot11.get_yticks()[0]) + [self._domain.cutoffMag])))

    def save(self, img_path='./image'):
        try:
            os.makedirs(img_path)
        except OSError as ex:
            if ex.errno != errno.EEXIST:
                raise IOError('Error creating image dir.')

        for plot, name in zip([self._plot11, self._plot12, self._plot21, self._plot22], ['stats.png', 'cutoff.png', 'delta.png', 'double-triple.png']):
            plot.savefig(img_path + name, dpi=400)


