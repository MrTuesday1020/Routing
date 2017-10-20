def f1(price):
	if price > 10:
		print("aaa")
		raise Exception
		print("sss")
	else:
		return price

def f2(price):
	try:
		a=f1(price)
	except:
		return('error')
	return a

def f3(price):
	a = f2(price)
	return a

try:
	a = f3(9)
	print("this is result of a:",a)
	b = f3(8)
	print("this is result of b:",b)
except:
	print("Error!")