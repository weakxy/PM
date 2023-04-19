import os.path
import datetime
from io import BytesIO

from django.shortcuts import render, redirect, HttpResponse
from django import forms
from django.conf import settings
from django.core.validators import RegexValidator
from django.core.exceptions import ValidationError
from django.db.models import Q

from app01 import models
from app01.utils.bootstrap import BootStrapModelForm, BootStrapForm
from app01.utils.code import check_code
from app01.utils.encrypt import md5

import uuid


def image_code(request):
    """ 生成图片验证码 """

    img, code_string = check_code()
    # 存入session中
    request.session['image_code'] = code_string
    # 设置60s超时
    request.session.set_expiry(60)

    stream = BytesIO()
    img.save(stream, 'png')

    return HttpResponse(stream.getvalue())


class LoginForm(BootStrapForm):
    mobile = forms.CharField(
        label="请输入邮箱或者手机号",
        widget=forms.TextInput,
        required=True,
    )
    password = forms.CharField(
        label="密码",
        widget=forms.PasswordInput(render_value=True),
        required=True,
    )
    code = forms.CharField(
        label="验证码",
        widget=forms.TextInput,
        required=True,
    )

    def clean_password(self):
        pwd = self.cleaned_data.get("password")
        return md5(pwd)


def home_show1(request):
    if request.method == "GET":
        form = LoginForm()
        return render(request, 'home_not_log_in.html', {"form": form})

    form = LoginForm(data=request.POST)
    if form.is_valid():
        user_input_code = form.cleaned_data.pop('code')
        code = request.session.get('image_code', "")
        if code.upper() != user_input_code.upper():
            form.add_error("code", "验证码错误")
            return render(request, 'home_not_log_in.html', {'form': form})

        information = form.cleaned_data['mobile']
        password = form.cleaned_data['password']
        user_admin = models.User.objects.filter(Q(email=information) | Q(mobile=information)).filter(
            password=password).first()
        if not user_admin:
            form.add_error("password", "手机号/邮箱或密码错误")
            return render(request, 'home_not_log_in.html', {'form': form})
        # print(user_admin.id,user_admin.mobile)

        request.session["info"] = {"id": user_admin.id, "mobile": user_admin.mobile, "name": user_admin.name}
        request.session.set_expiry(60 * 60 * 24 * 7)

        return redirect('/pm/home2/')

    return render(request, 'home_not_log_in.html', {'form': form})


def home_show2(request):
    info = request.session.get("info")
    if not info:
        return redirect('/pm/home1/')
    if request.method == "GET":
        form = LoginForm()
        return render(request, 'home_log_in.html', {"form": form})


class AdminModelForm(BootStrapModelForm):
    confirm_password = forms.CharField(label="确认密码", widget=forms.PasswordInput(render_value=True))
    mobile = forms.CharField(label="手机号",
                             validators=[RegexValidator(r'^(1[3|4|5|6|7|8|9])\d{9}$', '手机号格式错误')])
    bootstrap_exclude_fields = ['img']

    class Meta:
        model = models.User
        fields = ['name', 'password', 'confirm_password', 'mobile', 'email', 'gender', 'img']
        widgets = {
            "password": forms.PasswordInput(render_value=True),
        }

    # clean_ + 定义的password、mobile、confirm_password 为django内部自己就执行了
    def clean_password(self):
        pwd = self.cleaned_data.get("password")
        return md5(pwd)

    def clean_name(self):
        """ 用户名效验的钩子 """
        name = self.cleaned_data['name']

        # 效验用户名是否存在
        exits = models.User.objects.filter(name=name).exists()
        if exits:
            raise ValidationError("用户名已存在")
        return name

    def clean_mobile(self):
        """ 手机号效验的钩子 """
        mobile = self.cleaned_data['mobile']

        # 效验手机号是否存在
        exits = models.User.objects.filter(mobile=mobile).exists()
        if exits:
            raise ValidationError("手机号已存在")
        return mobile

    def clean_email(self):
        """ 邮箱效验的钩子 """
        email = self.cleaned_data['email']

        # 效验邮箱是否存在
        exits = models.User.objects.filter(email=email).exists()
        if exits:
            raise ValidationError("邮箱已存在")
        return email

    def clean_confirm_password(self):
        """ 判断两次输入密码是否一致的钩子 """
        pwd = self.cleaned_data.get("password")
        confirm = md5(self.cleaned_data.get("confirm_password"))
        if confirm != pwd:
            raise ValidationError("密码不一致, 请重新输入")
        return confirm


def home_add(request):
    """ 注册用户 """
    if request.method == "GET":
        form = AdminModelForm()
        return render(request, 'change.html', {"form": form})

    form = AdminModelForm(data=request.POST, files=request.FILES)

    if form.is_valid():
        cname = form.cleaned_data['name']
        instance = form.save()

        policy_object = models.PricePolicy.objects.filter(category=1, title='个人免费版').first()
        models.Transaction.objects.create(
            status=2,
            order=str(uuid.uuid4()),
            user=instance,
            price_policy=policy_object,
            count=0,
            price=0,
            start_datetime=datetime.datetime.now()
        )
        user_admin = models.User.objects.filter(name=cname).first()
        request.session["info"] = {"id": user_admin.id, "mobile": user_admin.mobile, "name": user_admin.name}
        request.session.set_expiry(60 * 60 * 24 * 7)

        return redirect('/pm/home2/')

    return render(request, 'change.html', {"form": form})


def home_logout(request):
    """ 注销登录 """
    request.session.clear()

    return redirect("/pm/home1/")


def orm(request):
    models.User.objects.all().delete()
    return HttpResponse("删除成功")
