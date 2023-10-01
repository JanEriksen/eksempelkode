import argparse
from socket import *
import threading as thread
import sys # In order to terminate the program
import re
import time
import math


## Setting up positional arguments
parser = argparse.ArgumentParser(description="positional arguments", epilog="end of help")

# Function to validate the user input for -p flag
# Value: stores user input casted to an int
# if: checks if the user input is within the allowed range
# returns the value to set the port to that value
def check_port(val):
    try: 
        value = int(val)
    except ValueError:
        raise argparse.ArgumentTypeError("Port needs to be an int, not a string")
    if (value < 1024 or value > 65535):
        raise argparse.ArgumentTypeError("Need a port between 1024 and 65535")
    return value

# Function to validate the user input for -P flag
# Value: stores user input casted to an int
# if: checks if the user input is within the allowed range
# returns the value to use the value as parallel connections
def check_para(val):
    try:
        value = int(val)
    except ValueError:
        raise argparse.ArgumentTypeError("Need to be an int, not a string")
    if (value < 1 or value > 5):
        raise argparse.ArgumentTypeError("Min value is 1 and Max value is 5")
    return value


# Function to validate the user input for -b and -I flag
# Value: stores user input
# regular expression to validate for valid IP addresses as dotted decimal notations
# if the user input matches the regular expression it returns is to set it as IP or connect to the IP
def check_IP(val):
    ## Regex checking for dotted desimal notation
    regex = '^(?:(?:\d|[1-9]\d|1\d\d|2[0-4]\d|25[0-5])\.){3}(?:\d|[1-9]\d|1\d\d|2[0-4]\d|25[0-5])$'  # https://regex101.com/r/sR7yY8/1
    value = val
    result = re.match(regex, value)
    if result:
        return value
    else:
        raise argparse.ArgumentTypeError("IP needs to be a dotted desimal notation, and a valid IP address. EX. 10.0.0.2")
        
# Function to validate the user input for -t flag
# Value: user input casted to an int
# if it is valid, (positiv int) return it to use as time
def check_time(val):
    value = int(val)
    if value >= 1:
        return value
    else:
        raise argparse.ArgumentTypeError("Time needs to be a positive integer")


## Server spesific arguments
parser.add_argument("-s", "--server", action="store_true", help="Runs simpleperf in server mode")
parser.add_argument("-b", "--bind", type=check_IP, help="IP for hosts to connect to", default="127.0.0.1")

## Common arguments
parser.add_argument("-p", "--port", type=check_port, default=8088, help="Port for hosts to connect to. Default: 8088")
parser.add_argument("-f", "--format", choices=("B", "KB", "MB"), default="MB", help="Choose the format of the summary of results. Default: MB")

## Client spesific arguments
parser.add_argument("-c", "--client", action="store_true", help="Run simpleperf in client mode")
parser.add_argument("-I", "--serverip", type=check_IP, help="Select the IP of the server", default="127.0.0.1")
parser.add_argument("-t", "--time", type=check_time, default=25, help="Total duration in seconds for which data should be generated. Must be a positive integer above 0. Default: 25")
parser.add_argument("-i", "--interval", default=1000, type=int, help="Print statistics per z seconds.")
parser.add_argument("-P", "--parallel", type=check_para, help="Creates parallel connections to the server. Min 1 - 5 Max", default=1)
parser.add_argument("-n", "--num", type=int, help="Transfer a specific number of bytes, format is dependent on '-f' flag. EX. -n 50 = 50MB as a default")

args = parser.parse_args()


# Handles if user doesn't run the program as server or a client
if args.server == False and args.client == False:
    print("You need to run the program as either a server or a client")
    sys.exit()

# Handles if user trys to run the program as both a server and a client
if args.server == True and args.client == True:
    print("You can only choose one mode at a time")
    sys.exit()

# Server-side code
if args.server:        
    ## Creating a server socket
    serverSocket = socket(AF_INET, SOCK_STREAM)

    # Binds the socket and listens for up to 5 connections at a time
    serverSocket.bind((args.bind, args.port))
    serverSocket.listen(5)

    # Client handeler to handle multiple connections
    def handleClient(connectionSocket, addr):
        total_bytes = 0                                 # create total_bytes as an int (0)
        start_time = time.time()                        # Set a start_time before the transfer to be able to calculate the rate of transfer
        while True:                                     # While loop to listen for data from the client for as long as it is being sent, and listens for a 'BYE' and closes the connection when received
            message = connectionSocket.recv(1024)       # receives data
            total_bytes += len(message)                 # adds to total_bytes for each loop
                
            if b"BYE" in message:
                break

        
        elapsed_time = time.time() - start_time         # Calculate the elapsed time from the start of the connection to the end of the connection
        bandwidth = total_bytes / elapsed_time          # Calculate the bandwidth of the connection by deviding the total bytes by the elapsed time

        # if sentence to format the output for bytes, kilobytes and megabytes by deviding the total bytes by 1000 for kilo and 1000000 for mega, since default in is bytes
        if args.format == "B":
            total_bytes_format = f"{total_bytes:.2f} Bytes"
        elif args.format == "KB":
            total_bytes_format = f"{total_bytes/1000:.2f} KB"
        else:
            total_bytes_format = f"{total_bytes/1000000:.2f} MB"

        # Prints the result
        print(f"ID                Interval        Received        Rate")
        print (f"{addr[0]}:{addr[1]}    0.0 - {elapsed_time:.0f}        {total_bytes_format}      {bandwidth/1000000:.2f} Mbps") 
        
        # Closes the connection gracefully
        connectionSocket.send(b"ACK:BYE")
        connectionSocket.close()

    # While loop to accept connections 
    while True:
        
        try:
            # Accept the connection(s) and print info to show where the connection(s) come from
            print("---------------------------------------------")
            print("A simpleperf server is listening on port", args.port)
            print("---------------------------------------------")
            connectionSocket, addr = serverSocket.accept()
            print(f"A simpleperf client with {addr[0]}:{addr[1]} is connected with {args.bind}:{args.port}")

            # Use the thread function to start a new thread for each connection
            thread._start_new_thread(handleClient, (connectionSocket,addr))

        # Handles exceptions. This prints an error and closes the connection
        except IOError:
            print("IOError")
            connectionSocket.close()
    

# Client-side code
if args.client:

    # Client handeler to handle multiple connections
    def connection(connectionSocket_client, addr_client):
        # Define multiple variables to handle intervals, bytes sent tracker and time
        interval1 = 0
        interval2 = 0
        total_bytes_sent = 0
        start_time = time.time()
        interval_start = start_time

        # if sentence to calculate and display correct number of bytes sent with the -n flag.
        if args.num is not None:
            if args.format == 'B':
                args.num = args.num 
            elif args.format == 'KB':
                args.num = args.num * 1000
            elif args.format == 'MB':
                args.num = args.num * 1000000

        # Print header of result
        print(f"ID                Interval        Received        Rate\n")
        
        # While loop to sent bytes
        while True:
            # if sentence to break the while loop if the duration of transfer is reached
            if time.time() - start_time > args.time:
                break
 
            # if sentence to calculate intervals every <args.interval> second(s)
            if time.time() - interval_start > args.interval:
                
                interval_start = time.time()
                interval_time = time.time() - start_time
                
                # if sentence to format the output for bytes, kilobytes and megabytes by deviding the total bytes by 1000 for kilo and 1000000 for mega, since default in is bytes
                if args.format == "B":
                    total_bytes_sent_format_interval = f"{total_bytes_sent:.2f} Bytes"
                elif args.format == "KB":
                    total_bytes_sent_format_interval = f"{total_bytes_sent/1000:.2f} KB"
                else:
                    total_bytes_sent_format_interval = f"{total_bytes_sent/1000000:.2f} MB"

                # sets interval_time to 1 if it is less than 1 so that you don't get devision by zero error
                if interval_time < 1:
                    interval_time = 1
                interval_bandwidth = total_bytes_sent / interval_time   # Calculate the bandwidth for each interval
                interval2 = interval1 + args.interval
                
                # Prints the result for every interval, additively
                print (f"{args.serverip}:{args.port}    {interval1:.0f} - {interval2:.0f}        {total_bytes_sent_format_interval}      {interval_bandwidth/1000000:.2f} Mbps")
                interval1 = interval2
            
            # if sentence to sent bytes until bytes sent = args.bytes set by the user using the -n flag
            if args.num is not None:
                args.time = 0
                while total_bytes_sent < args.num:
                    data = "0" * 1000
                    try:
                        client_socket.send(data.encode())
                    except:
                        continue
                    total_bytes_sent += len(data)    
            
            # Send bytes of data in chunkes of 1000 bytes
            data = "0" * 1000
            try:
                client_socket.send(data.encode())
            except:
                continue
            total_bytes_sent += len(data)    


        elapsed_time = time.time() - start_time                
        # Send finish/bye message and wait for acknowledgement
        try:
            client_socket.send(b'BYE')
            acknowledgement = client_socket.recv(1024)
            if acknowledgement:
                connectionSocket_client.close()
        except:
            pass


        # if sentence to format the output for bytes, kilobytes and megabytes by deviding the total bytes by 1000 for kilo and 1000000 for mega, since default sent is in bytes
        if args.format == "B":
            total_bytes_sent_format = f"{total_bytes_sent:.2f} Bytes"
        elif args.format == "KB":
            total_bytes_sent_format = f"{total_bytes_sent/1000:.2f} KB"
        else:
            total_bytes_sent_format = f"{total_bytes_sent/1000000:.2f} MB"

        # Calculate bandwidth based on total number of bytes sent and elapsed time
        
        bandwidth = total_bytes_sent / elapsed_time


        # Print results
        if args.interval != 1000:
            print("\n---------------------------------------------------------\n")
        if args.num is not None:
            print (f"{args.serverip}:{args.port}    0.0 - {elapsed_time:.2f}        {total_bytes_sent_format}      {bandwidth/1000000:.2f} Mbps") 
        else:
            print (f"{args.serverip}:{args.port}    0.0 - {elapsed_time:.0f}        {total_bytes_sent_format}      {bandwidth/1000000:.2f} Mbps") 
        

    # for loop to make a socket and connect for all instences of args.parallel
    try:            
        for i in range(0, args.parallel):
            client_socket = socket(AF_INET, SOCK_STREAM) 
            client_socket.connect((args.serverip, args.port))               # Connects to the server by args.serverip and args.port
            print("---------------------------------------------")          # prints info on connecting and on finished connection
            print(f"A simpleperf client connecting to {args.bind}, port {args.port}")
            print("---------------------------------------------")
            print(f"Client connected with {args.bind} port {args.port}\n")
            new_thread = thread.Thread(target=connection, args=(client_socket,(args.serverip, args.port)))  # Thread to make multiple connections to the server using the -P flag
            new_thread.start()

    # Handles connection error
    except:
        print("ConnectionError")
        sys.exit()
