import json
import os
from pathlib import Path
from django.conf import settings
import requests
import logging
from colorama import Fore, Style, init

# Khởi tạo colorama
init(autoreset=True)  # Để tự động reset màu sau mỗi lần in

# Cấu hình logging
logging.basicConfig(filename='logfile.ans', level=logging.INFO, format='%(message)s', encoding='utf-8')


def send_request(url):
    """
    Gửi request đến URL và trả về response.

    Args:
        url (str): URL cần gửi request.
        'https://example.com/'

    Returns:
        requests.models.Response: Response từ request.

    """
    try:
        response = requests.get(url)
        response.raise_for_status()  # Kiểm tra lỗi HTTP
        # print(Fore.GREEN + f"Gửi request thành công: {url}")
        log_with_color(f"Gửi request thành công: {url}", Fore.GREEN)
        return response
    except requests.RequestException as e:
        # print(Fore.RED + f"Có lỗi khi gửi request: {e}")
        log_with_color(f"Có lỗi khi gửi request: {e}", Fore.RED)
        return None


def log_with_color(message, color=Fore.GREEN):
    colored_message = f"{color}{message}{Style.RESET_ALL}"
    logging.info(colored_message)
    print(colored_message)


def save_json(danh_sach_truyen, file_path=None):
    """
    Lưu dữ liệu vào file json.

    Args:
        danh_sach_truyen (dict): Dữ liệu cần lưu.
        {'ten-truyen-1': {}, 'ten-truyen-2': {},...}
        file_path (str): Đường dẫn file json cần lưu.
        'data_json/data_list/danh_sach_truyen.json'

    Returns:
        str: Trạng thái lưu file.
        'OK' hoặc 'NG'

    """
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(danh_sach_truyen, f, ensure_ascii=False, indent=4)
        # print(Fore.GREEN + "Lưu file json thành công.")
        log_with_color("Lưu file json thành công.", Fore.GREEN)
        return "OK"
    except IOError as e:
        # print(Fore.RED + f"Có lỗi khi lưu file json: {e}")
        log_with_color(f"Có lỗi khi lưu file json: {e}", Fore.RED)
        return "NG"


# Đọc file json
def read_json(file_path):
    """
    Đọc dữ liệu từ file JSON.

    Args:
        file_path (str): Đường dẫn file JSON cần đọc.
        'data_json/data_list/danh_sach_truyen.json'

        Returns:
        dict: Dữ liệu từ file JSON.
        {'ten-truyen-1': {}, 'ten-truyen-2':,...}

    """
    path = Path(file_path)
    try:
        if path.is_file() == True:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            # print(Fore.GREEN + "Đọc file json thành công.")
            log_with_color("Đọc file json thành công.", Fore.GREEN)
            return data  # Trả về dữ liệu đọc được
        else:
            # print(Fore.RED + f"File {file_path} không tồn tại.")
            # log_with_color(f"File {file_path} không tồn tại.", Fore.RED)
            # return None
            pass
    except IOError as e:
        # print(Fore.RED + f"Có lỗi khi đọc file: {e}")
        log_with_color(f"Có lỗi khi đọc file: {e}", Fore.RED)
        return None


def get_max_page(the_loai_str):
    # Đọc dữ liệu từ file JSON
    danh_sach_truyen_json = os.path.join(settings.BASE_DIR, 'data_json', 'data_the_loai', 'the-loai-paginations.json')
    danh_sach_truyen = read_json(danh_sach_truyen_json)
    # Lấy số trang tối đa
    max_page = danh_sach_truyen[the_loai_str]
    # Kiểm tra max_page có phải số nguyên không
    if isinstance(max_page, int):
        return max_page
    else:
        # print(Fore.RED + "Dữ liệu không phải số nguyên.")
        log_with_color("Dữ liệu không phải số nguyên.", Fore.RED)
        return 1