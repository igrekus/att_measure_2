from PyQt5.QtCore import Qt, QAbstractTableModel, QModelIndex, QVariant, pyqtSlot


class ResultModel(QAbstractTableModel):
    _default_column_count = 1
    _default_headers = ['№'] * _default_column_count

    _labels = ['Att нач, дБ', 'Fнач, ГГц', 'Fкон, ГГц', 'Err амп, дБ', 'КСВ вх', 'КСВ вых']

    _standard = {
        0: [5, 0.01, 3, 1.0, 2.0, 2.0],
        1: [15, 0.01, 10, 1.5, 2.0, 2.0]
    }

    def __init__(self, parent=None, domain=None):
        super().__init__(parent)

        self._headers = self._default_headers
        self._columnCount = self._default_column_count

        self._domain = domain

        self._data = {
            0: list(self._labels),
            1: self.makeStandardColumn(self._standard[0]),
            2: [0] * len(self._standard[0])
        }

        self.initHeader()

    def makeStandardColumn(self, vals):
        return [f'{sym}{val}' for sym, val in zip(['< ', '< ', '> ', '< ±', '< ', '< '], vals)]

    def clear(self):
        self.beginRemoveRows(QModelIndex(), 0, len(self._data))
        self._data.clear()
        self.endRemoveRows()

    def init(self, chip: int):
        self.beginResetModel()
        self._data = {
            0: list(self._labels),
            1: self.makeStandardColumn(self._standard[chip]),
            2: [0] * len(self._standard[chip])
        }
        self.endResetModel()

    def initHeader(self, headers=('', 'по ТУ', 'Результат')):
        self._headers = list(headers)
        self._columnCount = len(headers)

    def headerData(self, section, orientation, role=None):
        if orientation == Qt.Horizontal:
            if role == Qt.DisplayRole:
                if section < len(self._headers):
                    return QVariant(self._headers[section])
        return QVariant()

    def rowCount(self, parent=None, *args, **kwargs):
        if parent.isValid():
            return 0
        return len(self._data[1])

    def columnCount(self, parent=None, *args, **kwargs):
        return self._columnCount

    def data(self, index, role=None):
        if not index.isValid():
            return QVariant()

        col = index.column()
        row = index.row()

        if role == Qt.DisplayRole:
            if not self._data:
                return QVariant()
            return QVariant(self._data[col][row])

        return QVariant()

    @pyqtSlot(int)
    def updateModel(self, chip):
        self.init(chip)
