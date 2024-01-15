from django.contrib.auth import logout
from django.shortcuts import render,redirect
from django.views import View
from goods.models import GoodsChannel
from contents.models import ContentCategory
from meiduo_mall.utils.my_category import get_categories

#1, 展示首页
class IndexView(View):
    def get(self,request):

        #1,获取分类数据
        categories = get_categories()

        #4,查询广告分类
        content_categories = ContentCategory.objects.order_by("id").all()
        contents = {}
        for content_category in content_categories:
            contents[content_category.key] = content_category.content_set.all()

        #5, 返回数据,渲染页面
        context = {
            "categories":categories,
            "contents":contents
        }
        return render(request,'index.html',context=context)

#2, 退出登录
class LogoutView(View):
    def get(self,request):
        #1, 清除session
        logout(request)

        #2, 清除cookie
        response = redirect("/")
        response.delete_cookie("username")
        return response

#3, 获取网站logo
class LoGoView(View):
    def get(self,request):

        return redirect("/static/favicon.ico")