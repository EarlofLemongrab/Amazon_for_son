from django.conf.urls import url
from django.contrib import admin
from . import views

urlpatterns = [
    url(r'^$',views.index),  
    url(r'^regist/$',views.regist),  
    url(r'^login/$',views.login),  
    url(r'^logout/$',views.logout),
    url(r'^order/$',views.order), 
    url(r'^purchase/$',views.purchase), 
]