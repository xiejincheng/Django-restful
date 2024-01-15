from django.db import models
from django.contrib.auth.models import AbstractUser
from meiduo_mall.utils.my_model import BaseModel

# 1,定义用户模型类
class User(AbstractUser):

    #1, 增加额外的属性
    mobile = models.CharField(verbose_name="手机号",max_length=11,unique=True)

    #2,是否激活邮箱
    email_active = models.BooleanField(verbose_name="激活邮箱",default=False)

    #3,用户的默认收货地址
    default_address = models.ForeignKey('Address', related_name='users', null=True, blank=True, on_delete=models.SET_NULL, verbose_name='默认地址')


    #4, 指定表名信息
    class Meta:
        db_table = "tb_users"

#2, 用户收货地址模型
class Address(BaseModel):
    """用户地址"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='addresses', verbose_name='用户')
    title = models.CharField(max_length=20, verbose_name='地址名称')
    receiver = models.CharField(max_length=20, verbose_name='收货人')
    province = models.ForeignKey('areas.Area', on_delete=models.PROTECT, related_name='province_addresses', verbose_name='省')
    city = models.ForeignKey('areas.Area', on_delete=models.PROTECT, related_name='city_addresses', verbose_name='市')
    district = models.ForeignKey('areas.Area', on_delete=models.PROTECT, related_name='district_addresses', verbose_name='区')
    place = models.CharField(max_length=50, verbose_name='地址')
    mobile = models.CharField(max_length=11, verbose_name='手机')
    tel = models.CharField(max_length=20, null=True, blank=True, default='', verbose_name='固定电话')
    email = models.CharField(max_length=30, null=True, blank=True, default='', verbose_name='电子邮箱')
    is_deleted = models.BooleanField(default=False, verbose_name='逻辑删除')

    class Meta:
        db_table = 'tb_address'
        ordering = ['-update_time']