import errno
import os

from PyQt5.QtWidgets import QGridLayout, QWidget
from mytools.plotwidget import PlotWidget


class PrimaryPlotWidget(QWidget):

    params = {
        0: {
            '11': {
                'title': 'Вносимые потери',
                'xlabel': 'Частота, ГГц',
                'xlim': [0.01, 6],
                'ylabel': 'αпот., дБ',
                'ylim': []
            },
            '12': {
                'title': 'Ошибка для состояния',
                'xlabel': 'Частота, ГГц',
                'xlim': [0.01, 6],
                'ylabel': 'Аош',
                'ylim': []
            },
            '21': {
                'title': f'Входные обратные потери',
                'xlabel': 'Частота, ГГц',
                'xlim': [0.01, 6],
                'ylabel': 'S11, дБ',
                'ylim': []
            },
            '22': {
                'title': 'Выходные обратные потери',
                'xlabel': 'Частота, ГГц',
                'xlim': [0.01, 6],
                'ylabel': 'S22, дБ',
                'ylim': []
            }
        },
        1: {
            '11': {
                'title': 'Вносимые потери',
                'xlabel': 'Частота, ГГц',
                'xlim': [0.01, 12],
                'ylabel': 'αпот., дБ',
                'ylim': []
            },
            '12': {
                'title': 'Ошибка для состояния',
                'xlabel': 'Частота, ГГц',
                'xlim': [0.01, 12],
                'ylabel': 'Аош',
                'ylim': []
            },
            '21': {
                'title': f'Входные обратные потери',
                'xlabel': 'Частота, ГГц',
                'xlim': [0.01, 12],
                'ylabel': 'S11, дБ',
                'ylim': []
            },
            '22': {
                'title': 'Выходные обратные потери',
                'xlabel': 'Частота, ГГц',
                'xlim': [0.01, 12],
                'ylabel': 'S22, дБ',
                'ylim': []
            }
        },
        # TODO adjust params for new device
        2: {
            '11': {
                'title': 'К-т усиления',
                'xlabel': 'Частота, ГГц',
                'xlim': [0.01, 12],
                'ylabel': 'Kур., дБ',
                'ylim': []
            },
            '12': {
                'title': 'Амплитудная ошибка',
                'xlabel': 'Частота, ГГц',
                'xlim': [0.01, 12],
                'ylabel': 'Аош',
                'ylim': []
            },
            '21': {
                'title': 'Входные обратные потери',
                'xlabel': 'Частота, ГГц',
                'xlim': [0.01, 12],
                'ylabel': 'S11, дБ',
                'ylim': []
            },
            '22': {
                'title': 'Выходные обратные потери',
                'xlabel': 'Частота, ГГц',
                'xlim': [0.01, 12],
                'ylabel': 'S22, дБ',
                'ylim': []
            }
        },
    }

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

    def _init(self, dev_id=0):

        def setup_plot(plot, pars: dict):
            # plot.set_tight_layout(True)
            plot.subplots_adjust(bottom=0.150)
            plot.set_title(pars['title'])
            plot.set_xlabel(pars['xlabel'], labelpad=-2)
            plot.set_ylabel(pars['ylabel'], labelpad=-2)
            plot.set_xlim(pars['xlim'][0], pars['xlim'][1])
            # plot.set_ylim(pars['ylim'][0], pars['ylim'][1])
            plot.grid(b=True, which='major', color='0.5', linestyle='-')
            plot.tight_layout()

        setup_plot(self._plot11, self.params[dev_id]['11'])
        setup_plot(self._plot12, self.params[dev_id]['12'])
        setup_plot(self._plot21, self.params[dev_id]['21'])
        setup_plot(self._plot22, self.params[dev_id]['22'])

    def clear(self):
        self._plot11.clear()
        self._plot12.clear()
        self._plot21.clear()
        self._plot22.clear()

    def plot(self, dev_id=1):
        self.clear()
        self._init(dev_id)
        print('plotting primary stats')
        self._plot11.plot(self._domain.insLossXs, self._domain.insLossYs)

        for xs, ys in zip(self._domain.errorPerCodeXs, self._domain.errorPerCodeYs):
            self._plot12.plot(xs, ys)

        for xs, ys in zip(self._domain.inputInverseLossXs, self._domain.inputInverseLossYs):
            self._plot21.plot(xs, ys)

        for xs, ys in zip(self._domain.outputInverseLossXs, self._domain.outputInverseLossYs):
            self._plot22.plot(xs, ys)

    def save(self, img_path='./image'):
        try:
            os.makedirs(img_path)
        except OSError as ex:
            if ex.errno != errno.EEXIST:
                raise IOError('Error creating image dir.')

        for plot, name in zip([self._plot11, self._plot12, self._plot21, self._plot22], ['stats.png', 'cutoff.png', 'delta.png', 'double-triple.png']):
            plot.savefig(img_path + name, dpi=400)


