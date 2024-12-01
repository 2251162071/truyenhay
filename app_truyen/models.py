from decimal import Decimal
from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User
# Create your models here.

# Model Genre: Quản lý thông tin thể loại truyện
class Genre(models.Model):
    name_full = models.CharField(max_length=50, default="noname")  # Tên thể loại có dấu, mặc định là "noname"
    name = models.SlugField(max_length=50, unique=True, blank=False)  # Tên không dấu, URL-friendly
    page_count = models.IntegerField(default=0)  # Số trang, mặc định là 0

    def __str__(self):
        return self.name_full

class Story(models.Model):
    title = models.SlugField(max_length=255, unique=True, blank=True, primary_key=True)  # Tên không dấu, URL-friendly
    title_full = models.CharField(max_length=255, default="noname")  # Tên truyện có dấu, mặc định là "noname"
    author = models.CharField(max_length=255, default="unknown")  # Tác giả, mặc định là "unknown"
    status = models.CharField(max_length=50, default="Full")  # Trạng thái, mặc định là "Full"
    chapter_number = models.IntegerField(default=0)  # Thêm field chapter_number để lưu số chương của truyện
    genres = models.ManyToManyField(Genre, through='StoryGenre', related_name='stories')
    image = models.URLField(max_length=1000, null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    views = models.PositiveIntegerField(default=0)
    rating = models.DecimalField(max_digits=4, decimal_places=2, default=Decimal('0.00'))
    updated_at = models.DateTimeField(default=timezone.now)

    def save(self, *args, **kwargs):
        if self.pk and Story.objects.filter(pk=self.pk).exists() and not self.title:
            raise ValueError("Title cannot be changed after creation.")
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title_full

class StoryGenre(models.Model):
    story = models.ForeignKey(Story, to_field='title', on_delete=models.CASCADE)
    genre = models.ForeignKey(Genre, to_field='name', on_delete=models.CASCADE)

    class Meta:
        unique_together = ('story', 'genre')

class Chapter(models.Model):
    story_chapter = models.CharField(max_length=255, primary_key=True, editable=False)
    title = models.CharField(max_length=255, default="noname")  # Tiêu đề chương, mặc định là "noname"
    story = models.ForeignKey(Story, to_field='title', on_delete=models.CASCADE, related_name='chapters')
    content = models.TextField(default="")
    chapter_number = models.IntegerField(null=False, blank=False)
    views = models.PositiveIntegerField(default=0)
    updated_at = models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = ('story', 'chapter_number')

    def save(self, *args, **kwargs):
        # Tự động tạo giá trị cho story_chapter
        self.story_chapter = f"{self.story.title}_{self.chapter_number}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.story.title} - Chapter {self.chapter_number} - Title: {self.title[:20]}"

class UserReading(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    story = models.ForeignKey(Story, on_delete=models.CASCADE, related_name='user_readings')
    last_chapter = models.ForeignKey(Chapter, on_delete=models.SET_NULL, null=True, related_name='+')
    last_read_at = models.DateTimeField(default=timezone.now)

class HotStory(models.Model):
    story = models.ForeignKey(Story, on_delete=models.CASCADE)
    added_at = models.DateTimeField()

    class Meta:
        unique_together = ('story',)

class NewUpdatedStory(models.Model):
    story = models.ForeignKey(Story, on_delete=models.CASCADE)
    added_at = models.DateTimeField()

    class Meta:
        unique_together = ('story',)


class URLViewCount(models.Model):
    path = models.CharField(max_length=255, unique=True)  # Đường dẫn của URL
    count = models.PositiveIntegerField(default=0)  # Số lượt xem

    def __str__(self):
        return f"{self.path} - {self.count} views"



class Comment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    page_url = models.CharField(max_length=255)

    def __str__(self):
        username = self.user.username if self.user else 'Anonymous'
        return f"{username}: {self.content[:20]}"
