"""
本程序为树莓派语音机器人项目中下位机(ESP8266-MicroPython)的代码
Starttime :2016-12-5
"""
#注意代码要以Python3.x的风格写
import time
import socket
import network
from machine import Pin
from machine import reset as machine_reset

#定义引脚(依据GPIO)
JDQ1_Pin = 4
JDQ2_Pin = 0
JDQ3_Pin = 2
JDQ4_Pin = 15

#将引脚设置为输出
jdq1 = Pin(JDQ1_Pin, Pin.OUT)
jdq2 = Pin(JDQ2_Pin, Pin.OUT)
jdq3 = Pin(JDQ3_Pin, Pin.OUT)
jdq4 = Pin(JDQ4_Pin, Pin.OUT)
#设置初始值为关闭
jdq1.high()
jdq2.high()
jdq3.high()
jdq4.high()


#通信部分
HOST = '192.168.1.100' #树莓派(主机)的地址
PORT = 21567  #主机端口
BUFSIZ = 1024 #缓冲区大小
ADDR = (HOST, PORT)

tcpSock = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
tcpSock.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR, 1)

wlan = network.WLAN(network.STA_IF)


try :
	while not wlan.isconnected() :
		time.sleep(2) #等待wifi连接

	tcpSock.connect(ADDR) #连接主机，阻塞
	print("已连接上位机")
	while True :
		recv_data = tcpSock.recv(BUFSIZ) #接收数据，阻塞
		if not len(recv_data) == 0 :
			recv_data = recv_data.decode() #bytes=>string
			##################
			#下面对从上位机接收到的数据进行处理
			ON_OFF_Flag = -1
			recv_data = recv_data.strip() #移除字符串末尾的换行符
			print(recv_data)
			
			command_list = recv_data.split("_")
			if command_list[0] == "ON" :
				ON_OFF_Flag = 0 #继电器为低电平触发
			elif command_list[0] == "OFF" :
				ON_OFF_Flag = 1

			if "jdq1" in command_list :
				jdq1.value(ON_OFF_Flag)
			if "jdq2" in command_list :
				jdq2.value(ON_OFF_Flag)
			if "jdq3" in command_list :
				jdq3.value(ON_OFF_Flag)
			if "jdq4" in command_list :
				jdq4.value(ON_OFF_Flag)

except Exception as e:
	tcpSock.close()
	print(e)
	time.sleep(3)
	machine_reset() #连接不上就重启(以重新连接)
