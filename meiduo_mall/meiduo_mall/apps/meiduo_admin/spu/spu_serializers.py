from rest_framework import serializers
from goods.models import SPU, Brand,GoodsCategory


#1, spu序列化器
class SPUSerializers(serializers.ModelSerializer):

    #1,重写brand,brand_id
    brand = serializers.CharField(read_only=True)
    brand_id = serializers.IntegerField()

    #2,一级,二级,三级分类重写
    category1 = serializers.CharField(read_only=True)
    category1_id = serializers.IntegerField()

    category2 = serializers.CharField(read_only=True)
    category2_id = serializers.IntegerField()

    category3 = serializers.CharField(read_only=True)
    category3_id = serializers.IntegerField()

    class Meta:
        model = SPU
        fields = "__all__"

#2, spu brand序列化器
class GoodsBrandSerializers(serializers.ModelSerializer):
    class Meta:
        model = Brand
        fields = ["id","name"]

#3, spu category序列化器
class GoodsCategorySerializers(serializers.ModelSerializer):
    class Meta:
        model = GoodsCategory
        fields = ["id","name"]