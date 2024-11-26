import re

import requests
from bs4 import BeautifulSoup


CRAWL_URL = 'https://truyenfull.io'
story_name = "chien-than-do-luc"
response = requests.get(f'{CRAWL_URL}/{story_name}/')
response.raise_for_status()  # Kiểm tra lỗi kết nối
print(response.status_code)
print(response.text)
soup = BeautifulSoup(response.text, 'html.parser')
pagination = soup.find('ul', class_='pagination')
# print(pagination)
# Regex để tìm số x trong định dạng "chuong-x"
pattern = rf'{CRAWL_URL}/{story_name}/chuong-(\d+)'
pattern2 = rf'{CRAWL_URL}/{story_name}/quyen-(\d+)-chuong-(\d+)'
numbers = []
page_numbers = []
if pagination is not None:
    # Tìm tất cả các thẻ li bên trong ul, rồi lặp qua từng thẻ li để tìm thẻ a có nội dung "Cuối"
    link_cuoi = None
    for li in pagination.find_all('li'):
        a_tag = li.find('a')
        if a_tag and "Cuối" in a_tag.get_text():
            link_cuoi = a_tag['href']
            print(link_cuoi)
            break  # Dừng lại nếu đã tìm thấy
    if link_cuoi is None:
        for li in pagination.find_all('li'):
            a_tag = li.find('a')
            if a_tag:
                # Check neu text cua the a la so
                if a_tag.get_text().isnumeric():
                    page_numbers.append(int(a_tag.get_text()))
        # Lay so lon nhat trong numbers
        last_page = max(page_numbers)
        link_cuoi = f'{CRAWL_URL}/{story_name}/trang-{last_page}/#list-chapter'
        print(link_cuoi)

    # Gửi request đến link đã tìm được
    response = requests.get(link_cuoi)
    response.raise_for_status()  # Kiểm tra lỗi kết nối

    # Phân tích HTML bằng BeautifulSoup
    so_chuong_soup = BeautifulSoup(response.text, 'html.parser')

    # Duyệt qua từng thẻ <a> và lấy số x
    for link in so_chuong_soup.find_all('a', href=True):
        match = re.search(pattern, link['href'])
        if match:
            number = int(match.group(1))  # Lấy số x và chuyển thành integer
            numbers.append(number)
        else:
            match = re.search(pattern2, link['href'])
            if match:
                print(link['href'])
                pattern3 = r'chuong-(\d+)'
                match3 = re.search(pattern3, link['href'])
                number = int(match3.group(1))
                numbers.append(number)

else:
    for link in soup.find_all('a', href=True):
        match = re.search(pattern, link['href'])
        if match:
            number = int(match.group(1))  # Lấy số x và chuyển thành integer
            numbers.append(number)
        else:
            match = re.search(pattern2, link['href'])
            if match:
                pattern3 = r'chuong-(\d+)'
                match3 = re.search(pattern3, link['href'])
                number = int(match3.group(1))
                numbers.append(number)
so_chuong = max(numbers) if numbers else 0
print(numbers)
print(so_chuong)