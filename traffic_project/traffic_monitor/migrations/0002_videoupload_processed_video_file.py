# Generated by Django 5.2.1 on 2025-05-29 18:14

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('traffic_monitor', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='videoupload',
            name='processed_video_file',
            field=models.FileField(blank=True, null=True, upload_to='processed_videos/'),
        ),
    ]
