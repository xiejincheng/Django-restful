from rest_framework import serializers
from goods.models import CategoryVisitCount

#1, 分类访问量序列化器
class CategoryVisitCountSerializer(serializers.ModelSerializer):

    #1,重写category, 目的,在序列化的时候,将category数据,显示成汉字形式
    # category = serializers.StringRelatedField(read_only=True)
    category = serializers.CharField(read_only=True)

    class Meta:
        model = CategoryVisitCount
        fields = "__all__"