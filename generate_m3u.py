import datetime
import json
import urllib.parse
import requests

USER_AGENT = "Mozilla/5.0 (iPhone; CPU iPhone OS 17_4_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4.1 Mobile/15E148 Safari/604.1"
REFERER = "https://xlz.domainkqt.cc/"

SPORT_ICONS = {
    "football": "⚽",
    "soccer": "⚽",
    "basketball": "🏀",
    "tennis": "🥎",
    "volleyball": "🏐",
    "lol": "🎮",
    "esports": "🎮",
    "game": "🎮",
}

# Danh sách các API Endpoint dự phòng của Xôi Lạc / Về Bờ / Cà Khía / Thập Cẩm
API_ENDPOINTS = [
    "https://api.vebo.xyz/api/match/featured",
    "https://api.vebotv.org/api/match/featured",
    "https://api.vungtau.xyz/api/match/featured",
    "https://api.cakhia.org/api/match/featured",
    "https://api.thapcam.net/api/match/featured",
    "https://api.vebo.xyz/api/match/live",
    "https://data-api.apisportdata.com/v1/matches/live",
]

# Danh sách Proxy giúp lách dải IP GitHub Actions bị Cloudflare chặn
PROXIES = [
    "",  # Thử trực tiếp
    "https://corsproxy.io/?",
    "https://api.allorigins.win/raw?url=",
]


def fetch_data_from_api(url, proxy_prefix=""):
    headers = {
        "User-Agent": USER_AGENT,
        "Referer": REFERER,
        "Origin": REFERER.rstrip("/"),
        "Accept": "application/json, text/plain, */*",
    }

    target_url = (
        f"{proxy_prefix}{urllib.parse.quote(url)}" if proxy_prefix else url
    )

    try:
        response = requests.get(target_url, headers=headers, timeout=10)
        if response.status_code == 200:
            try:
                data = response.json()
                if isinstance(data, dict) and "contents" in data:
                    data = json.loads(data["contents"])
                return data
            except Exception:
                return json.loads(response.text)
    except Exception as e:
        print(f"⚠️ Kết nối thất bại [{proxy_prefix or 'Direct'}]: {e}")
    return None


def extract_matches(data):
    if not data:
        return []

    matches = []
    if isinstance(data, dict):
        matches = (
            data.get("data", [])
            or data.get("item", [])
            or data.get("matches", [])
        )
        if isinstance(matches, dict):
            matches = matches.get("item", []) or matches.get("matches", [])
    elif isinstance(data, list):
        matches = data

    return matches if isinstance(matches, list) else []


def get_stream_urls(match):
    match_id = match.get("id") or match.get("fid") or match.get("_id")
    servers = (
        match.get("play_urls")
        or match.get("servers")
        or match.get("stream_links")
        or []
    )

    if not servers and match_id:
        for base_api in [
            "https://api.vebo.xyz/api/match",
            "https://api.vebotv.org/api/match",
        ]:
            detail_url = f"{base_api}/{match_id}/stream"
            detail_data = fetch_data_from_api(detail_url)
            if detail_data and isinstance(detail_data, dict):
                servers = (
                    detail_data.get("data", {}).get("play_urls")
                    or detail_data.get("data", {}).get("servers")
                    or []
                )
                if servers:
                    break

    links = []
    for s in servers:
        if isinstance(s, dict):
            url = (
                s.get("url")
                or s.get("play_url")
                or s.get("stream_url")
                or s.get("link")
                or s.get("m3u8")
            )
            blv = (
                s.get("name")
                or s.get("commentator")
                or s.get("blv")
                or "LIVE"
            )
        elif isinstance(s, str):
            url = s
            blv = "LIVE"
        else:
            continue

        if url and ("m3u8" in url or "http" in url):
            links.append((blv, url))

    if not links:
        single_url = (
            match.get("play_url")
            or match.get("stream_url")
            or match.get("m3u8")
        )
        if single_url:
            links.append(("LIVE", single_url))

    return links


def main():
    print("🚀 Bắt đầu quét danh sách trận đấu Xôi Lạc Z TV...")
    all_matches = []

    for api in API_ENDPOINTS:
        for proxy in PROXIES:
            print(
                f"📡 Đang thử kết nối: {api} (Proxy:"
                f" '{proxy or 'Kênh trực tiếp'}')"
            )
            raw_data = fetch_data_from_api(api, proxy)
            matches = extract_matches(raw_data)

            if matches:
                print(f"✅ Lấy thành công {len(matches)} trận từ {api}")
                all_matches = matches
                break

        if all_matches:
            break

    if not all_matches:
        print("❌ Không thể lấy dữ liệu từ tất cả API dự phòng.")

    entries = []
    for m in all_matches:
        home = (
            m.get("home", {}).get("name")
            or m.get("home_name")
            or m.get("home_team")
            or "Đội nhà"
        )
        away = (
            m.get("away", {}).get("name")
            or m.get("away_name")
            or m.get("away_team")
            or "Đội khách"
        )

        logo = (
            m.get("home", {}).get("logo")
            or m.get("home_logo")
            or m.get("logo")
            or ""
        )

        sport_type = str(
            m.get("sport_type") or m.get("type") or "football"
        ).lower()
        sport_icon = SPORT_ICONS.get(sport_type, "⚽")

        status = m.get("status")
        is_live = (
            status in ["live", "playing", 2, "2"] or m.get("is_live") is True
        )
        live_prefix = "🟢 " if is_live else ""

        match_time = m.get("match_time") or m.get("timestamp")
        if match_time:
            try:
                ts = match_time / 1000 if match_time > 1e11 else match_time
                dt = datetime.datetime.fromtimestamp(ts)
                time_str = dt.strftime("%H:%M %d/%m")
            except Exception:
                time_str = "00:00"
        else:
            time_str = m.get("time_str") or m.get("time") or "00:00"

        stream_links = get_stream_urls(m)

        for blv_name, stream_url in stream_links:
            inf_line = f'#EXTINF:-1 tvg-logo="{logo}" group-title="Xôi Lạc Z TV" , {live_prefix}{time_str} {sport_icon} {home} vs {away} ({blv_name})'
            ua_line = f"#EXTVLCOPT:http-user-agent={USER_AGENT}"
            ref_line = f"#EXTVLCOPT:http-referrer={REFERER}"

            entries.append(
                f"{inf_line}\n{ua_line}\n{ref_line}\n{stream_url}\n"
            )

    with open("xoilac.m3u", "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n\n")
        if entries:
            f.write("\n".join(entries))
            print(
                f"🎉 Đã xuất thành công {len(entries)} kênh vào file xoilac.m3u!"
            )
        else:
            print("⚠️ Cập nhật file xoilac.m3u rỗng!")


if __name__ == "__main__":
    main()
