import json
import re
import requests


class XoilacM3UGenerator:

    def __init__(self):
        self.base_url = "https://xoilaczbx.tv"
        self.api_live_url = "https://data-api.apisportdata.com/v1/matches/live"
        self.api_detail_url = (
            "https://data-api.apisportdata.com/v1/matches/detail"
        )
        self.headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
                " AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0"
                " Safari/537.36"
            ),
            "Referer": "https://xoilaczbx.tv/",
            "Origin": "https://xoilaczbx.tv",
            "Accept": "application/json, text/plain, */*",
        }

    def get_live_matches(self):
        """Lấy danh sách tất cả các trận đấu đang diễn ra"""
        try:
            res = requests.get(
                self.api_live_url, headers=self.headers, timeout=10
            )
            if res.status_code == 200:
                data = res.json()
                return data.get("data", [])
        except Exception as e:
            print(f"❌ Lỗi lấy danh sách trận live: {e}")
        return []

    def get_match_detail(self, match_id):
        """Lấy chi tiết thông tin server & link stream của 1 trận đấu"""
        try:
            res = requests.get(
                self.api_detail_url,
                headers=self.headers,
                params={"id": match_id},
                timeout=10,
            )
            if res.status_code == 200:
                return res.json().get("data", {})
        except Exception as e:
            print(f"❌ Lỗi lấy chi tiết trận {match_id}: {e}")
        return {}

    def scrape_fallback_html(self, match_id):
        """Phương án dự phòng: cào trực tiếp link m3u8 từ HTML trang live"""
        url = f"{self.base_url}/truc-tiep/{match_id}"
        try:
            res = requests.get(url, headers=self.headers, timeout=10)
            if res.status_code == 200:
                m3u8_links = re.findall(
                    r'https?://[^\s\'"]+\.m3u8[^\s\'"]*', res.text
                )
                return list(set(m3u8_links))
        except Exception as e:
            print(f"❌ Lỗi cào HTML dự phòng trận {match_id}: {e}")
        return []

    def generate_playlist(self, output_filename="playlist.m3u"):
        print("🔄 Đang lấy danh sách các trận đấu đang diễn ra...")
        matches = self.get_live_matches()

        playlist_entries = []

        if not matches:
            print("⚠️ Không tìm thấy trận đấu nào đang live qua API.")

        for match in matches:
            match_id = match.get("id") or match.get("fid")
            if not match_id:
                continue

            home_name = (
                match.get("home_name") or match.get("home", {}).get("name")
            ) or "Đội nhà"
            away_name = (
                match.get("away_name") or match.get("away", {}).get("name")
            ) or "Đội khách"
            title = f"{home_name} vs {away_name}"

            print(f"👉 Đang xử lý: {title} (ID: {match_id})")

            # 1. Gọi API chi tiết
            detail = self.get_match_detail(match_id)
            servers = detail.get("servers", [])

            added = False
            # Bóc tách từ danh sách servers
            for s in servers:
                play_url = s.get("play_url") or s.get("stream_url")
                commentator = (
                    s.get("commentator") or s.get("name") or "Server Live"
                )
                if play_url:
                    entry_title = f"{title} - BLV {commentator}"
                    playlist_entries.append((entry_title, play_url))
                    added = True

            # 2. Nếu không có servers list, kiểm tra link chính
            if not added and detail.get("play_url"):
                playlist_entries.append(
                    (f"{title} - Server Chuẩn", detail["play_url"])
                )
                added = True

            # 3. Phương án cào HTML nếu API không trả về link
            if not added:
                fallback_links = self.scrape_fallback_html(match_id)
                for idx, link in enumerate(fallback_links, 1):
                    playlist_entries.append(
                        (f"{title} - Server Backup {idx}", link)
                    )

        # Ghi nội dung vào file M3U
        with open(output_filename, "w", encoding="utf-8") as f:
            f.write("#EXTM3U\n")
            for entry_title, stream_url in playlist_entries:
                f.write(
                    f'#EXTINF:-1 group-title="Xoilac Live",{entry_title}\n'
                )
                f.write(f"{stream_url}\n")

        print(
            f"\n✅ Đã tạo file thành công: {output_filename} (Tổng cộng:"
            f" {len(playlist_entries)} kênh stream)"
        )


if __name__ == "__main__":
    generator = XoilacM3UGenerator()
    generator.generate_playlist("playlist.m3u")
    
