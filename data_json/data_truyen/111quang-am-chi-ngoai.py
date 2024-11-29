import json

# Đọc nội dung từ file JSON
with open('quang-am-chi-ngoai.json', 'r', encoding='utf-8') as file:
    data = json.load(file)

# Sửa tên chương
for chapter in data:
    # Tìm vị trí dấu ":" thứ hai
    parts = chapter["ten_chuong"].split(": ", 2)
    if len(parts) == 3:
        # Ghép lại chỉ với dấu ":" đầu tiên
        chapter["ten_chuong"] = f"{parts[0]}: {parts[2]}"

# Ghi lại nội dung đã sửa vào file JSON
with open('quang-am-chi-ngoai.json', 'w', encoding='utf-8') as file:
    json.dump(data, file, ensure_ascii=False, indent=4)

print("Đã sửa tên chương trong file JSON.")
