import sys
from PyQt5 import uic  # ← 이거 추가해야 함!
from PyQt5.QtWidgets import QApplication, QMainWindow
from ui_setup import setup_background_and_album
from data_mock import song_list
import ui.replay_rc

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setupUi()

    def setupUi(self):
        uic.loadUi("../ui/replay.ui", self)
        self.setWindowTitle("Replay UI")
        # 앞으로 uic.loadUi(), 버튼 연결, 스타일시트 등 이곳에 추가됨


        # 더미로 첫 번째 곡 세팅
        current_song = song_list[0]
        setup_background_and_album(self, current_song)
        self.songTitle.setText(current_song["title"])

if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = MainWindow()
    win.show()
    sys.exit(app.exec_())