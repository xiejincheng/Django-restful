from django.conf.urls import url
from . import views

urlpatterns = [
    url(r'^order/settlement/$',views.OrderSettlement.as_view()),
    url(r'^orders/commit/$',views.OrderCommitView.as_view()),
    url(r'^orders/success/$',views.OrderSuccessView.as_view()),
    url(r'^orders/info/(?P<page_num>\d+)/$',views.OrderInfoView.as_view()),
    url(r'^orders/comment/$',views.OrdersCommentView.as_view()),
    url(r'^comment/(?P<sku_id>\d+)/$',views.SKUCommentView.as_view()),
]