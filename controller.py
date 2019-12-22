###############################################################################
# Name: controller.py                                                         #
# Author: John Mortimore                                                      #
# Original:  11/19/2019                                                       #
# Moddified: 12/13/2019                                                       #
#                                                                             #
# This program talks back and forth to the routing program by sending an      #
# adjacency matrix for the current state of the network. It receives back a   #
# flow table, which it sends on to the simulated switch program (switch.py).  #
###############################################################################

from socket import *

###############################################################################
# Class: AddrMap                                                              #
# Description: Maps host IDs to IP address.                                   #
###############################################################################
class AddrMap:
	def __init__(self, ID: int, address):
		self.ID = ID
		self.address = address

###############################################################################
# Class: SrcPortDstMap                                                        #
# Description: Maps [sourceAddr]->[port]->[destinationAddr] triples.          #
###############################################################################
class SrcPortDstMap:
	def __init__(self, srcID: int, port: int, dstID: int):
		self.srcID = srcID
		self.port = port
		self.dstID = dstID

###############################################################################
# Func: loadNetTopo                                                           #
# Desc: Loads the initial network topology from file "adjMatrix.txt".         #
# Args: N/A                                                                   #
# Retn: N/A                                                                   #
###############################################################################
def loadNetTopo():
	global addressMapList, connectionList
	numVertex = 0
	k = 0	# k is the index in adj matrix part of packet.
	lineIndex = 0
	for line in open("adjMatrix.txt", 'r'):
		# Line 0.
		if lineIndex == 0:											
			line = line.replace(" ", "")
			numVertex = int(line.split(",")[1])
		# Lines [1...numVertex]: ID->Addr map.
		elif lineIndex <= numVertex:							
			line = line.replace(" ", "")
			line = line.replace("\n", "")
			ID = int(line.split("=")[0])
			address = line.split("=")[1]
			addressMapList.append(AddrMap(ID, address))
		# The actual adjacency matrix (ignore blank line).
		elif line != "\n":										
			line = line.replace(" ", "")
			for i, entry in enumerate(line.split(",")):
				if int(entry) != 0:
					connection = SrcPortDstMap(int(k), int(entry), int(i))
					connectionList.append(connection)
			k += 1
		lineIndex += 1

###############################################################################
# Func: CreateAdjMatrixPacket                                                 #
# Desc: Creates the Adjacency Matrix Packet to send to the router.            #
# Args: srcID {int} - ID of source vertex.                                    #
# Retn: {list: string} - the packet.                                          #
###############################################################################
def CreateAdjMatrixPacket(srcID):
	global addressMapList, connectionList

	packet = []
	numHost = len(addressMapList)
	# Src host and number of host.
	packet.append(str(srcID) + ", " + str(numHost)+"\n")
	# Host IDs and addresses.
	for host in addressMapList:
		packet.append(str(host.ID)+" = " +str(host.address)+"\n")
	packet.append("\n")
	
	matrix = [[0]*numHost for _ in range(numHost)]
	# Build matrix.
	for entry in connectionList:
		srcID = entry.srcID
		portNum = entry.port
		dstID = entry.dstID
		matrix[srcID][dstID] = portNum

	# Matrix as string (packet).
	y=0
	while y < numHost:
		x=0
		line = ""
		while x < numHost:
			line += str(matrix[y][x])
			line += ", " if (x < numHost-1) else "\n"
			x += 1
		packet.append(line)
		y += 1
	i=0

	return packet

###############################################################################
# Func: GetAddr                                                               #
# Desc: Returns the address of a host from its ID.                            #
# Args: ID {int} - the ID of the host.                                        #
# Retn: {string} - IPv4 address or -1 if host DNE.                            #
###############################################################################
def GetAddr(ID: int):
	global addressMapList
	addr = -1
	for entry in addressMapList:
		if entry.ID == ID:
			addr = entry.address
	return addr

###############################################################################
# Func: GetID                                                                 #
# Desc: Returns the ID of a host from its IPv4 address.                       #
# Args: addr {string} - the IPv4 address of the host.                         #
# Retn: {int} - the ID or -1 if host DNE.                                     #
###############################################################################
def GetID(addr):
	global addressMapList
	ID = -1
	for entry in addressMapList:
		if entry.address == addr:
			ID = entry.ID
	return ID

###############################################################################
# Func: FindAvailablePort                                                     #
# Desc: Find an unused port number on a host for the sake of establishing a   #
#       connection. Used by AddConnection to find an ingress port on the      #
#       destination host.                                                     #
# Retn: {int} - port number.                                                  #
###############################################################################
def FindAvailablePort(host):
	ports = []
	ports.append(0)		# 0 is not a vailid port, but list must not be empty.
	for entry in connectionList:			# Get list of ports in use.
		if entry.srcID == host:
			ports.append(int(entry.port))
	
	test = 1
	while True:								# Find an unused port number
		if test in ports:
			test += 1
		else:
			break
	return test

###############################################################################
# Func: AddConnection                                                         #
# Desc: Adds connection to the network.                                       #
# Args: srcID {int} - the ID of source of the connection.                     #
#       port {int} - the port number on the source to use.                    #
#       dstID {int} - the ID of the destination host.                         #
#       dstAddr {int} - the address of the destination host. Needed if the    #
#                       host is new to the network.                           #
# Retn: N/A                                                                   #
###############################################################################
def AddConnection(srcID, port, dstID, dstAddr):
	global addressMapList, connectionList
	srcAddr = GetAddr(srcID)

	# Error handling.
	for entry in connectionList:
		# If connection already exist -> fail.
		if entry.srcID == srcID and entry.dstID == dstID:
			print("│   ├─»Error: Connection between host already exist.\n"
				+ "│   │         Redundant connections forbidden.")
			print("│   └─»Add request failed.")
			return
		# If port number in use -> fail.
		if entry.srcID == srcID and entry.port == port:
			print("│   ├─»Error: Port number " + str(port) + " already in use.")
			print("│   └─»Add request failed.")
			return

	# If dst DNE -> add host.
	if dstID == -1:
		print("│   ├─»Destination host DNE on network.")
		print("│   ├─»Adding host to network.")
		dstID = len(addressMapList)
		addressMapList.append(AddrMap(dstID, dstAddr))
		
	# Success.
	print("│   └─»Adding port " + str(port) 
		+ " ("+str(srcAddr) + " ⭩ " + str(dstAddr) + ").")
	print("│   └─»Adding port " + str(FindAvailablePort(dstID)) 
		+ " ("+str(dstAddr) + " ⭩ " + str(srcAddr) + ").")
	connectionList.append(SrcPortDstMap(srcID, port, dstID))
	connectionList.append(SrcPortDstMap(dstID, FindAvailablePort(dstID), srcID))

###############################################################################
# Func: DeleteConnection                                                      #
# Desc: Remove connection from the network.                                   #
# Args: srcID {int} - the ID of source of the connection.                     #
#       port {int} - the port number on the source to use.                    #
# Retn: N/A                                                                   #
###############################################################################
def DeleteConnection(srcID, port):
	global connectionList
	srcAddr = GetAddr(srcID)

	connDNE=True
	for entry in connectionList:
		# If connection exist -> delete it (src -> dst).
		if entry.srcID == srcID and entry.port == port:
			connDNE = False
			dstID = entry.dstID
			connectionList.remove(entry)
			print("│   ├─»Deleting port "+ str(port)
				+ " (" + str(srcAddr) + " ⭩ " + str(GetAddr(entry.dstID)) + ").")

	# Remove the parallel connection (from dst -> src).
	if not connDNE:
		for entry in connectionList:
			if entry.srcID == dstID and entry.dstID == srcID:
				connectionList.remove(entry)
				print("│   └─»Deleting port "+ str(entry.port)
					+ " (" + GetAddr(entry.srcID) + " ⭩ " + GetAddr(entry.dstID) + ").")
	# If dst -> fail.
	else:
		print("│   ├─»Error: No such connection on network.")
		print("│   └─»Delete request failed.")

###############################################################################
addressMapList = []
connectionList = []
routerHost = 'localhost'
routerPort = 1234

loadNetTopo()									# Load initial network topology.

controllerPort = 2345
controllerSocket = socket(AF_INET, SOCK_STREAM)
controllerSocket.bind(('', controllerPort))
controllerSocket.listen(1)

while True:										# Run forever.

	print("Controller listening on port " + str(controllerPort) +".")
	switch, addr = controllerSocket.accept()
	packetUpdate = switch.recv(2048).decode()
	srcID = int(packetUpdate.split(", ")[0])
	command = packetUpdate.split(", ")[1]
	port = int(packetUpdate.split(", ")[2])
	dstAddr = packetUpdate.split(", ")[3]
	dstID = int(GetID(dstAddr))
	srcAddr = GetAddr(srcID)
	print("Connected to switch " + srcAddr + ".")
	print("├─»Update Packet received.")
	# ADD or DELETE port.
	if port != 0:
		if command == "ADD":
			print("│   ├─»Add request.")
			AddConnection(srcID, port, dstID, dstAddr)
		elif command == "DELETE":
			print("│   ├─»Delete request.")
			DeleteConnection(srcID, port)				
	else:
		print("│   └─»Flow table request.")
	# Send adj matrix to Router.
	print("├─»Creating Adjacency Matrix Packet.")
	packetAdjMatix = CreateAdjMatrixPacket(srcID)
	router = socket(AF_INET, SOCK_STREAM)
	router.connect((routerHost, routerPort))
	print("├─»Connected to router.")
	
	router.send(("".join(packetAdjMatix)).encode())
	print("│  ├─»Sending Adjacency Matrix Packet to router.")
	# Listen for response from Router.
	flowTable = router.recv(2048).decode()
	print("│  ├─»Flow table received from router.")
	print("│  └─»Disconnecting from router.")
	router.close()

	# Send flow table to switch.
	print("├─»Sending flow table to switch.")
	switch.send(flowTable.encode())
	print("└─»Disconnected from switch.")




