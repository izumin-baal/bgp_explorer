import sys
import socket
import yaml
import threading
import time
import random
import bgpformat

# STATE
# Idle: 1 
# Connect: 2
# Active: 3
# OpenSent: 4
# OpenConfirm: 5
# Established: 6
#
# mode
# 1: respnder
# 2: initiator
debug = True

class StateMachine:
    def __init__(self, ip, remoteAs, mode):
        self.ip = ip
        self.remoteAs = remoteAs
        self.state = 1
        self.mode = mode

    def stateMachine(self):
        if self.state == 1:
            self.tcpNego()
        elif self.state == 2:
            self.open()
        elif self.state == 3:
            pass
        elif self.state == 4:
            self.opensent()
        elif self.state == 5:
            self.openconfirm()
        elif self.state == 6:
            self.established()
        else:
            pass
        

    def tcpNego(self):
        if self.mode == 1:
            self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.s.bind(("", 179))
            self.s.listen()
            self.conn, self.addr = self.s.accept()
            print("Connected by", self.addr)
            self.state = 4
        else:
            self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.s.connect((self.ip, 179))
            print("Connect to " + self.ip)
            self.state = 2

    def opensent(self):
        while self.state == 4:
            data = self.s.recv(4096)
            BgpMsgArray = []
            for i,bytes in enumerate(data, 1):
                BgpMsgArray.append(bytes)
                if i == 19:
                    type = self.checkMessage(bytes)
            if type == 1:
                check = self.peerjadge(BgpMsgArray)
                if check: # True:Error False:OK
                    self.notification()
                    self.s.close()
                    time.sleep(10)
                    self.state = 1
                else:
                    self.keepalive()
                    self.state = 5

    def openconfirm(self):
        data = self.s.recv(4096)
        BgpMsgArray = []
        for i,bytes in enumerate(data, 1):
            BgpMsgArray.append(bytes)
            if i == 19:
                type = self.checkMessage(bytes)
        if type == 4:
            self.state = 6
            t = threading.Thread(target=self.intervalKeepalive)
            t.start()
            print("*** Established!!! ***")
            print("*** Neighbor Up ***")
        elif type == 3:
            self.s.close()
            time.sleep(10)
            self.state = 1
        else:
            print("Unknown Error")

    def established(self):
        self.s.settimeout(self.holdtime)
        try:
            self.s.recv(4096)
        except:
            print("TimeOut")
            print("*** Neighbor Down ***")
            self.state = 1

    def intervalKeepalive(self):
        while self.state == 6:
            self.keepalive()
            time.sleep(int(self.holdtime/4))

    def open(self):
        if self.mode == 1:
            bgpformat.b_openMsg(True)
            self.state = 4 # Opensent
        else:
            msg = bgpformat.b_openMsg(False)
            self.s.sendall(msg)
            print(">> Send Open Message")
            self.state = 4 # Opensent

    def keepalive(self):
        msg = bgpformat.b_keepaliveMsg()
        self.s.sendall(msg)
        print(">> Send KEEPALIVE Message")

    def notification(self):
        msg = bgpformat.b_notificateMsg()
        self.s.sendall(msg)
        print(">> Send NOTIFICATION Message")

    def checkMessage(self, type):
        if type == 1:
            print("<< receive OPEN Message")
            return 1
        elif type == 2:
            print("<< receive UPDATE Message")
            return 2
        elif type == 3:
            print("<< receive NOTIFICATION Message")
            return 3
        elif type == 4:
            print("<< receive KEEPALIVE Message")
            return 4
        else:
            print("Unknown")
            return 5
    
    def peerjadge(self, msg):
        with open('config.yaml', 'r') as yml:
            config = yaml.safe_load(yml)
        NEIGHBORCONF = config['bgp']['neighbor'][0]
        PARAMETERCONF = config['bgp']['parameter'][0]
        errorMsg = False
        # IP
        if self.mode == 1:
            if NEIGHBORCONF['IP'] == self.addr:
                pass
            else:
                if debug:
                    print("neighbor IP is incorrect")
                errorMsg = True
        # ASN
        if NEIGHBORCONF['Remote-as'] == (msg[20] * 8 + msg[21]):
            pass
        else:
            print(msg[20] * 8 + msg[21])
            if debug:
                print("neighbor ASN is incorrect")
            errorMsg = True
        # Version
        if PARAMETERCONF['Version'] == msg[19]:
            pass
        else:
            if debug:
                print("neighbor Version incorrect")
            errorMsg = True
        # Router-ID
        if PARAMETERCONF['RouterID'] == (str(msg[24]) + '.' + str(msg[25]) + '.' + str(msg[26]) + '.' + str(msg[27])):
            if debug:
                print("neighbor RouterID is incorrect")
            errorMsg = True
        # Holdtime決定
        if PARAMETERCONF['HoldTime'] < (msg[22] * 8 + msg[23]):
            if debug:
                print("Use my HoldTime")
            self.holdtime = PARAMETERCONF['HoldTime']
        else:
            if debug:
                print("Use Neighbor Holdtime")
            self.holdtime = msg[22] * 8 + msg[23]
            self.holdtimecnt = self.holdtime

        if errorMsg:
            self.state = 1
            return True
        else:
            return False

def server():
    print("### Responder mode ###")
    with open('config.yaml', 'r') as yml:
        config = yaml.safe_load(yml)
    NEIGHBORCONF = config['bgp']['neighbor'][0]
    ip = NEIGHBORCONF["IP"]
    remoteAs = NEIGHBORCONF["Remote-as"]
    state = StateMachine(ip, remoteAs, 1)
    while True:
        state.stateMachine()

def client():
    print("### Initiator mode ###")
    with open('config.yaml', 'r') as yml:
        config = yaml.safe_load(yml)
    NEIGHBORCONF = config['bgp']['neighbor'][0]
    ip = NEIGHBORCONF["IP"]
    remoteAs = NEIGHBORCONF["Remote-as"]
    state = StateMachine(ip, remoteAs, 2)
    while True:
        state.stateMachine()
