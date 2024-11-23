import os
import json

from colorama import Fore, init

# Khởi tạo colorama
init(autoreset=True)  # Để tự động reset màu sau mỗi lần in

def validate_json_file(file_path):
    # Kiểm tra xem file có tồn tại hay không
    if not os.path.exists(file_path):
        print("File không tồn tại.")
        return False

    # Kiểm tra xem file có rỗng hay không
    if os.path.getsize(file_path) == 0:
        print(Fore.RED + f"File {file_path} rỗng.")
        return False

    # Đọc và kiểm tra cấu trúc của file JSON
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            data = json.load(file)

            if data == [] or data == {} or data is None:
                print(Fore.RED + f"File {file_path} không chứa dữ liệu.")
                return False
            
            # Kiểm tra xem data có phải là một danh sách không
            if not isinstance(data, list):
                print(Fore.RED + f"File {file_path} không chứa danh sách.")
                return False

            # Kiểm tra từng mục trong danh sách có định dạng đúng hay không
            for item in data:
                if not isinstance(item, dict):
                    print(Fore.RED + f"Item trong JSON không phải là dictionary.")
                    return False
                if "link_chuong" not in item or "ten_chuong" not in item:
                    print(Fore.RED + f"{file_path}Thiếu 'link_chuong' hoặc 'ten_chuong' trong một mục.")
                    return False
                if not isinstance(item["link_chuong"], str) or not isinstance(item["ten_chuong"], str):
                    print(Fore.RED + f"{file_path}'link_chuong' hoặc 'ten_chuong' không phải là chuỗi.")
                    return False

        # Nếu tất cả điều kiện đều thỏa mãn
        # print(Fore.BLUE + f"File {file_path} hợp lệ.")
        return True

    except json.JSONDecodeError:
        print(Fore.RED + f"Lỗi định dạng {file_path}.")
        return False

# Sử dụng hàm với đường dẫn đến file JSON
# Thực hiển kiểm tra tất cả file json trong thư mục chứa file code này
current_dir = os.path.dirname(os.path.abspath(__file__))
danh_sach_truyen_khong_hop_le = []
for file in os.listdir(current_dir):
    if file.endswith('.json'):
        file_path = os.path.join(current_dir, file)
        print(f"Kiểm tra file {file}:")
        if validate_json_file(file_path) == False:
            file_name = os.path.splitext(os.path.basename(file_path))[0]
            danh_sach_truyen_khong_hop_le.append(file_name)

# Lưu danh sách truyện không hợp lệ vào file
if danh_sach_truyen_khong_hop_le:
    with open('1-danh_sach_truyen_khong_hop_le.txt', 'w', encoding='utf-8') as file:
        file.write("\n".join(danh_sach_truyen_khong_hop_le))
    print(Fore.RED + "Có truyện không hợp lệ. Danh sách đã được lưu vào file 'danh_sach_truyen_khong_hop_le.txt'.")
            


