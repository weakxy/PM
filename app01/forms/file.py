from django import forms
from django.core.exceptions import ValidationError
from app01 import models
from app01.utils.bootstrap import BootStrapModelForm
from app01.utils.cos import check_file


class FolderModelForm(BootStrapModelForm):
    class Meta:
        model = models.FileRepository
        fields = ['name']

    def __init__(self, request, parent_object, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.request = request
        self.parent_object = parent_object

    def clean_name(self):
        name = self.cleaned_data['name']

        if self.parent_object:
            exits = models.FileRepository.objects.filter(file_type=2, name=name, project=self.request.tracer.project,
                                                         parent=self.parent_object).exists()
        else:
            exits = models.FileRepository.objects.filter(file_type=2, name=name, project=self.request.tracer.project,
                                                         parent__isnull=True).exists()
        if exits:
            raise ValidationError('文件夹已存在')
        return name


class FileModelForm(forms.ModelForm):
    etag = forms.CharField(label='ETag')

    class Meta:
        model = models.FileRepository
        exclude = ['project', 'file_type', 'update_user', 'update_datetime']

    def __init__(self, request, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.request = request

    def clean_file_path(self):
        return "https://{}".format(self.cleaned_data['file_path'])

    """ 效验数据是否安全（防止恶意向数据库传送数据） """
    # def clean(self):
    #     etag = self.cleaned_data['etag']
    #     key = self.cleaned_data['key']
    #     size = self.cleaned_data['file_size']
    #     if not etag or not key:
    #         return self.cleaned_data
    #
    #     # 向COS效验文件是否合法
    #     from qcloud_cos.cos_exception import CosServiceError
    #     try:
    #         result = check_file(self.request.tracer.project.bucket, self.request.tracer.project.region, key)
    #     except CosServiceError as e:
    #         self.add_error('key', '文件不存在')
    #         return self.cleaned_data
    #
    #     cos_etag = result.get('ETag')
    #     if etag != cos_etag:
    #         self.add_error('etag', 'ETag错误')
    #
    #     cos_length = result.get('Content-Length')
    #     if int(cos_length) != size:
    #         self.add_error('file_size', '文件大小错误')
    #
    #     return self.cleaned_data
