# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('tweettrendsapp', '0002_toptrendingtweets_tweet_trend_rank'),
    ]

    operations = [
        migrations.AlterField(
            model_name='toptrendingtweets',
            name='number_tweet_predicted_negative',
            field=models.IntegerField(null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='toptrendingtweets',
            name='number_tweet_predicted_positive',
            field=models.IntegerField(null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='toptrendingtweets',
            name='tweet_trend_volume',
            field=models.IntegerField(null=True, blank=True),
        ),
    ]
