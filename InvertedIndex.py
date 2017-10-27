#! /usr/bin/env python
# -*- coding: utf-8 -*-
#Filename: InvertedIndex.py
#Author: Wu Xin
#Email: dango.xin@gmail.com
#Date: 2017.6.1

import re
import string
import pandas as pd

def create_inverted_index(filename):
	src_data = open(filename, errors = 'ignore').read()
	list_data = src_data.split(' ')
	set_data = set(list_data)
	
	frame = {word : list_data.count(word) for word in set_data}
	# 按词频排序
	frame = sorted(frame.items(), key = lambda d:d[1], reverse = True)
	# 倒排写入文件
	with open('InvertedIndex.txt', 'w', encoding = 'gbk') as fp:
		for key, value in frame:
			fp.write(str(value) + ' ' + key + '\n')
	

if __name__ == '__main__':
	create_inverted_index('words.txt')