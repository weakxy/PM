import json
import requests
from django.shortcuts import redirect, render, HttpResponse
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.urls import reverse
from app01.forms.file import FolderModelForm, FileModelForm
from app01 import models
from app01.utils.cos import delete_file, delete_file_list, credential


def file(request, project_id):
    """ 新建文件夹 """
    parent_object = None
    folder_id = request.GET.get('folder', "")
    if folder_id.isdecimal():
        parent_object = models.FileRepository.objects.filter(id=int(folder_id), file_type=2,
                                                             project=request.tracer.project).first()

    if request.method == "GET":
        # 导航条
        breadcrumb_list = []
        parent = parent_object
        while parent:
            breadcrumb_list.insert(0, {'id': parent.id, 'name': parent.name})
            parent = parent.parent

        # 获取当前文件夹下所有文件和文件夹
        queryset = models.FileRepository.objects.filter(project=request.tracer.project)
        if parent_object:
            file_object_list = queryset.filter(parent=parent_object).order_by('-file_type')
        else:
            file_object_list = queryset.filter(parent__isnull=True).order_by('-file_type')

        form = FolderModelForm(request, parent_object)
        context = {
            'form': form,
            'file_object_list': file_object_list,
            'breadcrumb_list': breadcrumb_list,
            'folder_object': parent_object,
        }
        return render(request, 'file.html', context)

    # 添加文件夹 & 修改文件夹
    fid = request.POST.get('fid', '')
    edit_object = None
    if fid.isdecimal():
        edit_object = models.FileRepository.objects.filter(id=int(fid), file_type=2,
                                                           project=request.tracer.project).first()
    if edit_object:
        form = FolderModelForm(request, parent_object, data=request.POST, instance=edit_object)
    else:
        form = FolderModelForm(request, parent_object, data=request.POST)

    if form.is_valid():
        form.instance.project = request.tracer.project
        form.instance.file_type = 2
        form.instance.update_user = request.tracer.user
        form.instance.parent = parent_object
        form.save()
        return JsonResponse({'status': True})
    return JsonResponse({'status': False, 'error': form.errors})


def file_delete(request, project_id):
    """ 删除文件 """
    fid = request.GET.get('fid')
    delete_object = models.FileRepository.objects.filter(id=fid, project=request.tracer.project).first()
    if delete_object.file_type == 1:
        # 删除文件
        # 返还空间
        request.tracer.project.use_space -= delete_object.file_size
        request.tracer.project.save()
        # 在COS中删除
        delete_file(request.tracer.project.bucket, request.tracer.project.region, delete_object.key)
        # 在数据库中删除
        delete_object.delete()
        return JsonResponse({'status': True})

    # 删除文件夹
    total_size = 0
    key_list = []
    folder_list = [delete_object, ]

    for folder in folder_list:
        child_list = models.FileRepository.objects.filter(project=request.tracer.project, parent=folder).order_by(
            "-file_type")
        for child in child_list:
            if child.file_type == 2:
                folder_list.append(child)
            else:
                total_size += child.file_size
                key_list.append({"Key": child.key})

    # 批量删除文件夹中的文件
    if key_list:
        delete_file_list(request.tracer.project.bucket, request.tracer.project.region, key_list)

    if total_size:
        request.tracer.project.use_space -= total_size
        request.tracer.project.save()
    delete_object.delete()
    return JsonResponse({"status": True})


@csrf_exempt
def cos_credential(request, project_id):
    """ 获取cos临时凭证 """
    total_size = 0
    per_file_limit = request.tracer.price_policy.project_size * 1024 * 1024
    file_list = json.loads(request.body.decode('utf-8'))
    for item in file_list:
        if item['size'] > per_file_limit:
            msg = "文件{}大小超出限制(最大{}M)".format(item['name'], request.tracer.price_policy.project_size)
            return JsonResponse({'status': False, 'error': msg})
        total_size += item['size']

    if request.tracer.project.use_space + total_size > request.tracer.price_policy.project_space * 1024 * 1024 * 1024:
        return JsonResponse({'status': False, 'error': "容量超过限制,请升级套餐"})

    data_dict = credential(request.tracer.project.bucket, request.tracer.project.region)
    return JsonResponse({'status': True, 'data': data_dict})


@csrf_exempt
def file_post(request, project_id):
    """ 将文件写入数据库
    name: fileName,
    key: key,
    size: fileSize,
    parent: CURRENT_FOLDER_ID,
    etag: data.ETag,
    file_path: data.Location,
    """
    form = FileModelForm(request, data=request.POST)
    if form.is_valid():
        # 通过ModelForm.save存储到数据库中返回的instance对象无法使用get_xx_display获取choice的中文
        # form.instance.file_type = 1
        # form.instance.update_user = request.tracer.user
        # instance = form.save()
        data_dict = form.cleaned_data
        data_dict.pop('etag')
        data_dict.update({
            'project': request.tracer.project,
            'file_type': 1,
            'update_user': request.tracer.user
        })
        instance = models.FileRepository.objects.create(**data_dict)

        # 项目已使用空间更新
        request.tracer.project.use_space += data_dict['file_size']
        request.tracer.project.save()

        result = {
            'id': instance.id,
            'name': instance.name,
            'file_size': instance.file_size,
            'username': instance.update_user.name,
            'datetime': instance.update_datetime.strftime("%Y年%m月%d日 %H:%M"),
            'download_url': reverse('file_download', kwargs={'project_id': project_id, 'file_id': instance.id})
            # 'file_type': instance.get_file_type_display(),
        }
        return JsonResponse({'status': True, 'data': result})

    return JsonResponse({'status': False, 'data': "文件错误"})


def file_download(request, project_id, file_id):
    """ 下载文件 """
    file_object = models.FileRepository.objects.filter(id=file_id, project_id=project_id).first()
    res = requests.get(file_object.file_path)
    data = res.content

    response = HttpResponse(data, content_type="application/octet-stream")

    response['Content-Disposition'] = "attachment; filename={}".format(file_object.name)
    return response
