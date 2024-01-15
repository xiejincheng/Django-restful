from django.conf.urls import url
from rest_framework_jwt.views import obtain_jwt_token
from meiduo_admin.home import home_views
from meiduo_admin.user import user_views
from rest_framework.routers import DefaultRouter
from meiduo_admin.sku import sku_views
from meiduo_admin.spu import spu_views
from meiduo_admin.spec import spec_views

urlpatterns = [
    url(r'^authorizations/$',obtain_jwt_token),
    url(r'^statistical/total_count/$',home_views.UserTotalCountView.as_view()),
    url(r'^statistical/day_increment/$',home_views.UserDayIncrementView.as_view()),
    url(r'^statistical/day_active/$',home_views.UserDayActiveView.as_view()),
    url(r'^statistical/day_orders/$',home_views.UserDayOrdersView.as_view()),
    url(r'^statistical/month_increment/$',home_views.UserMonthIncrementView.as_view()),
    url(r'^statistical/goods_day_views/$',home_views.GoodCategoryDayView.as_view()),
    url(r'^users/$',user_views.UserView.as_view()),

    #1,skus/categories
    url(r'^skus/categories/$',sku_views.SKUCategoryView.as_view()),

    # goods/simple/
    url(r'^goods/simple/$',sku_views.GoodSimpleView.as_view()),

    # goods/3/specs/
    url(r'^goods/(?P<spu_id>\d+)/specs/$',sku_views.GoodSpecsView.as_view()),

    #2,goods/brands/simple/
    url(r'^goods/brands/simple/$',spu_views.GoodsBrandSimpleView.as_view()),

    # goods/channel/categories/
    url(r'^goods/channel/categories/$',spu_views.GoodsCategoryView.as_view()),

    # /goods/channel/categories/' + sid +'/
    url(r'^goods/channel/categories/(?P<parent_id>\d+)/$',spu_views.GoodsCategoryTwoThreeView.as_view()),

    # goods/images/
    url(r'^goods/images/$',spu_views.GoodsImagesView.as_view()),
]

#3,goods/specs/
router = DefaultRouter()
router.register("goods/specs",spec_views.SpecModelViewSet,base_name="specs")
urlpatterns += router.urls

#2,goods
router = DefaultRouter()
router.register("goods",spu_views.SPUModelViewSet,base_name="goods")
urlpatterns += router.urls

#1, skus
router = DefaultRouter()
router.register("skus",sku_views.SKUModelViewSet,base_name="skus")
urlpatterns += router.urls