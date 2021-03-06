import os
import warnings
import sys
import argparse


from sklearn.exceptions import UndefinedMetricWarning
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import accuracy_score
from sklearn.metrics import f1_score
from sklearn.metrics import recall_score
from sklearn.utils import compute_class_weight



import torch
from torch.utils.data import DataLoader



from config import EMB_PATH
from dataloading import SentenceDataset
from models import BaselineDNN
from training import train_dataset, eval_dataset
from utils.load_datasets import load_MR, load_Semeval2017A
from utils.load_embeddings import load_word_vectors


from models.BaselineDNN import BaselineDNN
from models.LSTMNet import LSTMNet
from models.LSTMpool import LSTMpool
from models.NN_Attention import NN_Attention
from models.LSTM_Attention import LSTM_Attention
from models.BiLSTM_Attention import BiLSTM_Attention
from models.BiLSTMpool import BiLSTMpool



import numpy as np
import matplotlib 
import math
from matplotlib import pyplot as plt





warnings.filterwarnings("ignore", category=UndefinedMetricWarning)

########################################################
# Configuration
########################################################


# Download the embeddings of your choice
# for example http://nlp.stanford.edu/data/glove.6B.zip

# 1 - point to the pretrained embeddings file (must be in /embeddings folder)
FILENAME = "glove.twitter.27B.50d.txt" # or 'glove.twitter.27B.50d.txt'
EMBEDDINGS = os.path.join(EMB_PATH, FILENAME)

# 2 - set the correct dimensionality of the embeddings
EMB_DIM = 50

EMB_TRAINABLE = False
BATCH_SIZE = 128
EPOCHS = 25
DATASET = "Semeval2017A"  # options: "MR", "Semeval2017A"
MODEL =  'LSTM_Attention'    # options: 'BaselineDNN', 'LSTMNet', 'LSTMpool', 'NN_Attention', 'LSTM_Attention', 'BiLSTM_Attention', 'BiLSTMpool'
# if your computer has a CUDA compatible gpu use it, otherwise use the cpu
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

########################################################
# Define PyTorch datasets and dataloaders
########################################################

# load word embeddings
print("loading word embeddings...")
word2idx, idx2word, embeddings = load_word_vectors(EMBEDDINGS, EMB_DIM)

# load the raw data
if DATASET == "Semeval2017A":
    X_train, y_train, X_test, y_test = load_Semeval2017A()
elif DATASET == "MR":
    X_train, y_train, X_test, y_test = load_MR()
else:
    raise ValueError("Invalid dataset")

print('Sentiment Analysis')
print("Dataset: " + DATASET)
print("Embeddings: " + FILENAME)
print("Embeddings dimension: " + str(EMB_DIM))
print("Batch size: " + str(BATCH_SIZE))
print("Number of epochs: " + str(EPOCHS))
print("Model to be used: " + MODEL)
print("Device available: " + str(DEVICE))

#############################################################################
# Question 1
#############################################################################
# convert data labels from strings to integers

"""
print("\n\n\n~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")
print("QUESTION 1 - convert data labels from strings to integers\n")
"""

le = LabelEncoder()
le.fit(y_test)
y_train_original = y_train
y_test_original = y_test
y_train = list(le.transform(y_train))  # EX1
y_test = list(le.transform(y_test))  # EX1
n_classes = le.classes_.size  # EX1 - LabelEncoder.classes_.size

#############################################################################
# Question 2
#############################################################################
# Define our PyTorch-based Dataset

"""
print("\n\n\n~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")
print("QUESTION 2 - Define our PyTorch-based Dataset\n")
"""

train_set = SentenceDataset(X_train, y_train, word2idx)
test_set = SentenceDataset(X_test, y_test, word2idx)

"""
for i in range(10):
    print("sentence no.",i+1,": ")
    print(" ".join(X_train[i]))
    print("\nthis is returned by the class as: \n")
    print(train_set.data[i], "\n")


#############################################################################
# Question 3
#############################################################################
# Calculating the max length of training strings, to configure zero-padding

print("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")
print("\n\n\nQUESTION 3 - Calculating the max length of training strings, to configure zero-padding\n")

lengths = [len(x) for x in train_set.data]
average_length = int(np.mean(lengths))
max_length = max(lengths)
print("The average length of each sentiment is: " , average_length)
print("The maximum length of each sentiment is: " , max_length,"\n")
#we choose to keep every sentiment, so there is no data rejection, and therefore the 
#zero padding will be equal to max_len - len(sentiment).
for i in range(5):
    print("\nSentence embedding ",i+1)
    print("sentence: ", X_train[i],", target: ",y_train_original[i])
    print("sentence's word embedding: ",train_set[i][0], ", label: ",train_set[i][1] )
    print()

"""

# EX4 - Define our PyTorch-based DataLoader
train_loader = DataLoader(dataset=train_set, batch_size=BATCH_SIZE, shuffle=True)  # EX7
test_loader =  DataLoader(dataset=test_set, batch_size=BATCH_SIZE, shuffle=False)  # EX7



#############################################################################
# Question 4,5
#############################################################################
#Initializing the NN:

"""
print("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")
print("\n\n\nQUESTION 4,5 - Initializing the NN:\n")
"""
magkas = getattr(sys.modules[__name__], MODEL)
model = magkas(output_size=n_classes,  # EX8
                    embeddings=embeddings,
                    trainable_emb=EMB_TRAINABLE)

# move the mode weight to cpu or gpu
model.to(DEVICE)
print(model)



#############################################################################
# Question 8
#############################################################################
#Model Definition (Model, Loss Function, Optimizer)

"""
print("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")
print("\n\n\nQUESTION 8 - Model Definition (Model, Loss Function, Optimizer):\n")
# We optimize ONLY those parameters that are trainable (p.requires_grad==True)
"""

if n_classes==2:
    criterion = torch.nn.BCEWithLogitsLoss()
elif n_classes>2:
    criterion = torch.nn.CrossEntropyLoss()  # EX8
criterion = torch.nn.CrossEntropyLoss()
parameters = [] # EX8
for p in  model.parameters():
    if(p.requires_grad):
        parameters.append(p)
optimizer = torch.optim.Adam(parameters)  # EX8




#############################################################################
# Training Pipeline
#############################################################################

training_losses = [0]*(EPOCHS)
testing_losses = [0]*(EPOCHS)


for epoch in range(1, EPOCHS + 1):
    # train the model for one epoch
    train_dataset(epoch, train_loader, model, criterion, optimizer)

    # evaluate the performance of the model, on both data sets
    train_loss, (y_train_gold, y_train_pred) = eval_dataset(train_loader,
                                                            model,
                                                            criterion)



    test_loss, (y_test_gold, y_test_pred) = eval_dataset(test_loader,
                                                         model,
                                                         criterion)



    training_losses[epoch-1] = train_loss
    testing_losses[epoch-1] = test_loss
    print("\nMetric analysis for the model in this Epoch: \n")

    print('F1 metric for training: {}'.format(f1_score(y_train_gold, y_train_pred, average="macro")))
    print('Accuracy for training: {}'.format(accuracy_score(y_train_gold, y_train_pred)))
    print('Recall metric for training: {}'.format(recall_score(y_train_gold, y_train_pred, average="macro")))
    print('F1 metric for testing: {}'.format(f1_score(y_test_gold, y_test_pred, average="macro")))
    print('Accuracy for testing: {}'.format(accuracy_score(y_test_gold, y_test_pred)))
    print('Recall metric for testing: {}\n'.format(recall_score(y_test_gold, y_test_pred, average="macro")))




torch.save(model, MODEL + '.pt')
print("Model saved succesfully to " + MODEL + '.pt')



arr1 = np.array(training_losses)
arr2 = np.array(testing_losses)

fig = plt.figure()
axes = plt.gca()
bot = min(training_losses) - 0.05
top = max(max(training_losses) + 0.05, max(testing_losses) + 0.05)
axes.set_ylim([bot, top])
plt.plot(arr1,  label="train data")
plt.plot(arr2,  label="test data")
sup = 'Loss for training and testing of the model' + MODEL
fig.suptitle('Loss for training and testing of the model', fontsize=20)
plt.xlabel('Epoch number', fontsize=18)
plt.ylabel('Loss', fontsize=16)
plt.legend()
if DATASET == 'MR':
    plt.savefig('MR losses')
elif DATASET == 'Semeval2017A':
    name = 'Semeval2017A losses' + '_' + MODEL
    plt.savefig(name)
plt.show()
