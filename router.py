###############################################################################
# Name: router.py                                                             #
# Author: John Mortimore                                                      #
# Original:  11/19/2019                                                       #
# Moddified: 12/07/2019                                                       #
#                                                                             #
# A program that runs the forward-search algorithm (Dijkstra’s algorithm) and #
# creates a specifically formatted flow table which it communicates to the    #
# controller program (controller.py).                                         #
###############################################################################

from socket import *
import sys

###############################################################################
# Class: AddrMap                                                              #
# Description: Maps host IDs to IP address.                                   #
###############################################################################
class AddrMap:
	def __init__(self, ID, address):
		self.ID = ID
		self.address = address

###############################################################################
# Class: Flow                                                                 #
# Description: Port and destination address pairs.                            #
###############################################################################
class Flow:
	def __init__(self, address, port):
		self.address = address
		self.port = port

###############################################################################
# Func: Dijkstra                                                              #
# Desc: An implementation of Dijkstra's algorithm.                            #
# Args: numNodes {int} - the number of the nodes in the network.              #
# Retn: {list: int} - list of last-hop node (to reach each node in network).  #
#                     List is of node ID numbers or -1 for nodes that cannot  #
#                     be reached from the source.                             #
###############################################################################
def Dijkstra(numNodes):
	global sourceVertex, adjMatrix
	dist = [sys.maxsize]*numNodes		# Initialize distance list.
	prev = [-1]*numNodes				# Initialize previous node list.
	dist[sourceVertex] = 0				# Set distance to source = 0.
	queue = []							
	u=0
	while u < numNodes:					# Insert every node into queue.
		queue.append(u)
		u+=1
	
	while len(queue) > 0:				# Repeat until the queue is empty:
		minDist=sys.maxsize				
		minNode=-1
		# Find node with min dist.
		for node in queue:
			if dist[node] <= minDist:
				minNode = node
				minDist = dist[node]
		u = minNode						# u is node with min dist in queue.
		queue.pop(queue.index(u))		# Remove u from the queue.
		# Update prev and dist for all nodes reachable by u.
		for i, val in enumerate(adjMatrix[u]):
			if val != 0 and dist[u]+1 < dist[i]:
				dist[i] = dist[u]+1
				prev[i] = u
	return prev

###############################################################################
# Func: BuildTable                                                            #
# Desc: Creates the flow table based on the prev list returned by Dijkstra's  #
#       algorithm.                                                            #
# Args: numNodes {int} - the number of the nodes in the network.              #
# Retn: {list: Flow} - flow table.                                            #
###############################################################################
def BuildTable(numNodes):
	global prevList, addressMapList
	table = []

	for host, prevNode in enumerate(prevList):
		if prevNode != -1:							# If host is reachable:
			port = GetPort(host)					# Get the forwarding port.
			address = addressMapList[host].address	# Get the address of host.
			table.append(Flow(address, port))		# Add flow to flow table.
	return table


###############################################################################
# Func: GetPort                                                               #
# Desc: Recursive algorithm to find the appropiate port to use to reach a     #
#       given host. Uses the prev list created by Dijkstra's algorithm.       #
# Args: host {int} - ID of the host to reach.                                 #
# Retn: {int} - forwarding port number to reach host.                         #
###############################################################################
def GetPort(host):
	global sourceVertex, adjMatrix, prevList
	prev = prevList[host] 				# Get the ID of previous node in path.
	if prev == sourceVertex:			# If the prev. node is the source host,
		return adjMatrix[prev][host]	# retn port # to reach the current node.
	else:								# Otherwise,
		return GetPort(prev)			# recurse to the previos node.


###############################################################################
# Func: ParseAdjMatrixPacket                                                  #
# Desc: Creates the ID->Addr map list and the Adj. matrix.                    #
# Args: packetAdjMatix {string} - the packet.                                 #
# Retn: N/A                                                                   #
###############################################################################
def ParseAdjMatrixPacket(packetAdjMatix):
	global adjMatrix, addressMapList, sourceVertex
	adjMatrix = []
	addressMapList = []
	numVertex = 0
	k = 0	# k is the index in adj matrix part of packet.
	for line, val in enumerate(packetAdjMatix.splitlines()):
		# Line 0.
		if line == 0:											
			val = val.replace(" ", "")
			sourceVertex = int(val.split(",")[0])
			numVertex = val.split(",")[1]
		# Lines [1...numVertex]: ID->Addr map.
		elif line <= int(numVertex):							
			val = val.replace(" ", "")
			ID = val.split("=")[0]
			address = val.split("=")[1]
			addressMapList.append(AddrMap(ID, address))
			adjMatrix.append([])
		# The actual adjacency matrix (ignore blank line).
		elif val != "":										
			val = val.replace(" ", "")
			for entry in val.split(","):
				adjMatrix[k].append(int(entry))
			k += 1

###############################################################################
addressMapList = []
adjMatrix = []
sourceVertex = 0

routerPort = 1234
routerSocket = socket(AF_INET, SOCK_STREAM)
routerSocket.bind(('', routerPort))
routerSocket.listen(1)
while True:											# Run forever.
	print("Router listening on port "+ str(routerPort)+".")
	controller, addr = routerSocket.accept() 		
	print("Connected to controller.")

	packetAdjMatix = controller.recv(2048).decode()
	print("├─»Adjacency Matrix Packet received.")
	ParseAdjMatrixPacket(packetAdjMatix)
	print("├─»Running Dijkstra's algorithm.")
	prevList = Dijkstra(len(addressMapList))
	print("├─»Constructing flow table.")
	flowTable = BuildTable(len(addressMapList))
	print("├─»Creating Flow Table Packet.")
	packetFlowTbl = []
	for flow in flowTable:
		packetFlowTbl.append(str(flow.address)+", " +str(flow.port)+"\n")
	if len(packetFlowTbl) == 0: # Must send something or controller will deadlock.
		packetFlowTbl.append("EMPTY") 
	print("├─»Sending packet.")
	controller.send(("".join(packetFlowTbl)).encode())
	print("└─»Disconected from controller.")

	
