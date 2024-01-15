from rest_framework import serializers
from goods.models import SKU,GoodsCategory,SPU,SPUSpecification,SpecificationOption,SKUSpecification
from django.db import transaction

#0, skuspecfication序列化器
class SKUSpecificationSerializer(serializers.Serializer):
    spec_id = serializers.IntegerField()
    option_id = serializers.IntegerField()

#1, sku序列化器
class SKUSerializers(serializers.ModelSerializer):

    #1,重写category_id
    category_id = serializers.IntegerField()
    category = serializers.CharField(read_only=True)

    #2,重写spu_id
    spu_id = serializers.IntegerField()
    spu = serializers.CharField(read_only=True)

    #3,重写规格字段
    specs = SKUSpecificationSerializer(read_only=True,many=True)

    class Meta:
        model = SKU
        fields = "__all__"

    #3,重写create方法,将规格信息入库
    @transaction.atomic #开启事务
    def create(self, validated_data):

        #0,设置保存点
        sid = transaction.savepoint()

        try:
            #1,将基本信息入库
            sku = SKU.objects.create(**validated_data)

            #2,获取规格信息
            specs = self.context["request"].data["specs"]

            #3,入库规格信息
            for spec in specs:
                SKUSpecification.objects.create(
                    option_id=spec["option_id"],
                    spec_id=spec["spec_id"],
                    sku_id=sku.id)
        except Exception as e:
            transaction.savepoint_rollback(sid) #回滚
            raise serializers.ValidationError("数据入库失败")
        else:
            transaction.savepoint_commit(sid) #提交
            return sku

    #4,重写update方法,将规格信息修改
    @transaction.atomic  # 开启事务
    def update(self, instance, validated_data):

        #0,设置保存点
        sid = transaction.savepoint()

        try:
            #1,修改基本信息
            SKU.objects.filter(id=instance.id).update(**validated_data)

            #2,获取规格信息, 删除数据库已有的规格
            specs = self.context["request"].data["specs"]

            [spec.delete() for spec in instance.specs.all()]

            #3,修改规格信息
            for spec in specs:
                SKUSpecification.objects.create(
                    option_id=spec["option_id"],
                    spec_id=spec["spec_id"],
                    sku_id=instance.id)
        except Exception as e:
            transaction.savepoint_rollback(sid)  # 回滚
            raise serializers.ValidationError("数据修改失败")
        else:
            transaction.savepoint_commit(sid)  # 提交
            return instance

#2, sku,category序列化器
class SKUCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = GoodsCategory
        fields = ["id","name"]

#3, sku,spu序列化器
class GoodSimpleSerializer(serializers.ModelSerializer):
    class Meta:
        model = SPU
        fields = ["id","name"]

#4, spec, option序列化器
class SpecOptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = SpecificationOption
        fields = ["id","value"]

# sku,spu,specs序列化器
class GoodSpecsSerializer(serializers.ModelSerializer):

    #1,规格关联的选项; 规格是一方, 选项是多方
    options = SpecOptionSerializer(read_only=True,many=True)

    class Meta:
        model = SPUSpecification
        fields = "__all__"