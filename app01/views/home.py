import os.path
import uuid
import json
import datetime
from io import BytesIO

from django.shortcuts import render, redirect, HttpResponse
from django import forms
from django.conf import settings
from django.core.validators import RegexValidator
from django.core.exceptions import ValidationError
from django.db.models import Q
from django_redis import get_redis_connection

from app01 import models
from app01.utils.bootstrap import BootStrapModelForm, BootStrapForm
from app01.utils.code import check_code
from app01.utils.encrypt import md5, uid
from app01.utils.alipay import AliPay


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


def price(request):
    """ vip套餐页面 """
    policy_list = models.PricePolicy.objects.filter(category=2)
    return render(request, 'price.html', {'policy_list': policy_list})


def payment(request, policy_id):
    """ 支付页面 """
    policy_object = models.PricePolicy.objects.filter(id=policy_id, category=2).first()
    if not policy_object:
        return redirect('price')
    number = request.GET.get('number', "")
    if not number.isdecimal():
        return redirect('price')
    number = int(number)
    if number < 1:
        return redirect('price')
    # 验证通过，计算原价
    origin_price = number * policy_object.price
    # 计算实际价钱
    balance = 0
    _object = None
    if request.tracer.price_policy.category == 2:
        _object = models.Transaction.objects.filter(user=request.tracer.user, status=2).order_by('-id').first()
        total_timedelta = _object.end_datetime - _object.start_datetime
        balance_timedelta = _object.end_datetime - datetime.datetime.now()
        if total_timedelta.days == balance_timedelta.days:
            balance = _object.price / total_timedelta.days * (balance_timedelta.days - 1)
        else:
            balance = _object.price / total_timedelta.days * balance_timedelta.days
    if balance >= origin_price:
        return redirect('price')
    context = {
        'policy_id': policy_object.id,
        'number': number,
        'origin_price': origin_price,
        'balance': round(balance, 2),
        'total_price': origin_price - round(balance, 2),
    }
    conn = get_redis_connection()
    key = 'payment_{}'.format(request.tracer.user.mobile)
    conn.set(key, json.dumps(context), ex=60 * 30)

    context['policy_object'] = policy_object
    context['transaction'] = _object
    return render(request, 'payment.html', context)


def pay(request):
    """ 生成订单 """
    conn = get_redis_connection()
    key = 'payment_{}'.format(request.tracer.user.mobile)
    context_string = conn.get(key)
    if not context_string:
        return redirect('price')
    context = json.loads(context_string.decode('utf-8'))
    # 生成订单（数据库）
    order_id = uid(request.tracer.user.mobile)
    total_price = context['total_price']
    models.Transaction.objects.create(
        status=1,
        order=order_id,
        user=request.tracer.user,
        price_policy_id=context['policy_id'],
        count=context['number'],
        price=total_price,
    )
    # 跳转支付宝(生成链接)
    # params = {
    #     'app_id': "2021000122685118",
    #     'method': 'alipay.trade.page.pay',
    #     'format': 'JSON',
    #     'return_url': "http://127.0.0.1:8001/pay/notify/",
    #     'notify_url': "http://127.0.0.1:8001/pay/notify/",
    #     'charset': 'utf-8',
    #     'sign_type': 'RSA2',
    #     'timestamp': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    #     'version': '1.0',
    #     'biz_content': json.dumps({
    #         'out_trade_no': order_id,
    #         'product_code': 'FAST_INSTANT_TRADE_PAY',
    #         'total_amount': total_price,
    #         'subject': "tracer payment"
    #     }, separators=(',', ':'))
    # }
    #
    # # 获取待签名的字符串
    # unsigned_string = "&".join(["{0}={1}".format(k, params[k]) for k in sorted(params)])
    # from Crypto.PublicKey import RSA
    # from Crypto.Signature import PKCS1_v1_5
    # from Crypto.Hash import SHA256
    # from base64 import decodebytes, encodebytes
    #
    # private_key = RSA.importKey(open("app01/files/支付宝沙盒应用私钥.txt").read())
    # signer = PKCS1_v1_5.new(private_key)
    # signature = signer.sign(SHA256.new(unsigned_string.encode('utf-8')))
    #
    # # 对签名之后的执行进行base64 编码，转换为字符串
    # sign_string = encodebytes(signature).decode("utf8").replace('\n', '')
    #
    # # 把生成的签名赋值给sign参数，拼接到请求参数中。
    #
    # from urllib.parse import quote_plus
    # result = "&".join(["{0}={1}".format(k, quote_plus(params[k])) for k in sorted(params)])
    # result = result + "&sign=" + quote_plus(sign_string)
    #
    # gateway = "https://openapi.alipaydev.com/gateway.do"
    # ali_pay_url = "{}?{}".format(gateway, result)
    # return redirect(ali_pay_url)
    ali_pay = AliPay(
        appid=settings.ALI_APPID,
        app_notify_url=settings.ALI_NOTIFY_URL,
        return_url=settings.ALI_RETURN_URL,
        app_private_key_path=settings.ALI_PRI_KEY_PATH,
        alipay_public_key_path=settings.ALI_PUB_KEY_PATH
    )
    query_params = ali_pay.direct_pay(
        subject="trace payment",  # 商品简单描述
        out_trade_no=order_id,  # 商户订单号
        total_amount=total_price
    )
    pay_url = "{}?{}".format(settings.ALI_GATEWAY, query_params)
    return redirect(pay_url)


def pay_notify(request):
    ali_pay = AliPay(
        appid=settings.ALI_APPID,
        app_notify_url=settings.ALI_NOTIFY_URL,
        return_url=settings.ALI_RETURN_URL,
        app_private_key_path=settings.ALI_PRI_KEY_PATH,
        alipay_public_key_path=settings.ALI_PUB_KEY_PATH
    )

    if request.method == 'GET':
        # 只做跳转，判断是否支付成功了，不做订单的状态更新。
        # 支付吧会讲订单号返回：获取订单ID，然后根据订单ID做状态更新 + 认证。
        # 支付宝公钥对支付给我返回的数据request.GET 进行检查，通过则表示这是支付宝返还的接口。
        params = request.GET.dict()
        # print(params)
        sign = params.pop('sign', None)
        # print(1)
        # print(sign)
        # print(2)
        status = ali_pay.verify(params, sign)
        if status:
            return HttpResponse('支付完成')
        return HttpResponse('支付失败')
    else:
        from urllib.parse import parse_qs
        body_str = request.body.decode('utf-8')
        post_data = parse_qs(body_str)
        post_dict = {}
        for k, v in post_data.items():
            post_dict[k] = v[0]

        sign = post_dict.pop('sign', None)
        status = ali_pay.verify(post_dict, sign)
        if status:
            current_datetime = datetime.datetime.now()
            out_trade_no = post_dict['out_trade_no']
            _object = models.Transaction.objects.filter(order=out_trade_no).first()

            _object.status = 2
            _object.start_datetime = current_datetime
            _object.end_datetime = current_datetime + datetime.timedelta(days=365 * _object.count)
            _object.save()
            return HttpResponse('success')

        return HttpResponse('error')


def orm(request):
    models.User.objects.all().delete()
    return HttpResponse("删除成功")
