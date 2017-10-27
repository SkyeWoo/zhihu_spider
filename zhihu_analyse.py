#! /usr/bin/env python
# -*- coding: utf-8 -*-
#Filename: zhihu_analyse.py
#Author: Wu Xin
#Email: dango.xin@gmail.com
#Date: 2017.6.1

from zhihu_crawler import ZhihuCommon
from collections import deque
from collections import OrderedDict
import matplotlib.pyplot as plt
import json
import pandas as pd
import jieba
import re
from pandas import Series
import numpy as np

class Analyse(object):
	def __init__(self):
		self._topics = deque()
		self._answers = deque()
		self._users = deque()
	
	'''def(self):
		with open('topic.json', 'r', encoding = 'utf-8') as fp:
			for line in fp.readlines():
				self._topics.append(json.loads(line))'''
		
	def _analyse_answer(self):
		with open('answer.json', 'r', encoding = 'utf-8') as fp:
			for line in fp.readlines():
				self._answers.append(json.loads(line))
		
		# 统计匿名用户
		self.anonymous_cnt = 0
		for answer in self._answers:
			if answer["author"] == '匿名用户':
				self.anonymous_cnt += 1
		#print('anonymous author num: ' + str(self.anonymous_cnt))
		#print('answer num: ' + str(len(self._answers)))
		labels = 'unanonymous', 'anonymous'
		sizes = [len(self._answers), self.anonymous_cnt]
		fig = plt.figure()
		plt.pie(sizes, labels = labels, autopct = '%1.2f%%', shadow = True, colors = ['gold', 'silver'])
		plt.title('Anonymous Pie Chart')
		plt.axis('equal')
		plt.show()
	
	def _analyse_user(self):
		with open('user.json', 'r', encoding = 'utf-8') as fp:
			for line in fp.readlines():
				self._users.append(json.loads(line))
		
		# 统计用户性别
		self.male_num = 0
		self.female_num = 0
		self.unknown_gender = 0
		for user in self._users:
			if user['gender'] == 'Male':
				self.male_num += 1
			elif user['gender'] == 'Female':
				self.female_num += 1
			else:
				self.unknown_gender += 1
		#print('male: ' + str(self.male_num), ' female: ' + str(self.female_num), ' unknown gender: ' + str(self.unknown_gender))
		# 绘制性别分布饼图
		labels = 'Male', 'Female', 'Unknown'
		sizes = [self.male_num, self.female_num, self.unknown_gender]
		explode = (0, 0, 0.1)
		fig = plt.figure()
		plt.axes(aspect=1)
		plt.pie(sizes, explode = explode, labels = labels, autopct = '%1.2f%%', shadow = True, colors = ['deepskyblue', 'orangered', 'yellow'])
		plt.title('Gender Pie Chart')
		plt.axis('equal')
		plt.show()
	
	def _analyse_votecount_ans_len(self):
		vote_dis_part = 5000
		ans_len_dis_part = 10000
		part_num = 500
		
		self._votecount_distribution = [0] * part_num
		self._ans_len_distribution = [0] * part_num
		self._max_votecount = 0
		self._max_ans_len = 0
		for ans in self._answers:
			idx = (int)(ans['votecount'] / vote_dis_part)
			if idx >= part_num:
				idx = part_num - 1
			self._votecount_distribution[idx] += 1
			if ans['votecount'] > self._max_votecount:
				self._max_votecount = ans['votecount']
			
			idx = (int)(ans['answer_len'] / ans_len_dis_part)
			if idx >= part_num:
				idx = part_num - 1
			self._ans_len_distribution[idx] += 1
			if ans['answer_len'] > self._max_ans_len:
				self._max_ans_len = ans['answer_len']
		
		max_idx = (int)(self._max_votecount / vote_dis_part + 1)
		if max_idx >= part_num:
			max_idx = part_num - 1
		#print('Vote Count:')
		#print('Max vote count ' + str(self._max_votecount))
		
		# 绘制vote柱状图
		frame = OrderedDict()
		for i in range(max_idx + 1):
			if i == part_num - 1:
				frame[str(idx * vote_dis_part)] = self._votecount_distribution[idx]
			else:
				frame[str(i * vote_dis_part) + '~' + str((i + 1) * vote_dis_part - 1)] = self._votecount_distribution[i]
		frame = pd.Series(frame, index = frame.keys())
		frame.plot(kind = 'bar', colors = ['crimson'])
		plt.title('vote count bar')
		plt.show()
		
		max_idx = (int)(self._max_ans_len / ans_len_dis_part + 1)
		if max_idx >= part_num:
			max_idx = part_num - 1
		#print('Answer len:')
		frame = OrderedDict()
		for i in range(max_idx + 1):
			if i == part_num - 1:
				frame[str(i * ans_len_dis_part)] = self._ans_len_distribution[i]
			else:
				frame[str(i * ans_len_dis_part) + '~' + str((i + 1) * ans_len_dis_part - 1)] = self._ans_len_distribution[i]
		frame = pd.Series(frame, index = frame.keys())
		frame.plot(kind = 'barh', colors = ['dodgerblue'])
		plt.title('answer length bar')
		plt.show()
		#print('Max answer len ' + str(self._max_ans_len))
	
	def _analyse_extra(self):
		seg = re.compile(r'[^\u4e00-\u9fa5]')
		# 只提取中文
		with open('words.txt', 'w', encoding = 'gbk') as fp:
			for user in self._users:
				str = ''.join(user['extra'])
				str = ''.join(seg.split(str)).strip()
				seg_list = jieba.cut_for_search(str.encode('utf-8', 'ignore'))
				for i in seg_list:
					fp.write(i + ' ')
					
		fp.close()
	
	def do_analyse(self):
		#self._analyse_topic()
		self._analyse_answer()
		self._analyse_user()
		self._analyse_votecount_ans_len()
		#self._analyse_extra()
		pass

if __name__ == '__main__':
	z = Analyse()
	z.do_analyse()
	#z._analyse_user()
	#z._analyse_extra()