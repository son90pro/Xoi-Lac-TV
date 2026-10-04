import datetime
import json
import re
import requests

# Cấu hình User-Agent và Referer chuẩn Xôi Lạc Z TV
USER_AGENT = "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Mobile Safari/537.36"
REFERER = "https://xlz.domainkqt.cc/"

# Mapping Icon theo môn thể thao
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


class XoilacM3UGenerator:

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": USER_AGENT,
                "Referer": REFERER,
                "Origin": REFERER.rstrip("/"),
                "Accept": "application/json, text/plain, */*",
            }
        )

        # Danh sách các Nguồn API dự phòng (tránh lỗi GitHub Actions bị chặn IP)
        self.api_sources = [
            "https://api.vebo.xyz/api/match/featured",
            "https://api.vebotv.org/api/match/featured",
            "https://data-api.apisportdata.com/v1/matches/live",
            "https://api.sportpulseapiz.com/v1/matches/live",
        ]

    def fetch_matches(self):
        """Thử gọi lần lượt từng API cho đến khi lấy được danh sách trận đấu"""
        for api_url in self.api_sources:
            try:
                print(f"🔄 Đang kết nối API: {api_url}")
                res = self.session.get(api_url, timeout=12)
                if res.status_code == 200:
                    data = res.json()
                    matches = (
                        data.get("data", [])
                        if isinstance(data, dict)
                        else data
                    )

                    if isinstance(matches, dict):
                        matches = matches.get("item", []) or matches.get(
                            "matches", []
                        )

                    if matches and len(matches) > 0:
                        print(
                            f"✅ Lấy thành công {len(matches)} trận đấu từ"
                            f" {api_url}"
                        )
                        return matches, api_url
            except Exception as e:
                print(f"⚠️ Lỗi gọi API {api_url}: {e}")

        return [], None

    def extract_stream_links(self, match):
        """Rút trích các server stream & tên BLV từ dữ liệu trận đấu"""
        match_id = match.get("id") or match.get("fid") or match.get("_id")
        links = []

        servers = (
            match.get("play_urls")
            or match.get("servers")
            or match.get("stream_links")
            or []
        )

        # Nếu không có sẵn mảng server, thử gọi API detail theo ID trận
        if not servers and match_id:
            try:
                detail_url = f"https://api.vebo.xyz/api/match/{match_id}/stream"
                res = self.session.get(detail_url, timeout=6)
                if res.status_code == 200:
                    d_data = res.json()
                    servers = (
                        d_data.get("data", {}).get("play_urls")
                        or d_data.get("data", {}).get("servers")
                        or []
                    )
            except Exception:
                pass

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

        # Backup nếu trận chỉ trả về 1 link đơn
        if not links:
            single_url = match.get("play_url") or match.get("stream_url")
            if single_url:
                links.append(("LIVE", single_url))

        return links

    def build_m3u_content(self, matches):
        entries = []

        for m in matches:
            # 1. Tên 2 đội
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

            # 2. Logo đội bóng
            logo = (
                m.get("home", {}).get("logo")
                or m.get("home_logo")
                or m.get("logo")
                or ""
            )
            if not logo and m.get("home", {}).get("id"):
                sport_path = str(
                    m.get("sport_type") or "football"
                ).lower()
                team_id = m.get("home", {}).get("id")
                logo = f"https://imgts.sportpulseapiz.com/{sport_path}/team/{team_id}/image/small"

            # 3. Icon môn thể thao
            sport_type = str(
                m.get("sport_type") or m.get("type") or "football"
            ).lower()
            sport_icon = SPORT_ICONS.get(sport_type, "⚽")

            # 4. Trạng thái Live & Thời gian
            status = m.get("status")
            is_live = (
                status in ["live", "playing", 2, "2"]
                or m.get("is_live") is True
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

            # 5. Tạo các entry M3U chuẩn
            stream_links = self.extract_stream_links(m)

            for blv_name, stream_url in stream_links:
                inf_line = f'#EXTINF:-1 tvg-logo="{logo}" group-title="Xôi Lạc Z TV" , {live_prefix}{time_str} {sport_icon} {home} vs {away} ({blv_name})'
                ua_line = f"#EXTVLCOPT:http-user-agent={USER_AGENT}"
                ref_line = f"#EXTVLCOPT:http-referrer={REFERER}"

                entries.append(
                    f"{inf_line}\n{ua_line}\n{ref_line}\n{stream_url}\n"
                )

        return entries

    def generate(self, output_file="xoilac.m3u"):
        matches, source_used = self.fetch_matches()

        if not matches:
            print(
                "❌ Không lấy được dữ liệu từ tất cả các nguồn API dự phòng!"
            )
            with open(output_file, "w", encoding="utf-8") as f:
                f.write("#EXTM3U\n")
            return

        entries = self.build_m3u_content(matches)

        with open(output_file, "w", encoding="utf-8") as f:
            f.write("#EXTM3U\n\n")
            f.write("\n".join(entries))

        print(
            f"🎉 Đã cập nhật thành công {len(entries)} kênh vào file"
            f" {output_file}!"
        )


if __name__ == "__main__":
    generator = XoilacM3UGenerator()
    generator.generate("xoilac.m3u")
    
