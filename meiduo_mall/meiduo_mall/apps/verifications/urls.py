from django.conf.urls import url
from . import views

urlpatterns = [
    url(r'image_codes/(?P<uuid>.+)/$',views.ImageCodeView.as_view()),
    url(r'sms_codes/(?P<mobile>\d+)/$',views.SMSCodeView.as_view()),
]