# Generated by Django 2.2.4 on 2019-12-17 19:38

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('tom_targets', '0012_target_color'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='target',
            name='color',
        ),
    ]