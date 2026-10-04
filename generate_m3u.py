import requests
import json
import os

# API Endpoint bóng đá lấy từ mã nguồn trang web
API_URL = "https://fb-api.sportliveapiz.com/football"

# Header giả lập trình duyệt để bypass các lớp chặn cơ bản
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Referer": "https://xoilacxyc.io/",
    "Origin": "https://xoilacxyc.io",
    "Accept": "application/json, text/plain, */*"
}

def fetch_football_data():
    """Gọi API lấy danh sách tất cả trận đấu"""
    try:
        response = requests.get(API_URL, headers=HEADERS, timeout=15)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"[!] Lỗi khi kết nối API: {e}")
        return None

def extract_stream_links(match_data):
    """Bóc tách link stream và đóng gói thành mảng dữ liệu M3U"""
    channels = []
    
    # Kiểm tra danh sách trận đấu từ kết quả API
    matches = match_data.get("data", []) if isinstance(match_data, dict) else []
    
    # Mã trạng thái đang diễn ra: 2 (Hiệp 1), 3 (Nghỉ giữa hiệp), 4 (Hiệp 2)
    PLAYING_STATUSES = [2, 3, 4, 5, 6, 7]

    for match in matches:
        # Lọc trận đấu đang diễn ra hoặc chuẩn bị diễn ra
        status = match.get("status")
        
        home_team = match.get("home_name", "Đội nhà")
        away_team = match.get("away_name", "Đội khách")
        league = match.get("league_name", "Trực Tiếp Bóng Đá")
        logo = match.get("league_logo") or match.get("home_logo", "")
        
        match_title = f"{home_team} vs {away_team}"
        
        # Lấy danh sách luồng phát sóng / link M3U8 / nhúng của trận đấu
        links = match.get("links", []) or match.get("play_urls", []) or match.get("list_stream", [])
        
        if isinstance(links, list) and len(links) > 0:
            for idx, stream in enumerate(links, 1):
                url = stream.get("url") or stream.get("m3u8") or stream.get("link") if isinstance(stream, dict) else str(stream)
                commentator = stream.get("blv") or stream.get("name") if isinstance(stream, dict) else f"Luồng {idx}"
                
                # Chỉ lấy link có định dạng phát trực tiếp .m3u8 hoặc http
                if url and ("http" in url):
                    channels.append({
                        "name": f"{match_title} ({commentator})",
                        "logo": logo,
                        "group": league,
                        "url": url
                    })
        elif match.get("stream_url"):
            channels.append({
                "name": match_title,
                "logo": logo,
                "group": league,
                "url": match.get("stream_url")
            })

    return channels

def save_m3u_file(channels, filename="playlist.m3u"):
    """Tạo file M3U chuẩn cho các trình phát IPTV"""
    lines = ["#EXTM3U\n"]
    
    for ch in channels:
        lines.append(
            f'#EXTINF:-1 tvg-logo="{ch["logo"]}" group-title="{ch["group"]}",{ch["name"]}\n{ch["url"]}\n'
        )
        
    with open(filename, "w", encoding="utf-8") as f:
        f.writelines(lines)
        
    print(f"[✓] Đã tạo thành công {filename} với {len(channels)} luồng phát sóng!")

if __name__ == "__main__":
    data = fetch_football_data()
    if data:
        channel_list = extract_stream_links(data)
        save_m3u_file(channel_list)
    else:
        print("[!] Không có dữ liệu để tạo M3U.")
        
