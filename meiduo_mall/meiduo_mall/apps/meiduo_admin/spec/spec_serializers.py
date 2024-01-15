from rest_framework import serializers
from goods.models import SPUSpecification

#1, spec 序列化器
class SpecSerializers(serializers.ModelSerializer):

    #1,重写spu, spu_id
    spu = serializers.CharField(read_only=True)
    spu_id = serializers.IntegerField()

    class Meta:
        model = SPUSpecification
        fields = "__all__"