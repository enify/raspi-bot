# -*- coding:utf-8 -*-

"""
百度语音识别和语音合成的模块

主要有两个函数：
Speech_To_Text(speech_path)    -----输入speech文件的路径，返回得识别结果(列表形式)
Text_To_Speech(target_text)        -----输入文本，返回合成的speech文件路径
#返回TTS合成的MP3文件的路径
"""
import os
import requests
import uuid
import base64
import json

#读取配置文件的模块
from configobj import ConfigObj
#配置文件对象
Config = ConfigObj('./Config.ini', encoding= 'utf-8')


#语音识别的API地址
api_url = "http://vop.baidu.com/server_api"
#语音合成的API地址
baidu_tts_api_url = "http://tsn.baidu.com/text2audio"

#获取Access token 的部分
access_url = "https://openapi.baidu.com/oauth/2.0/token"    #Access token的获取地址
my_mac = uuid.UUID(int = uuid.getnode()).hex[-12:]     #获取本机MAC

       #参数
grant_type = Config['Baidu']['API']['grant_type']
client_id = Config['Baidu']['API']['client_id']      #百度的API KEY
client_secret = Config['Baidu']['API']['client_secret']   #百度的Secret KEY

     #构建表单
access_form = {
	'grant_type' : grant_type ,
	'client_id' : client_id ,
	'client_secret' : client_secret
}

#此函数用于获取Accesstoken
def  Get_Access_token() :
	try :
		access_page = requests.post(access_url, data =access_form)
		access_dict = access_page.json()
		access_token = access_dict["access_token"]

		return access_token
	except :
		print "获取Access token异常！请检查网络设置！"

		exit(0)

#取得百度的Access_token
access_token = Get_Access_token()

################################

#输入speech文件的路径到此函数，即可取得识别结果(列表形式)
def Speech_To_Text(speech_path) :
	with open(speech_path, "rb") as speech_file :
		speech_data = speech_file.read()

	speech_data_length = len(speech_data)  #原始语音数据长度
	speech_b64_data = base64.b64encode(speech_data).decode('utf-8')
	dict_data = {
		'format' : 'wav' ,
		'rate' : 8000 ,  #采样率
		'channel' : 1 ,
		'cuid' : my_mac ,
		'token' : access_token ,
		'lan' : 'zh' ,        #语种
		'speech' : speech_b64_data ,
		'len' : speech_data_length
	}

	json_data = json.dumps(dict_data).encode('utf-8')
	json_data_length = len(json_data)

	#构建请求头
	post_headers ={
		'Content-Type' : 'application/json' ,
		'Content-length' : json_data_length
	}

	print "正在发送录音数据到网络"
	try :
		result_page = requests.post(api_url, headers=post_headers, data=json_data,timeout=3)

	except requests.exceptions.Timeout :
		print "数据POST超时，是不是网络不好？"
		return None
	
	print "网络数据发送成功"
	dict_result = result_page.json()

	err_no = dict_result['err_no']
	if err_no == 0 :
		text_result_list = dict_result['result']
		
		text_result = text_result_list[0] #取候选词中的第一个
		if text_result.endswith(u"，") :
			text_result = text_result[:-1]

		return text_result
	else :
		print "识别结果错误！错误码为：%d" %err_no

		return None

###############################


#################################

#输入文本到此函数，返回百度合成的语音文件(合成的语音文件将被保存成tts_cache.mp3文件)
#返回TTS合成的MP3文件的路径
def Text_To_Speech(target_text) :
	
	if not target_text == None :
		#构建表单
		tts_form = {
		'tex' : target_text ,
		'lan' : 'zh' ,  #语言选择  --选填（可以不填）
		'tok' : access_token,
		'ctp' : 1 , #客户端类型选择
		'cuid' : my_mac ,
		#以下为选填的项目
		'spq' : 5 , #语速
		'pit' : 5 ,  #语调
		'vol' : 5 , #音量
		'per' : 0  #发音人选择,0为女声,1为男声
		}

		#提交数据给baidu_tts
		try :
			tts_result_page = requests.post(baidu_tts_api_url, data=tts_form, timeout=2)
		
		except requests.exceptions.Timeout :
			print "baidu_tts段数据POST超时"

			return None
		#获取响应头
		tts_result_headers = tts_result_page.headers
		
		#合成错误的话
		if tts_result_headers['Content-Type'] == 'application/json' :
			tts_result_error_dict =tts_result_page.json()
			print "合成错误！错误码为：%d"  %tts_result_error_dict['err_no']

			return None

		elif tts_result_headers['Content-Type'] == 'audio/mp3' :
			#获取合成文件的二进制数据
			tts_mp3_data = tts_result_page.content
			with open('./tts_cache.mp3', 'wb')  as tts_mp3_file :
				tts_mp3_file.write(tts_mp3_data)

			#如合成成功，则返回合成文件的路径，反之则返回None
			return './tts_cache.mp3'

	else :
		return None
#################################


if __name__ == "__main__":
	print access_token
	print Speech_To_Text("./test.wav")
	print Text_To_Speech("你叫什么名字？")
