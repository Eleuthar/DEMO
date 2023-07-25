from django.db import models

"""
SPORT name
MARKET name, sport
SELECTION name, odds, market
MATCH name, start_time, sport, market, \\ ordering, verbose_name_plural
"""

class Sport(models.Model):
	name = CharField(max_length=100)
	
	def __str__():
		return name
		

class Market(models.Model):
	name = CharField(max_length=100)
	sport = models.ForeignKey(Sport, on_delete=CASCADE)
	
	

