from django.shortcuts import render
from django.shortcuts import render
from django.core.mail import send_mail
from django.http import HttpResponseRedirect
from django.http import HttpResponse
from django.shortcuts import  render_to_response  
from django.template import  RequestContext  
from django.http import HttpResponseRedirect  
from django.contrib.auth.models import User 
from django.contrib import auth  
from .models import *
from django.contrib.auth.decorators import login_required
from datetime import datetime
from django.conf import settings
import requests
import argparse
import json
import pprint
import sys
import urllib
import socket
try:
    # For Python 3.0 and later
    from urllib.error import HTTPError
    from urllib.parse import quote
    from urllib.parse import urlencode
except ImportError:
    # Fall back to Python 2's urllib2 and urllib
    from urllib2 import HTTPError
    from urllib import quote
    from urllib import urlencode
import json
# Create your views here.
#Load index page 


HOST = 'localhost'
PORT = 6666



def index(req):   
    username=req.session.get('username', '')  
    content = {'user': username}  
    return render_to_response('index.html', content)

#Handles user registration; read in username, password, repassword, email to create MyUser instance and user instance from django auth.
def register(req):
    print (req)
    if req.session.get('username', ''):  
         return HttpResponseRedirect('/amazon_web/index.html')  
    status=""

    if req.POST:  
        username = req.POST.get("username","")  
        if User.objects.filter(username=username):  
            status = "user_exist"  
        else:
            password=req.POST.get("password","")  
            repassword = req.POST.get("repassword","")  
            if password!=repassword:  
                status = "re_err"  
            else:  
                newuser=User.objects.create_user(username=username,password=password)  
                newuser.save()                               
                new_myuser = MyUser(user=newuser,UPS=req.POST.get("UPS"),name = username)      
                new_myuser.save()  
                status = "success"  
                return HttpResponseRedirect("/amazon_web/login/")  
    return render(req,"regist.html",{"status":status,"user":""})  

#handles user login; Be aware that we use POST method to ensure data is transmitted in a secure way  
def login(req):  
    if req.session.get('username', ''):  
        return HttpResponseRedirect('/amazon_web/')  
    status=""  
    if req.POST:  
        username=req.POST.get("username","")  
        password=req.POST.get("password","")  
        user = auth.authenticate(username=username,password=password)   
        if user is not None:  
                auth.login(req,user)          
                req.session["username"]=username      
                return HttpResponseRedirect('/amazon_web/')  
        else:  
            status="not_exist_or_passwd_err"  
    return render(req,"login.html",{"status":status}) 


#hanles user logout     
@login_required
def logout(req):  
    auth.logout(req)  
    return HttpResponseRedirect('/amazon_web/')


@login_required
def order(req):
    username = req.session.get('username','')
    if username != '':
        user = MyUser.objects.get(name=username)
    else:
        user = ''

    try:
        print(user.name)
        o = orders.objects.filter(user__name = username)
        us_sta = "no"
        return render(req,"order.html",{"orders":o,"us_sta":us_sta,"user":user})
                  
    except:
        print ("except" )
        us_sta = "yes"        
        return render(req,"order.html",{"us_sta":us_sta,"user":user})



def purchase(req):
    username = req.session.get('username','') 
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((HOST, PORT)) 
    if username != '':  
        user = MyUser.objects.get(user__username=username)  
    else:  
        user = ''  
    if req.POST:
        description = req.POST.get("description","")
        count = req.POST.get("count","")
        
        try:
        	p = product.objects.get(description = description)
        	print "have in catalog"
        	lastest_order = orders.objects.all().last()
        	oid = 0
        	if lastest_order is None:
        		oid = 1
        	else:
        		oid = lastest_order.order_id+1
        	print oid
        	new_order = orders(order_id=oid,user = user, product = p,count=count,warehouse=0)
        	print new_order.order_id
        	new_order.save()
        	order_data = {'description':description,'count':count,'pid':p.pid,'whnum':0}
        	order_str = json.dumps(order_data)
        	s.send(order_str)
        	
        except:
            new_product = product(description=description,rate_count=0,rate = 0.00)
            print "not in catalog"
            new_product.save()
            lastest_order = orders.objects.all().last()
            oid = 0
            if lastest_order is None:
            	oid = 1
            else:
            	oid = lastest_order.order_id+1
            new_order = orders(order_id = oid,user = user, product = new_product,count=count,warehouse=0)
            new_order.save()
            order_data = {'description':description,'count':count,'pid':new_product.pid,'whnum':0}
            order_str = json.dumps(order_data)
            s.send(order_str)
        	
        
        return  HttpResponseRedirect("/amazon_web/")
    return  render(req,"purchase.html",{})



def catalog(req,description):
    print description
    description = description
    p = product.objects.filter(description__contains = description)

    return render(req,"catalog.html",{"products":p})



def rate(req,a,b):
    username = req.session.get('username','')   	
    if username != '':  
        user = MyUser.objects.get(user__username=username)  
    else:  
        user = ''
    pid = b
    oid = a
    if req.POST:
    	p = product.objects.get(pk = pid)
    	original_rate = p.rate
    	original_rate_history = p.rate_count
    	customer_rate = req.POST.get("rate","0")
    	new_rate = (original_rate*original_rate_history+int(customer_rate))/(original_rate_history+1)
    	p.rate = new_rate
    	p.rate_count=p.rate_count+1
    	p.save()
    	o = orders.objects.get(order_id = oid)
    	o.reviewed = True;
    	o.save()
    	rev = req.POST.get("review","")
    	r = usr_review(product = p,review_content = rev,user = username)
    	r.save()
    	return  HttpResponseRedirect("/amazon_web/")
    return render(req,"rate.html",{})


def review(req):
    Id = req.GET.get("id","no id")
    print "id is "+Id
    req.session["id"]=Id
    r = usr_review.objects.filter(product__pid = Id)
    return render(req,"review.html",{"reviews":r})


