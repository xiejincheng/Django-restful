from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from users.models import User
from datetime import date,timedelta
from rest_framework.permissions import IsAdminUser
from rest_framework.generics import ListAPIView
from goods.models import CategoryVisitCount
from . import home_serializers

# 1, 获取用户总数
class UserTotalCountView(APIView):

    #1, 设置管理员权限
    permission_classes = [IsAdminUser]

    def get(self,request):
        # 1, 查询用户总数
        count = User.objects.filter(is_staff=False).count()

        # 2, 返回响应
        return Response({
            "count":count
        })

# 2, 获取日增用户
class UserDayIncrementView(APIView):

    #1, 设置管理员权限
    permission_classes = [IsAdminUser]

    def get(self,request):
        # 1, 查询用户日增数量, 注意点: date.today() 获取的不带时分秒
        count = User.objects.filter(date_joined__gte=date.today(),is_staff=False).count()

        # 2, 返回响应
        return Response({
            "count":count
        })

# 3, 获取日活用户
class UserDayActiveView(APIView):
    def get(self,request):
        # 1, 查询用户日活数量
        count = User.objects.filter(last_login__gte=date.today(),is_staff=False).count()

        # 2, 返回响应
        return Response({
            "count":count
        })

# 4, 获取日下单用户
class UserDayOrdersView(APIView):
    def get(self,request):
        # 1, 查询用户日下单用户数量
        count = User.objects.filter(orderinfo__create_time__gte=date.today() ,is_staff=False).count()

        # 2, 返回响应
        return Response({
            "count":count
        })

# 5, 获取月增用户
class UserMonthIncrementView(APIView):

    #1, 设置管理员权限
    permission_classes = [IsAdminUser]

    def get(self,request):

        #1, 获取30天前的时间
        old_date = date.today() - timedelta(days=30)

        #2, 拼接数据
        count_list = []
        for i in range(1,31):

            # 2,1 获取当天时间
            current_date = old_date + timedelta(days=i)

            # 2,3 获取当天时间的下一天
            next_date = old_date + timedelta(days=i+1)

            # 2,4, 查询用户日增数量, 注意点: date.today() 获取的不带时分秒
            count = User.objects.filter(date_joined__gte=current_date,date_joined__lt=next_date,is_staff=False).count()

            count_list.append({
                "count":count,
                "date":current_date
            })

        # 2, 返回响应
        return Response(count_list)

# 6, 获取商品日分类访问量
"""
ListAPIView: 
1, 父类是GenericAPIView + ListModelMixin , 
2, 提供了get方法, 获取所有数据
"""
class GoodCategoryDayView(ListAPIView):
    pagination_class = None
    serializer_class = home_serializers.CategoryVisitCountSerializer
    queryset = CategoryVisitCount.objects.filter(date=date.today()).all()
