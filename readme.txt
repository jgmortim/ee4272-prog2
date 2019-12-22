##################################### OVERVIEW ####################################

The programs can be launched in any order; however, all must be running before the
switch can send an update packet. Between update packets from the switch, the 
router and controller can be closed and relaunched. The only issue is that the
controller will default back to the initial network state (as defined in 
adjMatrix.txt). Closing and relaunching the router will have no effect.

The programs are all verbose (the controller is exceptionally so), there should be
no issues in identifying what is happening during the simulation.

In the documentation (comments) for the python files, I use the terms host, node,
and vertex interchangeably.

I spent a lot of time making this simulation as robust as possible and I am quite
proud of the result.

For readability, tab width = 4

############################# Implementation Specifics ############################

Switch:
	My implementation supports multiple concurrent instances of the switch program.
	I have tested it with all 3 switches in the provided network being active at
	the same time. This does require frequent uses of the "ADD 0" command because 
    the switch doesn't send flow table packets to all switches at once (only to the
	one that sent the update packet). It's not true concurrency as only one switch
	can communicate with the controller at a time. By since the switches are 
	controlled using human input, it's close enough. 

	When you launch the switch you will be asked to chose which switch you want to
	simulate (1, 2, or 3). There is nothing to prevent you from creating two or 
	more instances of the same switch. In fact, this will have no adverse effects
	on the simulation.

	Every Update Packet has the same format and as a result contains an IPv4 
	address	(0.0.0.0 in the case of DELETE or ADD 0), this is simply ignored by the
	controller if it is not a true add request. This was simpler than creating 
	multiple packet formats.

Controller:
	Loads the initial network topology when launched. The switch program(s) can be 
	launched and closed multiple times and the controller will remember the state 
	of the network. 

	Every Add and Delete packet will either add or delete TWO ports. One on the 
	source host and one on the destination. This is necessary to allow for multiple
	switch programs. When adding ports, the port on the destination host will be
	lowest port number (>0) that is not in use. This implementation has no limits 
	on the number of ports a switch can have. Technically it is limited by the 
	number of hosts in the network as redundant connections are not permitted. And
	in turn, the number of hosts is limited by the number of valid IPv4 address. 
	Although, it is safe to assume that other factors will prevent you from adding
	over 4 billion hosts to the network.

	My controller does not store and maintain an adjacency matrix. It maintains a
	list of host ID and addresses for every host to ever be connected to the 
	network. And it also maintains a list of connections, which I define as a 
	triple of source ID, source port, and destination ID. Each connection is 
	unidirectional; however, a parallel connection exist from the destination back
	to the source, which makes each connection effectively bidirectional. This 
	design was chosen as it makes the creation of an adjacency matrix simple, 
	while removing the need to maintain a multidimensional array. That is to say,
	adjacency matrices are created on demand.

	Listens for switch on port 2345.

Router:
	Does not verify if SourceVertexID is valid as the user of the switch cannot 
	chose an invalid ID.

	Listens for controller on port 1234.

################################# Assumptions Made ################################

In the specifications it states:

"The switch program will be interactive, such that you can put in a destination IP
 address and ingress port and the program will print out which port that “packet” 
 will be forwarded out."

I assumed that the mentioning of an ingress port was a mistake as it conflicts with
the rest of the specifications.



