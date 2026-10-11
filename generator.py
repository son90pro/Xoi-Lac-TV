import os
import requests

# API endpoint cung cấp danh sách trận đấu trực tiếp
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
      return response.json().get("results", [])
  except Exception as e:
    print(f"Lỗi khi gọi API: {e}")
  return []


def generate_m3u():
  matches = fetch_matches()

  # Khởi tạo nội dung file M3U chuẩn
  m3u_content = "#EXTM3U x-tvg-url=\"\"\n"

  if not matches:
    print("Không lấy được dữ liệu trận đấu.")
    return

  for match in matches:
    match_id = match.get("id")
    status_id = match.get("status_id", 0)
    updated_at = match.get("updated_at", 0)

    # Phân loại trạng thái trận đấu (có thể tùy biến tên hiển thị)
    status_text = {
        2: "Đang diễn ra (Live)",
        3: Nghỉ giữa trận (HT)",
        4: "Hiệp 2",
        8: "Đã kết thúc (FT)",
        13: "Sắp diễn ra",
    }.get(status_id, "Trực tiếp")

    # Xây dựng tên hiển thị trên IPTV Player
    title = f"Trận đấu [{match_id}] - {status_text}"

    # Link phát sóng tương thích với Xôi Lạc / Quintiai (hoặc luồng stream nhúng)
    # Anh có thể thay đổi cấu trúc URL stream tùy theo player thực tế hỗ trợ
    stream_url = f"https://xoilacz.vip/live/{match_id}"

    # Định dạng dòng EXTINF chuẩn M3U
    m3u_content += f'#EXTINF:-1 tvg-id="{match_id}" '
    m3u_content += f'tvg-name="{title}" '
    m3u_content += f'tvg-chno="" '
    m3u_content += 'group-title="Bóng Đá Trực Tuyến - Xôi Lạc", '
    m3u_content += f"{title}\n"
    m3u_content += f"{stream_url}\n"

  # Ghi ra file playlist.m3u
  with open("playlist.m3u", "w", encoding="utf-8") as f:
    f.write(m3u_content)

  print(
      f"Đã cập nhật thành công {len(matches)} trận đấu vào file playlist.m3u!"
  )


if __name__ == "__main__":
  generate_m3u()

