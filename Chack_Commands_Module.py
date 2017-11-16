# -*- coding:utf-8 -*-

"""
本模块用于对命令进行处理(包括开关命令，提醒命令，以及对相应命令返回回复语)，
它还兼顾与下位机通讯的工作，工作原理主要是检查command_temp.txt文件中的命令，
并执行
包含两个函数，1）Chack_Commands()，它需要在线程内不断执行以及时响应
2）Write_Commands_Back_To_File()，用在finally中，遇到错误时把命令写回文本中
"""
"""
#DEBUG装饰器
def debug(func) :

	def wrapper(*args, **kwargs) :
		print '\033[94m' ,
		print '[DEBUG]: enter {}()'.format(func.__name__) ,
		print "\033[0m"
		with open('./command_temp.txt',"r") as f :
			print '调用前:' ,
			print f.read()
			print f_commands
		return func(*args, **kwargs)
	return wrapper
"""

#树莓派现在通过socket与下位机通讯，下位机为MicriPython的ESP8266

#回复模板随机选择
from random import choice
#时间库
from datetime import datetime
import time
#socket通信库
import socket
#WOL打开电脑的模块
from WOL_Module import *
#引入有颜色的输出的模块
from Print_With_Style_Module import *
#读取配置文件的模块
from configobj import ConfigObj


###
#通信部分(与下位机通信)
HOST = '192.168.1.142' #树莓派(主机)的地址
PORT = 21567  #主机端口
BUFSIZ = 1024 #缓冲区大小
ADDR = (HOST, PORT)

tcpServerSock = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
tcpServerSock.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1) #允许地址重用
tcpServerSock.bind(ADDR)

tcpServerSock.listen(1) #可挂起的最大连接数
tcpServerSock.settimeout(10) #设置连接的超时时间

#等待连接
try :
	print "等待下位机连接..."
	ESP8266Sock, ESP8266addr = tcpServerSock.accept() #接受客户端连接
	print "下位机已连接，地址为：" , ESP8266addr

except socket.timeout : 
	Print_With_Style("下位机连接超时", 'r+B')
	tcpServerSock.close()

	exit(0)
#没有错误的话，就会生成一个名为ESP8266Sock的socket连接对象
###


#配置文件对象
Config = ConfigObj('./Config.ini', encoding= 'utf-8')



#保存命令的临时文件的路径
command_file_path = Config["Config"]["Command"]["command_file_path"]

#回复语模板
reply_mods_ON = Config["Config"]["Command_Reply"]["reply_mods_ON"]
reply_mods_OFF = Config["Config"]["Command_Reply"]["reply_mods_OFF"]
reply_mods_ON_and_OFF = Config["Config"]["Command_Reply"]["reply_mods_ON_and_OFF"]
reply_mods_Tixing = Config["Config"]["Command_Reply"]["reply_mods_Tixing"]
reply_mods_Tixing_With_Time = Config["Config"]["Command_Reply"]["reply_mods_Tixing_With_Time"]
reply_mods_ONOFF_With_Time = Config["Config"]["Command_Reply"]["reply_mods_ONOFF_With_Time"]


#预先加载-----从文件中加载上次未完成的命令
f_commands = set([])   #从文件加载的命令包,这个包也是全局的命令包,后面的函数主要针对它处理
with open(command_file_path, 'r') as f :
	y_cm_lines = f.readlines()
y_new_lines = ''
for y_cm in y_cm_lines :
	if not y_cm.split('_')[1] == '0' : #预先加载-移除过期的命令
		if not (datetime.strptime(y_cm.split('_')[1], '%Y-%m-%d|%H:%M:%S') - datetime.now()).total_seconds() < 0 :
			y_new_lines += y_cm
			f_commands.add(y_cm)

with open(command_file_path, 'w') as f :
	f.write(y_new_lines)
#--------------------------------------预先加载结束

#这个函数用于命令刚生成时返回一个回复
#获取对'Remind_2016-11-19|07:30:00_起床','cnON_2016-11-19|07:30:00_'这种命令的回复语，即:
#好的，将在'2016年11月19日21点18分18秒'叫你[起床]'
#传入类型只有cnON,cnOFF,Remind三种命令
#@debug
def Get_Reply_Of_Command_With_TimeSign(cn_command) :
	global reply_mods_Tixing_With_Time #提醒事项回复语模板
	global reply_mods_ONOFF_With_Time  #开/关事项回复语模板

	cn_cm_list = cn_command.split('_')
	#先检查时间标记代表的时间是否已经过去，过去的话就回复"貌似这个时间已经过了耶，请重新设定个时间哦"
	if (datetime.strptime(cn_command.split('_')[1], '%Y-%m-%d|%H:%M:%S') - datetime.now()).total_seconds() < 0 :
		reply = "貌似这个时间已经过了耶，请重新设定个时间哦"
	else :
		#获取回复模板
		if cn_cm_list[0] == u'Remind' :
			if cn_cm_list[-1] != "闹钟\n" :
				reply_mod = choice(reply_mods_Tixing_With_Time)
				action = cn_cm_list[-1]
			else :    #是闹钟命令的话
				reply_mod = u"好的，已为您设置闹钟"
				action = "" #闹钟不需要回复"动作"
		else :
			reply_mod = choice(reply_mods_ONOFF_With_Time)
			if cn_cm_list[0] == u'cnON' :
				action_v = "打开"
			else :
				action_v = "关闭"
			action = action_v + cn_cm_list[-1]

		#合成回复
		cn_time_sign = datetime.strptime(cn_cm_list[1], '%Y-%m-%d|%H:%M:%S')
		cntime_str = cn_time_sign.strftime('%Y年%m月%d日 %H点%M分%S秒')
		cntime_str = unicode(cntime_str, 'utf-8')
		action = unicode(action, 'utf-8')
		action = action.replace('\n', '') #去除换行符
		reply_mod = reply_mod.replace('t',cntime_str)
		reply_mod = reply_mod.replace('v', action)

		reply = reply_mod
	#print '回复语：' ,
	#print reply

	return reply


#刷新命令包，即从文件中重新加载命令包,它将同时处理新生成的命令，例:
#'十分钟后叫我起床'-----返回'好的，将在'2016年11月19日21点18分18秒'叫你[起床]'
#一次刷新只会处理/添加一条命令到f_commands命令表
#@debug
def Fresh_Commands() :
	global command_file_path
	global f_commands

	with open(command_file_path, 'r') as f :
		cm_lines = f.readlines()
	for cm_line in cm_lines :
		if not cm_line in f_commands :
			f_commands.add(cm_line)
			if not cm_line.split('_')[1] == '0' :
				if any([cm_line.startswith("cn"), cm_line.startswith("Remind")]) : #只对中文命令回复
					#有新的'一段时间后的命令'，返回回复语,必须是中文命令

					return Get_Reply_Of_Command_With_TimeSign(cm_line)
	#如果是ON_OFF的英文命令，则只把它加入命令包而不回复
	return None


#时间到了就把时间标记设为0,需要同时更新f_commands和文件中的命令，对于时间已过的命令需要把它移除
#检查f_commands内是否有命令到时间了，到时间了就把它的时间标记部分设为0
#@debug
def Chack_Commands_Time() :
	global command_file_path
	global f_commands

	new_f_commands = set([])
	now_time = datetime.now() #当前时间
	for f_cm in f_commands :
		if not f_cm.split('_')[1] == '0' :
			cm_time = datetime.strptime(f_cm.split('_')[1], '%Y-%m-%d|%H:%M:%S')
			if 2> (now_time - cm_time).total_seconds() > -2 :  #命令时间点前后各给予一秒的余量
				#时间到了，把时间标记设为0
				f_cm = f_cm.replace(f_cm.split('_')[1], '0')
			elif (now_time - cm_time).total_seconds() > 0: #时间已经过去的话
				continue #时间已经过去，就不要把它放入命令表中了

		new_f_commands.add(f_cm)

	f_commands = new_f_commands #更新f_commands中的命令

	with open(command_file_path,'w') as f : #更新文件中的命令
		for new_cm in new_f_commands :
			f.write(new_cm)



#命令执行完后，调用这个函数把失效的命令从f_commands中清除(执行完后就是无效的命令了)
#@debug
def Clear_Disabled_Commands() :
	global command_file_path
	global f_commands

	new_f_commands = set([])
	for cm in f_commands :
		if not cm.split('_')[1] == '0' :
			new_f_commands.add(cm)

	f_commands = new_f_commands

	with open(command_file_path, 'w') as f :  #文件中的也要清除，不然又会被Flash_Commands()刷新进去f_commands
		for new_cm in new_f_commands :
			f.write(new_cm)


#命令时间到了时的回复
#获取对'Remind_0_吃饭'，'cnON_0_风扇'这种命令的回复，也就是执行命令的时间到了时的回复语，
#'cnON_0_风扇' ---'正在为你打开风扇'
#它只对cnON,cnOFF,Remind三种命令进行处理,这次处理是以命令包的形式
#@debug
def Get_Reply_Of_Command_On_Time(r_commands) :
	#回复语模板
	global reply_mods_ON
	global reply_mods_OFF
	global reply_mods_ON_and_OFF
	global reply_mods_Tixing

	#选择回复模板
	if len(r_commands) == 1 :
		if r_commands[0].startswith("cnON") :
			reply_mod = choice(reply_mods_ON)
		elif r_commands[0].startswith("cnOFF") :
			reply_mod = choice(reply_mods_OFF)
		elif r_commands[0].startswith("Remind") :
			if r_commands[0].endswith("闹钟\n") :
				reply_mod = u"闹钟设定的时间到了哦"
			else :
				reply_mod = choice(reply_mods_Tixing)
	else :
		reply_mod = choice(reply_mods_ON_and_OFF)

	#合成回复
	if r_commands[0].startswith("Remind") :
		action = r_commands[0].split('_')[-1]
		action = unicode(action, 'utf-8')
		#action = action.replace('\n', '') #去除换行符
		reply_mod = reply_mod.replace('v',action)

	else :
		for one_cm in r_commands :
			one_cm_split = one_cm.split('_')
			reply_n = []  #把要回复的名词放这
			for i in one_cm_split[2:] :
				reply_n.append(i)
				if not i == one_cm_split[-1] :
					reply_n.append("，") #放入逗号
			#如果有一个以上名词就把最后一个逗号替换为”和“
			if len(reply_n) > 2 :
				reply_n[-2] = '和'
			reply_n_string = "".join(reply_n)
			reply_n_string = unicode(reply_n_string, 'utf-8')
			#合成最终回复
			if one_cm.startswith("cnON") :
				reply_mod = reply_mod.replace('x', reply_n_string)
			if one_cm.startswith("cnOFF") :
				reply_mod = reply_mod.replace('y', reply_n_string)

	reply = reply_mod
	reply = reply.replace('\n', '')   #去除换行符
	Clear_Disabled_Commands() #执行完后把命令从f_commands中清除
	#print '回复语：' ,
	#print reply

	return reply


#执行时间标记为零的命令并返回回复语
#@debug
def Do_Commands() :
	global f_commands

	commands_cn = []
	commands_en = []
	commands_tixing = []
	for f_command in f_commands :
		if f_command.split('_')[1] == '0' : #只取时间标记为0的命令
			if f_command.startswith("cn") :
				commands_cn.append(f_command)
			elif f_command.startswith("O") :
				commands_en.append(f_command)
			elif f_command.startswith("Remind") :
				commands_tixing.append(f_command)
	#得到时间标记为0的英文包，中文包，提醒包
	
	commands_cn.extend(commands_tixing) #把提醒包放入中文包然后一起给获取回复语的函数处理
	#获取回复语
	reply = None  #初始值
	if not len(commands_cn) == 0 :
		reply = Get_Reply_Of_Command_On_Time(commands_cn)
	#下面是执行
	if not len(commands_en) == 0 :
		d_commands = commands_en #do_commands用英文包
		for one_command in d_commands :
			#关于电脑的指令
			if u'_computer' in one_command :
				if one_command[0:2] == u'ON' :    #如果是'ON'指令的话
					Wake_Up_Computer()  #唤醒电脑
				else : #如果是'OFF'指令的话
					ESP8266Sock.send("OFF_0_computer")
					#Arduino.write(("OFF_0_computer"+"\n").encode('utf-8')) #关闭电脑(交给Arduino处理)
					time.sleep(0.05)
				#执行完后把关于电脑的指令移除
				one_command = one_command.replace('_computer','')
			#指令格式'ON_0_jdq1_jdq2'
			"""这里放把剩余指令发送到串口的函数(添加换行符后发送)"""
			if len(one_command.split("_")) > 2 : #执行完打开/关闭电脑的操作后如果还有其它命令的话就发给Arduino处理
				ESP8266Sock.send(one_command)
				#Arduino.write((one_command+"\n").encode('utf-8'))
				time.sleep(0.05) #延时一下防止发送速度太快Arduino接收不到
	return reply

	
#这个函数写在try...finally...语句中的finally语句中，功能是在发生错误时把
#f_commands中的命令写回文本中
#@debug
def Write_Commands_Back_To_File() :
	global command_file_path
	global f_commands

	with open(command_file_path, 'w') as f :
		for b_cm in f_commands :
			f.write(b_cm)




#本模块的主要函数
#检查命令的函数，这个函数需要在线程内不断运行以及时响应命令
def Chack_Commands() :
	#给CPU留点时间
	time.sleep(0.1)
	global f_commands

	
	wt_reply = Fresh_Commands()   #命令刚生成时回复
	if not wt_reply == None :
		return wt_reply
	Chack_Commands_Time()  #检查f_commands中是否有命令到期，到期则把时间标记设为0，以便下面的程序处理并回复
	
	ot_reply = Do_Commands()      #命令时间到了时的回复与执行
	if not ot_reply == None :
		return ot_reply



if __name__ == "__main__" :
	try :
		while True :
			ret = Chack_Commands()
			if not ret == None :
				print "回复语" ,
				print ret
	finally :
		#Arduino.close()
		Write_Commands_Back_To_File()


