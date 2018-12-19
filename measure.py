import sys

from PyQt5.QtWidgets import QApplication
from mainwindow import MainWindow


def main(_):
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main(sys.argv)
