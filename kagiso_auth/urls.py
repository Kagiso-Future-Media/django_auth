from django.conf import settings
from django.conf.urls import url
from django.shortcuts import render

from kagiso_auth import views

urlpatterns = [
    url(r'^sign_up/', views.sign_up, name='sign_up'),
    url(r'^confirm_account/', views.confirm_account, name='confirm_account'),
    url(r'^sign_in/', views.sign_in, name='sign_in'),
    url(r'^sign_out/', views.sign_out, name='sign_out'),
    url(r'^oauth/(?P<provider>\w+)/', views.oauth, name='oauth'),
    url(r'^forgot_password/', views.forgot_password, name='forgot_password'),
    url(r'^reset_password/', views.reset_password, name='reset_password'),
    url(
        r'^resend_confirmation/',
        views.resend_confirmation,
        name='resend_confirmation'
    ),
]

if getattr(settings, 'UNIT_TEST_SETTINGS', False):
    # The host app will have the real home page
    def mock_home(request):
        return render(request, 'kagiso_auth/blank.html')

    urlpatterns.append(url(r'^$', mock_home))
