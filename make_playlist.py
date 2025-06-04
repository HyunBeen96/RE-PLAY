import pickle
import subprocess
import json

# 유튜브 플레이리스트 주소
playlist_url = "https://www.youtube.com/playlist?list=PLteBrxdKu3I-mPYty6ZSWxrKTCcOGqIkv"

# yt-dlp로 JSON 데이터 추출
cmd = [
    "yt-dlp",
    "--flat-playlist",
    "-J",
    playlist_url
]
result = subprocess.run(cmd, stdout=subprocess.PIPE, text=True, encoding="utf-8")
data = json.loads(result.stdout)

songs = []
for entry in data.get("entries", []):
    title = entry.get("title")
    video_id = entry.get("id")
    if title and video_id:
        songs.append({"title": title, "id": video_id})

# 저장
with open("data/playlist.pkl", "wb") as f:
    pickle.dump(songs, f)

print("✅ 저장 완료! 총 곡 수:", len(songs))