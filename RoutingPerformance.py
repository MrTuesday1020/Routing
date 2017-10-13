#!/usr/bin/python3
# COMP9331 Assignment2 RoutingPerformance
# z5092923 Wang Jintao
# z5104857 Shi Xiaoyun

from threading import Timer
import timeit

# network type values: CIRCUIT or PACKET
NETWORK_SCHEME = "CIRCUIT"
# routing scheme values: Shortest Hop Path (SHP), Shortest Delay Path (SDP) and Least Loaded Path (LLP)
ROUTING_SCHEME = "SHP"
# a file contains the network topology specification
TOPOLOGY_FILE = "topology.txt"
# a file contains the virtual connection requests in the network
WORKLOAD_FILE = "workload.txt"
# a positive integer value which show the number of packets per second which will be sent in each virtual connection.
PACKET_RATE = 2

# Graph
class Graph:
	# create a new graph
	def __init__(self,V = 26):
		self.edges = [[0 for x in range(V)] for y in range(V)]
		self.nV = V
		self.nE = 0
	
	# vertices v and w , delay d, link capacities c, status s
	def insertEdge(self,v,w,d,c,s = True):
		v = ord(v) - 65
		w = ord(w) - 65
		d = int(d)
		c = int(c)
		if self.edges[v][w] == 0:
			self.edges[v][w] = [d,c,s];
			self.edges[w][v] = [d,c,s];
			self.nE += 1;
	
	# return whether exist edge between two vertices
	def adjacent(self,v,w):
		v = ord(v) - 65
		w = ord(w) - 65
		return (self.edges[v][w] != 0)
	
	# change activity to True
	def active(self,v,w):
		v = ord(v) - 65
		w = ord(w) - 65
		self.edges[v][w][2] = True
		self.edges[w][v][2] = True

	# change activity to False
	def disactive(self,v,w):
		v = ord(v) - 65
		w = ord(w) - 65
		self.edges[v][w][2] = False
		self.edges[w][v][2] = False
	
	# return whether edge is active (status = True)
	def isactivity(self,v,w):
		v = ord(v) - 65
		w = ord(w) - 65
		return (self.edges[v][w][2] is True)
	
	def delay(self,v,w):
		v = ord(v) - 65
		w = ord(w) - 65
		return self.edges[v][w][0]
	
	# print edges in graph
	def showGraph(self):
		if self.nE == 0:
			print("nE = 0, No graph\n")
		else:
			print("nV: {}; nE: {}".format(self.nV,self.nE))
			for i in range(self.nV):
				for j in range(i+1,self.nV):
					if self.edges[i][j] != 0:
						print("{},{},{}".format(chr(i+65),chr(j+65),self.edges[i][j]))

# get all path end-to-end
def AllPath(graph,start,end):
	temp_path = [start]
	q = []
	path = []
	
	q.append(temp_path)
	while len(q) != 0:
		tmp_path = q.pop()
		last_node = tmp_path[-1]
		if last_node == end:
			path.append(tmp_path)
		for i in range(26):
			link_node = chr(i+65)
			if graph.adjacent(link_node,last_node) and link_node not in tmp_path and graph.isactivity(link_node, last_node):
				new_path = tmp_path + [link_node]
				q.append(new_path)
	return path

# Shortest Hop Path
def SHP(graph,start,end):
	path = AllPath(graph,start,end)
	min_len = float("inf")
	for i in path:
		if len(i) < min_len:
			min_len = len(i)
			sortest_path = i
	return sortest_path

# Shortest Delay Path
def SDP(graph,start,end):
	path = AllPath(graph,start,end)
	min_len = float("inf")
	for i in path:
		length = 0
		for j in range(len(i)-1):
			length += graph.delay(i[j],i[j+1])
		if length < min_len:
			min_len = length
			sortest_path = i
	return sortest_path
	
def LLP():
	pass

def doRequest():
	pass
	#print("do request")
	
def main():
	# open and read TOPOLOGY_FILE
	with open(TOPOLOGY_FILE) as f:
		routers = [line.strip().split(" ") for line in f]

	# open and reand WORKLOAD_FILE
	with open(WORKLOAD_FILE) as f:
		requests = [line.strip().split(" ") for line in f]
		
	graph = Graph()
	for router in routers:
		graph.insertEdge(router[0], router[1], router[2], router[3])
	
#	times = []
#	for i in range(len(requests)):
#		t = Timer(float(requests[i][0]),doRequest)
#		times.append(t)
#	
#	
#	for t in times:
#		t.start()
	
	x = SHP(graph, 'A', 'C')
	y = SDP(graph, 'A', 'C')
	print(y)
	

if __name__ == "__main__":
	main()