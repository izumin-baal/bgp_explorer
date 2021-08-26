import sys
import socket
import yaml
import threading
import time
import bgpformat
import rw

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

class StateMachine:
    def __init__(self, ip, remoteAs, mode):
        self.addr = ip
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
            self.s.connect((self.addr, 179))
            print("Connect to " + self.addr)
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
            print("\033[33m", "*** Neighbor Up ***", "\033[0m")
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
            msglencnt = len(BgpMsgArray)

            while True:
                msglen = BgpMsgArray[16] * 256 + BgpMsgArray[17]
                msglencnt -= msglen
                type = self.checkMessage(BgpMsgArray[18])    
                if type == BGP_MSG_UPDATE or type == BGP_MSG_KEEPALIVE:
                    if type == BGP_MSG_UPDATE:
                        self.getUpdate(BgpMsgArray)
                elif type == BGP_MSG_NOTIFICATION:
                    print("received notification")
                    self.state = BGP_STATE_IDLE
                else:
                    print("received Error")
                    self.state = BGP_STATE_IDLE
                if msglencnt <= 0:
                    break
                del BgpMsgArray[0:msglen]

        
        except socket.timeout:
            print("TimeOut")
            print("\033[33m", "*** Neighbor Down ***", "\033[0m")
            self.state = BGP_STATE_IDLE
        except:
            sys.exit()

    def getUpdate(self,msg):
        messageLength = msg[16] * 256 + msg[17]
        withdrawnLength = msg[19] * 256 + msg[20]
        # Withdrawn
        if withdrawnLength != 0:
            withdrawnStartByte = 21
            while withdrawnStartByte < 21 + withdrawnLength:
                prefixLength = msg[withdrawnStartByte]
                if prefixLength <= 8:
                    prefix_w = str(msg[withdrawnStartByte + 1]) + ".0.0.0/" + str(prefixLength)
                    withdrawnStartByte += 2
                elif prefixLength <= 16:
                    prefix_w = str(msg[withdrawnStartByte + 1]) + "." + str(msg[withdrawnStartByte + 2]) + ".0.0/" + str(prefixLength)
                    withdrawnStartByte += 3
                elif prefixLength <= 24:
                    prefix_w = str(msg[withdrawnStartByte + 1]) + "." + str(msg[withdrawnStartByte + 2]) + "." + str(msg[withdrawnStartByte + 3]) + ".0/" + str(prefixLength)
                    withdrawnStartByte += 4
                else:
                    prefix_w = str(msg[withdrawnStartByte + 1]) + "." + str(msg[withdrawnStartByte + 2]) + "." + str(msg[withdrawnStartByte + 3]) + "." + str(msg[withdrawnStartByte + 4]) + "/" + str(prefixLength)
                    withdrawnStartByte += 5
                print("\033[31m","Receive UPDATE Withdrawn Prefix: ", prefix_w, "\033[0m")
                rw.del_from_bgptable(prefix_w, self.addr)
        # PathAttribute
        pathAttributeLength = msg[21 + withdrawnLength] * 256 + msg[22 + withdrawnLength]
        pathAttributeStartByte = 23 + withdrawnLength
        if pathAttributeLength != 0:
            pathAttrLenCnt = pathAttributeLength
            to_bgptable_array = {}
            if debug:
                print("## pathAttribute ##")
                print("Total Path Attribute Length: ", pathAttributeLength)
                print("--------------------------")
            while pathAttrLenCnt > 0:
                attributeFlag =  msg[pathAttributeStartByte]
                attributetype = msg[pathAttributeStartByte + 1]
                s = format(attributeFlag, '08b')
                if int(s[3]) == 0:
                    # AttrLength = 1byte
                    attributelength = msg[pathAttributeStartByte + 2]
                    attributeArray = [attributeFlag, attributetype, attributelength]
                    for i in range(attributelength):
                        attributeArray.append(msg[pathAttributeStartByte + 3 + i])
                    pathAttributeStartByte += (3 + attributelength)
                    pathAttrLenCnt -= attributelength + 3
                else:
                    # AttrLength = 2byte
                    attributelength = msg[pathAttributeStartByte + 2] * 256 + msg[pathAttributeStartByte + 3]
                    attributeArray = [attributeFlag, attributetype, attributelength]
                    for i in range(attributelength):
                        attributeArray.append(msg[pathAttributeStartByte + 4 + i])
                    pathAttributeStartByte += (4 + attributelength)
                    pathAttrLenCnt -= attributelength + 4
                to_bgptable_array.update(self.selectPathAttribute(attributeArray))
        # NLRI
        nlriStartByte = 23 + withdrawnLength + pathAttributeLength
        while nlriStartByte < messageLength:
            prefixLength = msg[nlriStartByte]
            if prefixLength <= 8:
                prefix_n = str(msg[nlriStartByte + 1]) + ".0.0.0/" + str(prefixLength)
                nlriStartByte += 2
            elif prefixLength <= 16:
                prefix_n = str(msg[nlriStartByte + 1]) + "." + str(msg[nlriStartByte + 2]) + ".0.0/" + str(prefixLength)
                nlriStartByte += 3
            elif prefixLength <= 24:
                prefix_n = str(msg[nlriStartByte + 1]) + "." + str(msg[nlriStartByte + 2]) + "." + str(msg[nlriStartByte + 3]) + ".0/" + str(prefixLength)
                nlriStartByte += 4
            else:
                prefix_n = str(msg[nlriStartByte + 1]) + "." + str(msg[nlriStartByte + 2]) + "." + str(msg[nlriStartByte + 3]) + "." + str(msg[nlriStartByte + 4]) + "/" + str(prefixLength)
                nlriStartByte += 5
            print("\033[32m","Receive UPDATE NLRI Prefix: ", prefix_n, "\033[0m")
            rw.into_bgptable(prefix_n, to_bgptable_array)
        if debug:
            print("withdrawn Routes Length: ", withdrawnLength)

    def selectPathAttribute(self, attributeArray):
        attributeflag =  attributeArray[0]
        attributetype = attributeArray[1]
        attributelength = attributeArray[2]
        parameterArray = []
        for i in attributeArray[3:]:
            parameterArray.append(i)
        if attributetype == BGP_PASSATTR_ORIGIN:
            if debug:
                print('# ORIGIN #')
                print('origin: ', parameterArray[0])
            return {'origin': parameterArray[0]}
        elif attributetype == BGP_PASSATTR_AS_PATH:
            # SegmentType
            if parameterArray[0] == 1:
                # AS_SET
                pass
            elif parameterArray[0] == 2:
                # AS_SEQUENCE
                pass
            # SegmentLength
            segmentLen = parameterArray[1]
            as_path = []
            for i in range(segmentLen):
                as_path.append(parameterArray[(i*2) + 2] * 256 + parameterArray[(i*2) + 3])
            if debug:
                print('# AS_PATH #')
                print('as_path: ', as_path)
            return {'as_path': as_path}
        elif attributetype == BGP_PASSATTR_NEXT_HOP:
            next_hop = str(parameterArray[0]) + "." + str(parameterArray[1]) + "." + str(parameterArray[2]) + "." + str(parameterArray[3])
            if debug:
                print('# NEXT_HOP #')
                print('next_hop: ', next_hop)
            return {'next_hop': next_hop}
        elif attributetype == BGP_PASSATTR_MED:
            med = parameterArray[0] * (256 ^ 4) + parameterArray[1] * (256 ^ 3) + parameterArray[2] * (256 ^ 2) + parameterArray[3]
            if debug:
                print('# MED #')
                print('med: ', med)
            return {'med': med}
        else:
            pass
        if debug:
            print("--------------------------")
            print("attributeflag:", format(attributeArray[0], '08b'))
            print(" Optional:", format(attributeArray[0], '08b')[0])
            print(" Transitive:", format(attributeArray[0], '08b')[1])
            print(" Partial:", format(attributeArray[0], '08b')[2])
            print(" Extended-Length:", format(attributeArray[0], '08b')[3])
            print("attributetype:", attributeArray[1])
            print("attributelength:", attributeArray[2])
            print("--------------------------")




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
