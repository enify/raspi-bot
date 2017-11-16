# -*- coding:utf-8 -*-

"""
本模块定义了一个为输出添加格式的函数(颜色，加粗等)
Print_With_Style(p_str, p_style)   ----分别输入要打印的字符
串和需要的格式，str型
"""


#输入想要打印的字符串和打印格式，即可在终端打印出
#带颜色/格式的文本，其格式为：
#小写字母代表颜色：b(蓝色)，g(绿色)，r(红色)
#大写字母代表格式：B(加粗)，U(下划线)
#例：Print_With_Style(''Hello!'', 'g+B') ----绿色加粗打印"Hello"
def Print_With_Style(p_str, p_style) :
	if 'b' in p_style :            #蓝色
		print '\033[94m' ,
	if 'g' in p_style :            #绿色
		print '\033[92m' ,
	if 'r' in p_style :            #红色
		print '\033[31m' ,
	if 'B' in p_style :            #加粗
		print '\033[1m' ,
	if 'U' in p_style :            #下划线
		print '\033[4m' ,
	#打印正文
	print p_str ,

	print '\033[0m'   #END