# Generated by Django 3.2.18 on 2023-03-21 21:32

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('anno', '0006_auto_20190701_1508'),
    ]

    operations = [
        migrations.AlterField(
            model_name='anno',
            name='raw',
            field=models.JSONField(),
        ),
        migrations.AlterField(
            model_name='tag',
            name='id',
            field=models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID'),
        ),
        migrations.AlterField(
            model_name='target',
            name='id',
            field=models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID'),
        ),
    ]
