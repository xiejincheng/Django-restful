from django.shortcuts import render
from django.views import View
import json
from django import http
from meiduo_mall.utils.response_code import RET
from goods.models import SKU
from django_redis import get_redis_connection
import pickle,base64

#1,购物车处理
class CartsView(View):
    def post(self,request):
        #1,获取参数
        data_dict = json.loads(request.body.decode())
        sku_id = data_dict.get("sku_id")
        count = data_dict.get("count")

        #2,校验参数
        #2,1 为空校验
        if not all([sku_id,count]):
            return http.JsonResponse({"code":RET.PARAMERR,"errmsg":"参数不全"})

        #2,2 判断商品是否存在
        try:
            sku = SKU.objects.get(id=sku_id)
        except Exception as e:
            return http.JsonResponse({"code": RET.DBERR, "errmsg": "该商品不存在"})

        #2,3 判断count是否数值类型
        try:
            count = int(count)
        except Exception as e:
            return http.JsonResponse({"code": RET.DATAERR, "errmsg": "参数有误"})

        #2,4 库存是否足够
        if count > sku.stock:
            return http.JsonResponse({"code": RET.DATAERR, "errmsg": "库存不足"})

        #3,判断用户状态,添加购物车数据
        if request.user.is_authenticated:
            #3,1 获取redis对象
            redis_conn = get_redis_connection("carts")

            #3,2 保存数据到redis
            #获取redis原有数据
            redis_count = redis_conn.hget("carts_%s"%request.user.id,sku_id)

            #数据累加
            if redis_count:
                count += int(redis_count)

            #判断是否超过了5件商品
            if count > 5:
                redis_conn.hset("carts_%s"%request.user.id,sku_id,5)
            else:
                redis_conn.hset("carts_%s" % request.user.id, sku_id, count)

            redis_conn.sadd("selected_%s"%request.user.id,sku_id)

            #3, 返回响应
            return http.JsonResponse({"code":RET.OK})
        else:
            #4,1 获取cookie购物车数据
            cookie_cart = request.COOKIES.get("carts")

            #4,2 字符串数据转字典
            cookie_cart_cart = {}
            if cookie_cart:
                cookie_cart_cart = pickle.loads(base64.b64decode(cookie_cart.encode()))

            #4,4 修改购物车数据
            if sku_id in cookie_cart_cart:
                old_count = cookie_cart_cart[sku_id]["count"]
                count += old_count

            cookie_cart_cart[sku_id] = {
                "count":count,
                "selected":True
            }

            #4,5 拼接数据返回响应
            response = http.JsonResponse({"code":RET.OK})
            cookie_cart = base64.b64encode(pickle.dumps(cookie_cart_cart)).decode()
            response.set_cookie("carts",cookie_cart)
            return response

    def get(self,request):

        #1, 判断用户状态
        if request.user.is_authenticated:

            #1,1 获取redis对象
            redis_conn = get_redis_connection("carts")
            cart_dict = redis_conn.hgetall("carts_%s"%request.user.id)
            sku_ids = redis_conn.smembers("selected_%s"%request.user.id)

            #1,2 拼接数据
            sku_list = []
            for sku_id,count in cart_dict.items():
                sku = SKU.objects.get(id=sku_id)
                sku_dict = {
                    "id":sku.id,
                    "default_image_url":sku.default_image_url.url,
                    "name":sku.name,
                    "price":str(sku.price),
                    "count":int(count),
                    "amount":str(int(count) * sku.price),
                    "selected":str(sku_id in sku_ids)
                }
                sku_list.append(sku_dict)

            #1,3 返回响应
            return render(request, 'cart.html',context={"cart_skus":sku_list})
        else:
            #2,1 获取cookie购物车数据
            cookie_carts = request.COOKIES.get("carts")

            #2,2 字符串转字典
            cookie_carts_dict = {}
            if cookie_carts:
                cookie_carts_dict = pickle.loads(base64.b64decode(cookie_carts.encode()))

            #2,2 拼接数据
            sku_list = []
            for sku_id,selected_count in cookie_carts_dict.items():
                sku = SKU.objects.get(id=sku_id)
                sku_dict = {
                    "id": sku.id,
                    "default_image_url":sku.default_image_url.url,
                    "name":sku.name,
                    "price":str(sku.price),
                    "count":int(selected_count["count"]),
                    "amount":str(int(selected_count["count"]) * sku.price),
                    "selected":str(selected_count["selected"])
                }
                sku_list.append(sku_dict)

            #2,3 返回响应
            return render(request, 'cart.html', context={"cart_skus": sku_list})

    def put(self,request):
        #1,获取参数
        data_dict = json.loads(request.body.decode())
        sku_id = data_dict.get("sku_id")
        count = data_dict.get("count")
        selected = data_dict.get("selected")

        #2,校验参数
        #2,1 为空校验
        if not all([sku_id,count]):
            return http.JsonResponse({"code":RET.PARAMERR,"errmsg":"参数不全"})

        #2,2 判断count是否整数
        try:
            count = int(count)
        except Exception as e:
            return http.JsonResponse({"code": RET.DATAERR, "errmsg": "数量有误"})

        #2,3 判断selected是否bool类型
        try:
            selected = bool(selected)
        except Exception as e:
            return http.JsonResponse({"code": RET.DATAERR, "errmsg": "状态有误"})

        #2,4 判断商品是否存在
        try:
            sku = SKU.objects.get(id=sku_id)
        except Exception as e:
            return http.JsonResponse({"code": RET.DBERR, "errmsg": "商品不存在"})

        #2,5 判断库存是否足够
        if count > sku.stock:
            return http.JsonResponse({"code": RET.DATAERR, "errmsg": "库存不足"})

        #3,判断用户状态,数据保存
        if request.user.is_authenticated:
            #3,1 获取redis对象
            redis_conn = get_redis_connection("carts")

            #3,2 修改redis数据
            redis_conn.hset("carts_%s"%request.user.id,sku_id,count)
            if selected:
                redis_conn.sadd("selected_%s"%request.user.id,sku_id)
            else:
                redis_conn.srem("selected_%s" % request.user.id,sku_id)

            #3,3 拼接数据, 返回响应
            cart_sku = {
                    "id": sku.id,
                    "default_image_url":sku.default_image_url.url,
                    "name":sku.name,
                    "price":str(sku.price),
                    "count":int(count),
                    "amount":str(int(count) * sku.price),
                    "selected":selected
                }
            return http.JsonResponse({"code":RET.OK,"cart_sku":cart_sku})
        else:
            #4,1 获取cookie数据
            cookie_cart = request.COOKIES.get("carts")

            #4,2 字符串转字典
            cookie_cart_dict = {}
            if cookie_cart:
                cookie_cart_dict = pickle.loads(base64.b64decode(cookie_cart.encode()))

            #4,3 数据修改
            cookie_cart_dict[sku_id] = {
                "count":count,
                "selected":selected
            }

            #4,4 拼接数据返回响应
            cart_sku = {
                "id": sku.id,
                "default_image_url": sku.default_image_url.url,
                "name": sku.name,
                "price": str(sku.price),
                "count": int(count),
                "amount": str(int(count) * sku.price),
                "selected": selected
            }
            response = http.JsonResponse({"code": RET.OK, "cart_sku": cart_sku})
            cookie_cart = base64.b64encode(pickle.dumps(cookie_cart_dict)).decode()
            response.set_cookie("carts",cookie_cart)
            return response

    def delete(self,request):
        #1, 获取参数
        data_dict = json.loads(request.body.decode())
        sku_id = data_dict.get("sku_id")

        #2, 校验参数
        if not sku_id:
            return http.JsonResponse({"code":RET.PARAMERR,"errmsg":"参数不全"})

        #3, 判断用户,删除数据
        if request.user.is_authenticated:
            #3,1 获取redis对象
            redis_conn = get_redis_connection("carts")

            #3,2 删除数据
            redis_conn.hdel("carts_%s"%request.user.id,sku_id)
            redis_conn.srem("selected_%s"%request.user.id,sku_id)

            #3,3 返回响应
            return http.JsonResponse({"code": RET.OK})
        else:
            #4,1 获取cookie数据
            cookie_cart = request.COOKIES.get("carts")

            #4,2 字符串转字典
            cookie_cart_dict = {}
            if cookie_cart:
                cookie_cart_dict = pickle.loads(base64.b64decode(cookie_cart.encode()))

            #4,3 数据删除
            if sku_id in cookie_cart_dict:
                del cookie_cart_dict[sku_id]

            #4,4 拼接数据返回响应
            response = http.JsonResponse({"code": RET.OK})
            cookie_cart = base64.b64encode(pickle.dumps(cookie_cart_dict)).decode()
            response.set_cookie("carts",cookie_cart)
            return response

#2,购物车全选
class CartsAllSelectedView(View):
    def put(self,request):
        #1,获取参数
        data_dict = json.loads(request.body.decode())
        selected = data_dict.get("selected")

        #2,校验参数
        try:
            selected = bool(selected)
        except Exception as e:
            return http.JsonResponse({"code":RET.PARAMERR,"errmsg":"参数有误"})

        #3,判断用户状态,数据修改
        if request.user.is_authenticated:
            #3,1 获取redis对象
            redis_conn = get_redis_connection("carts")
            sku_ids = redis_conn.hkeys("carts_%s"%request.user.id)

            #3,2 修改数据
            if selected:
                redis_conn.sadd("selected_%s"%request.user.id,*sku_ids)
            else:
                redis_conn.srem("selected_%s" % request.user.id, *sku_ids)

            #3,3 返回响应
            return http.JsonResponse({"code": RET.OK})
        else:
            # 4,1 获取cookie数据
            cookie_cart = request.COOKIES.get("carts")

            # 4,2 字符串转字典
            cookie_cart_dict = {}
            if cookie_cart:
                cookie_cart_dict = pickle.loads(base64.b64decode(cookie_cart.encode()))

            # 4,3 数据全选,或者全不选
            for sku_id,selected_count in cookie_cart_dict.items():
                selected_count["selected"] = selected

            # 4,4 拼接数据返回响应
            response = http.JsonResponse({"code": RET.OK})
            cookie_cart = base64.b64encode(pickle.dumps(cookie_cart_dict)).decode()
            response.set_cookie("carts", cookie_cart)
            return response

#3,购物车简要信息
class CartsSimpleView(View):
    def get(self,request):
        #1,根据用户状态,获取数据
        if request.user.is_authenticated:
            #1,1 获取数据
            redis_conn = get_redis_connection("carts")
            cart_dict = redis_conn.hgetall("carts_%s"%request.user.id)

            #2,拼接数据
            sku_list = []
            for sku_id,count in cart_dict.items():
                sku = SKU.objects.get(id=sku_id)
                sku_dict = {
                    "id":sku.id,
                    "name":sku.name,
                    "default_image_url":sku.default_image_url.url,
                    "count":int(count)
                }
                sku_list.append(sku_dict)

            #3,返回响应
            return http.JsonResponse({"cart_skus":sku_list})
        else:
            # 4,1 获取cookie数据
            cookie_cart = request.COOKIES.get("carts")

            # 4,2 字符串转字典
            cookie_cart_dict = {}
            if cookie_cart:
                cookie_cart_dict = pickle.loads(base64.b64decode(cookie_cart.encode()))

            # 4,3 拼接数据
            sku_list = []
            for sku_id, selected_count in cookie_cart_dict.items():
                sku = SKU.objects.get(id=sku_id)
                sku_dict = {
                    "id": sku.id,
                    "name": sku.name,
                    "default_image_url": sku.default_image_url.url,
                    "count": int(selected_count["count"])
                }
                sku_list.append(sku_dict)

            # 4,4 返回响应
            return http.JsonResponse({"cart_skus": sku_list})