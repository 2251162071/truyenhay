import json
import os

from colorama import Fore

# Lấy đường dẫn tới thư mục chứa file Python hiện tại
current_dir = os.path.dirname(os.path.abspath(__file__))

# Đường dẫn tới file danh_sach_truyen.json
danh_sach_truyen_path = os.path.join(current_dir, 'total_danh_sach_truyen.json')

# Đọc dữ liệu từ file danh_sach_truyen.json
with open(danh_sach_truyen_path, 'r', encoding='utf-8') as f:
    data = json.load(f)

# Tạo danh sách từ dữ liệu đã đọc
dstruyen = []
for key, info in data.items():
    try:
        dstruyen.append({
            "ten_truyen": info["ten_truyen"],
            "link_truyen": info["link_truyen"],
            "ten_truyen_full": info["ten_truyen_full"],
            "tac_gia": info["tac_gia"],
            "the_loai": info["the_loai"],
            "trang_thai": info["trang_thai"],
            "so_chuong": info["so_chuong"],
            "description_html": info["description_html"],
            "rating_value": info["rating_value"]
        })
    except KeyError as e:
        print(Fore.RED + f"KeyError: {e} in item with key {key}")

# Đường dẫn tới file dstruyen.json
dstruyen_path = os.path.join(current_dir, 'total_dstruyen.json')

# Lưu danh sách vào file dstruyen.json
with open(dstruyen_path, 'w', encoding='utf-8') as f:
    json.dump(dstruyen, f, ensure_ascii=False, indent=4)
