from django.shortcuts import render
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.humanize.templatetags.humanize import intcomma
from django.utils import timezone

import re
import csv
import string
import tweepy
import numpy
import marshal
import math
from datetime import datetime, timedelta
import time
import matplotlib

# Force matplotlib to not use any Xwindows backend.
matplotlib.use('Agg')
import matplotlib.pyplot as plt

import base64
import cStringIO as cStringIO
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas

from tweettrendsapp.models import Greeting
from tweettrendsapp.models import TopTrendingTweets
from tweettrendsapp.models import QueriedTerms

access_token = "TWITTER_ACCESS_TOKEN_HERE"
access_secret = "TWITTER_ACCESS_SECRET_HERE"
consumer_key = "TWITTER_CUSTOMER_KEY_HERE"
consumer_secret = "TWITTER_CUSTOMER_SECRET_HERE"


#auth = tweepy.auth.OAuthHandler(consumer_key, consumer_secret)
#auth.set_access_token(access_token, access_secret)


auth = tweepy.AppAuthHandler(consumer_key, consumer_secret)
api = tweepy.API(auth, wait_on_rate_limit=True, wait_on_rate_limit_notify=True)
WOEID_USA = 23424977
TIME_THRESH = 180
TOP_TRENDS = 10
TEST_LANGUAGE_TWEET_SIZE = 10
THRESH = 0.6
NUM_DAYS = 7
COUNT_TWEET_MAX = 50


def index(request):
    # Add to the context object
    context = dict()
    return render(request, 'index.html', context)


def about(request):

    context = dict()
    context['count_max_tweet'] = COUNT_TWEET_MAX

    return render(request, 'about.html', context)


def sentiment_query(request):
    context = dict()
    query_term = request.POST.get('query_term')
    count_pos = None
    count_neg = None

    if query_term is not None and query_term != u'':
        query_term = str(query_term)
        count_tweet = 0
        count_english_tweet = 0
        try:
            for tweet in tweepy.Cursor(api.search, q=query_term, async=True).items():
                count_tweet += 1
                if tweet.lang == "en":
                    count_english_tweet += 1

                if count_tweet > TEST_LANGUAGE_TWEET_SIZE:
                    break
        except:
            pass

        # add only english tweets
        if THRESH * count_tweet < count_english_tweet:
            donut_image, count_neg, count_pos = perform_sentiment_analysis_query_term(query_term)
            context['donut_image'] = donut_image

        queried_term_object = QueriedTerms()
        queried_term_object.query_term_tag = query_term
        queried_term_object.number_tweet_predicted_negative = count_neg
        queried_term_object.number_tweet_predicted_positive = count_pos
        queried_term_object.save()

        context['query_term'] = query_term

    return render(request, 'query_term.html', context)


def sentiment_top_trends(request):
    context = dict()
    # check if recently pulled
    flag_perform_classification = False
    tweet_trend_group = 1
    try:
        tweet_trend_group = TopTrendingTweets.objects.latest('tweet_trend_group').tweet_trend_group
        top_trending_tweets_list = TopTrendingTweets.objects.filter(tweet_trend_group=tweet_trend_group).order_by('created_date')
        top_trending_tweet = top_trending_tweets_list[0]

        current_time = timezone.now()
        #current_time = datetime.now(timezone.utc)
        created_time = top_trending_tweet.created_date
        elapsed_time = (current_time - created_time).total_seconds()
        print top_trending_tweet.created_date, current_time
        print elapsed_time

        if elapsed_time > TIME_THRESH:
            flag_perform_classification = True
            tweet_trend_group = TopTrendingTweets.objects.latest('tweet_trend_group').tweet_trend_group + 1
        else:
            top_us_trends_list_sorted = list()

            for i, top_trending_tweets in enumerate(top_trending_tweets_list):
                trend_dict = dict()
                query_tag = top_trending_tweets.tweet_trend_tag
                query_url = top_trending_tweets.tweet_trend_url

                trend_dict['url'] = query_url
                trend_dict['hashtag'] = query_tag
                if top_trending_tweets.tweet_trend_volume is None:
                    trend_dict['tweet_volume'] = 0
                    trend_dict['tweet_volume_formatted'] = 'NA'
                else:
                    tweet_volume = top_trending_tweets.tweet_trend_volume
                    trend_dict['tweet_volume'] = tweet_volume
                    trend_dict['tweet_volume_formatted'] = intcomma(tweet_volume)

                rank = top_trending_tweets.tweet_trend_rank
                count_neg = top_trending_tweets.number_tweet_predicted_negative
                count_pos = top_trending_tweets.number_tweet_predicted_positive

                if count_neg is not None and count_pos:
                    count_tweet = count_neg + count_pos
                    context = generate_sentiment_plot(count_neg, count_pos, count_tweet, query_tag, query_url, rank-1, context)[0]

                top_us_trends_list_sorted.append(trend_dict)

            context['top_us_trends_list'] = top_us_trends_list_sorted
            print "Here: Reading From File"
        # use this to generate plots
    except ObjectDoesNotExist:
        flag_perform_classification = True

    if flag_perform_classification:
        start_time = time.time()
        context, top_us_trends_list_sorted = identify_top_trends(context)
        print "There: Identify Top Trends", time.time() - start_time
        start_time = time.time()
        context = perform_sentiment_analysis_live_tweets(context, tweet_trend_group)
        print "There: Perform sentiment analysis", time.time() - start_time

    return render(request, 'top_trends.html', context)


def identify_top_trends(context):
    top_us_trends = api.trends_place(WOEID_USA)
    top_us_trends_list = list()

    start_time = time.time()
    print "Identify top trends"
    print len(top_us_trends[0]['trends'])

    for i, trend in enumerate(top_us_trends[0]['trends']):
        count_tweet = 0
        count_english_tweet = 0
        try:
            for tweet in tweepy.Cursor(api.search, q=trend.get('name'), async=True).items():
                count_tweet += 1
                if tweet.lang == "en":
                    count_english_tweet += 1

                if count_tweet > TEST_LANGUAGE_TWEET_SIZE:
                    break
        except:
            pass

        # add only english tweets
        if THRESH * count_tweet < count_english_tweet:
            trend_dict = dict()
            trend_dict['url'] = trend.get('url')
            if trend.get('tweet_volume') is None:
                trend_dict['tweet_volume'] = 0
                trend_dict['tweet_volume_formatted'] = 'NA'
            else:
                trend_dict['tweet_volume'] = trend.get('tweet_volume')
                trend_dict['tweet_volume_formatted'] = intcomma(trend.get('tweet_volume'))
            trend_dict['hashtag'] = trend.get('name')
            trend_dict['query'] = trend.get('query')
            top_us_trends_list.append(trend_dict)

    print "There: Top Trends List Generated", time.time() - start_time
    top_us_trends_list_sorted = sorted(top_us_trends_list, key=lambda top_us_trends_list: (-top_us_trends_list['tweet_volume']))

    if len(top_us_trends_list_sorted) > TOP_TRENDS:
        context['top_us_trends_list'] = top_us_trends_list_sorted[:TOP_TRENDS]
    else:
        context['top_us_trends_list'] = top_us_trends_list_sorted

    return context, top_us_trends_list_sorted


def perform_sentiment_analysis_query_term(query_term):
    current_time = datetime.now().date() + timedelta(days=1)
    week_ago_time = (current_time - timedelta(days=NUM_DAYS))
    # train the classifier
    vocabulary, word_likelihood, prior_probabilities = train_classifier()
    count_tweet = 1
    count_pos = 0
    count_neg = 0
    for tweet in tweepy.Cursor(api.search, q=query_term, since=week_ago_time, until=current_time, lang="en", async=True).items():
        if not tweet.retweeted and tweet.lang == "en":
            count_tweet += 1
            input_tweet = tweet.text
            class_index, class_label, predict_ch = tweet_classify(input_tweet, vocabulary, word_likelihood, prior_probabilities)

            if class_index == 0:
                count_neg += 1
            else:
                count_pos += 1

            if count_tweet > COUNT_TWEET_MAX:
                break

    graph = generate_sentiment_plot(count_neg, count_pos, count_tweet)[1]
    return graph, count_neg, count_pos


def perform_sentiment_analysis_live_tweets(context, tweet_trend_group):
    flag_test_classifier = False
    # train the classifier
    vocabulary, word_likelihood, prior_probabilities = train_classifier()
    if flag_test_classifier:
        test_classifier(vocabulary, word_likelihood, prior_probabilities)

    current_time = datetime.now().date() + timedelta(days=1)
    week_ago_time = (current_time - timedelta(days=NUM_DAYS))

    top_us_trends_list_sorted = context['top_us_trends_list']
    # prepare for saving
    top_trending_tweets_list = list()
    for i, trend in enumerate(top_us_trends_list_sorted):
        top_trending_tweets = TopTrendingTweets()
        top_trending_tweets.tweet_trend_tag = trend.get('hashtag')
        top_trending_tweets.tweet_trend_url = trend.get('url')
        top_trending_tweets.tweet_trend_rank = i+1
        if trend.get('tweet_volume_formatted') != 'NA':
            top_trending_tweets.tweet_trend_volume = trend.get('tweet_volume')
        top_trending_tweets.tweet_trend_group = tweet_trend_group
        top_trending_tweets_list.append(top_trending_tweets)

    for ind, trend in enumerate(top_us_trends_list_sorted[:3]):
        count_tweet = 1
        count_pos = 0
        count_neg = 0
        query_tag = trend.get('hashtag')
        query_url = trend.get('url')
        for tweet in tweepy.Cursor(api.search, q=query_tag, since=week_ago_time, until=current_time, lang="en", async=True).items():
            if not tweet.retweeted and tweet.lang == "en":
                #print tweet
                #print count_tweet, tweet.id, tweet.text
                count_tweet += 1
                input_tweet = tweet.text
                class_index, class_label, predict_ch = tweet_classify(input_tweet, vocabulary, word_likelihood, prior_probabilities)

                if class_index == 0:
                    count_neg += 1
                else:
                    count_pos += 1

                if count_tweet > COUNT_TWEET_MAX:
                    break

        print query_tag, count_pos, count_neg, count_tweet

        top_trending_tweets = top_trending_tweets_list[ind]
        top_trending_tweets.number_tweet_predicted_negative = count_neg
        top_trending_tweets.number_tweet_predicted_positive = count_pos

        context = generate_sentiment_plot(count_neg, count_pos, count_tweet, query_tag, query_url, ind, context)[0]

    # save in the database
    for top_trending_tweets in top_trending_tweets_list:
        # check if already saved
        tweet_trend_group = top_trending_tweets.tweet_trend_group
        tweet_trend_rank = top_trending_tweets.tweet_trend_rank
        top_trending_tweet_object = TopTrendingTweets.objects.filter(tweet_trend_group=tweet_trend_group, tweet_trend_rank=tweet_trend_rank)

        if not top_trending_tweet_object:
            top_trending_tweets.save()

    return context


def generate_sentiment_plot(count_neg, count_pos, count_tweet, query_tag=None, query_url=None, index=0, context=None):
    donut_image = None
    if count_tweet > 0:
        fig, ax = plt.subplots(figsize=(4.5, 4.5), frameon=False)
        kwargs = dict(colors=['#FF4500', '#9ACD32'], labels=['-', '+'], startangle=90)
        outside = pie(ax, [100 * count_neg/float(count_tweet), 100 * count_pos/float(count_tweet)], radius=1, pctdistance=1 - 0.5 / 2, **kwargs)
        plt.setp(outside, width=0.5, edgecolor=(1, 1, 1))
        # plt.legend(loc='upper left', numpoints=1, fancybox=True, shadow=True, ncol=1)
        # Shrink current axis's height by 10% on the bottom
        box = ax.get_position()
        ax.set_position([box.x0, box.y0 + box.height * 0, box.width, box.height * 1])

        # Put a legend below current axis
        ax.legend(loc='upper center', bbox_to_anchor=(0.5, 1.1), fancybox=True, shadow=True, ncol=2)

        canvas_scatter = FigureCanvas(fig)
        output_str_scatter = cStringIO.StringIO()
        canvas_scatter.print_png(output_str_scatter)
        # Add to the context object
        donut_image = base64.b64encode(output_str_scatter.getvalue())
        if context is not None:
            context["donut_image" + str(index + 1)] = donut_image
            context["query_tag" + str(index + 1)] = query_tag
            context["query_url" + str(index + 1)] = query_url
        output_str_scatter.close()

    return context, donut_image


def database_info(request):

    greeting = Greeting()
    greeting.save()

    greetings = Greeting.objects.all()

    return render(request, 'db.html', {'greetings': greetings})


def train_classifier():
    DATA_DIRECTORY_PATH = settings.BASE_DIR + "/tweettrendsapp/templates/tweettrendsapp/"
    try:
        "-----Loading Processed Data-----"
        prior_probabilities_file = open(DATA_DIRECTORY_PATH + 'prior_probabilities.dat', 'rb')
        prior_probabilities = marshal.load(prior_probabilities_file)
        prior_probabilities_file.close()

        # save results
        vocabulary_file = open(DATA_DIRECTORY_PATH + 'vocabulary.dat', 'rb')
        vocabulary = marshal.load(vocabulary_file)
        vocabulary_file.close()

        word_likelihood_file = open(DATA_DIRECTORY_PATH + 'word_likelihood_dict.dat', 'rb')
        word_likelihood = marshal.load(word_likelihood_file)
        word_likelihood_file.close()

    except IOError:
        "-----Unavailable Processed Data. Processing Again. -----"
        filename_training = DATA_DIRECTORY_PATH + 'training.1600000.processed.noemoticon.csv'

        cnt_pos = 0
        cnt_neg = 0
        word_list = list()
        word_list_neg = list()
        word_list_pos = list()
        # open the file
        file_training = open(filename_training, 'rb')
        reader = csv.reader(file_training)
        cnt_tweets = 0
        training_data = list()
        training_label = list()
        # read each line and extract tweet words
        for row in reader:
            input_tweet_label = row[0]
            input_tweet = row[1]
            processed_tweet = process_tweet_text(input_tweet)

            if int(input_tweet_label) == 0 or int(input_tweet_label) == 4:
                training_label.append(input_tweet_label)
                training_data.append(processed_tweet)

                if int(input_tweet_label) == 0:
                    cnt_neg += 1
                    for token in processed_tweet:
                        word_list_neg.append(token)
                        word_list.append(token)
                else:
                    cnt_pos += 1
                    for token in processed_tweet:
                        word_list_pos.append(token)
                        word_list.append(token)

            # increment tweets
            cnt_tweets += 1
            #close the file
        file_training.close()

        #identify the unique words
        vocabulary = list(set(word_list))
        n_voc = len(vocabulary)
        n_word_pos = len(word_list_pos)
        n_word_neg = len(word_list_neg)
        print '\tNo. of Tweets = ', cnt_tweets
        print '\tNo. of Positive Tweets = ', cnt_pos
        print '\tNo. of Negative Tweets = ', cnt_neg
        print '\tWord Size = ', len(word_list)
        print '\tWords in Positive Examples = ', n_word_pos
        print '\tWords in Negative Examples = ', n_word_neg
        print '\tVocabulary Size = ', n_voc
        #initialize Frequency variables
        word_frequency = numpy.zeros((2, n_voc))
        word_likelihood = numpy.zeros((2, n_voc))
        #Estimate the likelihood model
        for i, word in enumerate(vocabulary):
            # count words from first class
            cnt_word_pos = word_list_pos.count(word)
            # count words from second class
            cnt_word_neg = word_list_neg.count(word)
            # Fill the Frequency and probability table
            word_frequency[0, i] = cnt_word_neg
            word_frequency[1, i] = cnt_word_pos
            word_likelihood[0, i] = float(cnt_word_neg + 1)/float(n_word_neg + n_voc)
            word_likelihood[1, i] = float(cnt_word_pos + 1)/float(n_word_pos + n_voc)
            #Estimate the Prior model
        prior_probabilities = numpy.zeros((2, 1))
        prior_probabilities[0, 0] = float(cnt_neg)/float(cnt_neg + cnt_pos)
        prior_probabilities[1, 0] = float(cnt_pos)/float(cnt_neg + cnt_pos)
        print '\tPrior Probabilities: ', prior_probabilities[0, 0], prior_probabilities[1, 0]
        # save results
        vocabulary_file = open(DATA_DIRECTORY_PATH + 'vocabulary.dat', 'wb')
        marshal.dump(vocabulary, vocabulary_file)
        vocabulary_file.close()

        prior_probabilities_file = open(DATA_DIRECTORY_PATH + 'prior_probabilities.dat', 'wb')
        marshal.dump(prior_probabilities.tolist(), prior_probabilities_file)
        prior_probabilities_file.close()

        word_likelihood_file = open(DATA_DIRECTORY_PATH + 'word_likelihood.dat', 'wb')
        marshal.dump(word_likelihood.tolist(), word_likelihood_file)
        word_likelihood_file.close()

        word_likelihood_dict = dict()
        for i, word in enumerate(vocabulary):
            word_likelihood_dict[word] = [word_likelihood[0][i], word_likelihood[1][i]]

        word_likelihood_dict_file = open('word_likelihood_dict.dat', 'wb')
        marshal.dump(word_likelihood_dict, word_likelihood_dict_file)
        word_likelihood_dict_file.close()

        word_likelihood = word_likelihood.tolist()
        prior_probabilities = prior_probabilities.tolist()

    return vocabulary, word_likelihood, prior_probabilities


def test_classifier(vocabulary, word_likelihood, prior_probabilities):
    DATA_DIRECTORY_PATH = settings.BASE_DIR + "/tweettrendsapp/templates/tweettrendsapp/"
    filename_testing = DATA_DIRECTORY_PATH + 'testdata.manual.2009.06.14.csv'
    #open the file
    file_testing = open(filename_testing, 'rb')
    reader = csv.reader(file_testing)
    count = 0
    count_correct = 0
    print 'Predict\tExpect\t Tweets'
    print '='*150
    #read each line and extract tweet words
    for row in reader:
        input_tweet_label = row[0]
        if int(input_tweet_label) == 0 or int(input_tweet_label) == 4:
            input_tweet = row[1]
            class_index, class_label, predict_ch = tweet_classify(input_tweet, vocabulary, word_likelihood, prior_probabilities)
            # assign the class label from the index
            if int(input_tweet_label) == 0:
                expect_ch = '-'
            else:
                expect_ch = '+'
            # count the number of correct predictions
            if class_label == int(row[0]):
                count_correct += 1
            #count the number of testing tweets
            count += 1
            #display the predictions and data
            print '   ' + predict_ch + '\t   ' + expect_ch + '\t' + input_tweet
    # display the accuracy
    print '='*150
    print '\t Accurately Identified: ' + str(count_correct) +'\n\t Total: ' + str(count) + '\n\t Percentage Accuracy : ' + str( 100* round(float(count_correct)/count,3))+'%'
    print '='*150


def tweet_classify(input_tweet, vocabulary, word_likelihood, prior_probabilities):
    processed_tweet = process_tweet_text(input_tweet)
    # compute the posterior probability of the doc
    posterior_probability = numpy.zeros((len(prior_probabilities), 1))
    log_likelihood = numpy.zeros((len(prior_probabilities), 1))
    for token in processed_tweet:
        # check if word exist in vocabulary and compute posterior if so
        token_data = word_likelihood.get(token)
        if token_data is not None:
            # compute log likelihood
            log_likelihood[0] += math.log(token_data[0], 2)
            log_likelihood[1] += math.log(token_data[1], 2)

        '''

        if token in vocabulary:
            # Extract index
            index = vocabulary.index(token)
            # compute log likelihood
            log_likelihood[0] += math.log(word_likelihood[0][index], 2)
            log_likelihood[1] += math.log(word_likelihood[1][index], 2)

        '''

    # incorporate prior to compute posterior
    posterior_probability[0] = log_likelihood[0] + math.log(prior_probabilities[0][0], 2)
    posterior_probability[1] = log_likelihood[1] + math.log(prior_probabilities[1][0], 2)

    # extract the Maximum
    class_index = posterior_probability.argmax(axis=0)
    # assign the class label from the index
    if class_index == 0:
        class_label = 0
        predict_ch = '-'
    else:
        class_label = 4
        predict_ch = '+'

    return class_index, class_label, predict_ch


def process_tweet_text(input_tweet):
    processed_tweet = list()
    # substitute tweet account names by USER from the tweet messages
    str1 = re.sub(r'@\w+', 'USER', input_tweet)
    # substitute hash-tag keywords
    str2 = re.sub(r'#\w+', 'HASHTAG', str1)
    # split the tweets using space and delete any non-letter characters
    words = re.findall('[%s]+' % string.ascii_letters, str2)
    #append each words to the database
    for str3 in words:
        #remove character duplicacy e.g lool, looooool -> lool
        processed_tweet.append(remove_successive_duplicate_characters(str3.lower()))

    return processed_tweet


# remove duplicate letters. eg. loooooooool, loooool, looool -> lool
def remove_successive_duplicate_characters(input_word):
    # initialize variables
    output_word = ''
    # initialize index
    ind = 0
    # iterate until end of word
    while ind < len(input_word):
        # extract character
        ch = input_word[ind]
        cnt = 0
        # check if repeated and count the number of character repetition
        for i in range(ind+1, len(input_word)):
            if ch == input_word[i]:
                cnt += 1
            else:
                break
        # append character if unique and duplicate twice, otherwise shorten to two characters
        if cnt == 0:
            output_word = output_word + ch
        else:
            output_word = output_word + ch+ ch
        # increment index
        ind += cnt+1
    #return result
    return output_word


def pie(ax, values, **kwargs):
    def formatter(pct):
        return '{:0.1f}%'.format(pct)

    wedges, _, labels = ax.pie(values, autopct=formatter, **kwargs)
    return wedges