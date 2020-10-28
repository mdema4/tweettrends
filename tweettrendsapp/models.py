from django.db import models


class TopTrendingTweets(models.Model):
    tweet_trend_id = models.AutoField(primary_key=True)
    tweet_trend_tag = models.CharField(max_length=1000, blank=True, null=True)
    tweet_trend_url = models.CharField(max_length=1000, blank=True, null=True)
    tweet_trend_volume = models.IntegerField(blank=True, null=True)
    tweet_trend_rank = models.IntegerField()
    tweet_trend_group = models.IntegerField()
    number_tweet_predicted_negative = models.IntegerField(blank=True, null=True)
    number_tweet_predicted_positive = models.IntegerField(blank=True, null=True)
    created_date = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = True
        db_table = 'top_trending_tweets'


class QueriedTerms(models.Model):
    query_term_id = models.AutoField(primary_key=True)
    query_term_tag = models.CharField(max_length=1000, blank=True, null=True)
    number_tweet_predicted_negative = models.IntegerField(blank=True, null=True)
    number_tweet_predicted_positive = models.IntegerField(blank=True, null=True)
    created_date = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = True
        db_table = 'queried_terms'


class Greeting(models.Model):
    when = models.DateTimeField('date created', auto_now_add=True)
