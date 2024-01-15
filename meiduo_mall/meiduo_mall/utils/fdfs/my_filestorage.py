"""
文件存储类自定义
1, 自定义类, 继承自Storage
2, 重写init方法,保证变量能够被初始化
3, 重写open,save方法
4, 选择性重写,exists(),url()方法

"""""
from django.core.files.storage import Storage
from django.conf import settings


# 1, 自定义类, 继承自Storage
class MyFileStorage(Storage):

    # 2, 重写init方法,保证变量能够被初始化
    def __init__(self,base_url=None):

        if not base_url:
            base_url = settings.BASE_URL

        self.base_url = base_url

    # 3, 重写open,save方法
    def save(self, name, content, max_length=None):
        """保存文件的时候调用"""
        pass

    def open(self, name, mode='rb'):
        """打开文件的时候调用"""
        pass

    # 4, 选择性重写,exists(),url()方法
    def exists(self, name):
        """判断文件是否存在"""
        # 返回false表示文件不存在, 返回true表示存在
        return False

    def url(self, name):
        # print("name = %s"%name)
        return self.base_url + name


