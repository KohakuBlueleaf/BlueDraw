'''
作者：DD藍葉DD(KohakuBlueleaf)

簡介：
	這是一個讀取SVG文件後使用中梓星音製作的SVG轉傅立葉程式產生傅立葉係數後計算並繪圖的程式
程序：
    1.從txt檔或svg檔讀曲線資訊(讀取SVG檔使用SVGreader.py)
    2.將所有曲線資訊丟入S2F的convert函式以產生傅立葉係數(使用popen 因為重複呼叫使用多進程的函數會出事)
    3.將所有的傅立葉係數組依序繪圖
'''

import turtle
import pickle
from math import sin, cos, pi
from SVGreader import read
from multiprocessing import Pool,freeze_support,Value


'''
Drawer based on turtle
'''
class tl_draw:
	def __init__(self,w,h,p=3,scope=1.5):
		freeze_support()
		self.scope = scope
		self.dx, self.dy = w//2,h//2				#中心點修正量 turtle正中間是0,0但是svg是左上角為0,0
		turtle.setup(round(w*scope),round(h*scope))	#設定畫面長寬高
		turtle.pensize(p)							#筆刷粗細

	def get_point(self,t):
		x = y = i = 0 
		for now_x, now_y in self.data[0]:			#計算傅立葉級數的加總
			temp = (-(i+1) if i%2 else i)/self.points*pi*t
			s_t, c_t = sin(temp), cos(temp)
			x += now_x * c_t - now_y * s_t
			y += now_x * s_t + now_y * c_t
			i += 1
		
		return (int(x),int(y))

	def initParam(self,d,p):
		self.data = d
		self.points = p

	def draw_tl(self,data,p,file):
		self.points = p
		self.data = data
		
		try:#如果路徑已經儲存就直接讀取
			with open(f'./DrawPath/{file}_{self.points}_{data[2]}','rb') as f:
				draw = pickle.load(f)
		
		except FileNotFoundError:#如果沒有儲存則進行計算
			print('Fourier to path')
			pool = Pool(initializer = self.initParam,initargs = (data,p))
			draw = pool.map_async(self.get_point, range(p+1))#先計算路徑
			
			pool.close()
			pool.join()
			draw.wait()
			draw = draw.get()
			
			#路徑存檔
			with open(f'./DrawPath/{file}_{p}_{data[2]}','wb') as f:
				pickle.dump(draw,f)
				
		turtle.penup()					#畫圖
		for x,y in draw:
			turtle.goto((x-self.dx)*self.scope,-(y-self.dy)*self.scope)
			turtle.pendown()
		turtle.penup()
		turtle.goto(-self.dx,-self.dy)	#畫完
		
		return draw,True


'''
Drawer based on pygame
Can draw the circles
'''
class pg_draw:
	def __init__(self,w,h,p=3,scope=1.5):
		#init pygame
		import pygame
		self.pg = pygame
		self.lw = p
		
		self.pg.init()

		#init screen
		self.scope = scope
		self.screen = self.pg.display.set_mode((round(w*self.scope),round(h*self.scope)))
		self.pg.display.set_caption("Draw")		
		 
		#init background
		self.bg = self.pg.Surface(self.screen.get_size())
		self.bg = self.bg.convert()
		self.bg.fill((255, 255, 255))
		self.screen.blit(self.bg, (0,0))
		self.pg.display.update()

	#draw game_map
	def draw(self,t):
		
		#重新繪幀
		self.bg.fill((255, 255, 255))
		
		#計算傅立葉各項的值
		x,y = [],[]
		x_sum, y_sum = 0, 0				#總和值（最後路徑點）
		offset = (pi*t)/self.points		#計算值的修正（詳見傅立葉係數求解公式）
		
		i = 0							#開始計算
		for now_x, now_y in self.data:
			theta = (-(i+1) if i%2 else i)*offset
			s_t, c_t = sin(theta), cos(theta)
			
			temp_x = now_x * c_t - now_y * s_t
			temp_y = now_x * s_t + now_y * c_t
			
			x.append(temp_x*self.scope)
			y.append(temp_y*self.scope)
			x_sum += temp_x*self.scope
			y_sum += temp_y*self.scope
			
			i += 1
		self.all.append((round(x_sum),round(y_sum)))
		
		#繪製圓形及其半徑線
		p,q = x[0],y[0]
		for i in range(1,len(x)):
			r,s = p+x[i],q+y[i]
			
			Radius = self.radius_list[i]
			
			if Radius:	#若直徑過小則忽略繪圖
				self.pg.draw.line(self.bg, (160,160,160), (int(p),int(q)), (int(r),int(s)), 1)
				self.pg.draw.circle(self.bg, (160,160,160),(int(p),int(q)), Radius, 1)
			
			p,q = r,s
			
		#繪製以前的路徑
		for i in self.paint:
			p,q = i[0][0],i[0][1]
			for (x,y) in i:
				self.pg.draw.line(self.bg, (20,20,20), (int(p),int(q)), (int(x),int(y)), self.lw)
				p,q = x,y
		
		#繪製現在的路徑
		if len(self.all)>1:
			p,q = self.all[0][0],self.all[0][1]
			for (x,y) in self.all:
				self.pg.draw.line(self.bg, (20,20,20), (int(p),int(q)), (int(x),int(y)), self.lw)
				p,q = x,y
				
		#刷新螢幕
		self.screen.blit(self.bg, (0,0))
		self.pg.display.update()

	def draw_pg(self,d,p,pt):
		self.data = d
		self.points = p
		self.paint = pt
		
		running = True
		i = 0;self.all = []
		
		#求所有半徑
		self.radius_list = [round((i[0]**2+i[1]**2)**0.5) for i in self.data]
		
		while running and i<p+1:
			for event in self.pg.event.get():
				if event.type == self.pg.QUIT:
					running = False
			self.draw(i)
			i+=1
		
		return self.all,running
