__author__ = 'mdema'

import csv

filename='training.1600000.processed.noemoticon.csv'

processed_data = []
f=open(filename, 'rb')
reader = csv.reader(f)
#read each line and extract tweet words
for row in reader:
    processed_data.append([row[0], row[5]])

with open('training.1600000.processed.noemoticon_new.csv', 'wb') as ofile2:
    writer = csv.writer(ofile2, delimiter=',')
    writer.writerows(processed_data)