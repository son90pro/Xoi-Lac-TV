from datetime import datetime, timedelta
import json
import os
import time
from playwright.sync_api import sync_playwright

# Các tên miền trang chủ Xôi Lạc / Về Bờ đang hoạt động
TARGET_URLS = [
    "https://xoilac.tv",
    "https://vebo.live",
    "https://xoilac365.tv",
]

SPORTS_MAP = {
    "football": "⚽ Bóng đá",
    "basketball": "🏀 Bóng rổ",
    "tennis": "🎾 Tennis",
}


def fetch_matches_with_playwright():
  captured_data = []

  with sync_playwright() as p:
    browser = p.chromium.launch(
        headless=True,
        args=[
            "--no-sandbox",
            "--disable-setuid-sandbox",
            "--disable-blink-features=AutomationControlled",
        ],
    )
    context = browser.new_context(
        user_agent=(
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            " (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
        ),
        viewport={"width": 1280, "height": 800},
    )
    page = context.new_page()

    # Bắt response JSON từ các request API ngầm của trang web
    def handle_response(response):
      if (
          "/match/list" in response.url or "/matches" in response.url
      ) and response.status == 200:
        try:
          data = response.json()
          captured_data.append((response.url, data))
          print(f"  [+] Đã bắt được API payload từ: {response.url[:60]}...")
        except Exception:
          pass

    page.on("response", handle_response)

    # Thử truy cập từng domain cho đến khi lấy được dữ liệu
    for url in TARGET_URLS:
      print(f"\n🌐 Đang mở trang: {url}")
      try:
        page.goto(url, timeout=20000, wait_until="domcontentloaded")
        page.wait_for_timeout(4000)  # Chờ Cloudflare challenge & API load

        if captured_data:
          print(f"✅ Vượt Cloudflare thành công trên {url}!")
          break
      except Exception as e:
        print(f"❌ Không thể truy cập {url}: {e}")

    browser.close()

  return captured_data


def parse_and_generate_m3u(captured_data):
  m3u_lines = ["#EXTM3U"]
  total_channels = 0
  seen_matches = set()

  for url, json_content in captured_data:
    matches = []
    if isinstance(json_content, dict):
      matches = (
          json_content.get("data")
          or json_content.get("list")
          or json_content.get("result", [])
      )
    elif isinstance(json_content, list):
      matches = json_content

    if not isinstance(matches, list):
      continue

    for match in matches:
      if not isinstance(match, dict):
        continue

      match_id = match.get("id") or match.get("_id")
      if match_id in seen_matches:
        continue
      seen_matches.add(match_id)

      home = (
          match.get("home_name")
          or match.get("home_team", {}).get("name")
          or "Đội nhà"
      )
      away = (
          match.get("away_name")
          or match.get("away_team", {}).get("name")
          or "Đội khách"
      )
      logo = (
          match.get("home_logo")
          or match.get("home_team", {}).get("logo")
          or "https://xoilac.tv/favicon.ico"
      )

      # Giờ thi đấu
      ts = match.get("match_time") or match.get("start_time")
      if ts:
        try:
          match_time = datetime.fromtimestamp(int(ts)).strftime("%H:%M %d/%m")
        except Exception:
          match_time = "Đang diễn ra"
      else:
        match_time = "Đang diễn ra"

      # Trạng thái trận đấu
      status = match.get("status", 1)
      status_icon = "🟢" if status in [2, 3, 4, 5, 6, 7] else "⚪"

      # Danh sách link stream
      links = match.get("links") or match.get("play_urls") or []
      if not links and ("stream_url" in match or "play_url" in match):
        links = [{
            "url": match.get("stream_url") or match.get("play_url"),
            "name": match.get("blv_name", "HD"),
        }]

      for link in links:
        if not isinstance(link, dict):
          continue

        stream_url = link.get("url") or link.get("play_url")
        if not stream_url or not stream_url.startswith("http"):
          continue

        blv = (
            link.get("blv_name")
            or link.get("commentator")
            or link.get("name")
            or "HD"
        )
        title = f"{status_icon} [{match_time}] {home} vs {away} (BLV {blv})"

        m3u_lines.append(
            f'#EXTINF:-1 tvg-logo="{logo}" group-title="Xôi Lạc TV",'
            f" {title}"
        )
        m3u_lines.append(
            "#EXTVLCOPT:http-user-agent=Mozilla/5.0 (Windows NT 10.0; Win64;"
            " x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0"
            " Safari/537.36"
        )
        m3u_lines.append("#EXTVLCOPT:http-referrer=https://xoilac.tv/")
        m3u_lines.append(stream_url)
        total_channels += 1

  # Xuất ra file m3u
  with open("xoilac.m3u", "w", encoding="utf-8") as f:
    f.write("\n".join(m3u_lines) + "\n")

  print(
      f"\n🎉 Hoàn tất! Đã xuất {total_channels} luồng phát trực tiếp vào file"
      " xoilac.m3u"
  )


def main():
  print("=== BẮT ĐẦU CÀO DỮ LIỆU BẰNG PLAYWRIGHT ===")
  data = fetch_matches_with_playwright()

  if not data:
    print("❌ Không bắt được API nào từ các trang web. Đang tạo file trống.")
    with open("xoilac.m3u", "w", encoding="utf-8") as f:
      f.write("#EXTM3U\n")
    return

  parse_and_generate_m3u(data)


if __name__ == "__main__":
  main()
    
