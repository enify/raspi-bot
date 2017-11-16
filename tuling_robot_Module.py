# -*- coding: utf-8 -*-

"""
图灵机器人聊天的模块

包含一个函数：
Get_Tuling_Result(info)      -----输入文本到此函数，返回图灵回应的文本
"""
import requests
import json
import uuid

#读取配置文件的模块
from configobj import ConfigObj
#配置文件对象
Config = ConfigObj('./Config.ini', encoding= 'utf-8')



#图灵的API 地址
tuling_api_url ="http://www.tuling123.com/openapi/api"
#本机MAC，用作用户标识
my_mac = uuid.UUID(int = uuid.getnode()).hex[-12:]

#输入文本，获取图灵机器人对你的回复
def Get_Tuling_Result(info) :
	global Config

	if not info == None :
		#构建json数据
		tuling_dict_data = {
		'key' : Config['Tuling']['API']['tuling_api_key'] ,
		'info' : info ,     #请求的内容
		'loc' : '' ,    #位置信息
		'userid' : my_mac
		}

		tuling_json_data = json.dumps(tuling_dict_data).encode('utf-8')

		#发送数据
		try :
			tuling_result_page =requests.post(tuling_api_url, data=tuling_json_data, timeout=2)

		except requests.exceptions.Timeout :
			print "图灵POST超时"

			return None
		#JSON转换为dict
		tuling_dict_result = tuling_result_page.json()
		#标识码
		tuling_result_code = tuling_dict_result['code']
		if tuling_result_code in [40001, 40002, 40004, 40007] :
			print "图灵数据已POST，但是出现异常，异常码为：%d"  %tuling_result_code

			return  None
		elif tuling_result_code in [200000, 302000, 308000] :
			print "图灵返回结果为链接类/新闻类/菜谱类，本程序将不会处理和返回结果"

			return  None
		elif tuling_result_code == 100000 :
			tuling_text_result = tuling_dict_result['text'].encode('utf-8')

			return tuling_text_result
	else :
		return None


#######################
if __name__ == "__main__":
	print Get_Tuling_Result("你好")