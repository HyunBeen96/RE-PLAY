import requests
from PyQt5.QtGui import QPixmap
from PIL import Image, ImageFilter
from io import BytesIO
from PyQt5.QtWidgets import QWidget
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QGraphicsDropShadowEffect

def setup_background_and_album(self, song_info):
    """배경 이미지와 앨범 커버, 그림자 효과 설정"""
    video_id = song_info["video_id"]
    url = f"https://img.youtube.com/vi/{video_id}/maxresdefault.jpg"
    response = requests.get(url).content

    # --- 흐림 처리된 배경 ---
    img = Image.open(BytesIO(response)).convert("RGB")
    blurred = img.filter(ImageFilter.GaussianBlur(radius=60))
    buf = BytesIO()
    blurred.save(buf, format="PNG")
    pix = QPixmap()
    pix.loadFromData(buf.getvalue())
    self.lblBackground.setPixmap(pix)
    self.lblBackground.setScaledContents(True)

    # --- 오버레이 위젯 추가 ---
    overlay = QWidget(self.lblBackground)
    overlay.setStyleSheet("background-color: rgba(0, 0, 0, 130);")
    overlay.setGeometry(self.lblBackground.rect())
    overlay.lower()
    overlay.show()

    # --- 앨범 커버 ---
    album_pix = QPixmap()
    album_pix.loadFromData(response)
    self.albumCover.setPixmap(album_pix)
    self.albumCover.setScaledContents(True)

    # --- 그림자 효과 ---
    shadow = QGraphicsDropShadowEffect(self)
    shadow.setBlurRadius(35)
    shadow.setXOffset(0)
    shadow.setYOffset(20)
    shadow.setColor(Qt.black)
    self.albumCover.setGraphicsEffect(shadow)