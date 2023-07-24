# Generated by Django 4.2.2 on 2023-06-26 11:20

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('pokedex_app', '0002_alter_move_options'),
    ]

    operations = [
        migrations.AlterField(
            model_name='move',
            name='pokemon',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='moves', to='pokedex_app.pokemon'),
        ),
    ]