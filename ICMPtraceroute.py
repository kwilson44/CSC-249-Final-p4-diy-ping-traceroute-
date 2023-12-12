# Attribution: this assignment is based on ICMP Traceroute Lab from Computer Networking: a Top-Down Approach by Jim Kurose and Keith Ross. 
# It was modified for use in CSC249: Networks at Smith College by R. Jordan Crouser in Fall 2022
# Sources that helped
from socket import *
from ICMPpinger import checksum
import os
import sys
import struct
import time
import select
import binascii

ICMP_ECHO_REQUEST = 8
MAX_HOPS = 30
TIMEOUT = 2.0
TRIES = 2

# The packet that we shall send to each router along the path is the ICMP echo
# request packet, which is exactly what we had used in the ICMP ping exercise.
# We shall use the same packet that we built in the Ping exercise
def build_packet():
    # In the sendOnePing() method of the ICMP Ping exercise, firstly the header of our
    # packet to be sent was made, secondly the checksum was appended to the header and
    # then finally the complete packet was sent to the destination.

    #---------------#
    # Fill in start #
    #---------------#

# TODO: Make the header in a similar way to the ping exercise.
# Append checksum to the header.
# Solution can be implemented in 10 lines of Python code.

    # Get a unique identifier for the packet (based on the process ID)
    ID = os.getpid() & 0xFFFF

    # Initialize a dummy checksum (will be updated later)
    myChecksum = 0

    # Create the initial header (without the checksum)
    header = struct.pack("bbHHh", ICMP_ECHO_REQUEST, 0, myChecksum, ID, 1)

    # Create the data part of the packet (current timestamp)
    data = struct.pack("d", time.time())

    # Calculate the checksum by combining header and data
    myChecksum = checksum(''.join(map(chr, header + data)))

    # Adjust the checksum based on the platform
    if sys.platform == 'darwin':
        myChecksum = htons(myChecksum) & 0xffff
    else:
        myChecksum = htons(myChecksum)

    # Add the correct checksum to the header
    header = struct.pack("bbHHh", ICMP_ECHO_REQUEST, 0, myChecksum, ID, 1)

    #-------------#
    # Fill in end #
    #-------------#

    # Don’t send the packet yet , just return the final packet in this function.
    packet = header + data
    return packet

def get_route(hostname):
    timeLeft = TIMEOUT
    for ttl in range(1,MAX_HOPS):
        for tries in range(TRIES):
            destAddr = gethostbyname(hostname)

            #---------------#
            # Fill in start #
            #---------------#

            # TODO: Make a raw socket named mySocket
            # Solution can be implemented in 2 lines of Python code.

            # Get the ICMP protocol number
            icmp = getprotobyname("icmp")
            # Create a raw socket with IPv4 (AF_INET), raw socket type (SOCK_RAW), and ICMP protocol
            mySocket = socket(AF_INET, SOCK_RAW, icmp)

            #-------------#
            # Fill in end #
            #-------------#

            mySocket.setsockopt(IPPROTO_IP, IP_TTL, struct.pack('I', ttl))
            mySocket.settimeout(TIMEOUT)

            try:
                d = build_packet()
                mySocket.sendto(d, (hostname, 0))
                t= time.time()
                startedSelect = time.time()
                whatReady = select.select([mySocket], [], [], timeLeft)
                howLongInSelect = (time.time() - startedSelect)

                if whatReady[0] == []: # Timeout
                    print(" * * * Request timed out.")

                recvPacket, addr = mySocket.recvfrom(1024)
                timeReceived = time.time()
                timeLeft = timeLeft - howLongInSelect

                if timeLeft <= 0:
                    print(" * * * Request timed out.")

            except timeout:
                continue

            else:
                #---------------#
                # Fill in start #
                #---------------#

                #TODO: Fetch the icmp type from the IP packet
                # Solution can be implemented in 2 lines of Python code.
                # Gets icmp type from the first byte of the icmp header
                types = recvPacket[20]  # Gets icmp type from the first byte of the icmp header

                #-------------#
                # Fill in end #
                #-------------#
                
                if types == 11:
                    bytes = struct.calcsize("d")
                    timeSent = struct.unpack("d", recvPacket[28:28 +bytes])[0]
                    print(" %d rtt=%.0f ms %s" %(ttl, (timeReceived -t)*1000, addr[0] ))

                elif types == 3:
                    bytes = struct.calcsize("d")
                    timeSent = struct.unpack("d", recvPacket[28:28 + bytes])[0]
                    print(" %d rtt=%.0f ms %s" %(ttl, (timeReceived-t)*1000, addr[0]))

                elif types == 0:
                    bytes = struct.calcsize("d")
                    timeSent = struct.unpack("d", recvPacket[28:28 + bytes])[0]
                    print(" %d rtt=%.0f ms %s" %(ttl, (timeReceived - timeSent)*1000, addr[0]))
                    return

                else:
                    print("error")

                break

            finally:
                mySocket.close()

# Runs program
if __name__ == "__main__":
    target = sys.argv[1]
    get_route(target)
