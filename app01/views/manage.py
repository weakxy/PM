from django.shortcuts import redirect, render, HttpResponse


def statistics(request, project_id):
    return render(request, 'statistics.html')



