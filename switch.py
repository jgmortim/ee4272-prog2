###############################################################################
# Name: switch.py                                                             #
# Author: John Mortimore                                                      #
# Original:  11/19/2019                                                       #
# Moddified: 12/12/2019                                                       #
#                                                                             #
# This simulated switch program is interactive, such that you can put in a    #
# destination IP address and the program will print out which port that       #
# “packet” will be forwarded out. You can also trigger routing updates by     #
# bringing connections up and down.                                           #
###############################################################################

from socket import *
import re

###############################################################################
# Class: Flow                                                                 #
# Description: Port and destination address pairs.                            #
###############################################################################
class Flow:
	def __init__(self, address, port):
		self.address = address
		self.port = port

###############################################################################
# Func: CreateUpdatePacket                                                    #
# Desc: Creates the update packet to send to the controller.                  #
# Args: command {string} - either add or delete.                              #
#       portNum {int} - the port number for the connection to add/delete.     #
#       IPaddr {string} - destination of connection.                          #
# Retn: {string} - the packet.                                                #
###############################################################################
def CreateUpdatePacket(command, portNum, IPaddr):
	global switchID
	packet = str(switchID) + ", " + command + ", " + str(portNum) + ", " + IPaddr
	return packet

###############################################################################
# Func: ParseFlowTablePacket                                                  #
# Desc: Contructs the flow table (data structure) from the packet.            #
# Args: flowTablePacket {string} - the packet recieved from the controller.   #
# Retn: N/A                                                                   #
###############################################################################
def ParseFlowTablePacket(flowTablePacket):
	global flowTable
	flowTable = []
	if flowTablePacket == "EMPTY":		# Switch has no active ports
		return
	for row in flowTablePacket.splitlines():
		address = re.search("^(" + IPv4 + "), ", str(row)).group(1)
		port = re.search(" (\d+)$", str(row)).group(1)
		if int(port) != -1:
			flowTable.append(Flow(address, port))

###############################################################################
# Func: CommHelp                                                              #
# Desc: Print the accepted commands.                                          #
# Args: N/A                                                                   #
# Retn: N/A                                                                   #
###############################################################################
def CommHelp():
	print("Command not recognized. Try:")
	print("       ADD [port#] [IPv4 address]")
	print("       ADD 0")
	print("         A [port#] [IPv4 address]")
	print("         A 0")
	print("    DELETE [port#]")
	print("         D [port#]")
	print("   FORWARD [IPv4 address]")
	print("         F [IPv4 address]")
	print("      exit")

###############################################################################
# Func: ControllerHandler                                                     #
# Desc: Sends update packet to the controller and receives the flow table.    #
# Args: packet {string} - the update packet.                                  #
# Retn: N/A                                                                   #
###############################################################################
def ControllerHandler(packet):
	global controllerHost, controllerPort
	controller = socket(AF_INET, SOCK_STREAM)
	controller.connect((controllerHost, controllerPort))
	print("Connected to controller.")
	print("├─»Sending packet.")
	controller.send(packet.encode())
	flowTablePacket = controller.recv(2048).decode()
	print("├─»New flow table received.")
	print("└─»Disconnecting from controller.")
	controller.close()
	ParseFlowTablePacket(flowTablePacket)

###############################################################################
switchID = 0					# Initialize to 0.
flowtable = []					# Global.
controllerHost = 'localhost'	# Global.
controllerPort = 2345			# Global.
# Define regex for an IPv4 address.
IPv4 = ("((25[0-5]|2[0-4][0-9]|1[0-9]{2}|[1-9][0-9]|[0-9])\.){3}"
	"(25[0-5]|2[0-4][0-9]|1[0-9]{2}|[1-9][0-9]|[0-9])")
# Define syntax for ADD.
reADD = re.compile("^ADD ((0)|(\d+ "+IPv4+"))$")
reShortADD = re.compile("^A ((0)|(\d+ "+IPv4+"))$")
# Define syntax for FORWARD.
reFORWARD = re.compile("^FORWARD "+IPv4+"$")
reShortFORWARD = re.compile("^F "+IPv4+"$")
# Define syntax for DELETE.
reDELETE = re.compile("^DELETE \d+$")
reShortDELETE = re.compile("^D \d+$")

print("Welcome to the interactive switch simulator!")
# Select a switch to simulate.
while int(switchID) < 1 or int(switchID) > 3:
	switchID = input("Please choose a switch:\n"
		 +" (1) - switch 1 (10.0.0.1)\n"
		 +" (2) - switch 2 (10.0.0.2)\n"
		 +" (3) - switch 3 (10.0.0.3)\n> ")
	switchID = int("0"+re.sub("\D", "", switchID))
switchID += 5 		# SW1 = ID 6; SW2 = ID 7; etc.

print("Simulation is live! Please ensure that the router\n"
	 +"and controller programs are running.")

while True:									# Run forever.
	command = input('> ')					# Prompt user for command
	if reADD.search(command) or reShortADD.search(command):				## ADD
		port = int(command.split(" ")[1])
		# ADD 0 for table request.
		addr = "0.0.0.0" if port == 0 else command.split(" ")[2]
		packet = CreateUpdatePacket("ADD", port, addr)
		ControllerHandler(packet)

	elif reDELETE.search(command) or reShortDELETE.search(command): 	## DELETE
		port = int(command.split(" ")[1])
		addr = "0.0.0.0"
		packet = CreateUpdatePacket("DELETE", port, addr)
		ControllerHandler(packet)

	elif reFORWARD.search(command) or reShortFORWARD.search(command):	## FORWARD
		try:
			forwardAddr = re.search("("+IPv4+")", command).group(1)
			match = False
			for entry in flowTable:		# Search flow table for match.
				if entry.address == forwardAddr:
					match = True
					print("Forwarding packet out port "
						+ str(entry.port) + ".")
			if match == False: print("No rule to match for packet.")
		except:
			print("Error: No flow table.")
		
	elif command == 'exit':												## EXIT
		break;

	else:																## BAD COMMAND
		CommHelp()

