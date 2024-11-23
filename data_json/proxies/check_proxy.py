import json
import requests
from requests.exceptions import RequestException

def load_proxies(filename):
    """Đọc danh sách proxy từ file JSON."""
    with open(filename, 'r') as file:
        proxies_data = json.load(file)
    return proxies_data

def test_proxy(proxy):
    """Kiểm tra proxy bằng cách gửi yêu cầu đến httpbin.org/ip."""
    url = 'https://httpbin.org/ip'  # URL kiểm tra IP
    proxies = {
        'http': f"http://{proxy['username']}:{proxy['password']}@{proxy['host']}:{proxy['port']}",
        'https': f"https://{proxy['username']}:{proxy['password']}@{proxy['host']}:{proxy['port']}"
    }
    
    try:
        response = requests.get(url, proxies=proxies, timeout=10)
        response.raise_for_status()  # Kiểm tra lỗi HTTP
        print(f"Proxy {proxy['host']}:{proxy['port']} hoạt động! Địa chỉ IP trả về: {response.json()['origin']}")
        return True
    except RequestException as e:
        print(f"Proxy {proxy['host']}:{proxy['port']} không hoạt động. Lỗi: {e}")
        return False

# Đọc danh sách proxy từ file JSON
proxies_list = load_proxies('proxies.json')

# Kiểm tra tất cả proxy trong danh sách
for proxy in proxies_list:
    test_proxy(proxy)
