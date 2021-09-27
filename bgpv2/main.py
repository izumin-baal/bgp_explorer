import sys
import socket
import yaml
import threading
import time
import bgpformat
import rw
import os

# exit
exitflag = False
# STATE
BGP_STATE_IDLE = 1
BGP_STATE_CONNECT = 2
BGP_STATE_ACTIVE = 3
BGP_STATE_OPENSENT = 4
BGP_STATE_OPENCONFIRM = 5
BGP_STATE_ESTABLISHED = 6
# MODE
BGP_MODE_RESPONDER = 1
BGP_MODE_INITIATOR = 2
# MESSAGE TYPE
BGP_MSG_OPEN = 1
BGP_MSG_UPDATE = 2
BGP_MSG_NOTIFICATION = 3
BGP_MSG_KEEPALIVE = 4
BGP_MSG_ROUTEREFRESH = 5
# PASSATTRIBUTE
BGP_PASSATTR_ORIGIN = 1
BGP_PASSATTR_AS_PATH = 2
BGP_PASSATTR_NEXT_HOP = 3
BGP_PASSATTR_MED = 4
# debug mode
debug = True
# peer state
peer_state = {}
# 
MSGTYPE_CHECK_BIN = 18
class peerState(threading.Thread):
    def __init__(self, neighborip, remoteas, nexthop, mode):
        global peer_state
        threading.Thread.__init__(self)
        self.neighborip = neighborip
        self.remoteas = remoteas
        self.nexthop = nexthop
        self.mode = mode
        peer_state[self.neighborip] = BGP_STATE_IDLE
        #self.mode = mode
        if debug:
            self.printState()

    def run(self):
        global peer_state
        if self.mode == BGP_MODE_INITIATOR:
            while True:
                if exitflag:
                    print("# " + self.neighborip + " thread down #")
                    sys.exit()
                s = None
                if  peer_state[self.neighborip] == BGP_STATE_IDLE:
                    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    #s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                    try:
                        peer_state[self.neighborip] == BGP_STATE_CONNECT
                        if debug:
                            self.printState()
                        print('Connect to ' + self.neighborip)
                        s.connect((self.neighborip, 179))
                        self.sendOpen(s)
                        peer_state[self.neighborip] == BGP_STATE_OPENSENT
                        if debug:
                            self.printState()
                    except:
                        peer_state[self.neighborip] = BGP_STATE_ACTIVE
                        if debug:
                            self.printState()
                        time.sleep(10)
                        peer_state[self.neighborip] = BGP_STATE_IDLE
                        if debug:
                            self.printState()
                if peer_state[self.neighborip] != BGP_STATE_IDLE and peer_state[self.neighborip] != BGP_STATE_ACTIVE:    
                    data = s.recv(4096)
                    self.operateByState(s, data)
        elif self.mode == BGP_MODE_RESPONDER:
            pass

    # State
    def printState(self):
        i = peer_state[self.neighborip]
        if i == 1:
            statestr = "IDLE"
        elif i == 2:
            statestr = "CONNECT"
        elif i == 3:
            statestr = "ACTIVE"
        elif i == 4:
            statestr = "OPENSENT"
        elif i == 5:
            statestr = "OPENCONFIRM"
        elif i == 6:
            statestr = "ESTABLISHED"
        print('Neighbor: ' + self.neighborip + ' is ' + statestr)

    def operateByState(self, s, data):
        global peer_state
        i = peer_state[self.neighborip]
        decData = self.convertBinToDec(data)
        if i == BGP_STATE_IDLE:
            pass
        elif i == BGP_STATE_CONNECT:
            pass
        elif i == BGP_STATE_ACTIVE:
            pass
        elif i == BGP_STATE_OPENSENT:
            self.openSent(decData)
        elif i == BGP_STATE_OPENCONFIRM:
            self.openconfirm()
        elif i == BGP_STATE_ESTABLISHED:
            self.established()
        else:
            pass

    # Other
    def convertBinToDec(self, data):
        data_digit_array = []
        for i, octet in enumerate(data):
            data_digit_array.append(octet)
            if i == MSGTYPE_CHECK_BIN:
                if octet == BGP_MSG_OPEN:
                    print('<< Recv OPEN')
                elif octet == BGP_MSG_UPDATE:
                    print('<< Recv UPDATE')
                elif octet == BGP_MSG_NOTIFICATION:
                    print('<< Recv NOTIFICATION')
                elif octet == BGP_MSG_KEEPALIVE:
                    print('<< Recv KEEPALIVE')
                elif octet == BGP_MSG_ROUTEREFRESH:
                    print('<< Recv ROUTEREFRESH')
                else:
                    print('<< Recv UNKNOWN')
        return data_digit_array

    # OPEN
    def openSent(self, decData):
        global peer_state
        if self.mode == BGP_MODE_INITIATOR:
            if decData[MSGTYPE_CHECK_BIN] == BGP_MSG_OPEN:
                if self.peerJadge(decData):
                    # OK
                    pass
                else:
                    # False
                    pass
            else:
                peer_state[self.neighborip] = BGP_STATE_IDLE
        elif self.mode == BGP_MODE_RESPONDER:
            pass

    def sendOpen(self, s):
        if self.mode == BGP_MODE_INITIATOR:
            msg = bgpformat.b_openMsg()
            s.sendall(msg)
        elif self.mode == BGP_MODE_RESPONDER:
            pass
        print(">> Send OPEN")

    def peerJadge(self, msg):
        with open('config.yaml', 'r') as yml:
            config = yaml.safe_load(yml)
        NEIGHBORCONF = config['bgp']['neighbor'][0]
        PARAMETERCONF = config['bgp']['parameter'][0]
        errorMsg = False
        # IP
        if self.mode == BGP_MODE_RESPONDER:
            if NEIGHBORCONF['IP'] == self.addr[0]:
                pass
            else:
                if debug:
                    print("neighbor IP is incorrect")
                errorMsg = True
        # ASN
        if NEIGHBORCONF['Remote-as'] == (msg[20] * 256 + msg[21]):
            pass
        else:
            print(msg[20] * 256 + msg[21])
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
        if PARAMETERCONF['HoldTime'] < (msg[22] * 256 + msg[23]):
            if debug:
                print("Use my HoldTime")
            self.holdtime = PARAMETERCONF['HoldTime']
        else:
            if debug:
                print("Use Neighbor Holdtime")
            self.holdtime = msg[22] * 256 + msg[23]
            self.holdtimecnt = self.holdtime
        if errorMsg:
            self.state = BGP_STATE_IDLE
            return True
        else:
            return False

def server():
    print("### Responder mode ###")
    with open('config.yaml', 'r') as yml:
        config = yaml.safe_load(yml)
    NEIGHBORCONF = config['bgp']['neighbor']
    ip = NEIGHBORCONF["IP"]
    remoteAs = NEIGHBORCONF["Remote-as"]
    state = StateMachine(ip, remoteAs, BGP_MODE_RESPONDER)
    while True:
        state.stateMachine()

def client():
    print("### Initiator mode ###")
    with open('config.yaml', 'r') as yml:
        config = yaml.safe_load(yml)
    NEIGHBORCONF = config['bgp']['neighbor']
    th = []
    for i, neighbor in enumerate(NEIGHBORCONF):
        neighborip = neighbor['NeighborIP']
        remoteas = neighbor['Remote-as']
        nexthop = neighbor['NextHop']
        th.append(peerState(neighborip, remoteas, nexthop, BGP_MODE_INITIATOR))
        th[i].start()
    try:
        while True:
            pass
    except KeyboardInterrupt:
        global exitflag
        exitflag = True
        print('# exitflag is True. wait...#')
        for i in range(len(th)):
            th[i].join()
        rw.del_all()
        print("exit.")
        sys.exit()

if __name__ == "__main__":
    #if os.geteuid() == 0 and os.getuid() == 0 :
    #    pass
    #else:
    #    print("Root Only!!!")
    #    sys.exit()
    arg = sys.argv
    if 2 <= len(arg):
        cmd = arg[1]
        if cmd == "sv":
            print("not support")
        elif cmd == "cl":
            client()
        elif cmd == "init":
            rw.del_all() # csv,routingtable初期化
        else:
            print("Unexpected argument(sv or cl)")
    else:
        print("Requires an argument")
