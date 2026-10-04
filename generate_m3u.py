import datetime
import json
import requests
import urllib3

# Tắt cảnh báo SSL
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
REFERER = "https://xoilacxbs.tv/"

HEADERS = {
    "User-Agent": USER_AGENT,
    "Referer": REFERER,
    "Origin": "https://xoilacxbs.tv",
    "Accept": "application/json, text/javascript, */*; q=0.01",
}

# Các Endpoint API danh sách trận đấu của hệ thống SportLive / Xôi Lạc
LIST_APIS = [
    "https://fb-api.sportliveapiz.com/football/match/list",
    "https://fb-api.sportliveapiz.com/match/list",
    "https://xoilacxbs.tv/api/match/list",
    "https://xoilacxbs.tv/api/match/live",
]


def fetch_matches():
    session = requests.Session()

    for url in LIST_APIS:
        try:
            print(f"📡 Đang tải danh sách trận đấu từ: {url}")
            res = session.get(url, headers=HEADERS, timeout=10, verify=False)

            if res.status_code == 200:
                data = res.json()
                matches = (
                    data.get("results")
                    or data.get("data")
                    or data.get("matches")
                    or []
                )

                if isinstance(matches, dict):
                    matches = matches.get("list") or matches.get("items") or []

                if isinstance(matches, list) and len(matches) > 0:
                    print(
                        f"✅ Lấy thành công {len(matches)} trận đấu từ {url}"
                    )
                    return matches
            else:
                print(f"⚠️ HTTP Status {res.status_code} từ {url}")
        except Exception as e:
            print(f"⚠️ Lỗi kết nối {url}: {e}")

    return []


def get_stream_urls(match):
    """Bóc tách đường dẫn m3u8 và tên BLV từ dữ liệu trận đấu"""
    match_id = match.get("id")
    links = []

    # 1. Kiểm tra stream có sẵn trong object trận đấu hay không
    play_urls = (
        match.get("play_urls")
        or match.get("urls")
        or match.get("streams")
        or []
    )

    # 2. Nếu rỗng, gọi API chi tiết của trận đấu theo ID
    if not play_urls and match_id:
        detail_api = (
            f"https://fb-api.sportliveapiz.com/football/match/detail?id={match_id}"
        )
        try:
            res = requests.get(
                detail_api, headers=HEADERS, timeout=5, verify=False
            )
            if res.status_code == 200:
                detail_data = res.json()
                play_urls = (
                    detail_data.get("data", {}).get("play_urls")
                    or detail_data.get("results", {}).get("play_urls")
                    or []
                )
        except Exception:
            pass

    # Xử lý danh sách link thu thập được
    if isinstance(play_urls, list):
        for item in play_urls:
            if isinstance(item, dict):
                url = (
                    item.get("url")
                    or item.get("m3u8")
                    or item.get("play_url")
                    or item.get("link")
                )
                blv = item.get("name") or item.get("blv") or "LIVE"
                if url:
                    links.append((blv, url))
            elif isinstance(item, str) and item.startswith("http"):
                links.append(("LIVE", item))

    # Trường hợp link là chuỗi đơn lẻ
    if not links:
        single_url = match.get("stream_url") or match.get("m3u8")
        if single_url:
            links.append(("LIVE", single_url))

    return links


def main():
    print("🚀 Bắt đầu cập nhật playlist từ xoilacxbs.tv ...")
    matches = fetch_matches()

    entries = []
    for m in matches:
        # Lấy tên đội bóng
        home_team = (
            m.get("home_team", {}).get("name")
            or m.get("home_name")
            or m.get("home")
            or "Đội nhà"
        )
        away_team = (
            m.get("away_team", {}).get("name")
            or m.get("away_name")
            or m.get("away")
            or "Đội khách"
        )

        logo = (
            m.get("home_team", {}).get("logo")
            or m.get("home_logo")
            or m.get("logo")
            or ""
        )

        # Trạng thái trận đấu
        status_id = m.get("status_id")
        is_live = status_id in [2, 3, 4, "2", "3", "4"] or m.get(
            "is_live", False
        )
        live_icon = "🟢 " if is_live else "⏰ "

        # Thời gian
        match_time = m.get("match_time") or m.get("start_time")
        if match_time:
            try:
                ts = match_time / 1000 if match_time > 1e11 else match_time
                dt = datetime.datetime.fromtimestamp(ts)
                time_str = dt.strftime("%H:%M")
            except Exception:
                time_str = "00:00"
        else:
            time_str = m.get("time") or "00:00"

        stream_links = get_stream_urls(m)

        for blv, url in stream_links:
            title = f"{live_icon}{time_str} ⚽ {home_team} vs {away_team} ({blv})"
            
            inf_line = f'#EXTINF:-1 tvg-logo="{logo}" group-title="Xôi Lạc XBS" , {title}'
            ua_line = f"#EXTVLCOPT:http-user-agent={USER_AGENT}"
            ref_line = f"#EXTVLCOPT:http-referrer={REFERER}"

            entries.append(f"{inf_line}\n{ua_line}\n{ref_line}\n{url}\n")

    # Ghi file m3u
    output_file = "xoilac.m3u"
    with open(output_file, "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n\n")
        if entries:
            f.write("\n".join(entries))
            print(
                f"🎉 Thành công! Đã xuất {len(entries)} link kênh vào file {output_file}"
            )
        else:
            print("⚠️ Không lấy được link stream nào từ API.")


if __name__ == "__main__":
    main()
    
