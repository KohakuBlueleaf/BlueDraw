'''
作者：DD藍葉DD(KohakuBlueleaf)

簡介：
	這是一個儲存功能性函數的檔案
'''
import sys,os
from subprocess import run,Popen,PIPE,STDOUT


encode = lambda x:bytes(x,encoding='utf-8')
decode = bytes.decode

def Print(string, flush=True, end='\n'):
	sys.stdout.write(string+end)
	if flush:sys.stdout.flush()

cmd = lambda command:eval(bytes.decode(run(command, stdout=PIPE).stdout))

def cmd_p(command):
	p = Popen(command, stdout=PIPE, stderr=STDOUT)
	
	for line in iter(p.stdout.readline, b''):
		l = decode(line)
		if l.find('ans:') != -1:
			sys.stdout.write('\n')
			return eval(l[4:])
		else:
			sys.stdout.write(l[:-1]+'\r')
