import requests
import json

# Đường dẫn nguồn JSON của anh (thay link raw JSON thực tế vào đây nếu cần)
JSON_URL = "https://raw.githubusercontent.com/kaytee1012/Kienplay/main/data.json"

def fetch_and_generate_m3u():
    print(f"Đang tải dữ liệu JSON từ: {JSON_URL}")
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    try:
        res = requests.get(JSON_URL, headers=headers, timeout=15)
        if res.status_code != 200:
            print(f"Không thể tải dữ liệu JSON, mã lỗi: {res.status_code}")
            return
            
        data = res.json()
        m3u_lines = ["#EXTM3U\n"]
        total_channels = 0

        # Duyệt qua cấu trúc phân tầng JSON của Kienplayer
        providers = data.get("providers", [])
        for provider in providers:
            groups = provider.get("groups", [])
            for group in groups:
                group_name = group.get("name", "Thể Thao Trực Tiếp")
                channels = group.get("channels", [])
                
                for channel in channels:
                    match_name = channel.get("name", "Trận đấu")
                    subtitle = channel.get("subtitle", "")
                    logo = channel.get("home_logo") or channel.get("image", {}).get("url", "")
                    
                    sources = channel.get("sources", [])
                    for source in sources:
                        contents = source.get("contents", [])
                        for content in contents:
                            streams = content.get("streams", [])
                            for stream in streams:
                                stream_name = stream.get("name", "HD")
                                remote_data = stream.get("remote_data", {})
                                stream_url = remote_data.get("url", "")
                                
                                if stream_url and "m3u8" in stream_url:
                                    # Dựng tiêu đề kênh hiển thị đẹp mắt trên tivi
                                    title = f"🟢 {match_name} - {stream_name}"
                                    if subtitle:
                                        title += f" ({subtitle})"
                                        
                                    inf_line = f'#EXTINF:-1 tvg-logo="{logo}" group-title="{group_name}" , {title}'
                                    m3u_lines.append(inf_line)
                                    m3u_lines.append(stream_url + "\n")
                                    total_channels += 1

        # Ghi nội dung ra tệp playlist.m3u
        with open("playlist.m3u", "w", encoding="utf-8") as f:
            f.write("\n".join(m3u_lines))
            
        print(f"Đã chuyển đổi thành công và tạo playlist với tổng số {total_channels} kênh!")
        
    except Exception as e:
        print(f"Lỗi khi xử lý dữ liệu JSON: {e}")

if __name__ == "__main__":
    fetch_and_generate_m3u()
    
