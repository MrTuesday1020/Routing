#!/usr/bin/python3
# COMP9331 Assignment2 RoutingPerformance
# z5092923 Wang Jintao
# z5104857 Shi Xiaoyun

import sched, time
from random import randint
import threading
import time

# network type values: CIRCUIT or PACKET
NETWORK_SCHEME = "CIRCUIT"
# routing scheme values: Shortest Hop Path (SHP), Shortest Delay Path (SDP) and Least Loaded Path (LLP)
ROUTING_SCHEME = "SHP"
# a file contains the network topology specification
TOPOLOGY_FILE = "topology.txt"
# a file contains the virtual connection requests in the network
# workload_small.txt or workload.txt
WORKLOAD_FILE = "workload_small.txt"
# a positive integer value which show the number of packets per second which will be sent in each virtual connection.
PACKET_RATE = 2

########################## Graph ##########################
class Graph:
	# create a new graph
	# O(nV^2)	nV = 26
	def __init__(self,V = 26):
		self.edges = [[0 for x in range(V)] for y in range(V)]
		self.nV = V
		self.nE = 0
		self.vSet = [chr(x+65) for x in range(self.nV)]
	
	# vertices v and w , delay d, link capacities c, status s
	# O(1)
	def insertEdge(self,v,w,d,c,s = 0):
		v = ord(v) - 65
		w = ord(w) - 65
		d = int(d)
		c = int(c)
		if self.edges[v][w] == 0:
			self.edges[v][w] = [d,c,s];
			self.edges[w][v] = [d,c,s];
			self.nE += 1;
	
	# return whether exist edge between two vertices
	# O(1)
	def adjacent(self,v,w):
		if type(v) is str:
			v = ord(v) - 65
		if type(w) is str:
			w = ord(w) - 65
		return (self.edges[v][w] != 0)
	
	# change activity to True
	# O(1)
	def active(self,v,w):
		if type(v) is str:
			v = ord(v) - 65
		if type(w) is str:
			w = ord(w) - 65
		self.edges[v][w][2] += 1
		self.edges[w][v][2] += 1

	# change activity to False
	# O(1)
	def disactive(self,v,w):
		if type(v) is str:
			v = ord(v) - 65
		if type(w) is str:
			w = ord(w) - 65
		self.edges[v][w][2] -= 1
		self.edges[w][v][2] -= 1
	
	# return whether edge is active (status = True)
	# O(1)
	def isactivity(self,v,w):
		if type(v) is str:
			v = ord(v) - 65
		if type(w) is str:
			w = ord(w) - 65
		return (self.edges[v][w][2] is True)
	
	# return delay
	# O(1)
	def delay(self,v,w):
		if type(v) is str:
			v = ord(v) - 65
		if type(w) is str:
			w = ord(w) - 65
		return self.edges[v][w][0]
	
	# return whether is node
	# O(nV)
	def validV(self,v):
		if type(v) is str:
			v = ord(v) - 65
		for i in range(26):
			if self.edges[v][i] != 0:
				return True
	
#	# check the valid node and return as list
#	# O(nV^2)	nV = 26
#	def _vSet(self):
#		self.vSet = [chr(x+65) for x in range(26) if self.validV(x)]
#		self.nV = len(self.vSet)
	
	# print edges in graph
	# O(nV^2)
	def showGraph(self):
		for i in range(self.nV):
			for j in range(i+1,self.nV):
				if self.edges[i][j] != 0:
					print("{},{},{}".format(chr(i+65),chr(j+65),self.edges[i][j]))


########################## Route Scheme ##########################
# Shortest Hop Path
# O(nV^2)
def SHP(graph,start,end):
	dist = [float("inf") for x in range(graph.nV)]
	dist[ord(start)-65] = 0
	pred = [ -1 for x in range(graph.nV)]
	visited = []
	start = ord(start)-65
	for j in range(graph.nV):
		source = ord(graph.vSet[start])-65
		visited.append(source)
		for i in range(graph.nV):
			if graph.adjacent(source,i) and i not in visited:
				if dist[i] > dist[source] + 1:
					dist[i] = dist[source] + 1
					pred[i] = source
		start += 1
		if start >= graph.nV:
			start -= graph.nV
	path = [end]
	end = ord(end)-65
	while dist[ord(path[-1])-65] != 0:
		path.append(chr(pred[end]+65))
		end = pred[end]
	path.reverse()
	return path

def packet_SHP(graph,start,visited = []):
	path = [start]
	for i in range(graph.nV):
		node = chr(i+65)
		if graph.adjacent(start,i) and node not in visited:
			return path+[node]

# Shortest Delay Path
# O(nV^2)
def SDP(graph,start,end):
	dist = [float("inf") for x in range(graph.nV)]
	dist[ord(start)-65] = 0
	pred = [ -1 for x in range(graph.nV)]
	visited = []
	start = ord(start)-65
	for j in range(graph.nV):
		source = ord(graph.vSet[start])-65
		visited.append(source)
		for i in range(graph.nV):
			if graph.adjacent(source,i) and i not in visited:
				if dist[i] > dist[source] + graph.delay(source, i):
					dist[i] = dist[source] + graph.delay(source, i)
					pred[i] = source
		start += 1
		if start >= graph.nV:
			start -= graph.nV
	path = [end]
	end = ord(end)-65 
	while dist[ord(path[-1])-65] != 0:
		end = pred[end]
		path.append(chr(end+65))
	path.reverse()
	return path

def packet_SDP(graph,start,visited = []):
	path = [start]
	for i in range(graph.nV):
		node = chr(i+65)
		if graph.adjacent(start,i) and node not in visited:
			if dist > graph.delay(start,i):
				dist = graph.delay(start,i)
				return_node = node
	return path+[return_node]

# Least Loaded Path
def LLP():
	pass

########################## Thread ##########################
class request (threading.Thread):
	def __init__(self, threadID, runTime):
		threading.Thread.__init__(self)
		self.threadID = threadID
		self.runTime = runTime
	def run(self):
		print("Request " + str(self.threadID) + " starts")
		time.sleep(float(self.runTime))
		print("Request " + str(self.threadID) + " runs " + str(self.runTime))

def doRequest(i, startTime, source, destination, runTime):
	thread = request(i,runTime)
	thread.start()
	
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
#	graph._vSet()
	
	x = SHP(graph, 'A', 'C')
	y = SDP(graph, 'A', 'O')
	print(x)
	print(y)
	
	# init a schedule
	schedule = sched.scheduler (time.time, time.sleep)
	# put requests into schedule
	for i in range(len(requests)):
		schedule.enter(float(requests[i][0]), 0, doRequest, (i, requests[i][0], requests[i][1], requests[i][2],requests[i][3]))
	
#	schedule.run()

if __name__ == "__main__":
	main()