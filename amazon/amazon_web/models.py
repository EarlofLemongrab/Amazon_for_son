from __future__ import unicode_literals

from django.db import models
from django.contrib.auth.models import User
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







class orders(models.Model):

    user = models.ForeignKey(MyUser, on_delete=models.CASCADE,null = True)
    product = models.OneToOneField(product, blank = False)
    count = models.IntegerField(blank = False)
    warehouse = models.IntegerField(blank = False)
    tracking_num=models.CharField(max_length=50,default='Not Ready')
    ready = models.BooleanField(null= False, default=False)
    arrive = models.BooleanField(null= False, default=False)
    load = models.BooleanField(null= False, default=False)
    def __unicode__(self):
        return self.product.description

