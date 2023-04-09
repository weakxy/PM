from django.db import models


# Create your models here.
class User(models.Model):
    name = models.CharField(verbose_name="用户名", max_length=32)
    password = models.CharField(verbose_name="密码", max_length=64)
    mobile = models.CharField(verbose_name="手机号", max_length=11)
    email = models.EmailField(verbose_name="邮箱", max_length=32)
    gender_choices = (
        (1, "男"),
        (2, "女"),
    )
    gender = models.SmallIntegerField(verbose_name="性别", choices=gender_choices)
    img = models.FileField(verbose_name="头像", max_length=128, null=True, blank=True, upload_to='user/')
