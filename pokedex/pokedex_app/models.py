from django.db import models

class Pokemon(models.Model):
    name = models.CharField(max_length=100)
    mon_type = models.CharField(max_length=100)
    height = models.IntegerField()
    weight = models.IntegerField()
    xp = models.IntegerField()
    attack = models.IntegerField()
    defense = models.IntegerField()
    special_attack = models.IntegerField()
    special_defense = models.IntegerField()
    speed = models.IntegerField()

    class Meta:
        verbose_name_plural = 'Pokemons'

    def __str__(self):
        return self.name

class Move(models.Model):
    move_name = models.CharField(max_length=100)
    pokemon = models.ForeignKey(Pokemon, on_delete=models.CASCADE)

    class Meta:
        verbose_name_plural = 'Move'

    def __str__(self):
        return f"{self.move_name}"
