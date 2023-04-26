import datetime
import time
import collections
from django.shortcuts import render
from django.db.models import Count
from django.http import JsonResponse
from app01 import models


def dashboard(request, project_id):
    """ 问题概览 """
    # 问题处理
    status_dict = {}
    for key, text in models.Issues.status_choices:
        status_dict[key] = {"text": text, "count": 0}
    issues_data = models.Issues.objects.filter(project_id=project_id).values('status').annotate(ct=Count('id'))
    for item in issues_data:
        status_dict[item['status']]['count'] = item['ct']

    # 成员处理
    user_list = models.ProjectUser.objects.filter(project_id=project_id).values_list('user_id', 'user__name')

    # 发表问题处理
    top_ten = models.Issues.objects.filter(project_id=project_id, assign__isnull=False).order_by('-id')[0:10]

    context = {
        'status_dict': status_dict,
        'user_list': user_list,
        'top_ten_object': top_ten,
    }

    return render(request, 'dashboard.html', context)


def issues_chart(request, project_id):
    """ 生成highcharts数据 """

    # 最近30天每天创建的问题数量
    today = datetime.datetime.now().date()
    date_dict = collections.OrderedDict()
    for i in range(0, 30):
        date = today - datetime.timedelta(days=i)
        date_dict[date.strftime("%Y-%m-%d")] = [time.mktime(date.timetuple()) * 1000, 0]
    # result = models.Issues.objects.filter(project_id=project_id,
    #                                       create_datetime__gte=today - datetime.timedelta(days=30)).extra(
    #     select={'ctime': "strftime('%%Y-%%m-%%d',app01_issues.create_datetime)"}).values('ctime').annotate(
    #     ct=Count('id'))

    for item in models.Issues.objects.filter(project_id=project_id,
                                             create_datetime__gte=today - datetime.timedelta(days=30))\
            .values_list('create_datetime'):
        each_date = item[0].strftime("%Y-%m-%d")
        date_dict[each_date][1] += 1

    return JsonResponse({'status': True, 'data': list(date_dict.values())})
