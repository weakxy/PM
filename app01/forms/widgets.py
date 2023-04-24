from django.forms import RadioSelect


class ColorRadioSelect(RadioSelect):
    """ 自定义ModelForm关于颜色的选项插件 """
    template_name = "widgets/color_radio/radio.html"
    option_template_name = "widgets/color_radio/radio_option.html"
