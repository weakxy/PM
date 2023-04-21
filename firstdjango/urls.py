"""firstdjango URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.utils import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.utils'))
"""
from django.contrib import admin
from django.urls import path, re_path, include
from django.views.static import serve
from django.conf import settings
from app01.views import home, project, manage, wiki

urlpatterns = [
    re_path(r'^media/(?P<path>.*)$', serve, {'document_root': settings.MEDIA_ROOT}, name='media'),
    # home1 为未登录时的主页, home2 为登录或注册过后的主页
    path('pm/home1/', home.home_show1),
    path('image/code/', home.image_code),
    path('pm/home2/', home.home_show2),

    # add为注册用户,logout为注销
    path('pm/add/', home.home_add),
    path('logout/', home.home_logout),

    path('orm/', home.orm),

    # 项目列表
    path('pm/project/list/', project.project_list, name='project_list'),
    path('pm/project/star/<str:project_type>/<int:project_id>/', project.project_star),
    path('pm/project/unstar/<str:project_type>/<int:project_id>/', project.project_unstar),

    # 项目管理
    path('manage/<int:project_id>/', include([
        path('dashboard/', manage.dashboard, name='dashboard'),
        path('issues/', manage.issues, name='issues'),
        path('statistics/', manage.statistics, name='statistics'),
        path('file/', manage.file, name='file'),
        path('wiki/', wiki.wiki, name='wiki'),
        path('wiki/add/', wiki.wiki_add, name='wiki_add'),
        path('wiki/catalog/', wiki.wiki_catalog, name='wiki_catalog'),
        path('wiki/delete/<int:wiki_id>/', wiki.wiki_delete, name='wiki_delete'),
        path('wiki/edit/<int:wiki_id>/', wiki.wiki_edit, name='wiki_edit'),
        path('setting/', manage.setting, name='setting'),
    ])),
]
