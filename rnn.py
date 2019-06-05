# -*- coding: utf-8 -*-
"""
Spyder Editor

This is a temporary script file.
"""

"""
Based Minimal character-level Vanilla RNN model. Originally written by Andrej Karpathy (@karpathy)
BSD License
"""
import numpy as np
from CSVFunc import csv_reader, datasquish, dotprod
import keyboard
import csv
datas_ = csv_reader("data.csv")
SQdatas = datasquish(datas_)


# hyperparameters
hidden_size = 500 # size of hidden layer of neurons
seq_length = 25 # number of steps to unroll the RNN for
learning_rate = 1e-1

# model parameters
Wxh = np.random.randn(hidden_size, 3)*0.01 # input to hidden
Whh = np.random.randn(hidden_size, hidden_size)*0.01 # hidden to hidden
Why = np.random.randn(1, hidden_size)*0.01 # hidden to output
bh = np.zeros((hidden_size, 1)) # hidden bias
by = np.zeros((1,1)) # output bias

def lossFun(inputs, targets, hprev):
  """
  inputs,targets are both list of integers.
  hprev is Hx1 array of initial hidden state
  returns the loss, gradients on model parameters, and last hidden state
  """
  xs, hs, ys, ps = [], [], [], []
  hs.append(np.copy(hprev))
  loss = 0
  #print(inputs)
  # forward pass
  #print("Computing forward pass")
  for t in range(len(inputs)):
    #print("t = ",t)
    xs.append(np.transpose([inputs[t]])) # xs[t] is a 3 dimentional vector 
    #print("x[t]",np.shape(xs[t]))
    hs.append(np.tanh(np.dot(Wxh, xs[t]) + np.dot(Whh, hs[t-1]) + bh)) # hidden state
    #print("h[t]",np.shape(hs[t]))
    ys.append(np.dot(Why, hs[t]) + by) # unnormalized log probabilities for next chars
    #print("y[t]",np.shape(ys[t]))
    ps.append(np.exp(ys[t]) / np.sum(np.exp(ys[t]))) # probabilities for next chars
    # formerly loss += -np.log(ps[t][targets[t],0])
    #print("p[t]", np.shape(ps[t]))
    loss += -np.log(ps[t]) # softmax (cross-entropy loss)
  # backward pass: compute gradients going backwards
  
  #print("Computing backward pass")
  dWxh, dWhh, dWhy = np.zeros_like(Wxh), np.zeros_like(Whh), np.zeros_like(Why)
  dbh, dby = np.zeros_like(bh), np.zeros_like(by)
  dhnext = np.zeros_like(hs[0])
  for t in reversed(range(len(inputs))):
    dy = np.copy(ps[t])
    
    # formerly dy[target[t]] -= 1
    dy -= 1 # backprop into y. see http://cs231n.github.io/neural-networks-case-study/#grad if confused here
    #print("dy  ",dy)
    dWhy += np.dot(dy, hs[t].T)
    #print("dWhy  ",dWhy)
    dby += dy
    #print("dby  ", dby)
    dh = np.dot(Why.T, dy) + dhnext # backprop into h
    dhraw = (1 - hs[t] * hs[t]) * dh # backprop through tanh nonlinearity
    dbh += dhraw
    dWxh += np.dot(dhraw, xs[t].T)
    dWhh += np.dot(dhraw, hs[t-1].T)
    dhnext = np.dot(Whh.T, dhraw)
  for dparam in [dWxh, dWhh, dWhy, dbh, dby]:
    np.clip(dparam, -5, 5, out=dparam) # clip to mitigate exploding gradients
  return loss, dWxh, dWhh, dWhy, dbh, dby, hs[len(inputs)-1]

def sample(h, Rt, squished = 1):
  """ 
  sample a sequence of integers from the model 
  h is memory state, seed_ix is seed letter for first time step
  """
  param = np.load('weights.npy', allow_pickle = True)
  Wxh_, Whh_, Why_, bh_, by_ = param
  if squished:
      x = Rt
  else:
      softsign = lambda x: 9*x/((1+abs(9*x/10000))*10000)
      x = [softsign(d) for d in Rt]
  #Whh_ = np.matrix(Whh_)

  h = [np.tanh(np.dot(Wxh_, x)[k] + dotprod(list(Whh_), list(h))[k] + bh_[k]) for k in range(hidden_size)]

  #print(h)
  y = np.dot(Why_, h) + by
  #print(y, np.shape(y))
  p = (np.exp(y) / np.sum(np.exp(y)))[0][0]

  pred = np.random.choice(range(2), p=(1-p,p))
  return p, h 


def fit():
    n, p, q = 0, 0, 0
    
    mWxh, mWhh, mWhy = np.zeros_like(Wxh), np.zeros_like(Whh), np.zeros_like(Why)
    mbh, mby = np.zeros_like(bh), np.zeros_like(by) # memory variables for Adagrad
    smooth_loss = -np.log(1.0/2)*seq_length # loss at iteration 0
    
    while True:
        
        while q == 1:
            if keyboard.is_pressed('r'):
                q = 0
                print('Fitting restarted.')
            elif keyboard.is_pressed('s'):
                np.save("weights.npy",[Wxh, Whh, Why, bh, by], allow_pickle=True)
                print('Weights saved, stopping.')
                return 1
            elif keyboard.is_pressed('e'):
                print('Weights not saved, stopping.')
                return 0
        for data in SQdatas:
          # prepare inputs (we're sweeping from left to right in steps seq_length long)
          if p+seq_length+1 >= len(data) or n == 0: 
            hprev = np.zeros((hidden_size,1)) # reset RNN memory
            p = 0 # go from start of data
          
          inputs = [data[t][1:4] for t in range(len(data[p:p+seq_length]))]
          targets = [data[t][4] for t in range(len(data[p:p+seq_length]))]
          
          #forward seq_length data points through the net and fetch gradient
          
          loss, dWxh, dWhh, dWhy, dbh, dby, hprev = lossFun(inputs, targets, hprev)
          smooth_loss = smooth_loss * 0.999 + loss * 0.001
          if n % 100 == 0: print('iter %d, loss: %f' % (n, smooth_loss)) # print progress
          
          # perform parameter update with Adagrad
          for param, dparam, mem in zip([Wxh, Whh, Why, bh, by], 
                                        [dWxh, dWhh, dWhy, dbh, dby], 
                                        [mWxh, mWhh, mWhy, mbh, mby]):
            mem += dparam * dparam
            param += -learning_rate * dparam / np.sqrt(mem + 1e-8) # adagrad update
        
          p += seq_length # move data pointer
          n += 1 # iteration counter
          
          if keyboard.is_pressed('q'):
              q = 1
              print('Fitting stopped, press "r to restart or "s" to save the weights.')
              break
        