import os
import requests

# API endpoint lấy danh sách trận đấu
API_URL = "https://fb-api.apiscoreflow.com/football/match/detail_live"

HEADERS = {
    "Accept": "application/json, text/javascript, */*; q=0.01",
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML,"
        " like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
    "Referer": "https://xoilacz.vip/",
}


def fetch_matches():
  try:
    print(f"Đang kết nối tới API: {API_URL}")
    response = requests.get(API_URL, headers=HEADERS, timeout=15)
    print(f"Mã phản hồi từ API: {response.status_code}")
    if response.status_code == 200:
      data = response.json()
      return data.get("results", [])
  except Exception as e:
    print(f"Lỗi ngoại lệ khi gọi API: {e}")
  return []


def generate_m3u():
  matches = fetch_matches()

  # Khởi tạo nội dung file M3U chuẩn
  m3u_content = '#EXTM3U x-tvg-url=""\n'

  if not matches:
    print("Cảnh báo: Không lấy được trận đấu nào, tạo file m3u trống an toàn.")
    with open("playlist.m3u", "w", encoding="utf-8") as f:
      f.write(m3u_content)
    return

  count = 0
  for match in matches:
    match_id = match.get("id")
    status_id = match.get("status_id", 0)

    if not match_id:
      continue

    # Phân loại trạng thái
    status_text = {
        2: "Đang diễn ra (Live)",
        3: "Nghỉ giữa trận (HT)",
        4: "Hiệp 2",
        8: "Đã kết thúc (FT)",
        13: "Sắp diễn ra",
    }.get(status_id, "Trực tiếp")

    title = f"Trận đấu [{match_id}] - {status_text}"
    stream_url = f"https://xoilacz.vip/live/{match_id}"

    # Ghi cấu trúc M3U
    m3u_content += f'#EXTINF:-1 tvg-id="{match_id}" '
    m3u_content += f'tvg-name="{title}" '
    m3u_content += 'group-title="Bóng Đá - Xôi Lạc", '
    m3u_content += f"{title}\n"
    m3u_content += f"{stream_url}\n"
    count += 1

  # Ghi ra file playlist.m3u
  with open("playlist.m3u", "w", encoding="utf-8") as f:
    f.write(m3u_content)

  print(f"Thành công! Đã ghi {count} trận vào file playlist.m3u.")


if __name__ == "__main__":
  generate_m3u()
    
