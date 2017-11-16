# -*- coding:utf-8 -*-

"""
小冰机器人聊天的模块
包含一个函数：
Get_Weibo_Xiaoice_Result(info)    ---输入文本到此函数，返回小冰回应的文本
"""

import requests
import requests.utils
from lxml import etree

from os import system as os_system
import os.path
import json
from time import sleep

#以下模块可以依情况而调用(当cookies过期无法直接登录时)
from PIL import Image
from StringIO import StringIO


#读取配置文件的模块
from configobj import ConfigObj
#配置文件对象
Config = ConfigObj('./Config.ini', encoding= 'utf-8')

###########################################
#检查本地保存的cookies可不可用，不可用则返回False，
#可用则返回已装载cookies的会话实例
def Check_Weibo_Cookies(weibo_cookies_path) :
	
	if os.path.exists(weibo_cookies_path) == False :
		print "当前cookies文件不存在"
		
		return False

	else :
		#cookies文件存在，下面检测它是否还有用
		with open(weibo_cookies_path, 'r') as cookies_file :
			#装载成dict
			cookies_dict = json.load(cookies_file)
		#用于检测的会话对象
		check_session = requests.Session()
		#加载cookies到会话
		check_session.cookies = requests.utils.cookiejar_from_dict(cookies_dict)
		#开始测试cookies
		check_page = check_session.get('http://weibo.cn')
		#没有登录的话会跳转到微博广场(http://weibo.cn/pub/)，登录了的话则不会跳转
		if check_page.url == 'http://weibo.cn/pub/' :
			print "cookies已失效！"

			return False
		
		elif check_page.url == 'http://weibo.cn/' :
			#print "cookies测试有效！"

			#返回实例
			return check_session


###########################################
#本程序返回一个可用的会话实例(它会判断是否需要登录)
def Get_Weibo_Session() :
	global Config

	weibo_session = Check_Weibo_Cookies('./weibo_xiao_ice_cookie.txt')
	
	#如果cookies已失效，则再次登录以获取一个新的可用的会话
	if weibo_session == False :
		#尝试6次，若六次都没获取到则退出程序，提示用户检查
		for i in range(6) :
			weibo_session = requests.Session()
			#微博登陆页的URL，从这里可以获得数据POST的一些信息
			weibo_login_page_url = 'http://login.weibo.cn/login/'

			#获取登录页
			weibo_login_page = weibo_session.get(weibo_login_page_url)


			#直接解析会报错，故用二进制数据生成etree
			weibo_login_page_etree = etree.HTML(weibo_login_page.content)

			#开始获取登录信息

			#POST网址--将登录信息POST到这个网址
			weibo_post_url = weibo_login_page_url + weibo_login_page_etree.xpath('/html/body/div[2]/form/@action')[0]
			#password名称
			weibo_post_password_name = weibo_login_page_etree.xpath('/html/body/div[2]/form/div/input[2]/@name')[0]
			#验证码地址
			weibo_yzm_url = weibo_login_page_etree.xpath('/html/body/div[2]/form/div/img[1]/@src')[0]
			#vk值
			weibo_post_vk_value = weibo_login_page_etree.xpath('/html/body/div[2]/form/div/input[8]/@value')[0]
			#capId值
			weibo_post_capId_value = weibo_login_page_etree.xpath('/html/body/div[2]/form/div/input[9]/@value')[0]

			#获取验证码
			weibo_yzm_page = weibo_session.get(weibo_yzm_url)

			weibo_yzm_img = Image.open(StringIO(weibo_yzm_page.content))
			#显示验证码
			weibo_yzm_img.show()

			#>>>提示用户输入验证码
			yzm_code = raw_input("\033[92m请输入你看到的验证码(注意切换窗口焦点)\033[1m>>>\033[0m")
			#关闭显示验证码的窗口(即名为'display'的进程)
			os.system('killall display')

			###########以下开始POST数据

			#构建请求头
			login_post_headers = {
				'User-Agent' : 'Mozilla/5.0 (X11; Ubuntu; Linux i686; rv:49.0) Gecko/20100101 Firefox/49.0'
			}

			#构建表单数据
			login_post_form = {
				'mobile' : Config['Xiaoice']['API']['mobile'] ,  #这里填手机号
				weibo_post_password_name : Config['Xiaoice']['API']['password'] ,    #这里填密码
				'code' : yzm_code ,    #这里填验证码
				'remember' : 'on' ,
				'backURL' : 'http%3A%2F%2Fweibo.cn' ,
				'backTitle' : u'手机新浪网' ,
				'tryCount' : ' ',
				'vk' : weibo_post_vk_value ,
				'capId' : weibo_post_capId_value ,
				'submit' : u'登录'
			}

			#POST后的页面
			weibo_after_post_page = weibo_session.post(weibo_post_url, headers= login_post_headers, data= login_post_form)


			if weibo_after_post_page.url[7:12] == 'weibo' :
				print "Weibo登录成功！"
				
				"""
				保存cookie为json数据
				"""
				#保存cookie为json数据
				with open('./weibo_xiao_ice_cookie.txt' , 'w') as weibo_xiao_ice_cookie :
					json.dump(requests.utils.dict_from_cookiejar(weibo_session.cookies), weibo_xiao_ice_cookie)

				return weibo_session


			elif weibo_after_post_page.url[7:12] == 'login' :
				print "Weibo登录失败！" ,
				weibo_after_post_page_etree = etree.HTML(weibo_after_post_page.content)

				#登录失败的原因
				weibo_login_error_code = weibo_after_post_page_etree.xpath('/html/body/div[2]')[0].text
				print '\033[31m' + weibo_login_error_code + '\033[0m'

				print "正在尝试重新登录。。。"
		print "第六次尝试登录后失败，请检查代码！"
		exit(0)
	else :
		return weibo_session


#本程序是从微博上获取小冰回复的主程序，输入为一个文本
def Get_Weibo_Xiaoice_Result(info) :

	if not info == None :

		#获取一个已经是登录状态的会话
		xiao_ice_session = Get_Weibo_Session()
		#注：与小冰聊天的界面网址为http://weibo.cn/im/chat?uid=5175429989&rl=1（固定值，不分帐号）
		xiaoice_chat_page_url = 'http://weibo.cn/im/chat?uid=5175429989&rl=1'

		xiaoice_chat_page = xiao_ice_session.get(xiaoice_chat_page_url)
		#下面获取聊天数据的POST地址
		xiaoice_chat_page_etree = etree.HTML(xiaoice_chat_page.content)
		
		xiaoice_chat_data_post_url = 'http://weibo.cn' + xiaoice_chat_page_etree.xpath('/html/body/form/@action')[0]
		

		#print xiaoice_chat_data_post_url


		#构建发送聊天数据的表单
		xiaoice_chat_form = {
			'content' : info ,
			'rl' : '2' ,
			'uid' : '5175429989' ,
			'send' : u'发送'
		}
		#构建发送聊天数据的请求头
		xiaoice_chat_headers = {
			'User-Agent' : 'Mozilla/5.0 (X11; Ubuntu; Linux i686; rv:49.0) Gecko/20100101 Firefox/49.0'
		}

		#发送聊天数据
		xiao_ice_session.post(xiaoice_chat_data_post_url, headers=xiaoice_chat_headers, data= xiaoice_chat_form)
		#一直try，直到微博返回包含信息的页面（尝试10次）
		for i in range(10) :
			#等待0.2秒
			sleep(0.2)
			try :
				#获取包含回复的页面(刷新)
				xiaoice_chat_page = xiao_ice_session.get(xiaoice_chat_page_url)

				xiaoice_chat_page_etree = etree.HTML(xiaoice_chat_page.content)

				
				#抓取聊天的回复[1:]用于去掉引号
				xiaoice_chat_text_result = xiaoice_chat_page_etree.xpath('/html/body/div[3]/img[2]')[0].tail[1:]
				#回复为空的话
				if len(xiaoice_chat_text_result) == 0 :
					continue
			except IndexError :    #获取不到回复的话
				#跳过此次循环的后半部分
				continue

			#print "我是len"
			#print len(xiaoice_chat_text_result)
			#如果没有错误则会返回
			if xiaoice_chat_text_result == u'分享语音[' :
				xiaoice_chat_text_result = u'小冰给你分享了一段语音，暂时无法查看'
			elif xiaoice_chat_text_result == u'分享图片[' :
				xiaoice_chat_text_result = u'小冰给你分享了一张图片，暂时无法查看'

			return xiaoice_chat_text_result
		
		print "远程服务器错误，获取不到回复"
		return None
	else :
		return None



if __name__ == "__main__":
	print Get_Weibo_Xiaoice_Result("你好")