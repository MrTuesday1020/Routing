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
# NETWORK_SCHEME = sys.argv[1]
NETWORK_SCHEME = "CIRCUIT"
# routing scheme values: Shortest Hop Path (SHP), Shortest Delay Path (SDP) and Least Loaded Path (LLP)
# ROUTING_SCHEME = sys.argv[2]
ROUTING_SCHEME = "SDP"
# a file contains the network topology specification
# TOPOLOGY_FILE = sys.argv[3]
TOPOLOGY_FILE = "topology.txt"
# a file contains the virtual connection requests in the network
# workload_small.txt or workload.txt
# WORKLOAD_FILE = sys.argv[4]
WORKLOAD_FILE = "workload.txt"
# a positive integer value which show the number of packets per second which will be sent in each virtual connection.
# PACKET_RATE = int(sys.argv[5])
PACKET_RATE = 10


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
	def __init__(self,V = 26):
		self.edges = [[0 for x in range(V)] for y in range(V)]
		self.myedge = [[] for x in range(V)]
		self.vSet = [chr(x+65) for x in range(V)]
		self.nV = V
		self.nE = 0
	
	# vertices v and w , timelist stores finish times
	def insertEdge(self, v, w, delay, capacity, time_list = []):
		v = ord(v) - 65
		w = ord(w) - 65
		delay = int(delay)
		capacity = int(capacity)
		if self.edges[v][w] == 0:
			self.edges[v][w] = [delay, capacity, time_list];
			self.edges[w][v] = [delay, capacity, time_list];
			self.myedge[v].append(w)
			self.myedge[w].append(v)
			self.nE += 1;
	
	# occupy a capacity between v,w
	def occupy(self,v,w,time):
		if type(v) is str:
			v = ord(v) - 65
		if type(w) is str:
			w = ord(w) - 65
		self.edges[v][w][2].append(time)
		self.edges[w][v][2].append(time)

	# release a capacity between v,w
	def release(self,time):
		for i in range(self.nV):
			for j in range(self.nV):
				if self.edges[i][j] != 0:
					time_tmp = []
					for k in range(len(self.edges[i][j][2])):
						if self.edges[i][j][2][k] > time:
							time_tmp.append(self.edges[i][j][2][k])
					self.edges[i][j][2] = time_tmp[:]
	
	# return whether edge is blocked
	def isBlock(self,v,w):
		if type(v) is str:
			v = ord(v) - 65
		if type(w) is str:
			w = ord(w) - 65
		return (self.edges[v][w][1] == len(self.edges[v][w][2]))
	
	# return delay
	def delay(self,v,w):
		if type(v) is str:
			v = ord(v) - 65
		if type(w) is str:
			w = ord(w) - 65
		return self.edges[v][w][0]
	
	# return already used capacities
	def used_capacity(self,v,w):
		if type(v) is str:
			v = ord(v) - 65
		if type(w) is str:
			w = ord(w) - 65
		return len(self.edges[v][w][2])
	
	# return capacities
	def capacity(self,v,w):
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
		source = adjed.pop(0)
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
					tmp = graph.used_capacity(source,i)*10000 / graph.capacity(source,i)
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


########################## Main ##########################
def main():
	global NoOfReq, NoOfAllPkt, NoOfSuccPkt, NoOfBlkPkt, NoOfHops, PDelays

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
	# request[0]: start time, request[1]: source, request[2]:destination, request[3]:duration
	NoOfReq = len(requests)	
	
	for request in requests:
		NoOfAllPkt += int(float(request[3]) * PACKET_RATE)
		
		# release sources
		graph.release(float(request[0]))
		
		# get path
		path = dijkstra(graph, request[1], request[2])
		print(path)
		
		# check if the path is blocked
		isblock = False
		for i in range(len(path)-1):
			if graph.isBlock(path[i], path[i+1]):
				isblock = True
				break
		
		if isblock: 
			NoOfBlkPkt += int(float(request[3]) * PACKET_RATE)
		else:
			NoOfSuccPkt += int(float(request[3]) * PACKET_RATE)
			for i in range(len(path)-1):
				graph.occupy(path[i], path[i+1], float(request[0]) + float(request[3]))

	
	print("total number of virtual connection requests:", NoOfReq)
	print("total number of packets:", NoOfAllPkt)
	print("number of successfully routed packets:", NoOfSuccPkt)
	print("percentage of successfully routed packets: {:.2f}".format(NoOfSuccPkt / NoOfAllPkt * 100))
	print("number of blocked packets:", NoOfBlkPkt)
	print("percentage of blocked packets: {:.2f}".format(NoOfBlkPkt / NoOfAllPkt * 100))
#	print("average number of hops per circuit: {:.2f}".format(NoOfHops / NoOfSuccReq))
#	print("average cumulative propagation delay per circuit: {:.2f}".format(PDelays / NoOfSuccReq))

if __name__ == "__main__":
	main()