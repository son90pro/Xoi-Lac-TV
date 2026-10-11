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
    response = requests.get(API_URL, headers=HEADERS, timeout=10)
    if response.status_code == 200:
      data = response.json()
      # Đảm bảo lấy đúng mảng results từ cấu trúc API
      return data.get("results", [])
  except Exception as e:
    print(f"Lỗi kết nối API: {e}")
  return []


def generate_m3u():
  matches = fetch_matches()

  # Khởi tạo nội dung file M3U chuẩn cho IPTV Player
  m3u_content = '#EXTM3U x-tvg-url=""\n'

  if not matches:
    print("Cảnh báo: Không có trận đấu nào được trả về từ API.")
    # Vẫn tạo file m3u rỗng để Git không bị lỗi thiếu file
    with open("playlist.m3u", "w", encoding="utf-8") as f:
      f.write(m3u_content)
    return

  for match in matches:
    match_id = match.get("id")
    status_id = match.get("status_id", 0)

    # Phân loại trạng thái trận đấu
    status_text = {
        2: "Đang diễn ra (Live)",
        3: "Nghỉ giữa trận (HT)",
        4: "Hiệp 2",
        8: "Đã kết thúc (FT)",
        13: "Sắp diễn ra",
    }.get(status_id, "Trực tiếp")

    title = f"Trận đấu [{match_id}] - {status_text}"
    stream_url = f"https://xoilacz.vip/live/{match_id}"

    # Ghi thông tin từng kênh/trận đấu theo chuẩn M3U
    m3u_content += f'#EXTINF:-1 tvg-id="{match_id}" '
    m3u_content += f'tvg-name="{title}" '
    m3u_content += 'group-title="Bóng Đá - Xôi Lạc", '
    m3u_content += f"{title}\n"
    m3u_content += f"{stream_url}\n"

  # Ghi đè file playlist.m3u
  with open("playlist.m3u", "w", encoding="utf-8") as f:
    f.write(m3u_content)

  print(f"Đã tạo thành công playlist với {len(matches)} trận đấu!")


if __name__ == "__main__":
  generate_m3u()
    
