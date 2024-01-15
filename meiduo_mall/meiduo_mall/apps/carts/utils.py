import pickle,base64
from django_redis import get_redis_connection

#购物车数据合并
def merge_cookie_redis_data(request,response):
    """
    :param request: 获取cookie数据, 获取redis数据使用的
    :param response: 清除cookie数据的
    :return:
    """
    #1, 获取cookie数据
    cookie_cart = request.COOKIES.get("carts")

    #2, 判断是否有cookie数据,字符串转字典
    cookie_cart_dict = {}
    if cookie_cart:
        cookie_cart_dict = pickle.loads(base64.b64decode(cookie_cart.encode()))
    else:
        return response

    #3, 数据合并
    redis_conn = get_redis_connection("carts")
    for sku_id,selected_count in cookie_cart_dict.items():
        #合并购物车数据
        redis_conn.hset("carts_%s"%request.user.id,sku_id,selected_count["count"])
        #合并选中状态
        selected = selected_count["selected"]
        if selected:
            redis_conn.sadd("selected_%s"%request.user.id,sku_id)
        else:
            redis_conn.srem("selected_%s" % request.user.id, sku_id)

    #4, 清空cookie数据
    response.delete_cookie("carts")

    #5, 返回响应
    return response