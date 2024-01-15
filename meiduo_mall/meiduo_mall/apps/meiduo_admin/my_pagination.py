from collections import OrderedDict

from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response

#1, 自定义分页对象
class MyPageNumberPagination(PageNumberPagination):
    #1, 可以在前端指定页面数据大小
    page_size_query_param = "pagesize"

    #2, 限制页面最大的数量
    max_page_size = 100

    # 重写响应值的方法
    def get_paginated_response(self, data):
        return Response(OrderedDict([
            ('page', self.page.number),
            ('pages', self.page.paginator.num_pages),
            ('lists', data)
        ]))