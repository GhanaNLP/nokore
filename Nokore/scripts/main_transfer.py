import time

import numpy as np
import pandas as pd
import random

from Simon import Simon 
from Simon.Encoder import Encoder
from Simon.LengthStandardizer import DataLengthStandardizerRaw

start_time = time.time()

### Read-in the emails and print some basic statistics

# Enron
EnronEmails = pd.read_csv('data/enron_emails_body.csv',dtype='str', header=None)
print("The size of the Enron emails dataframe is:")
print(EnronEmails.shape)
print("Ten Enron emails are:")
print(EnronEmails.loc[:10])

# Spam
SpamEmails = pd.read_csv('data/fraudulent_emails_body.csv',encoding="ISO-8859-1",dtype='str', header=None)
print("The size of the Spam emails dataframe is:")
print(SpamEmails.shape)
print("Ten Spam emails are:")
print(SpamEmails.loc[:10])

# Some hyper-parameters for the CNN we will use
maxlen = 20 # max length of each tabular cell <==> max number of characters in a line
max_cells = 500 # max number of cells in a column <==> max number of email lines
p_threshold = 0.5 # prediction threshold probability
Nsamp = 1000
nb_epoch = 20
batch_size = 8

checkpoint_dir = "pretrained_models/"
execution_config = 'Base.pkl'

DEBUG = True # boolean to specify whether or not print DEBUG information

# Convert everything to lower-case, put one sentence per column in a tabular
# structure
ProcessedEnronEmails=[row.lower().split('\n') for row in EnronEmails.iloc[:,1]]
#print("3 Enron emails after Processing (in list form) are:")
#print((ProcessedEnronEmails[:3]))
EnronEmails = pd.DataFrame(random.sample(ProcessedEnronEmails,Nsamp)).transpose()
EnronEmails = DataLengthStandardizerRaw(EnronEmails,max_cells)
#print("Ten Enron emails after Processing (in DataFrame form) are:")
#print((EnronEmails[:10]))
print("Enron email dataframe after Processing shape:")
print(EnronEmails.shape)

ProcessedSpamEmails=[row.lower().split('/n') for row in SpamEmails.iloc[:,1]]
#print("3 Spam emails after Processing (in list form) are:")
#print((ProcessedSpamEmails[:3]))
SpamEmails = pd.DataFrame(random.sample(ProcessedSpamEmails,Nsamp)).transpose()
SpamEmails = DataLengthStandardizerRaw(SpamEmails,max_cells)
#print("Ten Spam emails after Processing (in DataFrame form) are:")
#print((SpamEmails[:10]))
print("Spam email dataframe after Processing shape:")
print(SpamEmails.shape)

# orient the user a bit
with open('pretrained_models/Categories.txt','r') as f:
    Categories = f.read().splitlines()
print("former categories are: ")
Categories = sorted(Categories)
print(Categories)
category_count_prior = len(Categories)

# Load pretrained model via specified execution configuration
Classifier = Simon(encoder={}) # dummy text classifier
config = Classifier.load_config(execution_config, checkpoint_dir)
encoder = config['encoder']
checkpoint = config['checkpoint']

# Encode labels and data
Categories = ['spam','notspam']
category_count = len(Categories)
encoder.categories=Categories
header = ([['spam',]]*Nsamp)
header.extend(([['notspam',]]*Nsamp))

#print(header)

raw_data = np.column_stack((SpamEmails,EnronEmails)).T

print("DEBUG::raw_data:")
print(raw_data)

encoder.process(raw_data, max_cells)
X, y = encoder.encode_data(raw_data, header, maxlen)



# build classifier model
model = Classifier.generate_transfer_model(maxlen, max_cells, category_count_prior,category_count, checkpoint, checkpoint_dir,activation='sigmoid')
#Classifier.load_weights(checkpoint, None, model, checkpoint_dir)
model_compile = lambda m: m.compile(loss='binary_crossentropy', optimizer='adam', metrics=['binary_accuracy'])
model_compile(model)

#y = model.predict(X)
# discard empty column edge case
# y[np.all(frame.isnull(),axis=0)]=0
#result = encoder.reverse_label_encode(y,p_threshold)
### FINISHED LABELING COMBINED DATA AS CATEGORICAL/ORDINAL
#print("The predicted classes and probabilities are respectively:")
#print(result)

data = Classifier.setup_test_sets(X, y)
start = time.time()
history = Classifier.train_model(batch_size, checkpoint_dir, model, nb_epoch, data)
end = time.time()
print("Time for training is %f sec"%(end-start))
config = { 'encoder' :  encoder,
           'checkpoint' : Classifier.get_best_checkpoint(checkpoint_dir) }
Classifier.save_config(config, checkpoint_dir)
Classifier.plot_loss(history) #comment out on docker images...
        
pred_headers = Classifier.evaluate_model(max_cells, model, data, encoder, p_threshold)
#print("DEBUG::The predicted headers are:")
#print(pred_headers)
#print("DEBUG::The actual headers are:")
#print(header)
elapsed_time = time.time()-start_time
print("Total script execution time is : %.2f sec" % elapsed_time)