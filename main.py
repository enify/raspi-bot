# -*- coding:utf-8 -*-

"""
使用本程序前应先安装mpg123，安装方法：sudo apt-get install mpg123

本程序是语音机器人项目的主代码，其功能为语音识别--获取机器人对话--
语音合成
"""

import os
import time
import threading
import requests
#读取配置文件的模块
from configobj import ConfigObj
#树莓派独有模块
import RPi.GPIO as GPIO

#引入有颜色的输出的模块
from Print_With_Style_Module import *


##检测配置文件是否存在
if os.path.exists('./Config.ini') == False :
	Print_With_Style("配置文件Config.ini不存在！", 'r+B')
	exit(0)

##检测arecord录音程序是否存在
if os.path.exists("./arecord") == False :
	Print_With_Style("arecord程序不存在！请将程序放到此脚本路径下", 'r+B')
	exit(0)

##检测是否有网
net_test = requests.get('http://www.baidu.com')
if net_test.encoding == None :
	Print_With_Style("网络异常！是不是没有连接上互联网？", 'r+B')
	exit(0)

##检测下位机是否连接(连接了的话会生成一个用于通信socket对象)
#这一部分由Chack_Commands_Module模块来做
#×××××××××××××


#外部的模块
from baidu_voice_Module import *
from tuling_robot_Module import *
from xiaoice_robot_Module import *
from Speech_Command_Module import *
from Chack_Commands_Module import *


#配置类对象，所有的配置都保存在此对象中
Config = ConfigObj('./Config.ini', encoding= 'utf-8')



Lu_Yin_Pin = int(Config['Pin']['Lu_Yin_Pin'])     #引发中断的按键引脚
Lu_Yin_State_Pin = int(Config['Pin']['Lu_Yin_State_Pin'])   #显示录音状态的引脚
Lu_Yin_Flag = False #正在录音吗
New_speech_Flag = False #这个录音文件是不是新的录音文件(未识别过的)
previous_time = 0.0   #和current_time配对，目的是让录音事件在一定时间内只能触发一次


#设置录音指示灯的状态的函数
def Set_The_State_Light(lu_yin_flag) :
        #print "我是设置指示灯的函数，当前lu_yin_flag为%s" %lu_yin_flag
	pin_state = GPIO.input(Lu_Yin_State_Pin) #检测输出引脚现在的状态
	if pin_state == lu_yin_flag :
		pass
	else :
		GPIO.output(Lu_Yin_State_Pin, lu_yin_flag)



##
#第二线程上的函数（录音）
def Lu_Yin() :
	global Lu_Yin_Flag
	global New_speech_Flag
	#print "我是录音函数，初始Lu_Yin_Flag为%s，New_speech_Flag为%s" %(Lu_Yin_Flag, New_speech_Flag)

	Lu_Yin_Flag = True
	print "开始录音..."
	os.system("./arecord -Dplughw:CARD=Device -fcd -c1 -twav -r8000 -Vmono ./speech_cache.wav")
	Lu_Yin_Flag = False
	New_speech_Flag = True  #新建了一个录音文件
	print "(自动)结束录音"
	#print "我是录音函数，处理后Lu_Yin_Flag为%s，New_speech_Flag为%s" %(Lu_Yin_Flag, New_speech_Flag)


#建立中断的回调函数（会调用第二线程录音）
def Hui_Diao(Lu_Yin_Pin) :
	global Lu_Yin_Flag
	global New_speech_Flag
	global previous_time
	#print "我是回调函数，初始Lu_Yin_Flag为%s，New_speech_Flag为%s" %(Lu_Yin_Flag, New_speech_Flag)
	

	current_time = time.time()
	#print "我是回调函数，初始previous_time为%f，current_time为%f"  %(previous_time,current_time)
	if current_time - previous_time > 1 :     #1为阀值，保证下面的程序在1秒内只能触发一次
		previous_time = current_time

		if Lu_Yin_Flag == True :   #检测现在是否在录音，如果在录音的话就终止它(用于在嘈杂的环境下手动停止)
			os.system("pkill arecord")
			Lu_Yin_Flag = False
			New_speech_Flag = True   #新建了一个录音文件
			print "(手动)结束录音"
		else :
			t1=threading.Thread(target=Lu_Yin, args=())
			t1.setDaemon(False)   #关闭守护线程，也就是说录音结束后主线程才会结束
			t1.start()  #开启第二线程录音
##

###
#第三线程上的函数（播放语音）
def Play_Mp3() :
	#不知道为什么直接播放mp3会出现问题，所以将mp3转换成wav再播放
	os.system('mpg123 -q -w ./tts_cache.wav ./tts_cache.mp3')
	os.system('aplay -Dplughw:CARD=Device ./tts_cache.wav')
	print "播放语音数据完毕"		


#第三线程建立--播放语音的函数（建立播放线程）
def Play_Speech(tts_path) :
	if not tts_path == None :
		t2=threading.Thread(target=Play_Mp3, args=())
		t2.setDaemon(False)   #关闭守护线程
		t2.start()  #开启第三线程播放语音

###


####
#第四线程上的函数(检查并执行命令文本中的命令语句)
def Chack_And_Do_Commands() :
	while True :
		reply = Chack_Commands()
		if not reply == None :
			Print_With_Style(reply, 'g+B')
			tts_result_path = Text_To_Speech(reply)
			print "开始播放语音"
			Play_Speech(tts_result_path)      #播放语音
#第四线程建立
t3 = threading.Thread(target=Chack_And_Do_Commands, args=() )
t3.setDaemon(True) #打开守护线程，当主线程结束时会带着这个线程结束
t3.start()

####



#与机器人对话的函数，输入一个文本，合成并播放回复语
def Robot_Chat(speech_text_result) :
	global Config

	if Config['Config']['robot'] == 'Xiaoice' :    #选择小冰与你聊天
		chat_text_result = Get_Weibo_Xiaoice_Result(speech_text_result)
	else :      #选择图灵与你聊天
		chat_text_result = Get_Tuling_Result(speech_text_result)
	#语音合成
	tts_result_path = Text_To_Speech(chat_text_result)
	print "开始播放语音"
	Play_Speech(tts_result_path)      #播放语音

	return chat_text_result


#设置GPIO
GPIO.setmode(GPIO.BOARD)
GPIO.setup(Lu_Yin_State_Pin, GPIO.OUT)
GPIO.setup(Lu_Yin_Pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
#添加回调事件
GPIO.add_event_detect(Lu_Yin_Pin, GPIO.FALLING, callback=Hui_Diao, bouncetime=20)


#主线上的程序
def Main_Code() :
	global New_speech_Flag
	

	while True :
		#设置指示灯的状态
		Set_The_State_Light(Lu_Yin_Flag)
		#如果新录了一个音的话
		if New_speech_Flag == True :
			#语音识别
			speech_text = Speech_To_Text("./speech_cache.wav")
			Print_With_Style(speech_text, 'g+B')
			#分析语音命令并把它写入文本
			append_command = Append_Speech_Command(speech_text)
			#是否要调用机器人来进行语音对话
			if append_command == True : #有命令就由Chack_Commands()函数来回复并播放
				pass
			else :
				chat_text = Robot_Chat(speech_text)  #没命令就由机器人来回复并播放
				Print_With_Style(chat_text, 'g+B')
			'''
			#语音合成
			tts_result_path = Text_To_Speech(chat_text)
			print "开始播放语音"
			Play_Speech(tts_result_path)      #播放语音
			'''
			New_speech_Flag = False      #录音识别完成，不再是新文件了
		time.sleep(0.05)
		





try :
	#主线程序
	Main_Code()

finally :
	#将命令语句写回文本，这样语句的时间未到就不会被清除
	Write_Commands_Back_To_File()
	#删除缓存文件
	for cache_path in ['speech_cache.wav', 'tts_cache.wav', 'tts_cache.mp3'] :
		if os.path.exists(cache_path) :
			os.remove(cache_path)
	#释放Pin
	GPIO.cleanup(Lu_Yin_Pin)
	GPIO.cleanup(Lu_Yin_State_Pin)
	#释放socket(这两个对象在Chack_Commands_Module里)
	ESP8266Sock.close()
	tcpServerSock.close()
	
