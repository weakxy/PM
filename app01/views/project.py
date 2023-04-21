import time
from django.shortcuts import render, redirect, HttpResponse
from django.http import JsonResponse
from app01.forms.project import ProjectModelForm
from app01.utils.cos import create_bucket
from app01 import models


def project_list(request):
    # 项目总览
    if request.method == 'GET':
        project_dict = {'star': [], 'my': [], 'join': []}
        my_project_list = models.Project.objects.filter(creator=request.tracer.user)
        for row in my_project_list:
            if row.star:
                project_dict['star'].append({"value": row, 'type': 'my'})
            else:
                project_dict['my'].append(row)
        join_project_list = models.ProjectUser.objects.filter(user=request.tracer.user)
        for row in join_project_list:
            if row.star:
                project_dict['star'].append({"value": row.project, 'type': 'join'})
            else:
                project_dict['join'].append(row.project)

        form = ProjectModelForm(request)
        return render(request, 'project_list.html', {'form': form, 'project_dict': project_dict})
    form = ProjectModelForm(request, data=request.POST)
    if form.is_valid():
        # 创建COS桶
        bucket = "{}{}-1317188553".format(request.tracer.user.mobile,
                                          str(time.strftime('%Y%m%d%H%M%S', time.localtime(time.time()))))
        print(bucket)
        region = "ap-nanjing"
        create_bucket(bucket, region)

        form.instance.bucket = bucket
        form.instance.region = region
        form.instance.creator = request.tracer.user
        form.save()
        return JsonResponse({'status': True})
    return JsonResponse({'status': False, 'error': form.errors})


def project_star(request, project_type, project_id):
    # 收藏项目
    if project_type == 'my':
        models.Project.objects.filter(id=project_id, creator=request.tracer.user).update(star=True)
        return redirect('/pm/project/list/')
    if project_type == 'join':
        models.ProjectUser.objects.filter(project_id=project_id, user=request.tracer.user).update(star=True)
        return redirect('/pm/project/list/')

    return HttpResponse("错误")


def project_unstar(request, project_type, project_id):
    # 取消收藏项目
    if project_type == 'my':
        models.Project.objects.filter(id=project_id, creator=request.tracer.user).update(star=False)
        return redirect('/pm/project/list/')
    if project_type == 'join':
        models.ProjectUser.objects.filter(project_id=project_id, user=request.tracer.user).update(star=False)
        return redirect('/pm/project/list/')

    return HttpResponse("错误")
