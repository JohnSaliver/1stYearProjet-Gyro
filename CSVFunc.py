#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Thu Mar 28 20:06:35 2019

@author: heather
"""


import csv
import numpy as np
import matplotlib.pyplot as pt


def dotprod(a,b):
    c = []
    a = list(a)
    for i in range(len(a)):
        c.append([0])
        for j in range(len(a[i])):
            c[i][0] += a[i][j]*b[j][0]
    return np.array(c)

def capture_to_csv(t, decoded_bytes, eps):        
             with open("data.csv","a") as f:
                    writer = csv.writer(f,delimiter=";")
                    if decoded_bytes == 'S':
                        writer.writerow(decoded_bytes)
                    else:
                        writer.writerow([t]+[float(o) for o in decoded_bytes.split()]+[eps])
         
def csv_reader(filename):
    raw_data = open(filename, 'rt')
    reader = csv.reader(raw_data, delimiter=';', quoting=csv.QUOTE_NONE)
    x = list(reader)
    datas = []
    datindex = -1 #Tracks which aquisition we are appending to
    for dataslice in x:
        if dataslice != []:
            if(dataslice[0] == 'S'): #Split the data for each aquisition
                    datas.append([])
                    datindex += 1
            elif dataslice == '':
                    pass            
            else:
                datas[datindex].append([])
                for i in dataslice:
                    datas[datindex][-1].append(float(i))
    return datas

#print(csv_reader("data.csv"))

def datasquish(datas_):
    datas = np.copy(datas_)
    softsign = lambda x: 9*x/((1+abs(9*x/10000))*10000)
    for data in datas:
        for dp in data:
            dp[1:4] = [softsign(d) for d in dp[1:4]]
    return datas

#print(datasquish(csv_reader("data.csv")))