import errno
import os

from PyQt5.QtWidgets import QGridLayout, QWidget
from mytools.plotwidget import PlotWidget


class SecondaryPlotWidget(QWidget):

    params = {
        0: {
            '11': {
                'title': 'Нормализованный коэффициент ослабления',
                'xlabel': 'Частота, ГГц',
                'xlim': [0.01, 6],
                'ylabel': 'αпот.н, дБ',
                'ylim': []
            },
            '12': {
                'title': 'Ошибка для состояния',
                'xlabel': 'Частота, ГГц',
                'xlim': [0.01, 6],
                'ylabel': 'αпот, дБ',
                'ylim': []
            }
        },
        1: {
            '11': {
                'title': 'Нормализованный коэффициент ослабления',
                'xlabel': 'Частота, ГГц',
                'xlim': [0.01, 12],
                'ylabel': 'αпот.н, дБ',
                'ylim': []
            },
            '12': {
                'title': 'Ошибка для состояния',
                'xlabel': 'Частота, ГГц',
                'xlim': [0.01, 12],
                'ylabel': 'αпот, дБ',
                'ylim': []
            }
        },
        # TODO adjust params for new device
        2: {
            '11': {
                'title': 'Нормализованный коэффициент усиления',
                'xlabel': 'Частота, ГГц',
                'xlim': [0.01, 12],
                'ylabel': 'Kур.н., дБ',
                'ylim': []
            },
            '12': {
                'title': 'Амплитудная ошибка',
                'xlabel': 'Частота, ГГц',
                'xlim': [0.01, 12],
                'ylabel': 'Аош., дБ',
                'ylim': []
            }
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

        def setup_plot(plot, pars: dict):
            # plot.set_tight_layout(True)
            plot.subplots_adjust(bottom=0.150)
            plot.set_title(pars['title'])
            plot.set_xlabel(pars['xlabel'], labelpad=-2)
            plot.set_ylabel(pars['ylabel'], labelpad=-2)
            plot.set_xlim(pars['xlim'][0], pars['xlim'][1])
            # plot.set_ylim(pars['ylim'][0], pars['ylim'][1])
            plot.grid(b=True, which='major', color='0.5', linestyle='-')

        setup_plot(self._plot11, self.params[dev_id]['11'])
        setup_plot(self._plot12, self.params[dev_id]['12'])

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


