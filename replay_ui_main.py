import sys
import requests
import ui.replay_rc
import pickle
import pandas as pd
import random
import vlc

from sklearn.metrics.pairwise import linear_kernel
from PyQt5 import uic
from PyQt5.QtWidgets import *
from PyQt5.QtGui import QPixmap,QFontMetrics
from PyQt5.QtCore import Qt, QStringListModel, QSortFilterProxyModel
from PyQt5.QtWidgets import QGraphicsDropShadowEffect, QCompleter
from PIL import Image, ImageFilter
from io import BytesIO
from scipy.io import mmread
from gensim.models import Word2Vec
from yt_dlp import YoutubeDL

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        uic.loadUi("ui/replay.ui", self)

        # ✅ 모델 및 데이터 로딩 (self.으로 저장해야 아래 메서드에서 접근 가능)
        self.tfidf_matrix = mmread('./data/tfidf_movie_review.mtx').tocsr()
        with open('./data/tfidf.pickle', 'rb') as f:
            self.tfidf_vectorizer = pickle.load(f)
        self.word2vec_model = Word2Vec.load('./data/word2vec_movie_review.model')
        self.df = pd.read_csv('./data/sample_preprocessed_data.csv')  # title, id 컬럼 필요

        # ✅VLC 초기화
        self.vlc_instance = vlc.Instance()
        self.vlc_player = self.vlc_instance.media_player_new()

        # ✅ 자동완성용 제목 리스트 준비
        # 기존 title_list 준비는 동일
        self.title_list = self.df["title"].tolist()
        # 문자열 모델 생성
        string_model = QStringListModel()
        string_model.setStringList(self.title_list)
        # proxy 모델 생성 (중간 문자열도 매칭되도록 설정)
        proxy_model = QSortFilterProxyModel(self)
        proxy_model.setSourceModel(string_model)
        proxy_model.setFilterCaseSensitivity(Qt.CaseInsensitive)
        proxy_model.setFilterFixedString("")  # 초기엔 필터 없음
        # completer 설정
        self.completer = QCompleter(proxy_model, self)
        self.completer.setCompletionMode(QCompleter.PopupCompletion)
        self.completer.setCaseSensitivity(Qt.CaseInsensitive)
        # searchLine에 자동완성 붙이기
        self.searchLine.setCompleter(self.completer)
        #  입력 내용이 바뀔 때마다 proxy에 필터링 적용
        self.searchLine.textChanged.connect(proxy_model.setFilterFixedString)
        self.completer.setFilterMode(Qt.MatchContains)

        # ✅ 검색창 엔터 연결
        self.searchLine.returnPressed.connect(self.on_search)

        # ✅ 검색 결과 클릭 연결
        self.searchResults.itemDoubleClicked.connect(self.on_result_clicked)

        # # ✅ 랜덤 초기값 선택
        # random_row = self.df.sample(1).iloc[0]
        # title_raw = random_row["title"]
        # video_id = random_row["id"]
        # self.set_song_info_and_cover(title_raw, video_id)

        # ✅리스트 위젯에서 수평 스크롤바 비활성화
        self.searchResults.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        # ✅ 오버레이는 한번만 만들고 유지
        self.overlay = QWidget(self.lblBackground)
        self.overlay.setStyleSheet("background-color: rgba(0, 0, 0, 130);")
        self.overlay.setGeometry(self.lblBackground.rect())
        self.overlay.lower()
        self.overlay.show()

    def set_background_and_cover(self, video_id):
        url = f"https://img.youtube.com/vi/{video_id}/maxresdefault.jpg"
        response = requests.get(url).content
        img = Image.open(BytesIO(response)).convert("RGB")
        blurred = img.filter(ImageFilter.GaussianBlur(radius=60))

        buf = BytesIO()
        blurred.save(buf, format="PNG")
        pix = QPixmap()
        pix.loadFromData(buf.getvalue())
        self.lblBackground.setPixmap(pix)
        self.lblBackground.setScaledContents(True)

        album_pix = QPixmap()
        album_pix.loadFromData(response)
        self.albumCover.setPixmap(album_pix)
        self.albumCover.setScaledContents(True)

        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(35)
        shadow.setXOffset(0)
        shadow.setYOffset(20)
        shadow.setColor(Qt.black)
        self.albumCover.setGraphicsEffect(shadow)

    def get_similar_titles_by_keyword(self, keyword: str, topn: int = 20) -> list:
        if keyword not in self.word2vec_model.wv:
            return []

        sim_words = self.word2vec_model.wv.most_similar(keyword, topn=10)
        words = [keyword] + [w for w, _ in sim_words]

        weighted_sentence = []
        for i, word in enumerate(words):
            weighted_sentence += [word] * (10 - i)
        sentence = ' '.join(weighted_sentence)

        sent_vec = self.tfidf_vectorizer.transform([sentence])
        cosine_sim = linear_kernel(sent_vec, self.tfidf_matrix)
        sim_scores = sorted(list(enumerate(cosine_sim[-1])), key=lambda x: x[1], reverse=True)[:topn]
        indices = [i[0] for i in sim_scores]

        return self.df.iloc[indices][["title", "id"]].to_dict(orient="records")

    def on_search(self):
        keyword = self.searchLine.text().strip()
        if not keyword:
            return

        self.searchResults.clear()

        # 🎯 제목 리스트에 완전 일치하면 제목 기반으로 검색
        if keyword in self.title_list:
            result = self.df[self.df["title"] == keyword].iloc[0]
            video_id = result["id"]
            full_title = result["title"]
            fm = QFontMetrics(self.searchResults.font())
            elided = fm.elidedText(full_title, Qt.ElideRight, self.searchResults.viewport().width() - 20)

            item = QListWidgetItem(elided)
            item.setToolTip(full_title)
            item.setData(Qt.UserRole, video_id)
            self.searchResults.addItem(item)
        else:
            # 🧠 단어 기반 추천
            results = self.get_similar_titles_by_keyword(keyword)
            for item_data in results:
                full_title = item_data["title"]
                fm = QFontMetrics(self.searchResults.font())
                elided = fm.elidedText(full_title, Qt.ElideRight, self.searchResults.viewport().width() - 20)

                item = QListWidgetItem(elided)
                item.setToolTip(full_title)
                item.setData(Qt.UserRole, item_data["id"])
                self.searchResults.addItem(item)

    def set_song_info_and_cover(self, title_raw, video_id):
        main_part = title_raw.split('|')[0].strip()
        if '-' in main_part:
            composer, title_clean = map(str.strip, main_part.split('-', 1))
        else:
            composer, title_clean = "", main_part

        self.songTitle.setText(title_clean)
        self.songTitle_2.setText(composer)
        self.set_background_and_cover(video_id)
        self.play_song_from_youtube(video_id)

    def on_result_clicked(self, item):
        title_raw = item.text()
        video_id = item.data(Qt.UserRole)
        self.set_song_info_and_cover(title_raw, video_id)

    def play_song_from_youtube(self, video_id):
        try:
            stream_url = get_audio_url(video_id)

            if self.vlc_player.is_playing():
                self.vlc_player.stop()

            media = self.vlc_instance.media_new(stream_url)
            self.vlc_player.set_media(media)
            self.vlc_player.play()

            print(f"🎵 Now Playing: {stream_url}")
        except Exception as e:
            print("❌ VLC 재생 실패:", e)


def get_audio_url(video_id):
    url = f"https://www.youtube.com/watch?v={video_id}"
    ydl_opts = {
        'format': 'bestaudio/best',
        'quiet': True,
        'noplaylist': True,
    }

    with YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        return info['url']  # VLC에서 재생 가능한 직접 URL

if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = MainWindow()
    w.show()
    sys.exit(app.exec_())