from django.db import models


class Sport(models.Model):
	name = models.CharField(max_length=123)
	
	def __str__(self):
		return self.name
	

class Market(models.Model):
	name = models.CharField(max_length=123)
	sport = models.ForeignKey(
		Sport, 
		on_delete=models.CASCADE, 
		related_name='markets'
	)
	
	def __str__(self):
		return self.name + ' | ' + self.sport.name
		
		
class Selection(models.Model):
	name = models.CharField(max_length=123)
	oddz = models.FloatField()
	market = models.ForeignKey(
		Market, 
		on_delete=models.CASCADE,
		related_name = "selections"
	)
	

class Match(models.Model):
	name = models.CharField(max_length=123)
	start_time = models.DateTimeField()
	sport = models.ForeignKey(
		Sport,
		on_delete=models.CASCADE,
		related_name = 'matches'
	)
	market = models.ForeignKey(
		Market,
		on_delete=models.CASCADE,
		related_name = 'matches'
	)
	
	class Meta:
		ordering = ('start_time',),
		verbose_name_plural = 'Matches'
		
	def __str__(self):
		return self.name
	
