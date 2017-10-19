#!/usr/bin/python3
# COMP9331 Assignment2 RoutingPerformance
# z5092923 Wang Jintao
# z5104857 Shi Xiaoyun

from random import choice

import sched, time
from random import randint
import threading
import time
import sys

########################## Input Arguments ##########################
# network type values: CIRCUIT or PACKET
NETWORK_SCHEME = sys.argv[1]
# routing scheme values: Shortest Hop Path (SHP), Shortest Delay Path (SDP) and Least Loaded Path (LLP)
ROUTING_SCHEME = sys.argv[2]
# a file contains the network topology specification
TOPOLOGY_FILE = sys.argv[3]
# a file contains the virtual connection requests in the network
# workload_small.txt or workload.txt
WORKLOAD_FILE = sys.argv[4]
# a positive integer value which show the number of packets per second which will be sent in each virtual connection.
PACKET_RATE = int(sys.argv[5])

timeScale = 10

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

block_number_request = 0

########################## Graph ##########################
class Graph:
	# create a new graph
	def __init__(self,V = 26):
		self.edges = [[0 for x in range(V)] for y in range(V)]
		self.myedge = [[] for x in range(V)]
		self.vSet = [chr(x+65) for x in range(V)]
		self.nV = V
		self.nE = 0
	
	# vertices v and w , delay d, all capacities c, already used capacities s
	def insertEdge(self,v,w,d,c,s = 0):
		v = ord(v) - 65
		w = ord(w) - 65
		d = int(d)
		c = int(c)
		if self.edges[v][w] == 0:
			self.edges[v][w] = [d,c,s];
			self.edges[w][v] = [d,c,s];
			self.myedge[v].append(w)
			self.myedge[w].append(v)
			self.nE += 1;
	
	# occupy a capacity between v,w
	def occupy(self,v,w):
		if type(v) is str:
			v = ord(v) - 65
		if type(w) is str:
			w = ord(w) - 65
		self.edges[v][w][2] += 1
		self.edges[w][v][2] += 1

	# release a capacity between v,w
	def release(self,v,w):
		if type(v) is str:
			v = ord(v) - 65
		if type(w) is str:
			w = ord(w) - 65
		self.edges[v][w][2] -= 1
		self.edges[w][v][2] -= 1
	
	# return whether edge is blocked
	def isBlock(self,v,w):
		if type(v) is str:
			v = ord(v) - 65
		if type(w) is str:
			w = ord(w) - 65
		return (self.edges[v][w][1] == self.edges[v][w][2])
	
	# return delay
	def delay(self,v,w):
		if type(v) is str:
			v = ord(v) - 65
		if type(w) is str:
			w = ord(w) - 65
		return self.edges[v][w][0]
	
	# return already used capacities s
	def s(self,v,w):
		if type(v) is str:
			v = ord(v) - 65
		if type(w) is str:
			w = ord(w) - 65
		return self.edges[v][w][2]
	
	# return capacities c
	def c(self,v,w):
		if type(v) is str:
			v = ord(v) - 65
		if type(w) is str:
			w = ord(w) - 65
		return self.edges[v][w][1]
	
	# return all adjacent node
	def edge(self,v):
		if type(v) is str:
			v = ord(v) - 65
		return self.myedge[v]

########################## Route Scheme ##########################

# Shortest Delay Path
# O(nV^2)
def dijkstra(graph,start,end):
	start = ord(start)-65
	dist = [float("inf") for x in range(graph.nV)]
	pred = [ -1 for x in range(graph.nV)]
	visited = [False for x in range(graph.nV)]
	dist[start] = 0
	pred[start] = -2
	visited[start] = True
	adjed = [start]
	while len(adjed) != 0:
		source = adjed.pop()
		edge = graph.edge(source)
		for i in edge:
			if visited[i] == False:
				adjed.append(i)
				if ROUTING_SCHEME == "SDP":
					if dist[i] > dist[source] + graph.delay(source, i):
						dist[i] = dist[source] + graph.delay(source, i)
						pred[i] = source
					elif dist[i] == dist[source] + graph.delay(source,i):
						pred[i] = choice([source,pred[i]])
				elif ROUTING_SCHEME == "SHP":
					if dist[i] > dist[source] + 1:
						dist[i] = dist[source] + 1
						pred[i] = source
					elif dist[i] == dist[source] + 1:
						pred[i] = choice([source,pred[i]])
				elif ROUTING_SCHEME == "LLP":
					tmp = graph.s(source,i)*10000 / graph.c(source,i)
					if dist[i] > max(dist[source], tmp):
						dist[i] = max(dist[source], tmp)
						pred[i] = source
					elif dist[i] == max(dist[source], tmp):
						pred[i] = choice([source, pred[i]])
		visited[source] = True
	path = [end]
	end = ord(end)-65
	while pred[ord(path[-1])-65] != -2:
		end = pred[end]
		path.append(chr(end+65))
	path.reverse()
	return path

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
		global NoOfReq, NoOfAllPkt, NoOfSuccPkt, NoOfBlkPkt, NoOfHops, PDelays, NoOfSuccReq, blocklist
		# CIRCUIT network: the connection is established from start to end
		if(NETWORK_SCHEME == "CIRCUIT"):
			interval = self.runTime
		# PACKET network: the request should establish connection every 1/PACKET_RATE seconds
		elif(NETWORK_SCHEME == "PACKET"):
			interval = 1 / PACKET_RATE / timeScale
		
		currentTime = 0.0
		while currentTime < self.runTime:
			currentTime += interval
			print("Request " + str(self.threadID) + " starts with path:", end='')
			path = dijkstra(self.graph, self.source, self.destination)
			print(path)
			Lock.acquire()
			isBlock = False
			for i in range(len(path)-1):
				isBlock = self.graph.isBlock(path[i],path[i+1])
				# if this sub path is blocked then break the loop and the whole path is blocked
				if isBlock:
					print(path)
					break
			# if the path is not blocked then get ont capacity of all the sub paths
			if not isBlock:
				for i in range(len(path)-1):
					self.graph.occupy(path[i],path[i+1])
				NoOfSuccPkt += int(interval * PACKET_RATE * timeScale)
				NoOfSuccReq += 1
				NoOfHops += len(path)
				delay = self.graph.delay(path[i],path[i+1])
				PDelays += delay
			else:
				NoOfBlkPkt += int(interval * PACKET_RATE * timeScale)
#				print("Request " + str(self.threadID) + " has been blocked ")
			Lock.release()
			if not isBlock:
				# the time the connection lasts
				time.sleep(interval)
				# release resources
				Lock.acquire()
				for i in range(len(path)-1):
					self.graph.release(path[i],path[i+1])
				Lock.release()
#				if(NETWORK_SCHEME == "CIRCUIT"):
#					print("Request " + str(self.threadID) + " durates {:.6f}".format(interval))
#				else:
#					print("Request " + str(self.threadID) + " starts a request after {:.6f}".format(currentTime - interval))

def doRequest(threadID, graph, startTime, source, destination, runTime):
	thread = request(threadID, graph, startTime, source, destination, runTime)
	thread.start()
	global threads
	threads.append(thread)


########################## Main ##########################
def main():
	global NoOfReq, NoOfAllPkt, NoOfSuccPkt, NoOfBlkPkt, NoOfHops, PDelays, threads
	
	# graph initial
	# open and read TOPOLOGY_FILE
	with open(TOPOLOGY_FILE) as f:
		routers = [line.strip().split(" ") for line in f]
	graph = Graph()
	for router in routers:
		graph.insertEdge(router[0], router[1], router[2], router[3])
	
	# open and reand WORKLOAD_FILE
	with open(WORKLOAD_FILE) as f:
		requests = [line.strip().split(" ") for line in f]
	
	# compute statistics
	NoOfReq = len(requests)	
	for request in requests:
		NoOfAllPkt += int(float(request[3]) * PACKET_RATE)
		
	
	
	# init a schedule
	schedule = sched.scheduler (time.time, time.sleep)
	# put requests into schedule
	for i in range(len(requests)):
		startTime = float(requests[i][0]) / timeScale
		source = requests[i][1]
		destination = requests[i][2]
		runTime = float(requests[i][3]) / timeScale
		schedule.enter(startTime, 0, doRequest, (i, graph, startTime, source, destination, runTime))
	
	start  = time.time()
	
	schedule.run()
	
	for t in threads:
		t.join()
	
	print("RuntTime:{:.2f}".format(time.time()-start))
	
	print("total number of virtual connection requests:", NoOfReq)
	print("total number of packets:", NoOfAllPkt)
	print("number of successfully routed packets:", NoOfSuccPkt)
	print("percentage of successfully routed packets: {:.2f}".format(NoOfSuccPkt / NoOfAllPkt * 100))
	print("number of blocked packets:", NoOfBlkPkt)
	print("percentage of blocked packets: {:.2f}".format(NoOfBlkPkt / NoOfAllPkt * 100))
	print("average number of hops per circuit: {:.2f}".format(NoOfHops / NoOfSuccReq))
	print("average cumulative propagation delay per circuit: {:.2f}".format(PDelays / NoOfSuccReq))

if __name__ == "__main__":
	main()