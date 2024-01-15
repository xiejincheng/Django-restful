from goods.models import GoodsChannel


def get_categories():
    # 1, 定义好空字典
    categories = {}

    # 2, 查询所有的频道
    channels = GoodsChannel.objects.order_by("sequence").all()

    # 3, 遍历频道拼接前端需要的数据
    for channel in channels:

        # 3,1 取出组的编号
        group_id = channel.group_id

        # 3,2 初始化字典数据
        if group_id not in categories:
            categories[group_id] = {
                "channels": [],
                "sub_cats": []
            }

        # 3,3 添加频道信息(一级分类)
        cat1 = channel.category  # 取出关联的一级分类
        cat1_dict = {
            'url': channel.url,
            'name': cat1.name
        }
        categories[group_id]['channels'].append(cat1_dict)

        # 3,4 添加二级分类,三级分类
        cats2 = cat1.subs.all()

        for cat2 in cats2:
            categories[group_id]['sub_cats'].append({
                'name': cat2.name,
                'subs': cat2.subs.all()
            })

    #4, 返回分类数据
    return categories