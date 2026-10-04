import requests
import json
from datetime import datetime

# Domain & API Endpoint danh sách trận đấu
BASE_URL = "https://xoilaczbx.tv"
MATCH_API_URL = "https://fb-api.apiscoreflow.com/football/match/list"  # Endpoint chứa thông tin trận đấu & luồng live

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json, text/javascript, */*; q=0.01",
    "Referer": "https://xoilaczbx.tv/"
}

def fetch_matches():
    try:
        response = requests.get(MATCH_API_URL, headers=HEADERS, timeout=10)
        if response.status_code == 200:
            return response.json().get("data", [])
    except Exception as e:
        print(f"Lỗi khi kết nối API: {e}")
    return []

def format_time(timestamp):
    """Chuyển timestamp thành HH:MM DD/MM"""
    dt = datetime.fromtimestamp(timestamp)
    return dt.strftime("%H:%M %d/%m")

def build_m3u(matches):
    m3u_content = "#EXTM3U\n"
    
    for match in matches:
        # Trích xuất thông tin cơ bản
        match_time = format_time(match.get("match_time", 0))
        home_team = match.get("home_name", "Đội nhà")
        away_team = match.get("away_name", "Đội khách")
        logo = match.get("home_logo", "")
        
        # Danh sách các luồng phát (FHD, HD, SD, BLV)
        streams = match.get("links", [])
        
        for stream in streams:
            blv_name = stream.get("blv_name", "")
            quality = stream.get("quality", "")  # FHD, HD, SD
            stream_url = stream.get("play_url", "")
            
            if not stream_url:
                continue
                
            # Tạo tag hiển thị theo mẫu
            tag_info = f"({quality} {blv_name})".strip().replace("  ", " ") if quality or blv_name else ""
            display_name = f"{match_time} ⚽ {home_team} vs {away_team} {tag_info}".strip()
            
            m3u_content += f'#EXTINF:-1 tvg-logo="{logo}" group-title="Xôi Lạc Z TV",{display_name}\n'
            m3u_content += f'{stream_url}\n'
            
    return m3u_content

def main():
    matches = fetch_matches()
    m3u_text = build_m3u(matches)
    
    with open("xoilac.m3u", "w", encoding="utf-8") as f:
        f.write(m3u_text)
    print("Đã cập nhật danh sách xoilac.m3u thành công!")

if __name__ == "__main__":
    main()
  
