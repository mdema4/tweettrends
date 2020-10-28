# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('tweettrendsapp', '0003_auto_20160609_1828'),
    ]

    operations = [
        migrations.CreateModel(
            name='QueriedTerms',
            fields=[
                ('query_term_id', models.AutoField(serialize=False, primary_key=True)),
                ('query_term_tag', models.CharField(max_length=1000, null=True, blank=True)),
                ('number_tweet_predicted_negative', models.IntegerField(null=True, blank=True)),
                ('number_tweet_predicted_positive', models.IntegerField(null=True, blank=True)),
                ('created_date', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'db_table': 'queried_terms',
                'managed': True,
            },
        ),
    ]
