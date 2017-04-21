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
from models import *  
from django.contrib.auth.decorators import login_required
from datetime import datetime
from django.conf import settings
import requests
import argparse
import json
import pprint
import sys
import urllib
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
def index(req):   
    username=req.session.get('username', '')  
    content = {'user': username}  
    return render_to_response('index.html', content)

#Handles user registration; read in username, password, repassword, email to create MyUser instance and user instance from django auth.
def regist(req):  
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
    	print user.name
    	o = orders.objects.filter(user__name = username)
    	us_sta = "no"  
    	return render(req,"order.html",{"orders":o,"us_sta":us_sta,"user":user})  
                  
    except:
    	print "except"  
        us_sta = "yes"        
        return render(req,"order.html",{"us_sta":us_sta,"user":user})



def purchase(req):
    username = req.session.get('username','')  
    if username != '':  
        user = MyUser.objects.get(user__username=username)  
    else:  
        user = ''  
    if req.POST:
        description = req.POST.get("description","")
        count = req.POST.get("count","")
        try:
        	p = product.objects.get(description = description)
        	new_order = orders(user = user, product = p,count=count,warehouse=0)
        	new_order.save()

        	
        except:
        	new_product = product(description=description)
        	new_product.save()
        	new_order = orders(user = user, product = new_product,count=count,warehouse=0)
        	new_order.save()
        	
        
        return  HttpResponseRedirect("/amazon_web/")
    return  render(req,"purchase.html",{})
