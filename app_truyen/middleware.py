from app_truyen.models import URLViewCount
from django.db.utils import IntegrityError

class ViewCountMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Chỉ đếm lượt truy cập GET
        if request.method == "GET":
            path = request.path
            try:
                # Tìm hoặc tạo bản ghi tương ứng với URL
                obj, created = URLViewCount.objects.get_or_create(path=path)
                obj.count += 1
                obj.save()
            except IntegrityError:
                pass  # Xử lý lỗi nếu cần

        response = self.get_response(request)
        return response
