import os
import json


output_file = './total_danh_sach_truyen.json'

# Hàm đọc và xử lý file JSON trong thư mục
def process_files():
    # Đường dẫn tới thư mục chứa các file JSON cần xử lý và file danh_sach_truyen.json
    list_folder_path = ['dam-my', 'huyen-huyen', 'kiem-hiep', 'ngon-tinh', 'tien-hiep']
    # Đọc dữ liệu từ file danh_sach_truyen.json
    if os.path.exists(output_file):
        with open(output_file, 'r', encoding='utf-8') as f:
            danh_sach_truyen = json.load(f)
    else:
        danh_sach_truyen = {}
    # Lặp qua tất cả các thư mục con
    for folder in list_folder_path:
        folder_path = os.path.join('.', folder)
        # Lặp qua tất cả các file tên là danh_sach_truyen.json trong thư mục con
        for file_name in os.listdir(folder_path):
            if file_name == 'danh_sach_truyen.json':
                file_path = os.path.join(folder_path, file_name)
                
                # Đọc dữ liệu từ file JSON hiện tại
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # Kiểm tra và thêm dữ liệu chưa tồn tại vào danh_sach_truyen
                for key, value in data.items():
                    if key not in danh_sach_truyen:
                        danh_sach_truyen[key] = value

    
    # Ghi lại dữ liệu đã cập nhật vào total_danh_sach_truyen.json
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(danh_sach_truyen, f, ensure_ascii=False, indent=4)

# Thực thi hàm
process_files()
print("Quá trình xử lý hoàn tất. Dữ liệu mới đã được thêm vào danh_sach_truyen.json.")
