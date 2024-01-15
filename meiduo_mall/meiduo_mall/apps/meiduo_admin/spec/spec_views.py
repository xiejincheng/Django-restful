from rest_framework.viewsets import ModelViewSet
from meiduo_admin.my_pagination import MyPageNumberPagination
from . import spec_serializers
from goods.models import SPUSpecification

#1, specs 管理
class SpecModelViewSet(ModelViewSet):
    pagination_class = MyPageNumberPagination
    serializer_class = spec_serializers.SpecSerializers
    queryset = SPUSpecification.objects.all()