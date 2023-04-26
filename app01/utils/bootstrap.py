from django import forms

"""
不推荐
    因为这样的继承会增加模块的耦合度
    可以使用依赖反转
"""


class BootStrap:
    bootstrap_exclude_fields = []

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, filed in self.fields.items():
            if name in self.bootstrap_exclude_fields:
                continue

            if filed.widget.attrs:
                filed.widget.attrs["class"] = "{} form-control".format(filed.widget.attrs.get('class', ""))
                filed.widget.attrs["placeholder"] = filed.label
            else:
                filed.widget.attrs = {
                    "class": "form-control",
                    "placeholder": filed.label,
                }


class BootStrapModelForm(BootStrap, forms.ModelForm):
    pass


class BootStrapForm(BootStrap, forms.Form):
    pass
