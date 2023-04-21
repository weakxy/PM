from django import forms
from app01 import models
from app01.utils.bootstrap import BootStrapModelForm


class WikiModelForm(BootStrapModelForm):
    class Meta:
        model = models.Wiki
        exclude = ['project', 'depth', ]

    def __init__(self, request, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # 找到想要的字段并重置
        total_data_list = [("", "请选择")]
        data_list = models.Wiki.objects.filter(project=request.tracer.project).values_list('id', 'title')
        total_data_list.extend(data_list)
        self.fields['parent'].choices = total_data_list
