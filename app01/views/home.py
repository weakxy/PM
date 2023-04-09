import os.path

from django.shortcuts import render, redirect, HttpResponse
from django import forms
from django.conf import settings
from io import BytesIO
from django.core.exceptions import ValidationError

from app01 import models
from app01.utils.bootstrap import BootStrapModelForm, BootStrapForm
from app01.utils.code import check_code
from app01.utils.encrypt import md5


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
        label="手机号",
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

        user_admin = models.User.objects.filter(**form.cleaned_data).first()
        if not user_admin:
            form.add_error("password", "用户名或密码错误")
            return render(request, 'home_not_log_in.html', {'form': form})
        # print(user_admin.id,user_admin.mobile)

        request.session["info"] = {"id": user_admin.id, "mobile": user_admin.mobile, "name": user_admin.name}
        request.session.set_expiry(60 * 60 * 24 * 7)

        return redirect('/pm/home2/')

    return render(request, 'home_not_log_in.html', {'form': form})


def home_show2(request):
    info = request.session.get("info")
    print(info)
    if not info:
        return redirect('/pm/home1/')
    if request.method == "GET":
        form = LoginForm()
        return render(request, 'home_log_in.html', {"form": form})


class AdminModelForm(BootStrapModelForm):
    confirm_password = forms.CharField(label="确认密码", widget=forms.PasswordInput(render_value=True))
    bootstrap_exclude_fields = ['img']

    class Meta:
        model = models.User
        fields = "__all__"
        widgets = {
            "password": forms.PasswordInput(render_value=True),
        }

    def clean_password(self):
        pwd = self.cleaned_data.get("password")
        return md5(pwd)

    def clean_confirm_password(self):
        pwd = self.cleaned_data.get("password")
        confirm = md5(self.cleaned_data.get("confirm_password"))
        if confirm != pwd:
            raise ValidationError("密码不一致, 请重新输入")
        return confirm


def home_add(request):
    if request.method == "GET":
        form = AdminModelForm()
        return render(request, 'change.html', {"form": form})

    form = AdminModelForm(data=request.POST, files=request.FILES)
    if form.is_valid():
        print(form.cleaned_data)
        form.save()
        # user_admin = models.User.objects.filter(**form.cleaned_data).first()
        # request.session["info"] = {"id": user_admin.id, "mobile": user_admin.mobile}
        # request.session.set_expiry(60 * 60 * 24 * 7)

        # return redirect('/pm/home2/')

    return render(request, 'change.html', {"form": form})


def home_logout(request):
    """ 注销登录 """
    request.session.clear()

    return redirect("/login/")


def orm(request):
    models.User.objects.all().delete()
    return HttpResponse("删除成功")
