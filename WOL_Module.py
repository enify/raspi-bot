# -*- coding:utf-8 -*-

"""
本模块被Speech_Command_Module模块调用

WOL(网络唤醒)的模块，用到socket通信
包含一个函数：Wake_Up_Computer()   -------无需参数唤醒的机器由Config.ini决定

说明：局域网远程唤醒(WakeupOnLAN)--发送一个MagicPacket到某个MAC地址
            MagicPacket：UDP广播包，端口不限，数据是FF-FF-FF-FF-FF-FF加16个MAC
"""

import struct      #用于处理二进制
import socket
from socket import AF_INET, SOCK_DGRAM, SOL_SOCKET, SO_BROADCAST

#读取配置文件的模块
from configobj import ConfigObj
#配置文件对象
Config = ConfigObj('./Config.ini', encoding= 'utf-8')


#要唤醒的电脑的MAC
computer_mac = Config['Config']['WOL']['Computer_MAC']


def Wake_Up_Computer() :
	
	wake_data = ''.join(['FFFFFFFFFFFF', computer_mac.replace(':', '')*16])
	#幻数据包(编码成二进制)
	MagicPacket = b''
	for i in range(0, len(wake_data), 2) :
		byte_dat = struct.pack('B', int(wake_data[i: i + 2], 16))
		MagicPacket = MagicPacket + byte_dat

	#建立UDP发送
	wake_sock = socket.socket(AF_INET, SOCK_DGRAM)
	wake_sock.setsockopt(SOL_SOCKET, SO_BROADCAST, 1)
	wake_sock.sendto(MagicPacket, ('255.255.255.255', 7))
	wake_sock.close()
	print "唤醒成功！MAC为：" ,
	print computer_mac



if __name__ == "__main__" :
	Wake_Up_Computer()