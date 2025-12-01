import sys
from PyQt5.QtWidgets import QApplication

from main_window import MusicMainWindow
from util import dark_title_bar


def main():
    app = QApplication(sys.argv)
    win = MusicMainWindow()
    win.show()
    dark_title_bar(win)   # make Windows title bar dark
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
