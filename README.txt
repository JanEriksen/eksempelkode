----------------------------------------------------------------

		  Welcome to Simpleperf

----------------------------------------------------------------

		  What is simpleperf?

Simpleperf is a throughput measurement tool used to test the
bandwidth of a network. It is a program written in Python
and uses user-friendly command line arguments through argparse.

----------------------------------------------------------------

		   Prerequisites

To run simpleperf you need:
- simpleperf.py
- A test environment (ex. Mininet)
- A network topology for testing

----------------------------------------------------------------

		 How to use simpleperf?

To use simpleperf you simply run it in any command line kernel
through python either as a server, or as a client. NB! start the 
server up first, so that the client has something to connect to!

Simpleperf server:

python simpleperf.py -s

simpleperf client:

python simpleperf.py -c

for help to see more arguments supported by simpleperf, simply
run simpleperf with the -h flag:

python simpleperf.py -h

----------------------------------------------------------------

Please enjoy simpleperf! If you have any questions, feel free to
ask them by sending me a message on email.internetmail@Amail.com

