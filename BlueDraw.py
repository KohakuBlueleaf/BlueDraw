'''
作者：DD藍葉DD(KohakuBlueleaf)

簡介：
	這是一個讀取SVG文件後使用VG轉傅立葉程式產生傅立葉係數後計算並繪圖的程式
程序：
    1.從txt檔或svg檔讀曲線資訊(讀取SVG檔使用SVGreader.py)
    2.將所有曲線資訊丟入S2F的convert函式以產生傅立葉係數(使用popen 因為重複呼叫使用多進程的函數會出事)
    3.將所有的傅立葉係數組依序繪圖
'''
import sys,os
import pickle
from SVGreader import read
from drawer import *
from Error import *
from Functions import *


'''
圓圈數量跟繪畫點的最好數量跟圖畫複雜度有關(太高浪費太低不精細)
我直接使用svg的path資料的長度來判斷複雜度
這裡的係數可以自己按照需求改動
'''

circle_rate = 1			#圓圈數量係數 path資料長度乘上此係數即是使用的圓圈數量
point_rate = 1.5			#繪畫點數量係數 路徑長度乘以此係數即為使用的繪畫點數量

def get_arg(args):
	yield 'note','-p'
	yield args[1],'-t'
	yield args[1],args[2]
	raise OptionError("選項數量過多")

if __name__ == '__main__':
	#freeze_support()
	
	loader = get_arg(sys.argv)				#從命令列獲取檔案名稱
	for _ in range(len(sys.argv)):
		file, mode = next(loader)
	
	paths, w, h = read(f'./SVG/{file}.svg')	#從SVG讀取path
	
	if mode=='-p':
		drawer = pg_draw(w,h,scope=1)
	elif mode=='-t':
		drawer = tl_draw(w,h,scope=1)
	else:
		raise OptionError("錯誤的模式選項")
	
	#開始轉換
	datas = []
	print("\nStart convert SVG to path")
	print(f"File Name:{file}")
	for i in range(len(paths)):
		now = paths[i]
		print(f'Part({i}/{len(paths)}):')
<<<<<<< Updated upstream
		command = ['python', 'S2F.py', now, file, str(int(circle_rate*len(now)))]
=======

		if sys.platform!='win32':
			command = ['python3', 'S2F.py', now, file, str(int(circle_rate*len(now)))]
		else:
			command = ['python', 'S2F.py', now, file, str(int(circle_rate*len(now)))]
		
>>>>>>> Stashed changes
		datas.append(cmd_p(command))
	
	print("done\n")
		
	#input("按下Enter來開始")
	all = []
	for i in range(100):
		for data in datas:
			points = max(int(data[1]*point_rate),50)	#繪畫點數量
			try:
				if mode=='-p':
					path, iterupt = drawer.draw_pg(data[0],points,all)
				elif mode=='-t':
					path, iterupt = drawer.draw_tl(data,points,file)
			except KeyboardInterrupt:
				iterupt = True
			
			if not i:
  			all.append(path)
				print('繪圖路徑點數:{}\n繪圖使用圓圈數:{}'.format(points,len(data[0])))
			
			if not iterupt:
				print("繪圖已中斷")
				sys.exit()
		
	input("繪圖已完成 按下Enter來結束")
