import datetime
from django.utils.deprecation import MiddlewareMixin
from django.shortcuts import redirect
from django.conf import settings
from app01 import models


class Tracer(object):
    def __init__(self):
        self.user = None
        self.price_policy = None
        self.project = None


class AuthMiddleware(MiddlewareMixin):

    def process_request(self, request):
        request.tracer = Tracer()

        if request.path_info in ["/pm/home1/", "/image/code/", "/pm/add/"]:
            return

        info_dict = request.session.get("info")

        if not info_dict:
            return redirect("/pm/home1/")

        user_object = models.User.objects.filter(id=info_dict['id']).first()
        request.tracer.user = user_object

        # 登录之后获取额度（去最近交易的额度）
        _object = models.Transaction.objects.filter(user=user_object, status=2).order_by('-id').first()
        # # # # 判断是否额度已过期
        current_datetime = datetime.datetime.now()
        if _object.end_datetime and _object.end_datetime < current_datetime:
            _object = models.Transaction.objects.filter(user=user_object, status=2, price_policy__category=1).first()

        request.tracer.price_policy = _object.price_policy

    def process_view(self, request, view, args, kwargs):
        if not request.path_info.startswith('/manage/'):
            return

        project_id = kwargs.get('project_id')
        project_object = models.Project.objects.filter(creator=request.tracer.user, id=project_id).first()
        if project_object:
            request.tracer.project = project_object
            return

        project_user_object = models.ProjectUser.objects.filter(user=request.tracer.user, project_id=project_id).first()
        if project_user_object:
            request.tracer.project = project_user_object.project
            return

        return redirect('project_list')
