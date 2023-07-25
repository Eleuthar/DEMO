from django.db import models


class Friend(models.Model):
	name = Model.CharField(max_length=100)
	
	
class Belonging(models.Model):
	name = Model.CharField(max_length=100)
	
	
class Borrowing(models.Model):
	what = models.ForeignKey(Belonging, on_delete=CASCADE)
	to_who = models.ForeignKey(Friend, on_delete=CASCADE)
	when = models.DateTimeField(auto_now=True)
	returned = models.DateTimeField(null=True, blank=True)
	

