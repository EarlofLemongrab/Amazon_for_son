from __future__ import unicode_literals

from django.db import models
from django.contrib.auth.models import User
from decimal import Decimal
# Create your models here.


class MyUser(models.Model):  
    user = models.OneToOneField(User)       
    name = models.CharField(max_length=50)
    UPS = models.CharField(max_length=50)

    def __unicode__(self):  
        return self.name




class product(models.Model):
    pid = models.AutoField(primary_key=True)
    description = models.CharField(max_length=100)
    rate = models.DecimalField(max_digits=5,decimal_places=2,default=Decimal('0.00'))
    rate_count = models.IntegerField(default=0)


class usr_review(models.Model):
    product = models.ForeignKey(product,on_delete=models.CASCADE)
    review_content = models.CharField(max_length=250,default='')
    user = models.CharField(max_length=50,default='annoymous')




class orders(models.Model):
    order_id = models.IntegerField(primary_key=True)
    user = models.ForeignKey(MyUser, on_delete=models.CASCADE,null = True)
    product = models.ForeignKey(product, blank = False)
    count = models.IntegerField(blank = False)
    warehouse = models.IntegerField(blank = False)
    tracking_num=models.CharField(max_length=50,default='Not Ready')
    ready = models.BooleanField(null= False, default=False)
    arrive = models.BooleanField(null= False, default=False)
    load = models.BooleanField(null= False, default=False)
    reviewed = models.BooleanField(null= False, default=False)
    def __unicode__(self):
        return self.product.description

