import sys
import requests
import ui.replay_rc

from PyQt5 import uic
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget
from PyQt5.QtGui import QPixmap
from PIL import Image, ImageFilter
from io import BytesIO
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QGraphicsDropShadowEffect

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi("ui/replay.ui", self)

        # 1) 유튜브 썸네일 → 블러 처리 → 배경 라벨에 세팅
        video_id = "iw0sC4Cj3HE"
        url = f"https://img.youtube.com/vi/{video_id}/maxresdefault.jpg"
        response = requests.get(url).content
        img = Image.open(BytesIO(response)).convert("RGB")
        blurred = img.filter(ImageFilter.GaussianBlur(radius=60)) # radius= 값이 커질수록 흐릿해짐
        buf = BytesIO()
        blurred.save(buf, format="PNG")
        pix = QPixmap()
        pix.loadFromData(buf.getvalue())
        self.lblBackground.setPixmap(pix)
        self.lblBackground.setScaledContents(True)

        # 2) 오버레이 위젯추가 (코드상으로 추가한 것, 부모가 lblBackground)
        overlay = QWidget(self.lblBackground)
        overlay.setStyleSheet("background-color: rgba(0, 0, 0, 130);") #rgba(0, 0, 0, 여기 수치 올릴 수록 어두워짐)
        overlay.setGeometry(self.lblBackground.rect())
        overlay.lower()
        overlay.show()

        # 3) albumCover 라벨에 유튜브 썸네일 원본 이미지 표시
        album_pix = QPixmap()
        album_pix.loadFromData(response)  # 이미 위에서 response에 원본 이미지 bytes가 저장되어 있음!
        self.albumCover.setPixmap(album_pix)
        self.albumCover.setScaledContents(True)  # 필요시, 라벨 크기에 맞게 자동 맞춤
        # --- 그림자 효과 추가 ---
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(35)  # 퍼짐 정도 (크게!)
        shadow.setXOffset(0)  # X축 오프셋 0
        shadow.setYOffset(20)  # Y축 오프셋을 크게 주면 '아래에만' 그림자 느낌
        shadow.setColor(Qt.black)
        self.albumCover.setGraphicsEffect(shadow)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = MainWindow()
    w.show()
    sys.exit(app.exec_())