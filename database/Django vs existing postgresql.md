# Kết nối Django mới với Database PostgreSQL đã tồn tại

## 1. Cài đặt PostgreSQL Driver cho Django
Django cần driver để kết nối PostgreSQL. Cài đặt gói `psycopg2`:
```bash
pip install psycopg2
```

# Hướng dẫn kết nối Django mới với Database PostgreSQL đã tồn tại

## 2. Cấu hình Database trong `settings.py`
Mở file `settings.py` của Django và cập nhật phần `DATABASES` với thông tin của database PostgreSQL:

```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'your_database_name',      # Tên database
        'USER': 'your_username',           # Tên user PostgreSQL
        'PASSWORD': 'your_password',       # Mật khẩu của user
        'HOST': 'localhost',               # Địa chỉ host của PostgreSQL (mặc định là localhost)
        'PORT': '5432',                    # Cổng PostgreSQL (mặc định là 5432)
    }
}
```


## 3. Kiểm tra kết nối

Để kiểm tra xem Django có thể kết nối với database PostgreSQL hay không, thực hiện các bước sau:

1. Chạy lệnh sau trong terminal:
   ```bash
   python manage.py dbshell
    ```
## 4. Mapping các bảng đã tồn tại vào Django Models

Django có thể tự động tạo các models dựa trên cấu trúc các bảng đã tồn tại trong database PostgreSQL. Làm theo các bước sau:

### Bước 1: Sử dụng lệnh `inspectdb`
Chạy lệnh sau để tạo file models từ các bảng hiện có trong database:
```bash
python manage.py inspectdb > models.py
```

## 5. Tạo app mới để quản lý models

Nếu bạn chưa có app trong Django để quản lý các models, hãy làm theo các bước sau:

### Bước 1: Tạo app mới
Sử dụng lệnh sau để tạo một app mới trong dự án Django:
```bash
python manage.py startapp myapp
```


## 6. Tạo các file migration (nếu cần)

Migrations trong Django được sử dụng để quản lý các thay đổi trong cấu trúc database. Nếu bạn muốn Django tự động quản lý hoặc cập nhật schema của database hiện tại, bạn cần tạo các file migration.

---

### Bước 1: Tạo migration
Chạy lệnh sau để tạo file migration cho các models trong app:
```bash
python manage.py makemigrations
```

## 7. Sử dụng database trong Django

Khi bạn đã kết nối Django với database PostgreSQL và cấu hình models, bạn có thể sử dụng database thông qua Django ORM để truy vấn, thêm, sửa, và xóa dữ liệu.

---

### Bước 1: Import models
Để sử dụng bảng trong database, bạn cần import các models vào file Python mà bạn đang làm việc, ví dụ như `views.py`, `shell`, hoặc `tasks.py`:
```python
from app_truyen.models import Story
```

## 8. Kiểm tra ứng dụng

Sau khi đã cấu hình xong database và models, bạn cần kiểm tra xem ứng dụng Django hoạt động như mong đợi hay không.

---

### Bước 1: Chạy server
Sử dụng lệnh sau để khởi động server phát triển của Django:
```bash
python manage.py runserver

