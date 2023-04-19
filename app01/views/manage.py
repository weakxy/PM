from django.shortcuts import redirect, render, HttpResponse


def dashboard(request, project_id):
    return render(request, 'dashboard.html')


def issues(request, project_id):
    return render(request, 'issues.html')


def statistics(request, project_id):
    return render(request, 'statistics.html')


def file(request, project_id):
    return render(request, 'file.html')


def wiki(request, project_id):
    return render(request, 'wiki.html')


def setting(request, project_id):
    return render(request, 'setting.html')
