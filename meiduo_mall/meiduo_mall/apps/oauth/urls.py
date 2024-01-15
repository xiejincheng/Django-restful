from django.conf.urls import url
from . import views

urlpatterns = [
    url(r'^qq/login/$',views.QQLoginView.as_view()),
    url(r'^oauth_callback/$',views.OpenIDView.as_view()),
]