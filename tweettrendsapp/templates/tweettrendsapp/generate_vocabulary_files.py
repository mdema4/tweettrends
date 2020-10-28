__author__ = 'mdema'

import csv
import re
import marshal
import string
import numpy


def train_classifier():
    try:
        "-----Loading Processed Data-----"
        prior_probabilities_file = open( 'prior_probabilities.dat', 'rb')
        prior_probabilities = marshal.load(prior_probabilities_file)
        prior_probabilities_file.close()

        # save results
        vocabulary_file = open('vocabulary.dat', 'rb')
        vocabulary = marshal.load(vocabulary_file)
        vocabulary_file.close()

        word_likelihood_file = open('word_likelihood.dat', 'rb')
        word_likelihood = marshal.load(word_likelihood_file)
        word_likelihood_file.close()

    except IOError:
        "-----Unavailable Processed Data. Processing Again. -----"
        filename_training = 'training.1600000.processed.noemoticon.csv'
        filename_testing = 'testdata.manual.2009.06.14.csv'

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
            print cnt_tweets

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

            print i, word
            #Estimate the Prior model
        prior_probabilities = numpy.zeros((2, 1))
        prior_probabilities[0, 0] = float(cnt_neg)/float(cnt_neg + cnt_pos)
        prior_probabilities[1, 0] = float(cnt_pos)/float(cnt_neg + cnt_pos)
        print '\tPrior Probabilities: ', prior_probabilities[0, 0], prior_probabilities[1, 0]
        # save results
        vocabulary_file = open('vocabulary.dat', 'wb')
        marshal.dump(vocabulary, vocabulary_file)
        vocabulary_file.close()

        prior_probabilities_file = open('prior_probabilities.dat', 'wb')
        marshal.dump(prior_probabilities.tolist(), prior_probabilities_file)
        prior_probabilities_file.close()

        word_likelihood_file = open('word_likelihood.dat', 'wb')
        marshal.dump(word_likelihood.tolist(), word_likelihood_file)
        word_likelihood_file.close()

        word_likelihood = word_likelihood.tolist()
        prior_probabilities = prior_probabilities.tolist()

    return vocabulary, word_likelihood, prior_probabilities


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


train_classifier()