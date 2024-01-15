from django.shortcuts import render
from django.views import View
from areas.models import Area
from django import http
from meiduo_mall.utils.response_code import RET
from django.core.cache import cache

#1, 获取区域
class AreaView(View):
    def get(self,request):

        #0,获取参数
        area_id = request.GET.get("area_id")

        #1,判断获取省,还是市信息
        if not area_id:

            #1,0 判断是否有缓存,如果有直接返回
            province_list = cache.get('province_list')
            if province_list:
                data_dict = {
                    "code": RET.OK,
                    "province_list": province_list
                }
                return http.JsonResponse(data_dict)

            #1, 查询所有的省信息
            provinces = Area.objects.filter(parent=None).all()

            #2, 拼接数据
            province_list = []
            for province in provinces:
                item_dict = {
                    "id":province.id,
                    "name":province.name
                }
                province_list.append(item_dict)

            data_dict = {
                "code":RET.OK,
                "province_list":province_list
            }

            #2,1 设置缓存
            cache.set('province_list', province_list)

            #3, 返回响应
            return http.JsonResponse(data_dict)
        else:

            #0,获取缓存,如果有缓存直接返回
            subs = cache.get('subs_%s' % area_id)
            if subs:
                data_dict = {
                    "code": RET.OK,
                    "sub_data": {
                        "subs": subs
                    }
                }
                return http.JsonResponse(data_dict)

            #1, 根据省的id,获取该省的所有市; 或者根据市的id获取区的信息
            cities = Area.objects.filter(parent_id=area_id).all()

            #2, 拼接数据
            subs = []
            for city in cities:
                city_dict = {
                    "id":city.id,
                    "name":city.name
                }
                subs.append(city_dict)

            data_dict = {
                "code":RET.OK,
                "sub_data":{
                    "subs":subs
                }
            }

            #2,1 设置缓存
            cache.set('subs_%s'%area_id, subs)

            #3, 返回响应
            return http.JsonResponse(data_dict)
