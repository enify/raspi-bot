# -*- coding:utf-8 -*-

"""
本模块为处理语音命令的模块，用于将语音文本内的部分命令放入到command_temp.txt文本中
再由Chack_Commands模块提供的函数检查这个文本中的命令并执行
包含一个函数Append_Speech_Command(speech_text)
"""
#结巴分词模块
import jieba
import jieba.posseg as pseg

#读取配置文件的模块
from configobj import ConfigObj
#获取时间标记的模块(同时为本模块提供了jieba_Posseg_Cut()类)
from Time_Sign_Module import *



jieba.initialize()  # 手动初始化jieba(可选)
#配置文件对象
Config = ConfigObj('./Config.ini', encoding= 'utf-8')

#保存命令的临时文件的路径
command_file_path = Config["Config"]["Command"]["command_file_path"]
#提醒命令的命令名词(list)
keyword_TiXing = Config["Config"]["Command"]["keyword_TiXing"]
#打开/关闭的命令名词(list)
keyword_ON = Config["Config"]["Command"]["keyword_ON"]
keyword_OFF = Config["Config"]["Command"]["keyword_OFF"]
#命令动词
keywords_N = Config["Config"]["Command"]["keywords_N"]
#继电器绑定
JDQ_1 = Config["Config"]["Command"]["JDQ_1"]
JDQ_2 = Config["Config"]["Command"]["JDQ_2"]
JDQ_3 = Config["Config"]["Command"]["JDQ_3"]
JDQ_4 = Config["Config"]["Command"]["JDQ_4"]

#所有命令动词
keywords_ON_OFF = []
keywords_ON_OFF.extend(keyword_ON)
keywords_ON_OFF.extend(keyword_OFF)


"""
jieba带词性分词的类，返回各词性的词组成的二维list，
#每项由['词', '词性',词在原文中的顺序]组成,属性有：
self.cut_or_not  : 有没有执行分词(用于判断None)，返回值为True/False
self.ci_xing_m  : 词性为“数词”的词组成的列表
self.ci_xing_f  : 词性为“方位词”的词组成的列表
self.ci_xing_v : 词性为“动词”的词组成的列表
self.ci_xing_n  : 词性为“名词”的词组成的列表
self.ci_xing_r  : 词性为“代词”的词组成的列表
self.ci_xing_nr  : 词性为“人名”的词组成的列表
self.ci_xing_c  : 词性为“连词”的词组成的列表
self.ci_xing_ q : 词性为“量词”的词组成的列表
"""

"""
#！！！！下面这个类现在由Time_Sign_Module提供！！！！
#一个分词的类，包含的属性有:分词状态，每种词性的词的列表(每项由['词', '词性',词在原文中的顺序]组成，可包含多个项目)
class jieba_Posseg_Cut(object) :

	def __init__(self, cut_text) :
		self.cut_text = cut_text

		if self.cut_text == None :

			#分词了吗？
			self.cut_or_not =False
		else :
			p = pseg.cut(self.cut_text)
			self.text_cut_list = []     #-----新增的属性-----
			ci_number = 0  #词在原文中的顺序
			#转换成list
			for ci, ci_xing in p :
				self.text_cut_list.append([ci, ci_xing, ci_number])
				ci_number += 1
			#text_cut_list是一个二维list，每项由['词', '词性',词在原文中的顺序]组成
			#下面将它分类以便分析(只取我需要的词性，其它词性不处理)
			self.ci_xing_m = []             #数词，例:"十分钟，七点"
			self.ci_xing_f = []             #方位词，例:"后"
			self.ci_xing_v = []             #动词，例:"关闭"，"叫"，"起床"，"帮","提醒"
			self.ci_xing_n = []             #名词，例:"电脑"，"风扇"
			self.ci_xing_r = []             #代词，例:"我"，"他"
			self.ci_xing_nr = []             #人名，例:"小冰"
			#self.ci_xing_x = []             #非语素字，即标点，例:"，"
			self.ci_xing_c = []             #连词，例:"和"
			self.ci_xing_q = []             #量词，例:"分钟"

			for i in self.text_cut_list :
				if i[1] == 'm' :
					self.ci_xing_m.append(i)
				elif i[1] == 'f' :
					self.ci_xing_f.append(i)
				elif i[1] == 'v' :
					self.ci_xing_v.append(i)
				elif i[1] == 'n' :
					self.ci_xing_n.append(i)
				elif i[1] == 'r' :
					self.ci_xing_r.append(i)
				elif i[1] == 'nr' :
					self.ci_xing_nr.append(i)
				elif i[1] == 'c' :
					self.ci_xing_c.append(i)
				elif i[1] == 'q' :
					self.ci_xing_q.append(i)

			#分词了吗？
			self.cut_or_not = True
"""

#把命令语句写入临时文件的函数
def Write_Command_To_File(command_str) :
	global command_file_path
	global append_or_not

	append_or_not = True #这个函数被调用了，说明有命令被写入
	command_str = command_str.encode('utf-8')
	with open(command_file_path, 'r') as f :
		f_commands = f.readlines()
	with open(command_file_path, 'w') as f :
		for o_command in f_commands :
			f.write(o_command)
		if not command_str in f_commands :  #防止有重复的命令进入
			f.write(command_str)
			f.write('\n')


#有两种命令:提醒/闹钟，开/关
#通过分析语音文字生成指令表，包含一个英文命令包和一个中文命令包
def Text_To_Commands(speech_text) :
	global keyword_TiXing
	global keyword_ON
	global keyword_OFF
	global keywords_ON_OFF
	global keywords_N
	global JDQ_1, JDQ_2, JDQ_3, JDQ_4

	text_cut = jieba_Posseg_Cut(speech_text)
	if not text_cut.cut_or_not == False :
		#先看是不是提醒/闹钟命令
		tixing_action = ''
		for tixing_word in keyword_TiXing :

			if tixing_word in speech_text : #是提醒命令的话("半个小时后叫我起床")
				if not len(text_cut.ci_xing_r) == 0 :
					for one_ci in text_cut.text_cut_list :
						if one_ci[2] > text_cut.ci_xing_r[0][2] :
							tixing_action += one_ci[0]   #代词后面的词是提醒的动作
				tixing_time_sign = Get_Time_Sign(speech_text)
				tixing_time_str = '0'
				if not tixing_time_sign == None :
					tixing_time_str = tixing_time_sign.strftime('%Y-%m-%d|%H:%M:%S')
				Write_Command_To_File('Remind_%s_%s' %(tixing_time_str,tixing_action)) #命令写入文件
				text_cut.ci_xing_v = [] #因为证明了这条命令是提醒命令，所以把text_cut.ci_xing_v置零以让它跳过对开关指令的分析
				break

		for one_ci in text_cut.ci_xing_n :
			if u"闹钟" in one_ci :  #是设闹钟命令的话("设一个明天早上七点半的闹钟")
				tixing_time_sign = Get_Time_Sign(speech_text)
				tixing_time_str = '0'
				if not tixing_time_sign == None :
					tixing_time_str = tixing_time_sign.strftime('%Y-%m-%d|%H:%M:%S')
				Write_Command_To_File('Remind_%s_%s' %(tixing_time_str,u'闹钟'))
				text_cut.ci_xing_v = [] #因为证明了这条命令是提醒命令，所以把text_cut.ci_xing_v置零以让它跳过对开关指令的分析
				break

		

		#由动词开始分析句子
		if not len(text_cut.ci_xing_v) == 0 :
			command_v = []           #命令动词
			command_n_1 = []      #动词1对谁执行(命令名词)
			command_n_2 = []      #动词2对谁执行(命令名词)
			command_n_3 = []      #动词3对谁执行(命令名词)
			command_1 = []           #第1条命令
			command_2 = []           #第2条命令
			command_3 = []           #第3条命令

			for v_ci in text_cut.ci_xing_v :
				if v_ci[0] in keywords_ON_OFF :
					#把符合要求的动词放入command_v中(命令动词)
					command_v.append(v_ci)

			#开始分析名词--------开关量名词分析开始
			if len(command_v) == 1 and not len(text_cut.ci_xing_n) == 0 :
				print "一类"
				#只有一个规定动词的话
				for n_ci in text_cut.ci_xing_n :
					if n_ci[0] in keywords_N :
						#把符合要求的名词放入command_n中(命令名词)
						command_n_1.append(n_ci)
				#将动词和名词组合成一条命令放入command_1中
				if not len(command_n_1) == 0 :
					command_1.append(command_v[0])
					command_1.extend(command_n_1)

			elif len(command_v) == 2 and not len(text_cut.ci_xing_n) == 0 :
				print "二类"
				#有两个规定动词的话
				for n_ci in text_cut.ci_xing_n :
					if n_ci[0] in keywords_N :
						if n_ci[2] < command_v[1][2] :
							#标号小于第二个动词的标号的话，属于command_1
							command_n_1.append(n_ci)
						else :
							#标号大于第二个动词的标号的话，属于command_2
							command_n_2.append(n_ci)		
				#将动词和名词组合成命令后分别放入command_1和command_2中
				if not len(command_n_1) == 0 :
					command_1.append(command_v[0])
					command_1.extend(command_n_1)
				if not len(command_n_2) == 0 :
					command_2.append(command_v[1])
					command_2.extend(command_n_2)

			elif len(command_v) > 2  and not len(text_cut.ci_xing_n) == 0 :
				print "三类"
				#有三个规定动词的话(本程序规定最多只能有三个动词，多于三个则把名词交给第三个动词处理)
				for n_ci in text_cut.ci_xing_n :
					if n_ci[0] in keywords_N :
						if n_ci[2] < command_v[1][2] :
							#标号小于第二个动词的标号的话，属于command_1
							command_n_1.append(n_ci)

						elif n_ci[2] >command_v[1][2] and n_ci[2] < command_v[2][2]:
							#标号大于第二个动词的标号小于第三个动词的标号的话，属于command_2
							command_n_2.append(n_ci)
						else :
							#标号大于第三个动词的标号的话，属于command_3
							command_n_3.append(n_ci)		
				#将动词和名词组合成命令后分别放入command_1，command_2和command_3中
				if not len(command_n_1) == 0 :
					command_1.append(command_v[0])
					command_1.extend(command_n_1)
				if not len(command_n_2) == 0 :
					command_2.append(command_v[1])
					command_2.extend(command_n_2)
				if not len(command_n_3) == 0 :
					command_3.append(command_v[2])
					command_3.extend(command_n_3)
			else :
				print "四类"
				#print "没命令动词或没名词"
				if len(command_v) == 0 :
					print "三级过滤，有动词，没有命令动词"
				elif len(text_cut.ci_xing_n) == 0 :
					print "三级过滤，有命令动词，没有名词"
				else :
					print "其它"

				#没命令动词或没(普通)名词
				return None
			#-----------开关量名词分析结束

			#command_x 形式: [['动词', '词性', '标号'], ['名词', '词性', '标号'], ['名词', '词性', '标号']]
			#commands 形式: ['打开_0_名词_名词', '关闭_0_名词_名词']
			#合并命令结果
			command_ON = ''    #打开命令放这里(string形式)
			command_OFF = ''   #关闭命令放这里(string形式)
			for cm in [command_1, command_2, command_3] :
				if not len(cm) == 0 :
					if cm[0][0] in keyword_ON :
						#放入一个'ON_0'，其中0为备用位，以后用来放时间
						if not u'ON_0' in command_ON :
							command_ON += u'ON_0'
						#合并名词结果
						for cm_n in cm[1:] :
							if not cm_n[0] in command_ON :
								command_ON += '_'
								command_ON += cm_n[0]
					elif cm[0][0] in keyword_OFF :
						#放入一个'OFF_0'，其中0为备用位，以后用来放时间
						if not u'OFF_0' in command_OFF :
							command_OFF += u'OFF_0'
						#合并名词结果
						for cm_n in cm[1:] :
							if not cm_n[0] in command_OFF :
								command_OFF += '_'
								command_OFF += cm_n[0]

			#命令包
			commands_en = [] #英文命令包，格式:['ON_0_jdq1_jdq2', 'OFF_0_jdq3_jdq4']
			commands_cn = []  #中文命令包，格式:['ON_0_名词_名词', '关闭_0_名词_名词']
			for cm in [command_ON, command_OFF] :
				if not len(cm) == 0 :
					#放入中文命令包
					commands_cn.append(cm)
					#替换中文指令为英文
					#替换前：u'ON_0_电脑_风扇_台灯'
					#替换后：u'ON_0_computer_jdq1_jdq2'
					cm = cm.replace(u'电脑', 'computer')
					if not len(JDQ_1) == 0 :
						cm = cm.replace(JDQ_1, 'jdq1')
					if not len(JDQ_2) == 0 :
						cm = cm.replace(JDQ_2, 'jdq2')
					if not len(JDQ_3) == 0 :
						cm = cm.replace(JDQ_3, 'jdq3')
					if not len(JDQ_4) == 0 :
						cm = cm.replace(JDQ_4, 'jdq4')
					#放入英文命令包
					commands_en.append(cm)
			if len(commands_en) == 0 :
				#有命令动词没命令名词
				print "四级过滤，有命令动词，没命令名词"
				return None

			else :
				print "分析成功！有命令动词，有命令名词"
				#把两个命令包都返回，中文包用于回复信息，英文包用于执行命令
				return commands_en, commands_cn

		else :
			#没有动词
			print "二级过滤，没有动词"
			return None
	else :
		#输入为None
		print "一级过滤，输入为None"
		return None

#主要函数，从输入文本中获取命令并写入临时文件
def Append_Speech_Command(speech_text) :
	global append_or_not
	append_or_not = False #放入命令了吗？

	commands = Text_To_Commands(speech_text)
	if not commands == None :
		en_commands = commands[0] #英文包
		cn_commands = commands[1] #中文包
		#将时间标记文本写入命令中
		onoff_time_sign = Get_Time_Sign(speech_text)
		onoff_time_str = '0'
		if not onoff_time_sign == None :
			onoff_time_str = onoff_time_sign.strftime('%Y-%m-%d|%H:%M:%S') #时间标记文本

		#写入文件中
		for en_cm in en_commands :
			en_cm = en_cm.replace('0', onoff_time_str)
			Write_Command_To_File(en_cm)
		for cn_cm in cn_commands :
			cn_cm = cn_cm.replace('0', onoff_time_str)
			cn_cm = cn_cm.replace(u'ON',u'cnON')  #中文包现在由cnON作为前缀，方便分析
			cn_cm = cn_cm.replace(u'OFF',u'cnOFF')
			Write_Command_To_File(cn_cm)

	return append_or_not





#测试Do_Commands()
if __name__ == "__main__" :
	try :
		while True :
			text = raw_input("请输入你要说的话>>>")
			text = unicode(text,'utf-8')
			Append_Speech_Command(text)
	finally :
		#Arduino.close()
		pass


"""
#测试Text_To_Commands()
if __name__ == "__main__" :
	while True :
		text = raw_input("请输入要分词的句子>>")
		cms = Text_To_Commands(text)
		if not cms == None :
			for cm in cms :
				print cm
"""				
				


#测试jieba_Posseg_Cut()
"""
if __name__ == "__main__" :
	while True :
		text = raw_input("请输入要分词的句子>>")
		j_cut = jieba_Posseg_Cut(text)

		if not j_cut.cut_or_not == False :
			print j_cut.ci_xing_m
			print j_cut.ci_xing_f
			print j_cut.ci_xing_v
			print j_cut.ci_xing_n
			print j_cut.ci_xing_r
			print j_cut.ci_xing_nr
			print j_cut.ci_xing_c
			print j_cut.ci_xing_q

"""