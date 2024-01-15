from django.conf.urls import url
from . import views

urlpatterns = [
    url(r'^$',views.IndexView.as_view()),
    url(r'^logout/$',views.LogoutView.as_view()),
    url(r'^favicon.ico/$',views.LoGoView.as_view()),
]