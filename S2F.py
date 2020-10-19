'''
作者：DD藍葉DD(KohakuBlueleaf)
程序:
	1.读取svg原始信息，解析，并放入points列表中（二维坐标点列->复数列）
	2.用points列表计算轨道初始参数（复数列）
	3.输出轨道初始参数（复数列->二维坐标点列）
	
增修內容：
	1.將運算部份獨立成一個函式，使其他程式可以直接調用
	2.改用pickle儲存運算好的檔案，並且使用hash函數確保沒有重複儲存/運算的發生
	3.改善部份冗餘計算及程式碼
	4.改善排版、新增部份註解
'''

import sys,os
import re
import pickle
import multiprocessing as mp
from sys import argv
from math import pi
from cmath import exp
from _sha3 import sha3_256
from Functions import *
from SVGreader import read


prjNum = None
prjCur = None
points = []				#贝塞尔采集点
out = []				#傅立葉係數輸出容器
center = [0,0]			#中心点位置
curWeight = []			#各段曲线的时间权重容器
trDatas = []			#临时容器
oneOver2PI = 1/(pi*2)	#常量


#贝塞尔函数(三次)(a,b,c,d代表四個控制點)
def bezier(t,a,b,c,d):
	return (-a+3*b-3*c+d)*(t**3)+3*(a-2*b+c)*(t**2)+3*(-a+b)*t+a

#映射函数
def linear(x,a,b,c,d):
	return ((x-a)/(b-a))*(d-c)+c

#主要计算函数1-解析解
def prSolve(m,cs,ce,n):
	if m==0:
		return (ce-cs)*oneOver2PI/(n+1)
	if n==0:
		return (1j*oneOver2PI/m)*(exp(-m*1j*ce) - exp(-m*1j*cs))
	elif n:
		return (1j*oneOver2PI/m)*(exp(-m*1j*ce)) - n*1j/((ce-cs)*m)*prSolve(m,cs,ce,n-1)
	else:
		return 0
		
#主要计算函数2-贝塞尔曲线方程代入
def numSolve(m,cs,ce,pts):
	return (-pts[0] + 3*pts[1] - 3*pts[2] + pts[3]) * prSolve(m,cs,ce,3)+\
			3*(pts[0] - 2*pts[1] + pts[2]) * prSolve(m,cs,ce,2)+\
			3*(-pts[0] + pts[1]) * prSolve(m,cs,ce,1)+\
			pts[0]*prSolve(m,cs,ce,0)

#分離複數的實部虛部
def cpToList(cp):
	return [cp.real, cp.imag]

def initParam(pts, cw, pjc):
	global points,curWeight,prjCur
	points = pts
	curWeight = cw
	prjCur = pjc

#計算傅立葉係數 輸入的s為第幾項 輸出的複數的實部為a 虛部為b
def mainCalculation(s):
	global points,curWeight,prjCur
	m = 0
	
	if s>0:
		m = ((s+1)//2)*(1 if s%2 else -1)
		
	sum = 0j
	
	for i in range(len(points)):
		cs = linear(curWeight[i],0,1,0,pi*2)
		ce = linear(curWeight[i+1],0,1,0,pi*2)
		sum += numSolve(m,cs,ce,points[i])
	
	with prjCur.get_lock():
		prjCur.value += 1
	
	return cpToList(sum)

def convert(svg, file,amount=1000, cmd=True):
	#檢查此檔案是否運算過
	s = sha3_256()
	s.update(encode(svg+str(amount)))
	hash = s.hexdigest()
	
	try:
		with open('./FourierData/{}_{}'.format(file,hash), 'rb') as f:
			Print("The file is exists, return the value.",True)
			out = pickle.load(f)
			return out+[hash]
	except FileNotFoundError:
		pass
	
	#開始解析SVG資料
	Print("Converting start.",True)
	global end, prjNum, prjCur
	end = amount			#圓圈數量
	prjNum = end+1
	
	rawdata = svg
	curve = re.sub(r'\s','',"".join(rawdata))
	cells = re.findall(r'\w[\d\,\-\.]+',curve)
	
	for cell in cells:
		trcdata = []
		formatString = re.sub(r'-',',-',cell)
		trcdata.append(re.match(r'[A-Za-z]',formatString).group(0))
		rawvers = re.sub(r'[A-Za-z]\,?','',formatString).split(',')
		rawvers = [float(i) for i in rawvers]
		
		vergroup = []
		vercurgrp = []
		
		for st in range(len(rawvers)):
			vercurgrp.append(rawvers[st])
			if len(vercurgrp)>=2:
				vergroup.append(vercurgrp[0]+vercurgrp[1]*1j)
				vercurgrp.clear()
		
		if len(vercurgrp)>0:
			if re.match(r'v',trcdata[0],re.I):
				vergroup.append(0+vercurgrp[0]*1j)
			
			elif re.match(r'h',trcdata[0],re.I):
				vergroup.append(vercurgrp[0]+0j)
		
		trcdata.append(vergroup)
		trDatas.append(trcdata)

	for i in range(1,len(trDatas)):#解析SVG信息
		if re.match(r'[a-z]',trDatas[i][0]):
			for j in range(len(trDatas[i][1])):
				trDatas[i][1][j]+=trDatas[i-1][1][-1]
	
	for i in range(len(trDatas)):#解析SVG信息
		flag = trDatas[i][0]
		
		if re.match(r'm',flag,re.I):continue
		
		trDatas[i][1].insert(0,trDatas[i-1][1][-1])
		
		if re.match(r's',flag,re.I):
			trDatas[i][1].insert(1, 2*trDatas[i-1][1][-1]-trDatas[i-1][1][-2])
		
		if re.match(r'[lvh]',flag,re.I):
			trDatas[i][1].insert(1, trDatas[i][1][0]/3+trDatas[i][1][-1]*2/3)
			trDatas[i][1].insert(1, trDatas[i][1][0]*2/3+trDatas[i][1][-1]/3)
	
	offset = center[0]+1j*center[1]
	points = [i[1] for i in trDatas if not re.match(r'm',i[0],re.I)]	#解析SVG信息
	points = [[j-offset for j in i] for i in points]					#中心歸零
	
	
	#計算每個採集點的時間權重
	wsum = 0
	for curve in points:
		wst = 10 
		a,b,c,d = curve
		total = sum([abs(bezier(linear(i,0,wst,0,1),a,b,c,d)-bezier(linear(i-1,0,wst,0,1),a,b,c,d)) for i in range(1,wst)])
	   
		curWeight.append(total)
		wsum+=total
	
	#確保所有時間權重相加為一
	for i in range(len(curWeight)):
		curWeight[i] /= wsum
	
	#累加來讓時間權重變成時間座標
	for i in range(1,len(curWeight)):
		curWeight[i] += curWeight[i-1]
	
	#加入0,1的頭尾
	curWeight.insert(0,0)
	curWeight[-1] = 1
	
	#開始生成傅立葉係數
	prjCur = mp.Value('i',0)
	pool = mp.Pool(initializer = initParam,initargs = (points,curWeight,prjCur))
	out = pool.map_async(mainCalculation, range(0,end+1))
	
	#列印進度
	length = 50
	while True:
		cent = prjCur.value/prjNum
		nump = round(cent*length)
		Print("["+"="*nump+" "*(length-nump)+"]{}%".format(round(cent*100)),True,'\r' if cmd else '\n')
		if prjCur.value>=prjNum :
			if cmd:print()
			break
	
	#關閉多進程處理並獲取答案
	pool.close()
	pool.join()
	out.wait()
	out = out.get()
	
	#將輸出結果儲存至檔案中（使用pickle直接儲存變數)
	with open('./FourierData/{}_{}'.format(file,hash),'wb') as f:
		pickle.dump([out,wsum],f)
	
	return [out,wsum,hash]

def get_args(argv):
	yield None,None,None,None
	if len(argv)<4:
		paths, w, h = read(argv[1])
		yield paths[0], argv[1], 1000, False
		yield paths[0], argv[1], int(argv[2]), False
	else:
		yield None,None,None,None
		yield None,None,None,None
		yield argv[1], argv[2], int(argv[3]), True
	
if __name__=='__main__':
	loader = get_args(argv)
	for i in argv:
		svg, file, amount, sub = next(loader)
	
	mp.freeze_support()
	if sub:
		print('ans: ',convert(svg, file, amount, False))
	else:
		temp = file.split('/')
		file = '/'.join(temp[:-1]+temp[-1].split('.')[0:1])
		print('Start Convert')
		out, wsum, hash = convert(str(svg), file, amount, True)
		
		with open(file, 'w') as f:
			for i in out:
				f.write(str(i)+'\n')
		
		print('Convert Finish.')