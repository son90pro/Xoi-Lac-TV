from datetime import datetime, timedelta
import json
import os
import re
import requests

# Cấu hình User-Agent & Referrer chuẩn từ Xôi Lạc
DEFAULT_UA = "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Mobile Safari/537.36"
DEFAULT_REFERER = "https://xlz.domainkqt.cc/"

# Danh sách API các môn thể thao trích xuất từ Source Code Xôi Lạc
SPORTS_CONFIG = {
    "football": {
        "api": "https://fb-api.sportliveapiz.com/football",
        "emoji": "⚽",
        "name": "Bóng đá",
    },
    "basketball": {
        "api": "https://bkb.sportflowlivez.com/basketball",
        "emoji": "🏀",
        "name": "Bóng rổ",
    },
    "tennis": {
        "api": "https://tn.sportflowlivez.com/tennis",
        "emoji": "🥎",
        "name": "Tennis",
    },
    "badminton": {
        "api": "https://badminton.sportflowlivez.com/badminton",
        "emoji": "🏸",
        "name": "Cầu lông",
    },
    "volleyball": {
        "api": "https://volleyball.sportflowlivez.com/volleyball",
        "emoji": "🏐",
        "name": "Bóng chuyền",
    },
    "esports": {
        "api": "https://esports.sportflowlivez.com/esports",
        "emoji": "🎮",
        "name": "Esports",
    },
}

headers = {
    "User-Agent": DEFAULT_UA,
    "Referer": "https://xoilacxbs.tv/",
    "Origin": "https://xoilacxbs.tv",
}


def get_match_list(api_base, date_str):
  """Lấy danh sách trận đấu theo ngày"""
  url = f"{api_base}/match/list?date={date_str}"
  try:
    res = requests.get(url, headers=headers, timeout=10)
    if res.status_code == 200:
      data = res.json()
      return data.get("data", []) or data.get("list", [])
  except Exception as e:
    print(f"Lỗi kết nối API {url}: {e}")
  return []


def get_match_detail(api_base, match_id):
  """Lấy thông tin luồng phát chi tiết (link stream, BLV, chất lượng)"""
  url = f"{api_base}/match/detail?id={match_id}"
  try:
    res = requests.get(url, headers=headers, timeout=10)
    if res.status_code == 200:
      return res.json().get("data", {})
  except Exception as e:
    print(f"Lỗi lấy chi tiết trận {match_id}: {e}")
  return {}


def format_m3u():
  m3u_lines = ["#EXTM3U\n"]

  # Lấy ngày hôm nay và ngày mai (Định dạng YYYYMMDD và DD/MM)
  today = datetime.now()
  tomorrow = today + timedelta(days=1)
  dates_to_check = [
      (today.strftime("%Y%m%d"), today.strftime("%d/%m")),
      (tomorrow.strftime("%Y%m%d"), tomorrow.strftime("%d/%m")),
  ]

  for sport_key, sport_info in SPORTS_CONFIG.items():
    api_base = sport_info["api"]
    emoji = sport_info["emoji"]

    for date_code, date_formatted in dates_to_check:
      matches = get_match_list(api_base, date_code)

      for match in matches:
        match_id = match.get("id")
        home_team = (
            match.get("home_name")
            or match.get("home_team", {}).get("name")
            or "Home"
        )
        away_team = (
            match.get("away_name")
            or match.get("away_team", {}).get("name")
            or "Away"
        )
        logo = (
            match.get("home_logo")
            or match.get("home_team", {}).get("logo")
            or "https://xoilacxbs.tv/favicon-xoilac365-tv-192x192.png"
        )

        # Thời gian trận đấu (HH:MM)
        match_time_timestamp = match.get("match_time") or match.get(
            "start_time"
        )
        if match_time_timestamp:
          match_time = datetime.fromtimestamp(
              int(match_time_timestamp)
          ).strftime("%H:%M")
        else:
          match_time = "00:00"

        # Trạng thái (Đang diễn ra 🟢 / Sắp diễn ra ⚪)
        status = match.get("status", 1)
        status_icon = "🟢" if status in [2, 3, 4, 5, 6, 7, 51, 52] else "⚪"

        # Lấy chi tiết các link phát trực tiếp
        detail = get_match_detail(api_base, match_id)
        links = detail.get("links", []) or detail.get("play_urls", [])

        if not links and "stream_url" in match:
          links = [{
              "url": match["stream_url"],
              "name": match.get("blv_name", "HD"),
          }]

        for index, link_info in enumerate(links):
          stream_url = link_info.get("url") or link_info.get("play_url")
          if not stream_url:
            continue

          blv_name = (
              link_info.get("blv_name")
              or link_info.get("commentator")
              or link_info.get("name")
              or "HD"
          )
          quality_tag = link_info.get("quality", "").upper()

          # Đặt tên nhãn luồng phát (VD: HD KEN, FHD MARTY, SD1...)
          label_suffix = f"{quality_tag} {blv_name}".strip()

          # Cấu trúc tiêu đề đúng mẫu M3U yêu cầu
          # #EXTINF:-1 tvg-logo="..." group-title="Xôi Lạc Z TV" , 🟢 HH:MM DD/MM ⚽ Home vs Away (LABEL)
          title = f'{status_icon} {match_time} {date_formatted} {emoji} {home_team} vs {away_team} ({label_suffix})'

          m3u_lines.append(
              f'#EXTINF:-1 tvg-logo="{logo}" group-title="Xôi Lạc Z TV" ,'
              f" {title}"
          )
          m3u_lines.append(f"#EXTVLCOPT:http-user-agent={DEFAULT_UA}")
          m3u_lines.append(f"#EXTVLCOPT:http-referrer={DEFAULT_REFERER}")
          m3u_lines.append(f"{stream_url}\n")

  # Ghi file xoilac.m3u
  with open("xoilac.m3u", "w", encoding="utf-8") as f:
    f.writelines("\n".join(m3u_lines))

  print("Đã cập nhật xong file xoilac.m3u thành công!")


if __name__ == "__main__":
  format_m3u()
    
