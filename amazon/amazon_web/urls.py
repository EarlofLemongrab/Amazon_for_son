from django.conf.urls import url
from django.views.generic import TemplateView
from django.contrib import admin
from . import views

urlpatterns = [
    url(r'^$',views.index),  
    url(r'^regist/$',views.register),
    url(r'^login/$',views.login),  
    url(r'^logout/$',views.logout),
    url(r'^order/$',views.order), 
    url(r'^purchase/$',views.purchase), 
    url(r'^searchproduct/$',TemplateView.as_view(template_name='searchproduct.html')),
    url(r'^catalog/(?P<description>\w+)/$',views.catalog),
]