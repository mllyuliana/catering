# Generated by Django 5.2.1 on 2025-06-01 18:43

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('menu', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='menutype',
            name='image',
            field=models.ImageField(blank=True, null=True, upload_to='menu_types/', verbose_name='Изображение'),
        ),
    ]
