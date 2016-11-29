To install the application, ensure that python 3.15 is installed on the machine


dnf install python3


Afterwards, move to the emu folder in the terminal. 


To run as host or receiver:
python3 -m emu.host <config.json> <sender|receiver> <list of files>


To run as sender:
python3 -m emu.host hostconfig.json sender <list of files>


To run as receiver:
python3 -m emu.host hostconfig.json receiver <list of files>


To run the emulator:
python3 -m emu.emulator hostconfig.json <BER| Delay | Both | None>


To run the emulator with Delay:
python3 -m emu.emulator hostconfig.json Delay


To run the emulator with bit error rate:
python3 -m emu.emulator hostconfig.json BER


To run the emulator with both restrictions (delay and Bit Error Rate):
python3 -m emu.emulator hostconfig.json Both


To run the emulator with no restrictions:
python3 -m emu.emulator hostconfig.json None


Settings are configured in hostconfig.json


    "host0": "192.168.0.8",		#host0 IP (typically the sender)
    "host1": "192.168.0.10",		#host1 IP (typically the receiver)
    "emulator": "192.168.0.9",		#emulator ip
    "timeout": 0.3,			#seconds
    "port": 25500,			#port for all three 
    "window_size": 10,			#window size
    "delay": 1.0,			#seconds
    "BER":50				#percentage between 0 and 100
