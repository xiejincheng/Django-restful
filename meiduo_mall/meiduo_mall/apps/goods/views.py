from django.shortcuts import render
from django.views import View

from meiduo_mall.utils import constants
from meiduo_mall.utils.my_category import get_categories
from goods.models import SKU,GoodsCategory,CategoryVisitCount
from django.core.paginator import Paginator
from django import http
from datetime import datetime

from meiduo_mall.utils.my_loginview import LoginRequiredView
from meiduo_mall.utils.response_code import RET
import json
from django_redis import get_redis_connection

#1, 商品列表页
class ListView(View):
    def get(self,request,category_id,page):

        #0,获取参数
        sort = request.GET.get("sort","default")

        #0,1 根据sort,设置数据库查询的排序字段; sort给前端显示用的, sort_field数据排序查询用的
        if sort == "price":
            sort_field = "-price"
        elif sort == "hot":
            sort_field = "-sales"
        else:
            sort_field = "-create_time"

        #1,获取分类数据
        categories = get_categories()

        #2,查询skus数据
        skus = SKU.objects.filter(category_id=category_id).order_by(sort_field).all()

        #2,1 分页处理
        paginator = Paginator(skus,constants.SKU_LIST_PAGE_COUNT)
        paginate = paginator.page(page)
        skus_list = paginate.object_list #当前页对象列表
        current_page = paginate.number #当前页
        total_page = paginator.num_pages #总页数

        #3,获取分类对象
        category = GoodsCategory.objects.get(id=category_id)

        #拼接数据,渲染页面
        context = {
            "categories":categories,
            "category":category,
            "skus": skus_list,
            "current_page":current_page,
            "total_page":total_page,
            "sort":sort
        }

        return render(request,'list.html',context=context)

#2, 热门商品
class HotSkuView(View):
    def get(self,request,category_id):
        #1,根据分类编号获取skus数据
        skus = SKU.objects.filter(category_id=category_id).all()[:constants.SKU_HOT_COUNT]

        #2,拼接数据
        hot_sku_list = []
        for sku in skus:
            sku_dict = {
                "id":sku.id,
                "default_image_url":sku.default_image_url.url,
                "name":sku.name,
                "price":sku.price
            }
            hot_sku_list.append(sku_dict)

        #3,返回响应
        return http.JsonResponse({"hot_sku_list":hot_sku_list})

#3, 商品详情页
class SKUDetailView(View):
    def get(self,request,sku_id):
        #1, 获取商品分类
        categories = get_categories()

        #2, 获取面包屑需要的数据
        sku = SKU.objects.get(id=sku_id)
        category = sku.category

        #3, 商品规格信息
        # 构建当前商品的规格键
        sku_specs = sku.specs.order_by('spec_id')
        sku_key = []
        for spec in sku_specs:
            sku_key.append(spec.option.id)
        # 获取当前商品的所有SKU
        skus = sku.spu.sku_set.all()
        # 构建不同规格参数（选项）的sku字典
        spec_sku_map = {}
        for s in skus:
            # 获取sku的规格参数
            s_specs = s.specs.order_by('spec_id')
            # 用于形成规格参数-sku字典的键
            key = []
            for spec in s_specs:
                key.append(spec.option.id)
            # 向规格参数-sku字典添加记录
            spec_sku_map[tuple(key)] = s.id
        # 获取当前商品的规格信息
        goods_specs = sku.spu.specs.order_by('id')
        # 若当前sku的规格信息不完整，则不再继续
        if len(sku_key) < len(goods_specs):
            return
        for index, spec in enumerate(goods_specs):
            # 复制当前sku的规格键
            key = sku_key[:]
            # 该规格的选项
            spec_options = spec.options.all()
            for option in spec_options:
                # 在规格参数sku字典中查找符合当前规格的sku
                key[index] = option.id
                option.sku_id = spec_sku_map.get(tuple(key))
            spec.spec_options = spec_options


        #拼接数据
        context = {
            "categories":categories,
            "category":category,
            "sku":sku,
            "specs":goods_specs
        }
        return render(request,'detail.html',context=context)

#4, 统计商品分类访问量
class CategoryVisitCountView(View):
    def post(self,request,category_id):
        #1, 获取当天时间
        today = datetime.today()

        #2, 查询分类访问量对象
        try:
            category_visit_count = CategoryVisitCount.objects.get(date=today, category_id=category_id)
        except Exception as e:
            category_visit_count = CategoryVisitCount()

        #3, 设置访问数据,入库
        category_visit_count.date = today
        category_visit_count.category_id = category_id
        category_visit_count.count += 1
        category_visit_count.save()

        #4, 返回响应
        return http.JsonResponse({"code":RET.OK})

#5, 用户浏览历史记录
class BrowseHistoryView(LoginRequiredView):
    def post(self,request):
        #1,获取参数
        dict_data = json.loads(request.body.decode())
        sku_id = dict_data.get("sku_id")

        #2,校验参数
        if not sku_id:
            return http.JsonResponse({"code":RET.PARAMERR})

        #3,数据入库(redis)
        #3,1 去重
        redis_conn = get_redis_connection("history")
        redis_conn.lrem("history_%s"%request.user.id,0,sku_id)

        #3,2 存储
        redis_conn.lpush("history_%s"%request.user.id,sku_id)

        #3,3 截取
        redis_conn.ltrim("history_%s"%request.user.id,0,4)

        #4,返回响应
        return http.JsonResponse({"code":RET.OK})

    def get(self,request):

        #1,获取redis中的浏览记录
        redis_conn = get_redis_connection("history")
        sku_ids = redis_conn.lrange("history_%s"%request.user.id,0,-1)

        #2,拼接数据
        sku_list = []
        for sku_id in sku_ids:
            sku = SKU.objects.get(id=sku_id)
            sku_dict = {
                "id":sku.id,
                "default_image_url":sku.default_image_url.url,
                "name":sku.name,
                "price":sku.price
            }
            sku_list.append(sku_dict)

        #3,返回响应
        return http.JsonResponse({"skus":sku_list,"code":RET.OK})