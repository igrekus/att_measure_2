import errno
import os

from PyQt5.QtWidgets import QGridLayout, QWidget
from mytools.plotwidget import PlotWidget


class SecondaryPlotWidget(QWidget):

    params = {
        0: {
            'xlim': [0.01, 6]
        },
        1: {
            'xlim': [0.01, 12]
        },
        2: {
            'xlim': [0.01, 12]
        }
    }

    def __init__(self, parent=None, domain=None):
        super().__init__(parent)

        self._domain = domain

        self._grid = QGridLayout()

        self._plot11 = PlotWidget(parent=None, toolbar=True)
        self._plot12 = PlotWidget(parent=None, toolbar=True)

        self._grid.addWidget(self._plot11, 0, 0)
        self._grid.addWidget(self._plot12, 0, 1)

        self.setLayout(self._grid)

        self._init()

    def _init(self, dev_id=1):
        # self._plot11.set_tight_layout(True)
        self._plot11.subplots_adjust(bottom=0.150)
        self._plot11.set_title('Нормализованный коэффициент ослабления')
        self._plot11.set_xlabel('Частота, ГГц', labelpad=-2)
        self._plot11.set_ylabel('αпот.н, дБ', labelpad=-2)
        self._plot11.set_xlim(self.params[dev_id]['xlim'][0], self.params[dev_id]['xlim'][1])
        self._plot11.grid(b=True, which='major', color='0.5', linestyle='-')

        # self._plot12.set_tight_layout(True)
        self._plot12.subplots_adjust(bottom=0.150)
        self._plot12.set_title(f'Коэффициент ослабления для всех стостояний')
        self._plot12.set_xlabel('Частота, ГГц', labelpad=-2)
        self._plot12.set_ylabel('αпот, дБ', labelpad=-2)
        self._plot12.set_xlim(self.params[dev_id]['xlim'][0], self.params[dev_id]['xlim'][1])
        self._plot12.grid(b=True, which='major', color='0.5', linestyle='-')

    def clear(self):
        self._plot11.clear()
        self._plot12.clear()

    def plot(self, dev_id):
        self.clear()
        self._init(dev_id)
        print('plotting secondary stats')

        for xs, ys in zip(self._domain.normalizedAttXs, self._domain.normalizedAttYs):
            self._plot11.plot(xs, ys)

        for xs, ys in zip(self._domain.attenuationXs, self._domain.attenuationYs):
            self._plot12.plot(xs, ys)

    def save(self, img_path='./image'):
        try:
            os.makedirs(img_path)
        except OSError as ex:
            if ex.errno != errno.EEXIST:
                raise IOError('Error creating image dir.')

        for plot, name in zip([self._plot11, self._plot12, self._plot21, self._plot22], ['stats.png', 'cutoff.png', 'delta.png', 'double-triple.png']):
            plot.savefig(img_path + name, dpi=400)


