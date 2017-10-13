#!/usr/bin/python3
# COMP9331 Assignment2 RoutingPerformance
# z5092923 Wang Jintao
# z5104857 Shi Xiaoyun

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

# open and read TOPOLOGY_FILE
with open(TOPOLOGY_FILE) as f:
	routers = [line.strip().split(" ") for line in f]

# open and reand WORKLOAD_FILE
with open(WORKLOAD_FILE) as f:
	requests = [line.strip().split(" ") for line in f]

for router in routers:
	print("insert source " + str(router[0]) + " and destination " + str(router[1]) + " with values " + str(router[2:4]))