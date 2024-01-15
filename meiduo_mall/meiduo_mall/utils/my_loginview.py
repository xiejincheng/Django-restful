from django.contrib.auth.mixins import LoginRequiredMixin
from django.views import View


class LoginRequiredView(LoginRequiredMixin,View):
    login_url = '/login/' #未登录跳转的页面
    redirect_field_name = 'redirect_to' #记录从哪个页面来的(忽略)