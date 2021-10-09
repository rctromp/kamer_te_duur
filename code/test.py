# -*- coding: utf-8 -*-
"""
Created on Thu Sep 30 15:33:59 2021

@author: r.tromp
"""
import pandas as pd
import numpy as np

string = ['https://kamernet.nl/', 'kamer-groningen/trompstraat/kamer-1988224']

newList = []
for i in string:
    newList.append(i.split('-'))
                   
print(newList)

string = string.split('-')


string = string[:-4]
count_until = len(string) -2
string = string[count_until:]

print(string)


# df = pd.DataFrame(dict(
#     codes=[
#         {'amount': 12, 'code': 'a'},
#         {'amount': 19, 'code': 'x'},
#         {'amount': 37, 'code': 'm'},
#         np.nan,
#         np.nan,
#         np.nan,
#     ]
# ))

df = pd.DataFrame(dict(
    codes=[
        {'amount': 12, 'code': 'a'},
        {'amount': 19, 'code': 'x'},
        {'amount': 37, 'code': 'm'},
    ]
))


df = df.codes.apply(pd.Series)
df = df.drop('codes', 1).assign(**df.codes.apply(pd.Series))

