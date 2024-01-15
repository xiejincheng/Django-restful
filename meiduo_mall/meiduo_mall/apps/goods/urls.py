from django.conf.urls import url
from . import views

urlpatterns = [
    url(r'^list/(?P<category_id>\d+)/(?P<page>\d+)/$',views.ListView.as_view()),
    url(r'^hot/(?P<category_id>\d+)/$',views.HotSkuView.as_view()),
    url(r'^detail/(?P<sku_id>\d+)/$',views.SKUDetailView.as_view()),
    url(r'^detail/visit/(?P<category_id>\d+)/$',views.CategoryVisitCountView.as_view()),
    url(r'^browse_histories/$',views.BrowseHistoryView.as_view()),
]