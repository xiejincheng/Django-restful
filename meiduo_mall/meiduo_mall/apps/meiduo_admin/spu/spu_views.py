from rest_framework.viewsets import ModelViewSet
from meiduo_admin.my_pagination import MyPageNumberPagination
from . import spu_serializers
from goods.models import SPU,Brand,GoodsCategory
from rest_framework.generics import ListAPIView
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from fdfs_client.client import Fdfs_client
from django.conf import settings

#1, spu管理
class SPUModelViewSet(ModelViewSet):
    pagination_class = MyPageNumberPagination
    serializer_class = spu_serializers.SPUSerializers
    queryset = SPU.objects.all()

#2, spu brand信息
class GoodsBrandSimpleView(ListAPIView):
    pagination_class = None
    serializer_class = spu_serializers.GoodsBrandSerializers
    queryset = Brand.objects.all()

#3, spu category信息(一级分类)
class GoodsCategoryView(ListAPIView):
    pagination_class = None
    serializer_class = spu_serializers.GoodsCategorySerializers
    queryset = GoodsCategory.objects.filter(parent=None).all()

#3, 二级,三级分类
class GoodsCategoryTwoThreeView(ListAPIView):
    pagination_class = None
    serializer_class = spu_serializers.GoodsCategorySerializers

    #1,重写get_queryset,根据父级分类id 获取子分类数据
    def get_queryset(self):

        #1,获取正则中匹配到的参数
        parent_id = self.kwargs.get("parent_id")

        #2,获取分类数据
        return GoodsCategory.objects.filter(parent_id=parent_id).all()

#4, spu 图片上传
class GoodsImagesView(APIView):
    def post(self,request):

        #1,获取参数
        image = request.FILES.get("image")

        #2,校验参数
        if not image:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        #3,上传图片
        client = Fdfs_client(settings.FDFS_CONFIG)

        #上传
        result = client.upload_by_buffer(image.read())

        #判断是否上传成功
        if result["Status"] != "Upload successed.":
            return Response(status=status.HTTP_400_BAD_REQUEST)

        #获取图片名称
        image_name = result["Remote file_id"]

        #5,拼接数据,返回响应
        img_url = "{}{}".format(settings.BASE_URL,image_name)
        return Response({"img_url":img_url})
