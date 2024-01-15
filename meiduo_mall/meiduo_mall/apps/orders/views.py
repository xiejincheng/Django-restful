from django.core.paginator import Paginator
from django.shortcuts import render
from meiduo_mall.utils.my_loginview import LoginRequiredView
from meiduo_mall.utils.response_code import RET
from users.models import Address
from django_redis import get_redis_connection
from goods.models import SKU
from decimal import Decimal
import json
from django import http
from .models import OrderInfo,OrderGoods
from django.utils import timezone
import random
from decimal import Decimal
from django.db import transaction
from orders.models import OrderInfo
from django.views import View


#1,获取订单结算页
class OrderSettlement(LoginRequiredView):
    def get(self,request):

        #1, 获取用户收货地址
        addresses = Address.objects.filter(user_id=request.user.id,is_deleted=False).all()

        #2, 获取用户选中购物车的数据
        redis_conn = get_redis_connection("carts")
        cart_dict = redis_conn.hgetall("carts_%s" % request.user.id)
        sku_ids = redis_conn.smembers("selected_%s"%request.user.id)
        sku_list = []

        total_count = 0 #总数量
        total_amount = Decimal(0.0)#总金额
        for sku_id in sku_ids:
            sku = SKU.objects.get(id=sku_id)
            sku_dict = {
                "id":sku.id,
                "default_image_url":sku.default_image_url.url,
                "name":sku.name,
                "price":str(sku.price),
                "count":int(cart_dict[sku_id]),
                "amount":str(int(cart_dict[sku_id]) * sku.price)
            }
            sku_list.append(sku_dict)

            #累加
            total_count += int(cart_dict[sku_id])
            total_amount += (int(cart_dict[sku_id]) * sku.price)

        #运费和实付款
        freight = Decimal(10)
        payment_amount = total_amount + freight


        #携带数据,渲染页面
        context = {
            "addresses":addresses,
            "sku_list":sku_list,
            "total_count":total_count,
            "total_amount":total_amount,
            "freight":freight,
            "payment_amount":payment_amount
        }
        return render(request,'place_order.html',context=context)

#2,订单提交
class OrderCommitView(LoginRequiredView):
    @transaction.atomic
    def post(self,request):
        #1,获取参数
        data_dict = json.loads(request.body.decode())
        address_id = data_dict.get("address_id")
        pay_method = data_dict.get("pay_method")

        #2,校验参数
        #2,1 为空校验
        if not all([address_id,pay_method]):
            return http.JsonResponse({"code":RET.PARAMERR,"errmsg":"参数有误"})

        #2,2 判断地址是否存在
        try:
            address = Address.objects.get(id=address_id)
        except Exception as e:
            return http.JsonResponse({"code": RET.DBERR, "errmsg": "地址不存在"})

        #2,3 判断是否方式是否合法
        pay_method = int(pay_method)
        if pay_method not in [OrderInfo.PAY_METHODS_ENUM["CASH"],OrderInfo.PAY_METHODS_ENUM["ALIPAY"]]:
            return http.JsonResponse({"code": RET.DATAERR, "errmsg": "支付方式有误"})

        #3,订单信息表入库
        #3,1 生成订单编号(原则:尽量保证order_id的唯一性#)
        order_id = timezone.now().strftime("%Y%m%d%H%M%S") + "%09d%d"%(random.randint(0,999999999),request.user.id) #时间戳 + 随机字符串9 + 用户id

        #3,2 判断订单状态
        if pay_method == OrderInfo.PAY_METHODS_ENUM["CASH"]:
            status = OrderInfo.ORDER_STATUS_ENUM["UNPAID"]
        else:
            status = OrderInfo.ORDER_STATUS_ENUM["UNSEND"]

        #TODO 设置保存点
        sid = transaction.savepoint()

        order_info = OrderInfo.objects.create(
            order_id=order_id,
            user=request.user,
            address=address,
            total_count=0,
            total_amount=Decimal(0.0),
            freight=Decimal(10),
            pay_method=pay_method,
            status=status
        )

        #4,订单商品入库
        redis_conn = get_redis_connection("carts")
        cart_dict = redis_conn.hgetall("carts_%s"%request.user.id)
        sku_ids = redis_conn.smembers("selected_%s"%request.user.id)

        for sku_id in sku_ids:
            while True:
                #4,1 获取sku,count
                sku = SKU.objects.get(id=sku_id)
                count = int(cart_dict[sku_id])

                #4,2 库存判断
                if count > sku.stock:
                    #TODO 回滚
                    transaction.savepoint_rollback(sid)
                    return http.JsonResponse({"code":RET.DATAERR,"errmsg":"库存不足"})

                #TODO 模拟并发下单
                # import time
                # time.sleep(5)

                #TODO 解决并发下单
                old_stock = sku.stock
                old_sales = sku.sales
                new_stock = old_stock - count
                new_sales = old_sales + count

                #调用update返回的结果是整数,表示影响的行数
                ret = SKU.objects.filter(id=sku_id,stock=old_stock).update(stock=new_stock,sales=new_sales)

                if ret == 0:
                    # transaction.savepoint_rollback(sid)
                    # return http.JsonResponse({"code": RET.DBERR, "errmsg": "库存修改失败"})
                    continue

                #4,3 库存减少,销量增加
                # sku.stock -= count
                # sku.sales += count
                # sku.save()

                #4,4 创建订单商品对象
                OrderGoods.objects.create(
                    order=order_info,
                    sku=sku,
                    count=count,
                    price=sku.price,
                )

                #4,4 累加订单信息表
                order_info.total_count += count
                order_info.total_amount += (count * sku.price)

                #跳出
                break

        #5,保存订单信息表
        order_info.save()
        transaction.savepoint_commit(sid) #TODO 提交保存点(事务)

        #6,清除购物车中已经付过款的数据
        redis_conn.hdel("carts_%s"%request.user.id,*sku_ids)
        redis_conn.srem("selected_%s"%request.user.id,*sku_ids)

        #7,返回响应
        return http.JsonResponse({"code":RET.OK,"order_id":order_id})

#3,订单成功
class OrderSuccessView(LoginRequiredView):
    def get(self,request):
        #1,获取参数
        order_id = request.GET.get("order_id")
        payment_amount = request.GET.get("payment_amount")
        pay_method = request.GET.get("pay_method")

        #2,校验参数
        #2,1 为空校验
        if not all([order_id,payment_amount,pay_method]):
            return http.HttpResponseForbidden("参数不全")

        #2,2 订单是否存在
        try:
            order = OrderInfo.objects.get(order_id=order_id)
        except Exception as e:
            return http.HttpResponseForbidden('订单不存在')

        #2,3 支付方式是否正确
        if pay_method not in ["1","2"]:
            return http.HttpResponseForbidden("支付方式有误")

        #3,渲染页面
        context = {
            "order_id":order_id,
            "payment_amount":payment_amount,
            "pay_method":pay_method
        }
        return render(request,'order_success.html',context=context)

#4,订单展示
class OrderInfoView(LoginRequiredView):
    def get(self,request,page_num):

        #1,获取用户订单数据
        orders = OrderInfo.objects.filter(user=request.user).order_by("-create_time").all()

        #2,处理支付方式,订单状态
        for order in orders:
            order.pay_method = OrderInfo.PAY_METHOD_CHOICES[order.pay_method-1][1]
            order.status = OrderInfo.ORDER_STATUS_CHOICES[order.status-1][1]

        #3,订单数据分页
        paginate = Paginator(object_list=orders,per_page=3)
        page = paginate.page(page_num)
        orders_list = page.object_list #当前页对象列表
        current_page = page.number #当前页面
        total_page = paginate.num_pages #总页数

        #拼接数据
        context = {
            "orders":orders_list,
            "current_page":current_page,
            "total_page":total_page
        }
        return render(request,'user_center_order.html',context=context)

#5,订单评价
class OrdersCommentView(LoginRequiredView):
    def get(self,request):

        #1,获取参数
        order_id = request.GET.get("order_id")

        #2,校验参数
        try:
            order_info = OrderInfo.objects.get(order_id=order_id)
            order_goods = order_info.skus.all()
        except Exception as e:
            return render(request,'404.html')

        #3,拼接数据
        sku_list = []
        for order_good in order_goods:
            sku_dict = {
                "default_image_url":order_good.sku.default_image_url.url,
                "name":order_good.sku.name,
                "price":str(order_good.price),
                "order_id":order_id,
                "sku_id":order_good.sku_id
            }
            sku_list.append(sku_dict)

        #4,渲染页面,携带数据
        return render(request,'goods_judge.html',context={"skus":sku_list})

    def post(self,request):
        #1,获取参数
        dict_data = json.loads(request.body.decode())
        order_id = dict_data.get("order_id")
        sku_id = dict_data.get("sku_id")
        score = dict_data.get("score")
        is_anonymous = dict_data.get("is_anonymous")
        comment = dict_data.get("comment")

        #2,校验参数
        #2,1 判断订单是否存在
        try:
            order_info = OrderInfo.objects.get(order_id=order_id)
        except Exception as e:
            return http.JsonResponse({"code":RET.DBERR,"errmsg":"订单不存在"})

        #2,2 判断商品order_good是否存在
        try:
            order_good = OrderGoods.objects.get(order_id=order_id,sku_id=sku_id)
        except Exception as e:
            return http.JsonResponse({"code":RET.DBERR,"errmsg":"商品不存在"})

        #2,3 判断分数合理性
        if score < 0 or score > 5:
            return http.JsonResponse({"code":RET.DATAERR,"errmsg":"分数不合理"})

        #2,4 判断匿名评价是否bool类型
        if not isinstance(is_anonymous,bool):
            return http.JsonResponse({"code":RET.DATAERR,"errmsg":"匿名评价数据有误"})

        #3,写入评价相关数据
        try:
            order_good.comment = comment
            order_good.score = score
            order_good.is_anonymous = is_anonymous
            order_good.is_commented = True
            order_good.save()

            #增加评价数量
            order_good.sku.comments += 1
            order_good.sku.save()
            order_good.sku.spu.comments += 1
            order_good.sku.spu.save()

            #修改订单状态
            order_info.status = OrderInfo.ORDER_STATUS_ENUM["FINISHED"]
            order_info.save()
        except Exception as e:
            return http.JsonResponse({"code":RET.DBERR,"errmsg":"评价数量设置失败"})

        #4,返回响应
        return http.JsonResponse({"code":RET.OK,"errmsg":"评价成功"})

#6,获取评价信息
class SKUCommentView(View):
    def get(self,request,sku_id):

        #1,判断该商品是否存在,查询该商品的评价信息
        try:
            order_goods = OrderGoods.objects.filter(sku_id=sku_id,is_commented=True).order_by("-create_time").all()
        except Exception as e:
            return http.JsonResponse({"code":RET.DBERR,"errmsg":"商品订单不存在"})

        #3,数据拼接
        comment_list = []
        for order_good in order_goods:
            comment_dict = {
                "username":order_good.order.user.username,
                "content":order_good.comment
            }
            comment_list.append(comment_dict)

        #4,返回响应
        return http.JsonResponse({"code":RET.OK,"goods_comment_list":comment_list})