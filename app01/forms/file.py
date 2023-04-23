from django import forms
from django.core.exceptions import ValidationError
from app01 import models
from app01.utils.bootstrap import BootStrapModelForm


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
