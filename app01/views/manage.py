from django.shortcuts import redirect, render, HttpResponse


def dashboard(request, project_id):
    return render(request, 'dashboard.html')


def statistics(request, project_id):
    return render(request, 'statistics.html')



