from django.utils.deprecation import MiddlewareMixin
from django.shortcuts import redirect


class AuthMiddleware(MiddlewareMixin):

    def process_request(self, request):

        if request.path_info in ["/pm/home1/", "/image/code/", "/pm/add/"]:
            return

        info_dict = request.session.get("info")
        if info_dict:
            return

        return redirect("/pm/home1/")
