# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Greeting',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('when', models.DateTimeField(auto_now_add=True, verbose_name=b'date created')),
            ],
        ),
        migrations.CreateModel(
            name='TopTrendingTweets',
            fields=[
                ('tweet_trend_id', models.AutoField(serialize=False, primary_key=True)),
                ('tweet_trend_tag', models.CharField(max_length=1000, null=True, blank=True)),
                ('tweet_trend_url', models.CharField(max_length=1000, null=True, blank=True)),
                ('tweet_trend_volume', models.IntegerField()),
                ('tweet_trend_group', models.IntegerField()),
                ('number_tweet_predicted_negative', models.IntegerField()),
                ('number_tweet_predicted_positive', models.IntegerField()),
                ('created_date', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'db_table': 'top_trending_tweets',
                'managed': True,
            },
        ),
    ]
