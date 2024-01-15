from alipay import AliPay
from django.shortcuts import render
from meiduo_mall.utils.my_loginview import LoginRequiredView
from django import http
from meiduo_mall.utils.response_code import RET
from django.conf import settings
from orders.models import OrderInfo
from pays.models import Payment

#1,获取支付页面
class PaymentView(LoginRequiredView):
    def get(self,request,order_id):

        #0,获取订单
        try:
            order = OrderInfo.objects.get(order_id=order_id)
        except Exception as e:
            return http.HttpResponseForbidden('该订单不存在')

        #1,创建公钥,私钥字符串
        app_private_key_string = open(settings.APP_PRIVATE_KEY).read()
        alipay_public_key_string = open(settings.ALIPAY_PUBLIC_KEY).read()

        #2,创建alipay对象
        alipay = AliPay(
            appid=settings.ALIPAY_APPID,
            app_notify_url=settings.ALIPAY_RETURN_URL,  # 默认回调url
            app_private_key_string=app_private_key_string,
            # 支付宝的公钥，验证支付宝回传消息使用，不是你自己的公钥,
            alipay_public_key_string=alipay_public_key_string,
            sign_type="RSA2",  # RSA 或者 RSA2
            debug = settings.ALIPAY_DEBUG  # 默认False
        )

        #3,创建订单字符串
        subject = "测试订单"
        order_string = alipay.api_alipay_trade_page_pay(
            out_trade_no=order_id,
            total_amount=str(order.total_amount + order.freight),
            subject=subject,
            return_url=settings.ALIPAY_RETURN_URL
        )

        #4,生成支付链接
        alipay_url = settings.ALIPAY_URL + "?" + order_string

        return http.JsonResponse({"code":RET.OK,"alipay_url":alipay_url})

#2,支付结果保存
class PaymentStatusView(LoginRequiredView):
    def get(self,request):
        #1,获取参数,request.GET查询字典,request.GET.dict()普通字典
        data_dict = request.GET.dict()
        signature = data_dict.pop("sign")
        out_trade_no = data_dict.get("out_trade_no")
        trade_no = data_dict.get("trade_no")

        # 2,创建alipay对象
        app_private_key_string = open(settings.APP_PRIVATE_KEY).read()
        alipay_public_key_string = open(settings.ALIPAY_PUBLIC_KEY).read()
        alipay = AliPay(
            appid=settings.ALIPAY_APPID,
            app_notify_url=settings.ALIPAY_RETURN_URL,  # 默认回调url
            app_private_key_string=app_private_key_string,
            # 支付宝的公钥，验证支付宝回传消息使用，不是你自己的公钥,
            alipay_public_key_string=alipay_public_key_string,
            sign_type="RSA2",  # RSA 或者 RSA2
            debug=settings.ALIPAY_DEBUG  # 默认False
        )

        #3,校验signature正确性
        success = alipay.verify(data_dict, signature)
        if success:
            #3,1 创建支付结果对象,保存数据
            Payment.objects.create(out_trade_no=out_trade_no,trade_no=trade_no)

            #3,2 改变订单状态
            OrderInfo.objects.filter(order_id=out_trade_no).update(status=OrderInfo.ORDER_STATUS_ENUM["UNCOMMENT"])

            #3,3 渲染页面
            return render(request,'pay_success.html',context={"order_id":out_trade_no})
        else:
            return http.HttpResponseForbidden("支付结果被篡改")