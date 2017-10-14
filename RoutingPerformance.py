#!/usr/bin/python3
# COMP9331 Assignment2 RoutingPerformance
# z5092923 Wang Jintao
# z5104857 Shi Xiaoyun

import sched, time
from random import randint
import threading
import time

########################## Input Arguments ##########################
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


########################## Output  ##########################
# The total number of virtual connection requests.
NoOfReq = 0
# The total number of packets.
NoOfAllPkt = 0
# The number (and percentage) of successfully routed packets.
NoOfSuccPkt = 0
# The number (and percentage) of blocked packets.
NoOfBlkPkt = 0
# The total number of hops (i.e. links) consumed per successfully routed circuit. 
NoOfHops = 0
# The total source-to-destination cumulative propagation delay per successfully routed circuit.
PDelays = 0
# The total number of success requests
NoOfSuccReq = 0


########################## Graph ##########################
class Graph:
	# create a new graph
	# O(nV^2)	nV = 26
	def __init__(self,V = 26):
		self.edges = [[0 for x in range(V)] for y in range(V)]
		self.vSet = [chr(x+65) for x in range(V)]
		self.nV = V
		self.nE = 0
	
	# vertices v and w , delay d, all capacities c, already used capacities s
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
	
	# occupy a capacity between v,w
	# O(1)
	def occupy(self,v,w):
		if type(v) is str:
			v = ord(v) - 65
		if type(w) is str:
			w = ord(w) - 65
		self.edges[v][w][2] += 1
		self.edges[w][v][2] += 1

	# release a capacity between v,w
	# O(1)
	def release(self,v,w):
		if type(v) is str:
			v = ord(v) - 65
		if type(w) is str:
			w = ord(w) - 65
		self.edges[v][w][2] -= 1
		self.edges[w][v][2] -= 1
	
	# return whether edge is blocked
	# O(1)
	def isBlock(self,v,w):
		if type(v) is str:
			v = ord(v) - 65
		if type(w) is str:
			w = ord(w) - 65
		return (self.edges[v][w][1] == self.edges[v][w][2])
	
	# return delay
	# O(1)
	def delay(self,v,w):
		if type(v) is str:
			v = ord(v) - 65
		if type(w) is str:
			w = ord(w) - 65
		return self.edges[v][w][0]
	
#	# return whether is node
#	# O(nV)
#	def validV(self,v):
#		if type(v) is str:
#			v = ord(v) - 65
#		for i in range(self.nV):
#			if self.edges[v][i] != 0:
#				return True
	
#	# check the valid node and return as list
#	# O(nV^2)	nV = 26
#	def _vSet(self):
#		self.vSet = [chr(x+65) for x in range(26) if self.validV(x)]
#		self.nV = len(self.vSet)
	
#	# print edges in graph
#	# O(nV^2)
#	def showGraph(self):
#		for i in range(self.nV):
#			for j in range(i+1,self.nV):
#				if self.edges[i][j] != 0:
#					print("{},{},{}".format(chr(i+65),chr(j+65),self.edges[i][j]))

########################## Route Scheme ##########################
# Shortest Hop Path
# O(nV^2)
def circuit_SHP(graph,start,end):
	dist = [float("inf") for x in range(graph.nV)]
	dist[ord(start)-65] = 0
	pred = [ -1 for x in range(graph.nV)]
	start = ord(start)-65
	adjed = [start]
	visited = [start]
	while len(adjed) != 0:
		source = adjed.pop()
		for i in range(graph.nV):
			if graph.adjacent(source,i) and i not in visited:
				adjed.append(i)
				if dist[i] > dist[source] + 1:
					dist[i] = dist[source] + 1
					pred[i] = source
		visited.append(source)
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
def circuit_SDP(graph,start,end):
	dist = [float("inf") for x in range(graph.nV)]
	dist[ord(start)-65] = 0
	pred = [ -1 for x in range(graph.nV)]
	start = ord(start)-65
	adjed = [start]
	visited = [start]
	while len(adjed) != 0:
		source = adjed.pop()
		for i in range(graph.nV):
			if graph.adjacent(source,i) and i not in visited:
				adjed.append(i)
				if dist[i] > dist[source] + graph.delay(source, i):
					dist[i] = dist[source] + graph.delay(source, i)
					pred[i] = source
		visited.append(source)
	path = [end]
	end = ord(end)-65
	while dist[ord(path[-1])-65] != 0:
		end = pred[end]
		path.append(chr(end+65))
	path.reverse()
	return path

def packet_SDP(graph,start,visited = []):
	path = [start]
	dist = float("inf")
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
Lock = threading.Lock()
threads = []

class request (threading.Thread):
	def __init__(self, threadID, graph, startTime, source, destination, runTime):
		threading.Thread.__init__(self)
		self.threadID = threadID
		self.graph = graph
		self.startTime = startTime
		self.source = source
		self.destination = destination
		self.runTime = runTime
	
	def run(self):
		global NoOfReq, NoOfAllPkt, NoOfSuccPkt, NoOfBlkPkt, NoOfHops, PDelays, NoOfSuccReq
		if(NETWORK_SCHEME == "CIRCUIT"):
			print("Request " + str(self.threadID) + " starts with path:", end='')
			if(ROUTING_SCHEME == "SHP"):
				path = circuit_SHP(self.graph, self.source, self.destination)
			elif(ROUTING_SCHEME == "SDP"):
				path = circuit_SDP(self.graph, self.source, self.destination)
			else:
				pass
			print(path)
			isBlock = False
			Lock.acquire()
			for i in range(len(path)-1):
				isBlock = self.graph.isBlock(path[i],path[i+1])
				# if this sub path is blocked then break the loop and the whole path is blocked
				if isBlock:
					break
			# if the path is not blocked then get ont capacity of all the sub paths
			if not isBlock:
				for i in range(len(path)-1):
					self.graph.occupy(path[i],path[i+1])
				NoOfSuccPkt += int(float(self.runTime) * PACKET_RATE)
				NoOfSuccReq += 1
				NoOfHops += len(path)
				delay = self.graph.delay(path[i],path[i+1])
				PDelays += delay
			else:
				NoOfBlkPkt += int(float(self.runTime) * PACKET_RATE)
				print("Request " + str(self.threadID) + " has been blocked ")
			Lock.release()
			if not isBlock:
				# the time the connection lasts
				time.sleep(float(self.runTime))
				# release resources
				Lock.acquire()
				for i in range(len(path)-1):
					self.graph.release(path[i],path[i+1])
				Lock.release()
				print("Request " + str(self.threadID) + " runs " + str(self.runTime))

def doRequest(threadID, graph, startTime, source, destination, runTime):
	thread = request(threadID, graph, startTime, source, destination, runTime)
	thread.start()
	global threads
	threads.append(thread)
	

########################## Main ##########################
def main():
	global NoOfReq, NoOfAllPkt, NoOfSuccPkt, NoOfBlkPkt, NoOfHops, PDelays, threads
	# open and read TOPOLOGY_FILE
	with open(TOPOLOGY_FILE) as f:
		routers = [line.strip().split(" ") for line in f]

	# open and reand WORKLOAD_FILE
	with open(WORKLOAD_FILE) as f:
		requests = [line.strip().split(" ") for line in f]
	# compute statistics
	NoOfReq = len(requests)	
	for request in requests:
		NoOfAllPkt += int(float(request[3]) * PACKET_RATE)
	
	graph = Graph()
	for router in routers:
		graph.insertEdge(router[0], router[1], router[2], router[3])
#	graph._vSet()
	
#	x = SHP(graph, 'K', 'D')
#	y = SDP(graph, 'F', 'L')
#	print(x)
#	print(y)
	
	# init a schedule
	schedule = sched.scheduler (time.time, time.sleep)
	# put requests into schedule
	for i in range(len(requests)):
		startTime = requests[i][0]
		source = requests[i][1]
		destination = requests[i][2]
		runTime = requests[i][3]
		schedule.enter(float(startTime), 0, doRequest, (i, graph, startTime, source, destination, runTime))
	
	schedule.run()
	
	for t in threads:
		t.join()
	
	print("total number of virtual connection requests:", NoOfReq)
	print("total number of packets:", NoOfAllPkt)
	print("number of successfully routed packets:", NoOfSuccPkt)
	print("percentage of successfully routed packets: {.2f}".format(NoOfSuccPkt/NoOfAllPkt*100))
	print("number of blocked packets:", NoOfBlkPkt)
	print("percentage of blocked packets: {.2f}".format(NoOfBlkPkt/NoOfAllPkt*100))
	print("average number of hops per circuit: {.2f}".format(NoOfHops/NoOfSuccReq*100))
	print("average cumulative propagation delay per circuit: {.2f}".format(PDelays/NoOfSuccReq*100))

if __name__ == "__main__":
	main()