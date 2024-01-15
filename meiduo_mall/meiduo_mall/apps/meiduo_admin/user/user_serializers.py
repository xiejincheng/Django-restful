from rest_framework import serializers
from users.models import User

#1, 用户序列化器
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id","username","mobile","email","password"]

        #1,给password增加额外的约束选项,不进行返回
        extra_kwargs = {
            "password":{
                'write_only':True
            }
        }

    #1,重写create方法,密码加密
    def create(self, validated_data):
        return User.objects.create_user(**validated_data)