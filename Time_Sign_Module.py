# -*- coding:utf-8 -*-

"""
本模块被Speech_Command_Module模块调用

本模块用于在语句中获取获取时间标记，包含一个函数：
Get_Time_Sign(speech_text)，它返回一个datetime对象或者None
"""

import jieba
import jieba.posseg as pseg

from datetime import datetime, timedelta #时间


jieba.initialize()  # 手动初始化jieba(可选)


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
			self.ci_xing_i = []             #习用语，例:"大后天"

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
				elif i[1] == 'i' :
					if i[0] == u"大后天" :  #习用语只接收"大后天"
						self.ci_xing_q.append(i)

			#分词了吗？
			self.cut_or_not = True



#分析单个时间数，它可能是时/分/秒中的一个
def Time_Str_To_Value(time_str) :
	time_value = 0

	ge_str = time_str
	#分析十位数
	ten_place = time_str.find(u'十') #找到'十'的位置，看时间是一位数还是两位数
	if not ten_place == -1 :
		#是两位数时间数
		ten_str = time_str[0:ten_place]
		if len(ten_str) == 0 : #十几
			time_value += 10
		else :    #二十几/三十几...
			if u'二' in ten_str :
				time_value += 20
			elif u'三' in ten_str :
				time_value += 30
			elif u'四' in ten_str :
				time_value += 40
			elif u'五' in ten_str :
				time_value += 50
			elif u'六' in ten_str :
				time_value += 60
			elif u'七' in ten_str :
				time_value += 70
			elif u'八' in ten_str :
				time_value += 80
			elif u'九' in ten_str :
				time_value += 90
		ge_str = time_str[ten_place:] #移除十位数剩下个位数
	#分析个位数
	if u'一' in ge_str :
		time_value += 1
	elif u'两' in ge_str :
		time_value += 2
	elif u'二' in ge_str :
		time_value += 2
	elif u'三' in ge_str :
		time_value += 3
	elif u'四' in ge_str :
		time_value += 4
	elif u'五' in ge_str :
		time_value += 5
	elif u'六' in ge_str :
		time_value += 6
	elif u'七' in ge_str :
		time_value += 7
	elif u'八' in ge_str :
		time_value += 8
	elif u'九' in ge_str :
		time_value += 9

	if u'半' in ge_str :  #"半"可以与上面的数同时出现，所以分开处理
		time_value += 0.5

	return time_value



#获取时间标记---一段时间后(推荐格式:一小时三十分二十八秒后)
def Time_After_To_Time_Sign(t_text) :

	if not u'分钟' in t_text :
		t_text = t_text.replace(u'分',u'分钟') #把'分'换成'分钟'

	H_place = t_text.find(u'小时')
	M_place = t_text.find(u'分钟')
	S_place = t_text.find(u'秒')
	H_value = 0 #初始值
	M_value = 0
	S_value = 0
	#分析'时'
	if not H_place == -1 :
		H_str = t_text[0:H_place]
		#print H_str
		H_value = Time_Str_To_Value(H_str)
		M_start_place = H_place + 2    #切割'分'时间数的开始位置
	else :
		M_start_place = 0             #切割'分'时间数的开始位置
	#分析'分'
	if not M_place == -1 :
		M_str = t_text[M_start_place:M_place]
		#print M_str
		M_value = Time_Str_To_Value(M_str)
		S_start_place = M_place + 2  #切割'秒'时间数的开始位置
	else :
		S_start_place = 0
	#分析'秒'
	if not S_place == -1 :
		if not H_place == -1 :
			S_str = t_text[M_start_place:S_place]  #有'时'无'分'有'秒'的情况
		else :
			S_str = t_text[S_start_place:S_place]
		#print S_str
		S_value = Time_Str_To_Value(S_str)
	#分析结束
	if all([H_value==0, M_value==0, S_value==0]) :
		return None  #无时间标记，返回None
	else :
		now_time = datetime.now() #当前时间
		target_time = now_time + timedelta(hours=H_value, minutes=M_value, seconds=S_value)

		#print u'小时：%s；分钟：%d；秒：%d后' %(H_value, M_value, S_value),
		#print str(target_time)

		return target_time  #返回时间标记
		


#获取时间标记----时间点(推荐输入格式:明天早上七点四十五分)
def Time_Point_To_Time_Sign(tp_text) :
	D_value = 0 #初始值，注意这里的各种value和Time_After_To_Time_Sign()函数中的value含义是不一样的
	H_value = 0
	M_value = 0

	#分析'天'
	if u'明天' in tp_text :
		D_value += 1
		tp_text = tp_text.replace(u'明天','')
	elif u'大后天' in tp_text :
		D_value += 3
		tp_text = tp_text.replace(u'大后天','')
	elif u'后天' in tp_text :
		D_value += 2
		tp_text = tp_text.replace(u'后天','')
	#分析'时辰'，本程序中把时间换算成24小时制来算
	tp_text = tp_text.replace(u'今天','')
	tp_text = tp_text.replace(u'早上','')
	tp_text = tp_text.replace(u'上午','')
	tp_text = tp_text.replace(u'中午','')
	if u'晚上' in tp_text :
		H_value += 12
		tp_text = tp_text.replace(u'晚上','')
	elif u'下午' in tp_text :
		H_value += 12
		tp_text = tp_text.replace(u'下午','')
	#分析'时',它以'点'为标志
	H_place = tp_text.find(u'点')
	M_place = tp_text.find(u'分')
	if not H_place == -1 :
		H_str = tp_text[0:H_place]
		#print H_str
		H_value += Time_Str_To_Value(H_str)
		M_start_place = H_place + 1
		#分析'分',必须'时'存在
		if not M_place == -1 :
			M_str = tp_text[M_start_place:M_place]
		else :
			M_str = tp_text[M_start_place:]
		if u'半' in M_str : #'点'作为标志时'半'必须单独分析，而不应该交给'分'分析
			M_value += 30
			M_str = M_str.replace(u'半','')
		#print M_str
		M_value += Time_Str_To_Value(M_str)
	#分析结束
	if all([D_value==0, H_value==0, M_value==0]) :

		return None    #没有时间标记的话

	now_time = datetime.now() #当前时间
	if all([D_value!=0, H_value==0, M_value==0]) :
		target_time = now_time + timedelta(days=D_value) #为了应对'明天/后天的这个时候叫我起床'这种情况
	else :
		target_time = datetime(now_time.year, now_time.month, now_time.day, H_value, M_value) + timedelta(days=D_value) #目标时间

	#print u'%s天后%s点%s分' %(D_value,H_value,M_value),
	#print str(target_time)

	return target_time  #返回时间标记





#获取时间标记-------主要函数
def Get_Time_Sign(speech_text) :
	if u'闹钟' in speech_text :
		speech_text = speech_text.replace(u'一个','') #为了应对"设一个七点三十八的闹钟"这种情况

	text_cut = jieba_Posseg_Cut(speech_text)

	if text_cut.cut_or_not == True :
		#由方位词开始分析
		time_str_start = 0 #初始值
		time_str_end = 0
		if not len(text_cut.ci_xing_f) == 0 :
			if text_cut.ci_xing_f[0][0] == u"后" :
				#有方位词"后"，表明是一段时间
				if len(text_cut.ci_xing_m) > 0 :
					time_str_start = text_cut.ci_xing_m[0][2] #时间语开始的位置
				time_str_end = text_cut.ci_xing_f[0][2]   #时间语结束的位置
				time_str = '' #时间语----一段时间后
				for t_ci in text_cut.text_cut_list[time_str_start:time_str_end] :
					time_str += t_ci[0]

				print time_str

				time_sign = Time_After_To_Time_Sign(time_str)
				if not time_sign == None :
					print "时间后，结果：" ,
					print str(time_sign)
		#代表一个时间点或无时间标记
		else :
			for t_ci in text_cut.text_cut_list :
				if t_ci[1] == 't' or t_ci[1] == 'm' or t_ci[1] == 'i':
					time_str_start = t_ci[2]   #时间语开始的位置
					break

			for t_ci in reversed(text_cut.text_cut_list) :
				if t_ci[1] == 'm' :
					time_str_end = t_ci[2]     #时间语结束的位置
					break

			time_str = '' #时间语----特点时间点
			for t_ci in text_cut.text_cut_list[time_str_start:time_str_end + 1] :
				time_str += t_ci[0]

			print time_str

			time_sign = Time_Point_To_Time_Sign(time_str)
			if not time_sign == None :
				print "时间点，结果：" ,
				print str(time_sign)

		return time_sign




if __name__ == "__main__" :
	while True :
		text = raw_input("请输入要测试命令>>>")
		text = unicode(text, 'utf-8')
		Get_Time_Sign(text)