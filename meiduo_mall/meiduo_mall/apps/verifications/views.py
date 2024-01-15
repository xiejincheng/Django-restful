from django.shortcuts import render
from django.views import View
from meiduo_mall.libs.captcha.captcha import captcha
from django import http
from django_redis import get_redis_connection
import re
import random
from meiduo_mall.libs.yuntongxun.sms import CCP
from meiduo_mall.utils import constants
from meiduo_mall.utils.response_code import RET

#1,获取图片验证码
class ImageCodeView(View):
    def get(self,request,uuid):

        #1, 获取图片验证码, 图片
        _,text,image_data = captcha.generate_captcha()

        #2, 存储图片验证码的值到redis中
        redis_conn = get_redis_connection("code")
        redis_conn.set("image_code_%s" % uuid, text, constants.REDIS_IMAGE_CODE_EXPIRES)

        #3,返回响应
        return http.HttpResponse(image_data,content_type="image/png")

#2,获取短信验证码
class SMSCodeView(View):
    def get(self,request,mobile):
        #1,获取参数
        image_code = request.GET.get("image_code")
        image_code_id = request.GET.get("image_code_id")

        #1,1 判断标记是否过期
        redis_conn = get_redis_connection("code")
        pipeline = redis_conn.pipeline()
        send_flag = redis_conn.get("send_flag_%s"%mobile)
        if send_flag:
            return http.JsonResponse({"code": RET.DBERR, "errmsg": "短信频繁发送"},status=400)

        #2,校验参数
        #2,1 为空检验
        if not all([image_code,image_code_id]):
            return http.JsonResponse({"code":RET.PARAMERR,"errmsg":"参数不全"})

        #2,1 手机号格式
        if not re.match(r'^1[3-9]\d{9}$',mobile):
            return http.JsonResponse({"code": RET.DATAERR,"errmsg":"手机号格式有误"})

        #2,2 图片验证码正确性
        redis_image_code = redis_conn.get("image_code_%s"%image_code_id)

        if not redis_image_code:
            return http.JsonResponse({"code": RET.DATAERR, "errmsg": "图片验证码已过期"})

        if image_code.upper() != redis_image_code.decode().upper():
            return http.JsonResponse({"code": RET.DATAERR, "errmsg": "图片验证码错误"})

        #3,发送短信,数据入库
        sms_code = "%06d"%random.randint(0,constants.SMS_CODE_MAX)
        print("sms_code = %s"%sms_code)

        #使用celery发送短信
        from celery_tasks.sms.tasks import send_message
        send_message.delay(mobile,sms_code)

        #模拟短信发送耗时
        # import time
        # time.sleep(10)

        # result = CCP().send_template_sms(mobile, [sms_code, 5], 1)
        #
        # #3,1 判断是否发送成功
        # if result == -1:
        #     return http.JsonResponse({"code": 4001, "errmsg": "短信发送失败"})

        # 3,2 保存短信验证码到redis,方便之后判断短信的正确性
        pipeline.set("sms_code_%s"%mobile,sms_code,constants.REDIS_SMS_CODE_EXPIRES)

        #3,1 设置标记,防止1分钟之内, 短信多次发送
        pipeline.set("send_flag_%s"%mobile,1,constants.REDIS_SEND_FLAG_EXPIRES)

        #3,2 提交pipeline
        pipeline.execute()

        #4,返回响应
        return http.JsonResponse({"code":RET.OK})