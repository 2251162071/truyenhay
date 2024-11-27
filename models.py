# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from django.db import models


class AppTruyenChapter(models.Model):
    id = models.BigAutoField(primary_key=True)
    title = models.CharField(max_length=255)
    content = models.TextField()
    chapter_number = models.IntegerField()
    views = models.IntegerField()
    updated_at = models.DateTimeField()
    story = models.ForeignKey('AppTruyenStory', models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'app_truyen_chapter'


class AppTruyenGenre(models.Model):
    id = models.BigAutoField(primary_key=True)
    name = models.CharField(unique=True, max_length=50)
    name_full = models.CharField(max_length=50)
    page_count = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'app_truyen_genre'


class AppTruyenHotstory(models.Model):
    id = models.BigAutoField(primary_key=True)
    added_at = models.DateTimeField()
    story = models.ForeignKey('AppTruyenStory', models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'app_truyen_hotstory'


class AppTruyenNewupdatedstory(models.Model):
    id = models.BigAutoField(primary_key=True)
    added_at = models.DateTimeField()
    story = models.ForeignKey('AppTruyenStory', models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'app_truyen_newupdatedstory'


class AppTruyenStory(models.Model):
    id = models.BigAutoField(primary_key=True)
    title = models.CharField(unique=True, max_length=255)
    author = models.CharField(max_length=255)
    status = models.CharField(max_length=50)
    views = models.IntegerField()
    updated_at = models.DateTimeField()
    description = models.TextField(blank=True, null=True)
    image = models.CharField(max_length=500, blank=True, null=True)
    title_full = models.CharField(max_length=255)
    rating = models.DecimalField(max_digits=4, decimal_places=2)
    chapter_number = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'app_truyen_story'


class AppTruyenStorygenre(models.Model):
    id = models.BigAutoField(primary_key=True)
    genre = models.ForeignKey(AppTruyenGenre, models.DO_NOTHING)
    story = models.ForeignKey(AppTruyenStory, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'app_truyen_storygenre'


class AppTruyenUserreading(models.Model):
    id = models.BigAutoField(primary_key=True)
    user_id = models.IntegerField()
    last_read_at = models.DateTimeField()
    last_chapter = models.ForeignKey(AppTruyenChapter, models.DO_NOTHING, blank=True, null=True)
    story = models.ForeignKey(AppTruyenStory, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'app_truyen_userreading'


class AuthGroup(models.Model):
    name = models.CharField(unique=True, max_length=80)

    class Meta:
        managed = False
        db_table = 'auth_group'


class AuthGroupPermissions(models.Model):
    id = models.BigAutoField(primary_key=True)
    group = models.ForeignKey(AuthGroup, models.DO_NOTHING)
    permission = models.ForeignKey('AuthPermission', models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'auth_group_permissions'
        unique_together = (('group', 'permission'),)


class AuthPermission(models.Model):
    name = models.CharField(max_length=50)
    content_type = models.ForeignKey('DjangoContentType', models.DO_NOTHING)
    codename = models.CharField(max_length=100)

    class Meta:
        managed = False
        db_table = 'auth_permission'
        unique_together = (('content_type', 'codename'),)


class AuthUser(models.Model):
    password = models.CharField(max_length=128)
    last_login = models.DateTimeField()
    is_superuser = models.BooleanField()
    username = models.CharField(unique=True, max_length=30)
    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=30)
    email = models.CharField(max_length=75)
    is_staff = models.BooleanField()
    is_active = models.BooleanField()
    date_joined = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'auth_user'


class AuthUserGroups(models.Model):
    id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(AuthUser, models.DO_NOTHING)
    group = models.ForeignKey(AuthGroup, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'auth_user_groups'
        unique_together = (('user', 'group'),)


class AuthUserUserPermissions(models.Model):
    id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(AuthUser, models.DO_NOTHING)
    permission = models.ForeignKey(AuthPermission, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'auth_user_user_permissions'
        unique_together = (('user', 'permission'),)


class DjangoAdminLog(models.Model):
    action_time = models.DateTimeField()
    object_id = models.TextField(blank=True, null=True)
    object_repr = models.CharField(max_length=200)
    action_flag = models.SmallIntegerField()
    change_message = models.TextField()
    content_type = models.ForeignKey('DjangoContentType', models.DO_NOTHING, blank=True, null=True)
    user = models.ForeignKey(AuthUser, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'django_admin_log'


class DjangoContentType(models.Model):
    name = models.CharField(max_length=100)
    app_label = models.CharField(max_length=100)
    model = models.CharField(max_length=100)

    class Meta:
        managed = False
        db_table = 'django_content_type'
        unique_together = (('app_label', 'model'),)


class DjangoMigrations(models.Model):
    id = models.BigAutoField(primary_key=True)
    app = models.CharField(max_length=255)
    name = models.CharField(max_length=255)
    applied = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'django_migrations'
