from django.conf.urls import url
from . import views
urlpatterns = [
    url(r'^register/$',views.RegisterView.as_view()),
    url(r'^usernames/(?P<username>\w{5,20})/count/$',views.CheckUsernameView.as_view()),
    url(r'^mobiles/(?P<mobile>\d+)/count/$',views.CheckMobileView.as_view()),
    url(r'^login/$',views.LoginView.as_view()),
    url(r'^info/$',views.UserInfoView.as_view()),
    url(r'^emails/$',views.EmailView.as_view()),
    url(r'^verify/email/$',views.VerifyEmailView.as_view()),
    url(r'^addresses/$',views.AddressesView.as_view()),
    url(r'^addresses/create/$',views.AddressesCreateView.as_view()),
    url(r'^addresses/(?P<address_id>\d+)/$',views.AddressesUpdateView.as_view()),
    url(r'^addresses/(?P<address_id>\d+)/default/$',views.AddressesDefaultView.as_view()),
    url(r'^addresses/(?P<address_id>\d+)/title/$',views.AddressesTitleView.as_view()),
    url(r'^password/$',views.UserPassWordView.as_view()),
]