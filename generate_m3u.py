import datetime
import json
import re
import time
from playwright.sync_api import sync_playwright

USER_AGENT = "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Mobile Safari/537.36"
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


def fetch_matches_with_playwright():
    captured_matches = []

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
            user_agent=USER_AGENT,
            viewport={"width": 412, "height": 915},
            is_mobile=True,
            has_touch=True,
        )
        page = context.new_page()

        # Bắt API response ngầm khi trình duyệt nạp trang
        def handle_response(response):
            nonlocal captured_matches
            url = response.url
            if ("api/match" in url or "matches/live" in url) and response.status == 200:
                try:
                    data = response.json()
                    matches = (
                        data.get("data", [])
                        if isinstance(data, dict)
                        else data
                    )
                    if isinstance(matches, dict):
                        matches = matches.get("item", []) or matches.get(
                            "matches", []
                        )

                    if isinstance(matches, list) and len(matches) > 0:
                        captured_matches = matches
                        print(
                            f"✅ Bắt thành công {len(matches)} trận đấu từ API:"
                            f" {url}"
                        )
                except Exception:
                    pass

        page.on("response", handle_response)

        # Danh sách domain Xôi Lạc / Về Bờ để truy cập thử
        target_domains = [
            "https://vebo.xyz",
            "https://xlz.domainkqt.cc",
            "https://bit.ly/xoilac",
        ]

        for domain in target_domains:
            try:
                print(f"🌐 Trình duyệt đang truy cập: {domain}")
                page.goto(domain, wait_until="domcontentloaded", timeout=20000)
                page.wait_for_timeout(4000)

                if captured_matches:
                    break
            except Exception as e:
                print(f"⚠️ Không thể tải {domain}: {e}")

        # Trường hợp không bắt được qua Network, gọi trực tiếp API trong ngữ cảnh trình duyệt
        if not captured_matches:
            print("🔄 Đang thử fetch trực tiếp API qua Browser context...")
            api_endpoints = [
                "https://api.vebo.xyz/api/match/featured",
                "https://api.vebotv.org/api/match/featured",
            ]
            for api in api_endpoints:
                try:
                    res_text = page.evaluate(
                        f"""async () => {{
                        let res = await fetch('{api}');
                        return await res.text();
                    }}"""
                    )
                    data = json.loads(res_text)
                    matches = (
                        data.get("data", [])
                        if isinstance(data, dict)
                        else data
                    )
                    if isinstance(matches, dict):
                        matches = matches.get("item", []) or matches.get(
                            "matches", []
                        )
                    if isinstance(matches, list) and len(matches) > 0:
                        captured_matches = matches
                        print(
                            f"✅ Fetch trực tiếp thành công {len(matches)} trận"
                            f" từ {api}"
                        )
                        break
                except Exception as e:
                    print(f"⚠️ Lỗi fetch API {api}: {e}")

        browser.close()

    return captured_matches


def build_m3u(matches):
    entries = []

    for m in matches:
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
        if not logo and m.get("home", {}).get("id"):
            sport_path = str(m.get("sport_type") or "football").lower()
            team_id = m.get("home", {}).get("id")
            logo = f"https://imgts.sportpulseapiz.com/{sport_path}/team/{team_id}/image/small"

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

        # Tách lấy link stream & BLV
        servers = (
            m.get("play_urls") or m.get("servers") or m.get("stream_links") or []
        )
        links = []

        for s in servers:
            if isinstance(s, dict):
                url = (
                    s.get("url")
                    or s.get("play_url")
                    or s.get("stream_url")
                    or s.get("link")
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

            if url:
                links.append((blv, url))

        if not links:
            single_url = m.get("play_url") or m.get("stream_url")
            if single_url:
                links.append(("LIVE", single_url))

        for blv_name, stream_url in links:
            inf_line = f'#EXTINF:-1 tvg-logo="{logo}" group-title="Xôi Lạc Z TV" , {live_prefix}{time_str} {sport_icon} {home} vs {away} ({blv_name})'
            ua_line = f"#EXTVLCOPT:http-user-agent={USER_AGENT}"
            ref_line = f"#EXTVLCOPT:http-referrer={REFERER}"

            entries.append(
                f"{inf_line}\n{ua_line}\n{ref_line}\n{stream_url}\n"
            )

    return entries


def main():
    matches = fetch_matches_with_playwright()

    with open("xoilac.m3u", "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n\n")
        if matches:
            entries = build_m3u(matches)
            f.write("\n".join(entries))
            print(f"🎉 Đã xuất thành công {len(entries)} kênh vào xoilac.m3u")
        else:
            print("⚠️ Không lấy được trận đấu nào!")


if __name__ == "__main__":
    main()
