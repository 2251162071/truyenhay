import json

# Đọc file JSON
with open('than-cap-dai-diem-truong.json', 'r', encoding='utf-8') as file:
    data = json.load(file)

# In ra dữ liệu
print(data[0])