import sys
import socket
import yaml
import threading
import time
import bgpformat

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

# debug mode
debug = True

class StateMachine:
    def __init__(self, ip, remoteAs, mode):
        self.ip = ip
        self.remoteAs = remoteAs
        self.state = BGP_STATE_IDLE
        self.mode = mode
        self.t = None

    def stateMachine(self):
        if self.state == BGP_STATE_IDLE:
            self.tcpNego()
        elif self.state == BGP_STATE_CONNECT:
            self.open()
        elif self.state == BGP_STATE_ACTIVE:
            pass
        elif self.state == BGP_STATE_OPENSENT:
            self.opensent()
        elif self.state == BGP_STATE_OPENCONFIRM:
            self.openconfirm()
        elif self.state == BGP_STATE_ESTABLISHED:
            self.established()
        else:
            pass

    def tcpNego(self):
        if self.t:
            self.t.join()
        if self.mode == BGP_MODE_RESPONDER:
            self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.s.bind(("", 179))
            self.s.listen()
            self.conn, self.addr = self.s.accept()
            print("Connected by", self.addr)
            self.state = BGP_STATE_OPENSENT
        else:
            self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.s.connect((self.ip, 179))
            print("Connect to " + self.ip)
            self.state = BGP_STATE_CONNECT

    def opensent(self):
        while self.state == BGP_STATE_OPENSENT:
            if self.mode == BGP_MODE_RESPONDER:
                data = self.conn.recv(4096)
            else:
                data = self.s.recv(4096)                
            BgpMsgArray = []
            for i,bytes in enumerate(data, 1):
                BgpMsgArray.append(bytes)
                if i == 19:
                    type = self.checkMessage(bytes)
            if type == BGP_MSG_OPEN:
                check = self.peerjadge(BgpMsgArray)
                if check: # True:Error False:OK
                    self.notification()
                    if self.mode == BGP_MODE_RESPONDER:
                        #self.conn.close()
                        pass
                    else:
                        self.s.close()
                    time.sleep(10)
                    self.state = BGP_STATE_IDLE
                else:
                    if self.mode == BGP_MODE_RESPONDER:
                        self.open()
                        self.state = BGP_STATE_OPENCONFIRM
                    else:
                        self.keepalive()
                        self.state = BGP_STATE_OPENCONFIRM

    def openconfirm(self):
        if self.mode == BGP_MODE_RESPONDER:
            data = self.conn.recv(4096)
        else:
            data = self.s.recv(4096)
        BgpMsgArray = []
        for i,bytes in enumerate(data, 1):
            BgpMsgArray.append(bytes)
            if i == 19:
                type = self.checkMessage(bytes)
        if type == BGP_MSG_KEEPALIVE:
            self.state = BGP_STATE_ESTABLISHED
            self.t = threading.Thread(target=self.intervalKeepalive)
            self.t.start()
            print("*** Established!!! ***")
            print("*** Neighbor Up ***")
        elif type == BGP_MSG_NOTIFICATION:
            if self.mode == BGP_MODE_RESPONDER:
                #self.conn.close()
                pass
            else:
                self.s.close()
            time.sleep(10)
            self.state = BGP_STATE_IDLE
        else:
            print("Unknown Error")

    def established(self):
        if self.mode == BGP_MODE_RESPONDER:
            self.conn.settimeout(self.holdtime)
        else:
            self.s.settimeout(self.holdtime)
        try:
            if self.mode == BGP_MODE_RESPONDER:
                data = self.conn.recv(4096)
            else:
                data = self.s.recv(4096)
            BgpMsgArray = []
            for i,bytes in enumerate(data, 1):
                BgpMsgArray.append(bytes)
                if i == 19:
                    type = self.checkMessage(bytes)
            if type == BGP_MSG_UPDATE or type == BGP_MSG_KEEPALIVE:
                pass
            else:
                print("received Error")
                self.state = BGP_STATE_IDLE
        except socket.timeout:
            print("TimeOut")
            print("*** Neighbor Down ***")
            self.state = BGP_STATE_IDLE
        except:
            sys.exit()

    def intervalKeepalive(self):
        while self.state == BGP_STATE_ESTABLISHED:
            self.keepalive()
            time.sleep(int(self.holdtime/4))

    def open(self):
        if self.mode == BGP_MODE_RESPONDER:
            msg = bgpformat.b_openMsg()
            self.conn.sendall(msg)
            print(">> Send Open Message")
            self.state = BGP_STATE_OPENSENT # Opensent
        else:
            msg = bgpformat.b_openMsg()
            self.s.sendall(msg)
            print(">> Send Open Message")
            self.state = BGP_STATE_OPENSENT # Opensent

    def keepalive(self):
        msg = bgpformat.b_keepaliveMsg()
        if self.mode == BGP_MODE_RESPONDER:
            self.conn.sendall(msg)
        else:
            self.s.sendall(msg)
        print(">> Send KEEPALIVE Message")

    def notification(self):
        msg = bgpformat.b_notificateMsg()
        if self.mode == BGP_MODE_RESPONDER:
            self.conn.sendall(msg)
        else:
            self.s.sendall(msg)
        print(">> Send NOTIFICATION Message")

    def checkMessage(self, type):
        if type == BGP_MSG_OPEN:
            print("<< receive OPEN Message")
            return 1
        elif type == BGP_MSG_UPDATE:
            print("<< receive UPDATE Message")
            return 2
        elif type == BGP_MSG_NOTIFICATION:
            print("<< receive NOTIFICATION Message")
            return 3
        elif type == BGP_MSG_KEEPALIVE:
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
    NEIGHBORCONF = config['bgp']['neighbor'][0]
    ip = NEIGHBORCONF["IP"]
    remoteAs = NEIGHBORCONF["Remote-as"]
    state = StateMachine(ip, remoteAs, BGP_MODE_RESPONDER)
    while True:
        state.stateMachine()

def client():
    print("### Initiator mode ###")
    with open('config.yaml', 'r') as yml:
        config = yaml.safe_load(yml)
    NEIGHBORCONF = config['bgp']['neighbor'][0]
    ip = NEIGHBORCONF["IP"]
    remoteAs = NEIGHBORCONF["Remote-as"]
    state = StateMachine(ip, remoteAs, BGP_MODE_INITIATOR)
    while True:
        state.stateMachine()

if __name__ == "__main__":
    arg = sys.argv
    if 2 <= len(arg):
        cmd = arg[1]
        if cmd == "sv":
            server()
        elif cmd == "cl":
            client()
        else:
            print("Unexpected argument(sv or cl)")
    else:
        print("Requires an argument")
