from bs4 import BeautifulSoup as BS

def read(path):
	with open(path,'r',encoding='utf-8') as f:
		data = f.read()
	
	soup = BS(data,'lxml-xml')
	svg = soup.find("svg")
	p = svg.findAll('path')
	d = [str(i.get('d')) for i in p]
	
	ox,oy,w,h = [int(i) for i in str(svg.get('viewBox')).split()]
	return d,w,h