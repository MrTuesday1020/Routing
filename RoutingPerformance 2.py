#! /usr/bin/python
# -*- coding: utf-8 -*-
import os
import sys
import heapq
from random import choice

NETWORK_SCHEME = "CIRCUIT"
ROUTING_SCHEME = "SHP"
PACKET_RATE = 10

graph = {}

# path_record
path_record = ['0' for i in range(26)]

topology_file_path = "topology.txt"
workload_file_path="workload.txt"


# final statistics
total_number_request = 0
total_number_packet = 0
success_number_packet = 0
block_number_packet = 0
success_total_number_hop = 0
success_total_number_delay = 0
# update
success_number_request = 0
block_number_request = 0


class Edge(object):
    """ use this class to represent one edge 
         edge A -> B is equals to B -> A and 
         represent by "AB"
    """
    def __init__(self, name, delay, capacity):
        self.name = name
        self.delay = delay
        self.capacity = capacity
        self.connect_end_time = []

    def isBlocked(self):
        return len(self.connect_end_time) >= self.capacity

    def update_connect(self, current):
        self.connect_end_time = filter(lambda x: x > current, self.connect_end_time)


class Node(object):
    def __init__(self, no, start_time, sourceId, dstId, end_time):
        self.no = no
        self.start_time = start_time
        self.sourceId = sourceId
        self.dstId = dstId
        self.end_time = end_time
        self.next = None 

def path_record_initial(sourceId):
    global path_record
    for i in range(26):
        path_record[i] = sourceId

def getEdge(sourceId, dstId):
    name = ""
    if ord(sourceId) < ord(dstId):
        name = sourceId + dstId
    else:
        name = dstId + sourceId
    return graph.get(name)

# initial of model of network, as show before, we use 2-dimensional array to describe one network
# we assume the input file is topology.txt
def graph_initial():
    global graph
    if not os.path.exists(topology_file_path):
        print "topology.txt is not exist, please add it!"
        exit()

    file = open(topology_file_path)
    for line in file:
        line = line.rstrip('\n')
        line_list = line.split(' ')
        if (len(line_list) != 4) :
            print "file format is wrong, and line is " + line
            exit()
        else:
            name = ""
            if ord(line_list[0]) > ord(line_list[1]):
                name = line_list[1]+line_list[0]
            else:
                name = line_list[0]+line_list[1]

            if not graph.has_key(name):
                graph[name] = Edge(name, int(line_list[2]), int(line_list[3]))

# step one of dijkstra
def initial_cost_array(sourceId):
    cost_array = [0 for i in range(26)]
    for i in range(26):
        edge = getEdge(sourceId, chr(i + ord('A')))
        if ROUTING_SCHEME == "SHP":
            if edge != None:
                cost_array[i] = 1
            else:
                cost_array[i] = sys.maxint
        elif ROUTING_SCHEME == "SDP":
            if edge != None:
                cost_array[i] = edge.delay
            else:
                cost_array[i] = sys.maxint
        else:
            if edge != None:
                cost_array[i] = len(edge.connect_end_time)*10000 / edge.capacity
            else:
                cost_array[i] = sys.maxint
    return cost_array

# step four of dijkstra
def update_cost_array(current_node, temp_min_node, cost_array):
    global path_record
    edge = getEdge(current_node, temp_min_node)
    if edge != None:
        i = ord(current_node) - ord('A')
        j = ord(temp_min_node) - ord('A')
        if ROUTING_SCHEME == "SHP":
            if cost_array[i] > cost_array[j] + 1:
                cost_array[i] = cost_array[j] + 1
                path_record[i] = temp_min_node
            elif cost_array[i] == cost_array[j] + 1:
                path_record[i] = choice([temp_min_node, path_record[i]])
        elif ROUTING_SCHEME == "SDP":
            if cost_array[i] > cost_array[j] + edge.delay:
                cost_array[i] = cost_array[j] + edge.delay
                path_record[i] = temp_min_node
            elif cost_array[i] == cost_array[j] + edge.delay:
                path_record[i] = choice([temp_min_node, path_record[i]])
        else:
            load = len(edge.connect_end_time)
            if cost_array[i] > max(cost_array[j], load*10000 / edge.capacity):
                cost_array[i] = max(cost_array[j], load*10000 / edge.capacity)
                path_record[i] = temp_min_node
            elif cost_array[i] == max(cost_array[j], load*10000 / edge.capacity):
                path_record[i] = choice([temp_min_node, path_record[i]])

def dijkstra(sourceId, dstId):
    visited_node = [False for k in range(26)]
    visited_node[ord(sourceId) - ord('A')] = True

    # step one : initial the least cost array
    cost_array = initial_cost_array(sourceId)

    # step two: initial the path_record
    path_record_initial(sourceId)

    while True:
        # step three: find min
        temp_min = sys.maxint
        random_array = []
        for i in range(26):
            if visited_node[i] == False:
                if cost_array[i] < temp_min:
                    temp_min = cost_array[i]
                    random_array = [i]
                elif cost_array[i] == temp_min:
                    random_array.append(i)
        # there is no connect from source to destination
        if len(random_array) == 0:
            return False

        temp_min_node = chr(choice(random_array) + ord('A'))

        if temp_min_node == dstId:
            return True

        visited_node[ord(temp_min_node) - ord('A')] = True

        # step four: update
        for i in range(26):
            if (visited_node[i] == False): 
                update_cost_array(chr(i + ord('A')), temp_min_node, cost_array)

def put_node(node, linkedList):
    if linkedList.next == None:
        linkedList.next = node
    else:
        pre = linkedList
        temp = linkedList.next
        while (temp != None and node.start_time > temp.start_time):
            pre = pre.next
            temp = temp.next
        pre.next = node
        node.next = temp


def handle_workload_packet():
    global total_number_request
    global total_number_packet
    global success_number_packet
    global block_number_packet
    global success_total_number_hop
    global success_total_number_delay

    global success_number_request
    global block_number_request

    block_request = {}

    delay_packet = 1000000 / PACKET_RATE

    head_of_list = Node(0, 0, "0", "0", 0)
    current_node = head_of_list
    file = open(workload_file_path)
    iter_id = 0
    for line in file:
        line = line.rstrip('\n')
        line_list = line.split(' ')
        start_time = int(float(line_list[0])*1000000)
        sourceId = line_list[1]
        dstId = line_list[2]
        duration_time = int(float(line_list[3])*1000000) 
        # use linkedList to handle packet circuit
        if (duration_time >= delay_packet):
            p = Node(iter_id, start_time, sourceId, dstId, start_time + duration_time)
            current_node.next = p
            current_node = p
            total_number_request += 1
            iter_id += 1

    while (head_of_list.next != None):
        temp_node = head_of_list.next
        head_of_list.next = temp_node.next

        start_time = temp_node.start_time
        sourceId = temp_node.sourceId
        dstId = temp_node.dstId
        end_time = temp_node.end_time
        no = temp_node.no

         # run the dijkstra
        if ROUTING_SCHEME == "LLP":
            for edge in graph.values():
                edge.update_connect(start_time)
         # run the dijkstra
        result = dijkstra(sourceId, dstId)

        sum_of_delay = 0
        sum_of_hop = 0

        #case one:  there is no phisical path from source to des => blocked
        if result == False:
            block_number_packet += 1
            if (not block_request.has_key(no)) :
                block_request[no] = 1
        else:
            dst_of_link = dstId
            source_of_link = path_record[ord(dst_of_link) - ord('A')]
            flag = True
            path = []
            while source_of_link != dst_of_link:
                edge = getEdge(source_of_link, dst_of_link)
                edge.update_connect(start_time)

                path.append(edge)
                # case two: the load of link = capacity => blocked
                if edge.isBlocked():
                    block_number_packet += 1
                    if (not block_request.has_key(no)) :
                        block_request[no] = 1
                    flag = False
                    break
                else:
                    sum_of_hop += 1
                    sum_of_delay += edge.delay
                dst_of_link = source_of_link
                source_of_link = path_record[ord(dst_of_link) - ord('A')]
            if flag:
                for i in range(len(path)):
                    path[i].connect_end_time.append(start_time + delay_packet)
                success_total_number_hop += sum_of_hop
                success_total_number_delay += sum_of_delay
                success_number_packet += 1
        total_number_packet += 1

        if start_time + 2*delay_packet <= end_time:
            put_node(Node(no, start_time + delay_packet, sourceId, dstId, end_time), head_of_list)

        block_number_request = len(block_request.keys())
        success_number_request = total_number_request - block_number_request

def handle_workload():
    global total_number_request
    global total_number_packet
    global success_number_packet
    global block_number_packet
    global success_total_number_hop
    global success_total_number_delay

    global success_number_request
    global block_number_request

    delay_packet = 1000000 / PACKET_RATE

    file = open(workload_file_path)
    for line in file:
        line = line.rstrip('\n')
        line_list = line.split(' ')
        start_time = int(float(line_list[0])*1000000)
        sourceId = line_list[1]
        dstId = line_list[2]
        duration_time = int(float(line_list[3])*1000000) 

        num_packet = int(duration_time / delay_packet)

        # run the dijkstra
        if ROUTING_SCHEME == "LLP":
            for edge in graph.values():
                edge.update_connect(start_time)
        result = dijkstra(sourceId, dstId)

        sum_of_delay = 0
        sum_of_hop = 0

        #case one:  there is no phisical path from source to des => blocked
        if result == False:
            block_number_packet += num_packet
            block_number_request += 1
        else:
            dst_of_link = dstId
            source_of_link = path_record[ord(dst_of_link) - ord('A')]
            flag = True
            path = []
            while source_of_link != dst_of_link:
                edge = getEdge(source_of_link, dst_of_link)
                edge.update_connect(start_time)
                path.append(edge)
                # case two: the load of link = capacity => blocked
                if edge.isBlocked():
                    block_number_packet += num_packet
                    block_number_request += 1
                    flag = False
                    break
                else:
                    sum_of_hop += 1
                    sum_of_delay += edge.delay
                dst_of_link = source_of_link
                source_of_link = path_record[ord(dst_of_link) - ord('A')]
            if flag:
                for i in range(len(path)):
                    path[i].connect_end_time.append(start_time + duration_time)
                success_total_number_hop += sum_of_hop * num_packet
                success_total_number_delay += sum_of_delay * num_packet
                success_number_packet += num_packet
                success_number_request += 1
        total_number_request += 1
        total_number_packet += num_packet

#NETWORK_SCHEME = sys.argv[1]
#ROUTING_SCHEME = sys.argv[2]
#topology_file_path = sys.argv[3]
#workload_file_path = sys.argv[4]
#PACKET_RATE = int(sys.argv[5])

graph_initial()
if NETWORK_SCHEME == "CIRCUIT":
    handle_workload()
else:
    handle_workload_packet()
print "total number of virtual circuit requests: " + str(total_number_request)
# print "total number of packets: " + str(total_number_packet)
# print "number of successfully routed packets: " + str(success_number_packet)
# print "percentage of successfully routed packets: " + "%.2f" % (float(success_number_packet * 100) / total_number_packet)
# print "number of blocked packets: " + str(block_number_packet)
# print "percentage of blocked packets: " + "%.2f" % (float(block_number_packet * 100) / total_number_packet)
print "number of successfully routed requests: " + str(success_number_request)
print "percentage of successfully routed request: " + "%.5f" % (float(success_number_request * 100) / total_number_request)
print "number of blocked requests: " + str(block_number_request)
print "percentage of blocked requests: " + "%.5f" % (float(block_number_request * 100) / total_number_request)
print "average number of hops per circuit: " + "%.5f" % (float(success_total_number_hop) / success_number_packet)
print "average cumulative propagation delay per circuit: " + "%.5f" % (float(success_total_number_delay) / success_number_packet)
