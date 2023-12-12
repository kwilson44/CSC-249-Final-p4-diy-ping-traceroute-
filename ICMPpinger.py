# Attribution: this assignment is based on ICMP Pinger Lab from Computer Networking: a Top-Down Approach by Jim Kurose and Keith Ross. 
# It was modified for use in CSC249: Networks at Smith College by R. Jordan Crouser in Fall 2022, and by Brant Cheikes for Fall 2023.
#I received help from https://www.baeldung.com/cs/raw-sockets, https://www.programcreek.com/python/?CodeExample=receive+one+ping,
# https://www.rfc-editor.org/rfc/rfc792, https://stackoverflow.com/questions/15921816/how-to-get-informations-about-icmp-in-received-packages, and http://sock-raw.org/papers/sock_raw

from socket import * 
import os
import sys 
import struct 
import time 
import select 
import binascii


ICMP_ECHO_REQUEST = 8

# -------------------------------------
# This method takes care of calculating
#   a checksum to make sure nothing was
#   corrupted in transit.
#  
# You do not need to modify this method
# -------------------------------------
def checksum(string): 
    csum = 0
    countTo = (len(string) // 2) * 2 
    count = 0

    while count < countTo: 
        thisVal = ord(string[count+1]) * 256 + ord(string[count]) 
        csum = csum + thisVal
        csum = csum & 0xffffffff 
        count = count + 2

    if countTo < len(string):
        csum = csum + ord(string[len(string) - 1]) 
        csum = csum & 0xffffffff

    csum = (csum >> 16) + (csum & 0xffff) 
    csum = csum + (csum >> 16)

    answer = ~csum

    answer = answer & 0xffff
 
    answer = answer >> 8 | (answer << 8 & 0xff00) 
    return answer


def receiveOnePing(mySocket, ID, timeout, destAddr): 
    
    timeLeft = timeout
    
    while True:
        startedSelect = time.time()

        whatReady = select.select([mySocket], [], [], timeLeft) 
        howLongInSelect = (time.time() - startedSelect)
        if whatReady[0] == []: # Timeout 
            return "Request timed out."

        timeReceived = time.time()
        recPacket, addr = mySocket.recvfrom(1024)

        #---------------#
        # Fill in start #
        #---------------#

            # TODO: Fetch the ICMP header from the IP packet
            # Soluton can be implemented in 6 lines of Python code.

        #Extract the ICMP header from the received packet
        icmpHeader = recPacket[20:28]# set icmp header to bits after bit 160

        #Unpack the ICMP header data (type, code, checksum, packetID, sequence)
        type, code, checksum, packetID, sequence = struct.unpack("bbHHh", icmpHeader) #unpacket data 

        #Check if the packetID matches the expected ID
        if packetID == ID:

            #Determine the size of the double (d) data type
            bytesInDouble = struct.calcsize("d")
            #Extract the sent time from the received packet
            timeSent = struct.unpack("d", recPacket[28:28 + bytesInDouble])[0] #determine sent time
            #Calculate the round-trip time (time between when sent and when received)
            return timeReceived - timeSent #time between when sent and when recevied

        #-------------#
        # Fill in end #
        #-------------#

        timeLeft = timeLeft - howLongInSelect 
        
        if timeLeft <= 0:
            return "Request timed out."

def sendOnePing(mySocket, destAddr, ID):
    # Header is type (8), code (8), checksum (16), id (16), sequence (16)
    myChecksum = 0

    # Make a dummy header with a 0 checksum
 
    # struct -- Interpret strings as packed binary data
    header = struct.pack("bbHHh", ICMP_ECHO_REQUEST, 0, myChecksum, ID, 1) 
    data = struct.pack("d", time.time())

    # Calculate the checksum on the data and the dummy header. 
    myChecksum = checksum(''.join(map(chr, header+data)))

    # Get the right checksum, and put in the header 
    if sys.platform == 'darwin':
        # Convert 16-bit integers from host to network byte order 
        myChecksum = htons(myChecksum) & 0xffff
    else:
        myChecksum = htons(myChecksum)

    header = struct.pack("bbHHh", ICMP_ECHO_REQUEST, 0, myChecksum, ID, 1) 
    packet = header + data

    mySocket.sendto(packet, (destAddr, 1)) # AF_INET address must be tuple, not str 
    # Both LISTS and TUPLES consist of a number of objects
    # which can be referenced by their position number within the object.

def doOnePing(destAddr, timeout): 
    icmp = getprotobyname("icmp")

    # SOCK_RAW is a powerful socket type. For more details:	http://sock-raw.org/papers/sock_raw
    mySocket = socket(AF_INET, SOCK_RAW, icmp)

    myID = os.getpid() & 0xFFFF # Return the current process i 
    sendOnePing(mySocket, destAddr, myID)
    delay = receiveOnePing(mySocket, myID, timeout, destAddr)
 
    mySocket.close() 
    return delay

#Modified Ping Function for compute and display the RTT for each ping request that yields an associated pong.
def ping(host, timeout=1, repeat=3):

    # timeout=1 means: If one second goes by without a reply from the server,
    # the client assumes that either the client's ping or the server's pong is lost 
    dest = gethostbyname(host)
    print(f"Pinging {host} [{dest}] {repeat} times using Python:")

    # Send ping requests to a server separated by approximately one second 
    # Do this only a fixed number of times as determined by 'repeat' argument
    numPings = 1
    while (numPings <= repeat) :
        delay = doOnePing(dest, timeout) 

        if isinstance(delay, str):
            print(f"Ping {numPings} Request timed out.")
            print(f"Ping {numPings} RTT {delay} sec")
        else:
         print(f"Ping {numPings} Response received in {delay:.3f} seconds")
        
        time.sleep(1) # one second 
        numPings += 1
    return delay

#Original Ping Function
'''def ping(host, timeout=1, repeat=3):

    # timeout=1 means: If one second goes by without a reply from the server,
    # the client assumes that either the client's ping or the server's pong is lost 
    dest = gethostbyname(host)
    print(f"Pinging {host} [{dest}] {repeat} times using Python:")

    # Send ping requests to a server separated by approximately one second 
    # Do this only a fixed number of times as determined by 'repeat' argument
    numPings = 1
    while (numPings <= repeat) :
        delay = doOnePing(dest, timeout) 
        print(f"Ping {numPings} RTT {delay} sec")
        time.sleep(1) # one second 
        numPings += 1
    return delay '''

# Runs program
if __name__ == "__main__":
    # Check if the correct number of command-line arguments is provided
    if len(sys.argv) != 2:
        print("Usage: python ICMPpinger.py <target>")
        sys.exit(1)

    # get target address from command line
    target = sys.argv[1]
    ping(target)
