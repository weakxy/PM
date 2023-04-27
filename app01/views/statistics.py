import collections
from django.shortcuts import redirect, render, HttpResponse
from django.http import JsonResponse
from django.db.models import Count
from app01 import models


def statistics(request, project_id):
    """ 显示列表 """
    return render(request, 'statistics.html')


def statistics_priority(request, project_id):
    """ 优先级显示饼图 """
    start = request.GET.get('start')
    end = request.GET.get('end')

    data_dict = collections.OrderedDict()
    for key, text in models.Issues.priority_choices:
        data_dict[key] = {'name': text, 'y': 0}
    result = models.Issues.objects.filter(project_id=project_id, create_datetime__gte=start,
                                          create_datetime__lt=end).values('priority').annotate(ct=Count('id'))

    for item in result:
        data_dict[item['priority']]['y'] = item['ct']
    return JsonResponse({'status': True, 'data': list(data_dict.values())})


def statistics_project_user(request, project_id):
    """ 柱状图（问题类型配比） """
    # 所有项目成员
    all_user_dict = collections.OrderedDict()
    all_user_dict[request.tracer.project.creator.id] = {
        'name': request.tracer.project.creator.name,
        'status': {item[0]: 0 for item in models.Issues.status_choices}
    }
    all_user_dict[None] = {
        'name': '未指派',
        'status': {item[0]: 0 for item in models.Issues.status_choices}
    }
    user_list = models.ProjectUser.objects.filter(project_id=project_id)
    for item in user_list:
        all_user_dict[item.user_id] = {
            'name': item.user.username,
            'status': {item[0]: 0 for item in models.Issues.status_choices}
        }
    # 所有问题
    start = request.GET.get('start')
    end = request.GET.get('end')
    issues = models.Issues.objects.filter(project_id=project_id, create_datetime__gte=start, create_datetime__lt=end)
    for item in issues:
        if not item.assign:
            all_user_dict[None]['status'][item.status] += 1
        else:
            all_user_dict[item.assign_id]['status'][item.status] += 1

    # 获取所有成员
    categories = [data['name'] for data in all_user_dict.values()]

    # 最后传参
    data_result_dict = collections.OrderedDict()
    for item in models.Issues.status_choices:
        data_result_dict[item[0]] = {'name': item[1], "data": []}

    for key, text in models.Issues.status_choices:
        for row in all_user_dict.values():
            count = row['status'][key]
            data_result_dict[key]['data'].append(count)

    context = {
        'status': True,
        'data': {
            'categories': categories,
            'series': list(data_result_dict.values())
        }
    }

    return JsonResponse(context)
