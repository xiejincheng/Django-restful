#1, 加载配置文件
import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "meiduo_mall.settings.dev")

#2, 初始化django
import django
django.setup()

#3, 导入包
import time
from django.template import loader
from meiduo_mall.utils.my_category import get_categories
from contents.models import ContentCategory
from django.conf import settings


def generate_static_index_html():
    """
    生成静态的主页html文件
    """
    print('%s: generate_static_index_html' % time.ctime())

    # 1, 获取商品频道和分类
    categories = get_categories()

    # 2,广告内容
    contents = {}
    content_categories = ContentCategory.objects.all()
    for cat in content_categories:
        contents[cat.key] = cat.content_set.filter(status=True).order_by('sequence')

    # 3,渲染模板
    context = {
        'categories': categories,
        'contents': contents
    }

    # 4,获取首页模板文件
    template = loader.get_template('index.html')

    # 5,渲染首页html字符串
    html_text = template.render(context)

    # 6,将首页html字符串写入到指定目录，命名'index.html'
    file_path = os.path.join(settings.STATICFILES_DIRS[0], 'index.html')
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(html_text)

if __name__ == '__main__':
    generate_static_index_html()