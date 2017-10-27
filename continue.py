#! /usr/bin/env python
# -*- coding: utf-8 -*-
#Filename: zhihu_crawler.py
#Author: Wu Xin
#Email: dango.xin@gmail.com
#Date: 2017.5.30

import requests
import re
import json
import time
from bs4 import BeautifulSoup
from collections import deque
# 解除警告
from requests.packages.urllib3.exceptions import InsecureRequestWarning,InsecurePlatformWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
requests.packages.urllib3.disable_warnings(InsecurePlatformWarning)

''' 共有类 '''
class ZhihuCommon(object):
	headers = {
	'User-Agent':'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/53.0.2785.116 Safari/537.36',
	'Accept':'*/*',
	'Accept-Language':'zh-CN,zh;q=0.8,en-US;q=0.5,en;q=0.3',
	'Accept-Encoding':'gzip, deflate, br',
	'Referer':'https://www.zhihu.com/'
	}
	topic_id = 19776749			# 根话题
	unclassed_id = 19776751		# 未分类话题
	traverse_level = 3			# 遍历深度
	login_url = 'https://www.zhihu.com/#signin'
	config_file = 'config'
	_xsrf = None
	_session = requests.Session()
	adapter = requests.adapters.HTTPAdapter(max_retries = 20)
	_session.mount('https://', adapter)
	_session.mount('http://', adapter)

	_cookie = None
	_base_url = 'https://www.zhihu.com'
	
	@staticmethod
	def get_session():
		return ZhihuCommon._session
	
	@staticmethod
	def set_xsrf(xsrf):
		ZhihuCommon._xsrf = xsrf
	
	@staticmethod
	def get_xsrf():
		return ZhihuCommon._xsrf
	
	@staticmethod
	# 从文件中获得cookie
	def get_cookie():
		if ZhihuCommon._cookie == None:
			try:
				with open(ZhihuCommon.config_file, 'r') as fp:
					cookies = {}
					for line in fp.read().split(';'):
						name, value = line.strip().split('=', 1)
						cookies[name] = value
					return cookies
			except Exception as e:
				print('fail to get cookies, error info: ' + str(e))
				return None
		else:
			return ZhihuCommon._cookie
	
	@staticmethod
	def get(url):
		response = ZhihuCommon.get_session().get(url, headers = ZhihuCommon.headers, cookies = ZhihuCommon.get_cookie(), timeout = 30)
		# python标准库HTML解析器
		soup = BeautifulSoup(response.text, 'html.parser')
		return response.text, soup
	
	@staticmethod
	def post(url, post_dict):
		response = requests.post(url, headers = ZhihuCommon.headers, cookies = ZhihuCommon.get_cookie(), data = post_dict, timeout = 30)
		return response
	
	@staticmethod
	# 二进制形式保存网页
	def get_and_save_page(url, path):
		try:
			response = ZhihuCommon.get_session().get(url, headers = ZhihuCommon.headers, cookies = ZhihuCommon.get_cookie(), verify = False)
			'''with open(path, 'w', response.encoding) as fp:
				fp.write(response.text)'''
			with open(path, 'wb+') as fp:
				fp.write(response.content)
			return
		except Exception as e:
			print('fail to get ' + url + ', error info: ' + str(e))
			return

class Topic(object):
	def __init__(self, id):
		url = 'https://www.zhihu.com/topic/' + str(id)
		self._base_url = ZhihuCommon._base_url
		self._topic_id = id
		self._url = url
		self._child_topic_id = []			# 子话题
		self._top_answer_urls = []
		
		# 不解析未归类话题
		if id == ZhihuCommon.unclassed_id:
			self._valid = False
			print('skip unclassed topic')
			return
		self._valid = self._parse_topic()
		if self._valid == True:
			self._parse_child_topic()
			self._parse_top_answer()
	
	def is_valid(self):
		return self._valid
	
	def get_url(self):
		return self._url
	
	def get_top_answers(self):
		return self._top_answer_urls
	
	def get_child_topic(self):
		return self._child_topic_id
	
	def get_level(self):
		return self._level
	
	def set_level(self, level):
		self._level = level
	
	@staticmethod
	# 转成dict数据, 便于json dump
	def obj_to_dict(obj):
		tmp_dict = {}
		tmp_dict['name'] = obj._name
		tmp_dict['url'] = obj._url
		return tmp_dict
	
	# 分析话题
	def _parse_topic(self):
		is_ok = False
		try:
			_, soup = ZhihuCommon.get(self._url)
			self.soup = soup
			print(self._url)
			# 获取话题名称
			topic_info_tag = soup.find('h1', class_ = 'zm-editable-content')
			self._name = topic_info_tag.contents[0]
			time.sleep(1)
			is_ok = True
		except Exception as e:
			print('topic url ' + self._url + ', errno info: ' + str(e))
			time.sleep(1)
		finally:
			return is_ok
	
	# bfs爬下以根话题为起点的完整话题结构, 所有子话题存放在队列_child_topic_id中
	def _parse_child_topic(self):
		continue_flag = True
		first_flag = True
		
		# 完整话题结构
		topic_tree_url = self._url + '/organize/entire'
		post_dict = {
			'_xsrf': ZhihuCommon.get_xsrf()
		}
		
		while continue_flag:
			if first_flag:
			# 还未开始分析
				query_url = topic_tree_url
				first_flag = False
			else:
			# 存在'加载更多'
				query_url = topic_tree_url + '?child=' + last_topic + '&parent=' + parent_topic
				# 用Chrome Network捕捉 例如 "实体(id = 19778287)"子话题"商品(id = 19584724)"
				# https://www.zhihu.com/topic/19778287/organize/entire?child=19584724&parent=19778287
				#print(ZhihuCommon.post(query_url, post_dict).json())
				'''{'r': 0, 'msg': [['topic', '实体', '19778287'], 
				[[['topic', '人', '19561047'], 
				[[['load', '显示子话题', '', '19561047'], []]]], 
				[['topic', '生活用品', '19647124'], 
				[[['load', '显示子话题', '', '19647124'], []]]], 
				[['topic', '食物', '19552062'], 
				[[['load', '显示子话题', '', '19552062'], []]]], 
				[['topic', '自然', '19553627'], 
				[[['load', '显示子话题', '', '19553627'], []]]], 
				[['topic', '设备', '19563277'], 
				[[['load', '显示子话题', '', '19563277'], []]]], 
				[['topic', '产品', '19552131'], 
				[[['load', '显示子话题', '', '19552131'], []]]]]]}'''
			
			response_login = ZhihuCommon.post(query_url, post_dict)
			#print(response_login)
			rep_msg = response_login.json()
			#print(rep_msg)
			'''{'msg': [['topic', '「根话题」', '19776749'], 
			[[['topic', '「未归类」话题', '19776751'], 
			[[['load', '显示子话题', '', '19776751'], []]]], 
			[['topic', '学科', '19618774'], 
			[[['load', '显示子话题', '', '19618774'], []]]], 
			[['topic', '实体', '19778287'], 
			[[['load', '显示子话题', '', '19778287'], []]]], 
			[['topic', '「形而上」话题', '19778298'], 
			[[['load', '显示子话题', '', '19778298'], []]]], 
			[['topic', '产业', '19560891'], 
			[[['load', '显示子话题', '', '19560891'], []]]], 
			[['topic', '生活、艺术、文化与活动', '19778317'], 
			[[['load', '显示子话题', '', '19778317'], []]]]]], 'r': 0}'''
			
			if not response_login.json()['r'] == 0:
				return
			
			for tmp_topic in rep_msg['msg'][1]:
				if tmp_topic[0][1] == '加载更多':
					last_topic = tmp_topic[0][2]
					parent_topic = tmp_topic[0][3]
					break
				topic_id = int(tmp_topic[0][2])
				self._child_topic_id.append(topic_id)
			else:
				continue_flag = False
	
	# 解析话题的精华回答
	def _parse_top_answer(self):
		go_next_page = True
		page = 1
		while (go_next_page):
			go_next_page = self._parse_top_answer_one_page(page)
			page += 1
			#if page > 10:
			#	break
		'''# 一般情况下知乎每个话题有1000个精华帖 每页20个 计50页
		for page in range(1, 51):
			if (self._parse_top_answer_one_page(page) == False):
				break'''
	
	# _top_answer_urls队列维护所有话题精华的url
	def _parse_top_answer_one_page(self, page):
		page_url = self._url + '/top-answers?page=' + str(page)
		
		try:
			_, soup = ZhihuCommon.get(page_url)
		except Exception as e:
			print('fail to get page ' + page_url + ', error info: ' + str(e))
			ZhihuCommon.get_and_save_page(page_url, 'last_page_in_topic.html')
			return False
		
		for tag in soup.find_all('div', class_ = 'zm-item-rich-text expandable js-collapse-body'):
			#print(tag)
			''' <div class="zm-item-rich-text expandable js-collapse-body" 
			data-action="/answer/content" 
			data-author-name="肥肥猫" 
			data-entry-url="/question/28626263/answer/41992632" 
			data-resourceid="3633413">
			<textarea class="content" hidden="">'''
			try:
				question_url = self._base_url + tag['data-entry-url']
				self._top_answer_urls.append(question_url)
			except:
				print('fail to get question url in ' + self._url + ' page, error info: ' + str(page))
				continue
		
		# 如果还有下一页 继续爬
		for tag in soup.find_all('a'):
			if tag.contents[0] == '下一页':
				return True
		
		# ZhihuCommon.get_and_save_page(page_url, 'last_page_in_topic.html')
		print('last page in topic ' + page_url)
		return False

class Answer(object):
	def __init__(self, url):
		self._base_url = ZhihuCommon._base_url
		self._url = url
		self._valid = self._parse_answer()
	
	def is_valid(self):
		return self._valid
	
	def get_author_url(self):
		return self._author_url
	
	def get_author_name(self):
		return self._author_name
	
	@staticmethod
	def obj_to_dict(obj):
		tmp_dict = {}
		tmp_dict['question'] = obj._question
		tmp_dict['url'] = obj._url
		tmp_dict['author'] = obj._author_name
		tmp_dict['votecount'] = obj._votecount
		tmp_dict['answer_len'] = obj._answer_len
		
		return tmp_dict
	
	def _parse_answer(self):
		is_ok = False
		try:
			_, soup = ZhihuCommon.get(self._url)
			self.soup = soup
			
			# 获取问题题目
			question_tag = soup.find('h1', class_ = 'QuestionHeader-title')
			self._question = question_tag.contents[0]
			#print('title', self._question)
			
			# 获取问题链接
			'''question_tag = soup.find('div', class_ = 'Card', attrs = {'data-za-module': 'MessageItem'})
			print('here',question_tag)
			a_tag = question_tag.find('a')
			self._question_url = self._base_url + a_tag['href']
			print('question url:', self._question_url)'''
			
			# 获取赞同人数
			top_answer_tag = soup.find('div', class_ = 'QuestionAnswer-content')
			vote_tag = top_answer_tag.find('meta', itemprop = 'upvoteCount')
			#print(vote_tag)
			'''<meta content="152902" itemprop="upvoteCount"/>'''
			self._votecount = int(vote_tag['content'])
			#print(self._votecount, '人赞同')
			
			# 获取作者名称和url
			author_tag = top_answer_tag.find('div', class_ = 'AuthorInfo-content')
			author_tag = author_tag.find('a', class_ = 'UserLink-link')
			# 匿名
			if author_tag is None:
				author_tag = soup.find('div', class_ = 'AnswerAuthor-user-content')
				author_tag = author_tag.find('span', class_ = 'UserLink')
				self._author_url = None
			else:
				self._author_url = self._base_url + author_tag['href']
			self._author_name = author_tag.contents[0]
			#print('author name:', self._author_name)
			
			# 获取回答内容和长度
			ans_content_tag = top_answer_tag.find('div', class_ = 'RichContent-inner')
			self._answer_len = 0
			for ans_str in ans_content_tag.stripped_strings:
				self._answer_len += len(ans_str)
			
			print('parse ' + self._url + ' ok. ' + self._question + 'vote: ' + str(self._votecount) + ' author:' + self._author_name + ' answer_len: ' + str(self._answer_len))
			
			time.sleep(1)
			is_ok = True
		
		except Exception as e:
			print('fail to parse ' + self._url + ', error info: ' + str(e))
			time.sleep(1)
			ZhihuCommon.get_and_save_page(self._url, 'fail_answer.html')
		finally:
			return is_ok

class User(object):
	
	def __init__(self, url):
		self._user_url = url
		self._valid = self._parse_user_page()
	
	def is_valid(self):
		return self._valid
	
	def get_url(self):
		return self._user_url
	
	@staticmethod
	def obj_to_dict(obj):
		tmp_dict = {}
		tmp_dict['name'] = obj._name
		tmp_dict['url'] = obj._user_url
		tmp_dict['gender'] = obj._gender
		tmp_dict['extra'] = obj._extra
		
		return tmp_dict
	
	def _parse_user_page(self):
		try:
			_, soup = ZhihuCommon.get(self._user_url)
			self.soup = soup
			head_tag = soup.find('div', class_ = 'ProfileHeader-content')
			
			# 获取名称
			name_tag = head_tag.find('span', class_ = 'ProfileHeader-name')
			self._name = name_tag.contents[0]
			
			# 获取性别
			gender_tag = head_tag.find('svg', class_ = 'Icon Icon--male')
			if head_tag.find('svg', class_ = 'Icon Icon--female') is not None:
				self._gender = 'Female'
			elif head_tag.find('svg', class_ = 'Icon Icon--male') is not None:
				self._gender = 'Male'
			else:
				self._gender = 'Unknown gender'
			
			self._extra = []
			head_tag = soup.find_all('div', class_ = 'ProfileHeader-infoItem')
			if head_tag is not None:
				for tag in head_tag:
					for str in tag.stripped_strings:
						self._extra.append(str)
			#print(self._extra)
			
			time.sleep(1)
			is_ok = True
			
			print('parse user ' + self._name + ' ok.')
		
		except Exception as e:
			print('fail to parse user page ' + self._user_url + 'error info: ' + str(e))
			time.sleep(1)
			is_ok = False
		finally:
			return is_ok
	
	'''def parse_extra_info(self):
		self._extra_info = {}
		for key in self._extra_info_key:
			tag = self.soup.find('span', class_ = key)
			if tag is not None:
				self._extra_info[key] = tag['title']'''

class Crawler(object):
	def __init__(self):
		self._base_url = ZhihuCommon._base_url
		# 分别维护已经遍历的topic, answer, user
		self._visited_topic_url = set()
		self._visited_answer_url = set()
		self._visited_user_url = set()
		ZhihuCommon._session = requests.Session()
		adapter = requests.adapters.HTTPAdapter(max_retries = 20)
		ZhihuCommon._session.mount('https://', adapter)
		ZhihuCommon._session.mount('http://', adapter)
		#TODO!
		with open('topic.json', 'r', encoding = 'utf-8') as fp:
			for line in fp.readlines():
				self._visited_topic_url.add(json.loads(line)['url'])
		fp.close()
		with open('answer.json', 'r', encoding = 'utf-8') as fp:
			for line in fp.readlines():
				self._visited_answer_url.add(json.loads(line)['url'])
		fp.close()
		with open('user.json', 'r', encoding = 'utf-8') as fp:
			for line in fp.readlines():
				self._visited_user_url.add(json.loads(line)['url'])
		fp.close()
	
	def init_xsrf(self):
		try:
			_, soup = ZhihuCommon.get(self._base_url)
			input_tag = soup.find('input', {'name':'_xsrf'})
			xsrf = input_tag['value']
			ZhihuCommon.set_xsrf(xsrf)
		except Exception as e:
			print("fail to init xsrf, error info: " + str(e))
	
	def login(self):
		ZhihuCommon.get_and_save_page(ZhihuCommon.login_url, 'login.html')
	
	def do_crawler(self):
		bfs_q = deque()
		
		topic = Topic(ZhihuCommon.topic_id)
		if topic.is_valid():
			#TODO!
			'''self._visited_topic_url.add(topic.get_url())
			self._save_topic(topic)'''
			if topic.get_url() not in self._visited_topic_url:
				self._save_topic(topic)
				self._visited_topic_url.add(topic.get_url())
			self._parse_top_answers(topic.get_top_answers())
			# 深度为1
			topic.set_level(1)
			bfs_q.append(topic)
		
		# 队列非空时 bfs遍历
		while len(bfs_q) != 0:
			parent_topic = bfs_q.popleft()
			if parent_topic.get_level() >= ZhihuCommon.traverse_level:
			# 超过遍历深度
				break
			
			for topic_id in parent_topic.get_child_topic():
				topic_url = 'https://www.zhihu.com/topic/' + str(topic_id)
				if topic_id not in self._visited_topic_url:
					new_topic = Topic(topic_id)
					if not new_topic.is_valid():
						continue
					# 遍历深度增加
					new_topic.set_level(parent_topic.get_level() + 1)
					#TODO!
					if new_topic.get_url() not in self._visited_topic_url:
						self._visited_topic_url.add(new_topic.get_url())
						self._save_topic(new_topic)
					'''self._visited_topic_url.add(new_topic.get_url())
					self._save_topic(new_topic)'''
					self._parse_top_answers(new_topic.get_top_answers())
					bfs_q.append(new_topic)
	
	def _parse_top_answers(self, top):
		#cnt = 0
		for url in top:
			if url in self._visited_answer_url:
				continue
			
			answer = Answer(url)
			if not answer.is_valid():
				continue
			
			self._visited_answer_url.add(url)
			self._save_answer(answer)
			
			if (answer.get_author_url() is not None) and (answer.get_author_url() not in self._visited_user_url):
				author = User(answer.get_author_url())
				if author.is_valid():
					self._visited_user_url.add(author.get_url())
					self._save_user(author)
			
			'''cnt += 1
			if cnt > 10:
				break'''
	
	def _save_topic(self, topic):
		with open('topic.json', 'a', encoding = 'utf-8') as fp:
			json_str = json.dumps(topic, default = Topic.obj_to_dict, ensure_ascii = False, sort_keys = True)
			fp.write(json_str + '\n')
	
	def _save_answer(self, answer):
		with open('answer.json', 'a', encoding = 'utf-8') as fp:
			json_str = json.dumps(answer, default = Answer.obj_to_dict, ensure_ascii = False, sort_keys = True)
			fp.write(json_str + '\n')
	
	def _save_user(self, user):
		with open('user.json', 'a', encoding = 'utf-8') as fp:
			json_str = json.dumps(user, default = User.obj_to_dict, ensure_ascii = False, sort_keys = True)
			fp.write(json_str + '\n')

if __name__ == '__main__':
	z = Crawler()
	z.init_xsrf()
	#z.login()
	z.do_crawler()
