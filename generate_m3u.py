import json
import requests

def build_m3u(matches):
    """
    Hàm dựng file M3U chuẩn định dạng Xôi Lạc Z TV.
    Xử lý an toàn: Không crash nếu matches là None hoặc rỗng.
    """
    if not matches:
        return "#EXTM3U\n"

    user_agent = "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Mobile Safari/537.36"
    referrer = "https://xlz.domainkqt.cc/"

    lines = ["#EXTM3U\n"]

    for match in matches:
        # Lấy các thông số trận đấu
        status = match.get("status", "🟢")  # 🟢 cho live
        time_str = match.get("time", "")     # Ví dụ: "09:00 04/10"
        sport_icon = match.get("icon", "⚽") # ⚽ 🏀 🥎 🏐 🎮
        match_name = match.get("name", "")   # Ví dụ: "Belize vs French Guiana"
        blv = match.get("blv", "").strip()   # Tên BLV
        logo = match.get("logo", "")

        # Chuỗi tiêu đề cơ bản
        title_base = f"{status} {time_str} {sport_icon} {match_name}".strip()

        # 1. Thêm luồng SD (nếu có)
        sd_url = match.get("sd_link")
        if sd_url:
            blv_sd = f"({blv})" if blv else ""
            extinf_sd = f'#EXTINF:-1 tvg-logo="{logo}" group-title="Xôi Lạc Z TV" , {title_base} {blv_sd}'.strip()
            
            lines.append(extinf_sd)
            lines.append(f"#EXTVLCOPT:http-user-agent={user_agent}")
            lines.append(f"#EXTVLCOPT:http-referrer={referrer}")
            lines.append(sd_url)
            lines.append("")  # Dòng trống phân cách

        # 2. Thêm luồng HD (nếu có)
        hd_url = match.get("hd_link")
        if hd_url:
            blv_hd = f"(HD {blv})" if blv else "(HD)"
            extinf_hd = f'#EXTINF:-1 tvg-logo="{logo}" group-title="Xôi Lạc Z TV" , {title_base} {blv_hd}'.strip()
            
            lines.append(extinf_hd)
            lines.append(f"#EXTVLCOPT:http-user-agent={user_agent}")
            lines.append(f"#EXTVLCOPT:http-referrer={referrer}")
            lines.append(hd_url)
            lines.append("")  # Dòng trống phân cách

    return "\n".join(lines)


def fetch_xoilac_matches():
    """
    Hàm lấy dữ liệu trận đấu từ API/Nguồn Xoilac.
    Luôn trả về list (rỗng nếu có lỗi) để tránh lỗi 'NoneType' object is not iterable.
    """
    api_url = "https://xlz.domainkqt.cc/api/matches" # Hoặc endpoint API tương đương của web
    headers = {
        "User-Agent": "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36",
        "Referer": "https://xlz.domainkqt.cc/"
    }

    try:
        response = requests.get(api_url, headers=headers, timeout=15)
        if response.status_code != 200:
            print(f"Cảnh báo: HTTP {response.status_code}")
            return []

        data = response.json()
        matches = []

        # Giả định cấu trúc JSON từ API Xoilac
        for item in data.get("data", []):
            # Xác định icon môn thể thao
            sport_type = item.get("sport_type", "football")
            sport_icons = {
                "football": "⚽",
                "basketball": "🏀",
                "tennis": "🥎",
                "volleyball": "🏐",
                "esports": "🎮",
                "lol": "🎮"
            }
            icon = sport_icons.get(sport_type, "⚽")

            matches.append({
                "status": "🟢" if item.get("is_live") else "",
                "time": item.get("match_time", ""), # e.g. "09:00 04/10"
                "icon": icon,
                "name": f"{item.get('home_team')} vs {item.get('away_team')}",
                "blv": item.get("commentator", ""),
                "logo": item.get("team_logo", ""),
                "sd_link": item.get("stream_sd"), # Link .flv
                "hd_link": item.get("stream_hd")  # Link .flv?auth_key=...
            })

        return matches

    except Exception as e:
        print(f"Lỗi khi cào dữ liệu: {e}")
        return [] # Luôn return list rỗng khi lỗi


def main():
    print("Đang lấy danh sách trận đấu...")
    matches = fetch_xoilac_matches()
    
    # Tạo nội dung file M3U
    m3u_content = build_m3u(matches)
    
    # Ghi ra file
    with open("xoilac.m3u", "w", encoding="utf-8") as f:
        f.write(m3u_content)
        
    print(f"Đã xuất thành công file xoilac.m3u ({len(matches)} trận).")

if __name__ == "__main__":
    main()
