import time
from django.shortcuts import redirect, render, HttpResponse
from django.urls import reverse
from django.http import JsonResponse
from django.views.decorators.clickjacking import xframe_options_sameorigin
from django.views.decorators.csrf import csrf_exempt
from app01.forms.wiki import WikiModelForm
from app01 import models
from app01.utils.cos import upload_file


def wiki(request, project_id):
    """ wiki首页 """
    wiki_id = request.GET.get('wiki_id')
    if not wiki_id or not wiki_id.isdecimal():
        return render(request, 'wiki.html')

    wiki_object = models.Wiki.objects.filter(id=wiki_id, project_id=project_id).first()
    return render(request, 'wiki.html', {'wiki_object': wiki_object})


def wiki_add(request, project_id):
    """ wiki添加 """
    if request.method == 'GET':
        form = WikiModelForm(request)
        return render(request, 'wiki_form.html', {'form': form})
    form = WikiModelForm(request, data=request.POST)
    if form.is_valid():
        # 判断是否有父
        if form.instance.parent:
            form.instance.depth = form.instance.parent.depth + 1
        else:
            form.instance.depth = 1
        form.instance.project = request.tracer.project
        form.save()
        url = reverse('wiki', kwargs={'project_id': project_id})
        return redirect(url)
    return render(request, 'wiki_form.html', {'form': form})


def wiki_catalog(request, project_id):
    """ wiki目录 """
    data = models.Wiki.objects.filter(project=request.tracer.project).values("id", "title", "parent_id").order_by(
        'depth', 'id')
    return JsonResponse({'status': True, 'data': list(data)})


def wiki_delete(request, project_id, wiki_id):
    """ wiki删除 """
    models.Wiki.objects.filter(project_id=project_id, id=wiki_id).delete()
    url = reverse('wiki', kwargs={'project_id': project_id})
    return redirect(url)


def wiki_edit(request, project_id, wiki_id):
    """ wiki编辑 """
    wiki_object = models.Wiki.objects.filter(project_id=project_id, id=wiki_id).first()
    if not wiki_object:
        url = reverse('wiki', kwargs={'project_id': project_id})
        return redirect(url)
    if request.method == "GET":
        form = WikiModelForm(request, instance=wiki_object)
        return render(request, 'wiki_form.html', {'form': form})
    form = WikiModelForm(request, data=request.POST, instance=wiki_object)
    if form.is_valid():
        if form.instance.parent:
            form.instance.depth = form.instance.parent.depth + 1
        else:
            form.instance.depth = 1
        form.instance.project = request.tracer.project
        form.save()
        url = reverse('wiki', kwargs={'project_id': project_id})
        preview_url = "{0}?wiki_id={1}".format(url, wiki_id)
        return redirect(preview_url)
    return render(request, 'wiki.html', {'form': form})


@csrf_exempt
@xframe_options_sameorigin
def wiki_upload(request, project_id):
    """ markdown上传图片 """
    result = {
        'success': 0,
        'message': None,
        'url': None
    }
    image_object = request.FILES.get('editormd-image-file', None)
    if not image_object:
        result['message'] = "文件不存在"
        return JsonResponse(result)
    ext = image_object.name.rsplit('.')[-1]
    key = "{}.{}".format(str(time.strftime('%Y%m%d%H%M%S', time.localtime(time.time()))), ext)
    image_url = upload_file(
        request.tracer.project.bucket,
        request.tracer.project.region,
        image_object,
        key
    )
    result['success'] = 1
    result['url'] = image_url
    return JsonResponse(result)
