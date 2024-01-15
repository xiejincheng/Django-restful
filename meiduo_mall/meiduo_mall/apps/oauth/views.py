from django.contrib.auth import login
from django.shortcuts import render, redirect
from django.views import View
from QQLoginTool.QQtool import OAuthQQ
from django.conf import  settings
from django import http

from carts.utils import merge_cookie_redis_data
from meiduo_mall.utils import constants
from meiduo_mall.utils.my_encrypt import encode_openid, decode_openid
from oauth.models import QQUserModel
import re
from django_redis import get_redis_connection
from users.models import User

#1, qq登录页面
class QQLoginView(View):
    def get(self,request):
        #1, 获取参数
        next = request.GET.get("next","/")

        #2, 创建OAuthQQ对象
        oauth = OAuthQQ(client_id=settings.QQ_CLIENT_ID, client_secret=settings.QQ_CLIENT_SECRET,
                        redirect_uri=settings.QQ_REDIRECT_URI, state=next)

        #3, 获取qq登录页面
        login_url = oauth.get_qq_url()

        #4, 返回响应
        return http.JsonResponse({"login_url":login_url})

#2, openid处理
class OpenIDView(View):
    def get(self,request):
        #1,获取code
        code = request.GET.get("code")

        if not code:
            return http.HttpResponseForbidden("code丢失")

        #2,换取access_token
        oauth = OAuthQQ(client_id=settings.QQ_CLIENT_ID, client_secret=settings.QQ_CLIENT_SECRET,
                        redirect_uri=settings.QQ_REDIRECT_URI, state=next)
        access_token = oauth.get_access_token(code)

        if not access_token:
            return http.HttpResponseForbidden("access_token丢失")

        #3,换取openid
        openid = oauth.get_open_id(access_token)

        #4,通过openid查询数据库中是否存在qq用户
        try:
            qq_user = QQUserModel.objects.get(openid=openid)
        except Exception as e:
            #5, 初次授权
            #5,1 加密openid
            token = encode_openid(openid)

            #5,2 渲染页面
            return render(request,'oauth_callback.html',context={"token":token})
        else:
            #6,非初次授权
            #6,1 状态保持
            user = qq_user.user
            login(request,user)

            #6,2 重定向到首页
            response =  redirect("/")
            response.set_cookie("username",user.username,max_age=constants.REDIS_SESSION_COOKIE_EXPIRES)
            response = merge_cookie_redis_data(request,response)#合并购物车
            return response

    def post(self,request):
        #1,获取参数
        access_token = request.POST.get("access_token")
        mobile = request.POST.get("mobile")
        pwd = request.POST.get("pwd")
        sms_code = request.POST.get("sms_code")

        #2,校验参数
        #2,1 为空校验
        if not all([access_token,mobile,pwd,sms_code]):
            return http.HttpResponseForbidden("参数不全")

        #2,2 校验access_token正确性
        openid = decode_openid(access_token)

        if not openid:
            return http.HttpResponseForbidden("openid失效")

        #2,3 手机号格式校验
        if not re.match(r'^1[3-9]\d{9}$',mobile):
            return http.HttpResponseForbidden("手机号格式有误")

        #2,4 短信验证码正确性校验
        redis_conn = get_redis_connection("code")
        redis_sms_code = redis_conn.get("sms_code_%s"%mobile)

        if not redis_sms_code:
            return http.HttpResponseForbidden("短信验证码已过期")

        if sms_code != redis_sms_code.decode():
            return http.HttpResponseForbidden("短信验证码错误")

        #3,数据入库
        try:
            user = User.objects.get(mobile=mobile)
        except Exception as e:
            #4,1 美多用户不存在, 创建美多用户
            user = User.objects.create_user(username=mobile,password=pwd,mobile=mobile)

            #4,2 绑定美多用户和qq用户
            QQUserModel.objects.create(user=user,openid=openid)

            #4,3 状态保持
            login(request,user)

            #4,3 返回响应
            response = redirect("/")
            response.set_cookie("username",user.username,max_age=constants.REDIS_SESSION_COOKIE_EXPIRES)
            response = merge_cookie_redis_data(request, response)#合并购物车
            return response
        else:
            #5.0 校验密码
            if not user.check_password(pwd):
                return http.HttpResponseForbidden("密码不对")

            #5,1 绑定
            QQUserModel.objects.create(user=user, openid=openid)

            #5,2 状态保持
            login(request, user)

            #5,3 返回响应
            response = redirect("/")
            response.set_cookie("username",user.username,max_age=constants.REDIS_SESSION_COOKIE_EXPIRES)
            response = merge_cookie_redis_data(request, response)#合并购物车
            return response

