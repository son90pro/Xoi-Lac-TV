from datetime import datetime, timedelta
import json
import os
import requests

DEFAULT_UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"

# Danh sách các Domain API dự phòng của Xôi Lạc (sẽ thử lần lượt nếu bị chặn)
API_DOMAINS = [
    "https://fb-api.sportliveapiz.com",
    "https://api.sportflowlivez.com",
    "https://api.xoilac.tv",
    "https://sportliveapiz.com",
]

SPORTS_CONFIG = {
    "football": {"path": "/football", "emoji": "⚽", "name": "Bóng đá"},
    "basketball": {"path": "/basketball", "emoji": "🏀", "name": "Bóng rổ"},
    "tennis": {"path": "/tennis", "emoji": "🥎", "name": "Tennis"},
    "badminton": {"path": "/badminton", "emoji": "🏸", "name": "Cầu lông"},
    "volleyball": {"path": "/volleyball", "emoji": "🏐", "name": "Bóng chuyền"},
    "esports": {"path": "/esports", "emoji": "🎮", "name": "Esports"},
}

headers = {
    "User-Agent": DEFAULT_UA,
    "Referer": "https://xoilac.tv/",
    "Origin": "https://xoilac.tv",
    "Accept": "application/json, text/plain, */*",
}


def get_data_from_api(domain, path, date_str):
  url = f"{domain}{path}/match/list?date={date_str}"
  try:
    res = requests.get(url, headers=headers, timeout=8)
    print(f" -> Thử API: {url} | Status Code: {res.status_code}")
    if res.status_code == 200:
      json_data = res.json()
      if isinstance(json_data, dict):
        return (
            json_data.get("data")
            or json_data.get("list")
            or json_data.get("result", [])
        )
      elif isinstance(json_data, list):
        return json_data
  except Exception as e:
    print(f"    ❌ Lỗi kết nối API: {e}")
  return None


def get_match_detail(domain, path, match_id):
  url = f"{domain}{path}/match/detail?id={match_id}"
  try:
    res = requests.get(url, headers=headers, timeout=8)
    if res.status_code == 200:
      data = res.json()
      return (
          data.get("data")
          if isinstance(data, dict) and "data" in data
          else data
      )
  except Exception:
    pass
  return {}


def main():
  m3u_lines = ["#EXTM3U"]
  today = datetime.now()
  tomorrow = today + timedelta(days=1)

  dates_to_check = [
      (today.strftime("%Y%m%d"), today.strftime("%d/%m")),
      (tomorrow.strftime("%Y%m%d"), tomorrow.strftime("%d/%m")),
  ]

  total_matches_found = 0

  for sport_key, sport_info in SPORTS_CONFIG.items():
    path = sport_info["path"]
    emoji = sport_info["emoji"]
    sport_name = sport_info["name"]

    print(f"\n=== Đang lấy dữ liệu môn: {sport_name} ===")

    for date_code, date_formatted in dates_to_check:
      matches = None
      active_domain = None

      # Thử qua từng domain API dự phòng
      for domain in API_DOMAINS:
        matches = get_data_from_api(domain, path, date_code)
        if matches:
          active_domain = domain
          break

      if not matches:
        print(f"❌ Không lấy được dữ liệu ngày {date_formatted}")
        continue

      if isinstance(matches, dict):
        matches = (
            matches.get("list")
            or matches.get("matches")
            or matches.get("data", [])
        )

      if not isinstance(matches, list):
        continue

      print(
          f"✅ Lấy thành công {len(matches)} trận ngày {date_formatted} từ"
          f" domain: {active_domain}"
      )

      for match in matches:
        if not isinstance(match, dict):
          continue

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

        match_time_ts = match.get("match_time") or match.get("start_time")
        if match_time_ts:
          try:
            match_time = datetime.fromtimestamp(int(match_time_ts)).strftime(
                "%H:%M"
            )
          except Exception:
            match_time = "00:00"
        else:
          match_time = "00:00"

        status = match.get("status", 1)
        status_icon = "🟢" if status in [2, 3, 4, 5, 6, 7, 51, 52] else "⚪"

        # Lấy link phát trực tiếp
        detail = (
            get_match_detail(active_domain, path, match_id) if match_id else {}
        )
        links = (
            detail.get("links")
            or detail.get("play_urls")
            or match.get("links", [])
        )

        if not links and ("stream_url" in match or "play_url" in match):
          links = [{
              "url": match.get("stream_url") or match.get("play_url"),
              "name": match.get("blv_name", "HD"),
          }]

        for link_info in links:
          if not isinstance(link_info, dict):
            continue
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
          label_suffix = f"{quality_tag} {blv_name}".strip()

          title = f"{status_icon} {match_time} {date_formatted} {emoji} {home_team} vs {away_team} ({label_suffix})"

          m3u_lines.append(
              f'#EXTINF:-1 tvg-logo="{logo}" group-title="Xôi Lạc Z TV" ,'
              f" {title}"
          )
          m3u_lines.append(f"#EXTVLCOPT:http-user-agent={DEFAULT_UA}")
          m3u_lines.append(f"#EXTVLCOPT:http-referrer=https://xoilac.tv/")
          m3u_lines.append(f"{stream_url}")
          total_matches_found += 1

  # Ghi file xoilac.m3u
  with open("xoilac.m3u", "w", encoding="utf-8") as f:
    f.write("\n".join(m3u_lines) + "\n")

  print(
      f"\n🎉 Hoàn tất! Đã xuất {total_matches_found} luồng phát vào file"
      " xoilac.m3u"
  )


if __name__ == "__main__":
  main()
    
