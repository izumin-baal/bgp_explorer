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
BGP_PASSATTR_LP = 5
BGP_PASSATTR_ATOMIC_AGGR = 6
BGP_PASSATTR_AGGR = 7
BGP_PASSATTR_COMMUNITIES = 8

# debug mode
debug = True
# peer state
peer_state = {}
# 
globalLock = threading.Lock()
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
                    peer_state[self.neighborip] = BGP_STATE_IDLE
                    sys.exit()
                if  peer_state[self.neighborip] == BGP_STATE_IDLE:
                    s = None
                    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    #s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                    try:
                        peer_state[self.neighborip] = BGP_STATE_CONNECT
                        if debug:
                            self.printState()
                        print('Connect to ' + self.neighborip)
                        s.connect((self.neighborip, 179))
                        self.timeout = 5
                        s.settimeout(self.timeout)
                        self.sendOpen(s)
                        peer_state[self.neighborip] = BGP_STATE_OPENSENT
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
                    try:
                        data = s.recv(4096)
                    except socket.timeout:
                        if peer_state[self.neighborip] == BGP_STATE_ESTABLISHED:
                            if debug:
                                print('[E][' + self.neighborip + '] Timeout HoldTime.')
                            print('Neighbor ' + self.neighborip + ' Down.')
                            peer_state[self.neighborip] = BGP_STATE_IDLE
                            time.sleep(10)
                        else:
                            if debug:
                                print('[E][' + self.neighborip + '] No response.')
                            peer_state[self.neighborip] = BGP_STATE_IDLE
                    self.operateByState(s, data)
        elif self.mode == BGP_MODE_RESPONDER:
            pass

    # State
    def printState(self):
        global peer_state
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
            self.openSent(s, decData)
        elif i == BGP_STATE_OPENCONFIRM:
            self.openConfirm(s, decData)
        elif i == BGP_STATE_ESTABLISHED:
            self.established(s, decData)

        else:
            pass

    def openSent(self, s, decData):
        global peer_state
        if self.mode == BGP_MODE_INITIATOR:
            if decData[MSGTYPE_CHECK_BIN] == BGP_MSG_OPEN:
                if self.checkRecvOpen(decData):
                    # OK
                    self.sendKeepalive(s)
                    peer_state[self.neighborip] = BGP_STATE_OPENCONFIRM
                    if debug:
                        self.printState()
                else:
                    # False
                    peer_state[self.neighborip] = BGP_STATE_IDLE
                    if debug:
                        self.printState()
            else:
                peer_state[self.neighborip] = BGP_STATE_IDLE
                if debug:
                    self.printState()
        elif self.mode == BGP_MODE_RESPONDER:
            pass

    def openConfirm(self, s, decData):
        global peer_state
        if self.mode == BGP_MODE_INITIATOR:
            if decData[MSGTYPE_CHECK_BIN] == BGP_MSG_KEEPALIVE:
                ### KEEPALIVE thread ###
                peer_state[self.neighborip] = BGP_STATE_ESTABLISHED
                s.settimeout(self.timeout)
                t = threading.Thread(target=self.intervalKeepalive, args=(s,))
                t.start()
                print('Neighbor ' + self.neighborip + ' Up.')    
                if debug:
                    self.printState()
                self.sendUpdate(s) # Update
            else:
                peer_state[self.neighborip] = BGP_STATE_IDLE
                if debug:
                    self.printState()
        elif self.mode == BGP_MODE_RESPONDER:
            pass

    def established(self, s, decData):
        global peer_state
        if self.mode == BGP_MODE_INITIATOR:
            if decData[MSGTYPE_CHECK_BIN] == BGP_MSG_UPDATE:
                self.recvUpdate(decData)
            elif decData[MSGTYPE_CHECK_BIN] == BGP_MSG_KEEPALIVE:
                pass
            elif decData[MSGTYPE_CHECK_BIN] == BGP_MSG_NOTIFICATION:
                pass
            elif decData[MSGTYPE_CHECK_BIN] == BGP_MSG_ROUTEREFRESH:
                pass
            else:
                pass
        elif self.mode == BGP_MODE_RESPONDER:
            pass


    # OPEN
    def sendOpen(self, s):
        if self.mode == BGP_MODE_INITIATOR:
            msg = bgpformat.b_openMsg()
            s.sendall(msg)
        elif self.mode == BGP_MODE_RESPONDER:
            pass
        if debug:
            print(">>[" + self.neighborip + "] Send OPEN")

    def checkRecvOpen(self, decData):
        global peer_state
        with open('config.yaml', 'r') as yml:
            config = yaml.safe_load(yml)
        PARAMETERCONF = config['bgp']['parameter']
        errorMsg = False
        # ASN
        if self.remoteas != (decData[20] * 256 + decData[21]):
            if debug:
                print('[E][' + self.neighborip + '] neighbor ASN is incorrect.')
            errorMsg = True
        # Version
        if PARAMETERCONF['Version'] != decData[19]:
            if debug:
                print('[E][' + self.neighborip + '] neighbor Version incorrect.')
            errorMsg = True
        # Router-ID
        if PARAMETERCONF['RouterID'] == (str(decData[24]) + '.' + str(decData[25]) + '.' + str(decData[26]) + '.' + str(decData[27])):
            if debug:
                print("[E][" + self.neighborip + "] Duplicate RouterID.")
            errorMsg = True
        # Holdtime
        if PARAMETERCONF['HoldTime'] < (decData[22] * 256 + decData[23]):
            if debug:
                print("[I][" + self.neighborip + "] Use my HoldTime.")
            self.holdtime = PARAMETERCONF['HoldTime']
            self.timeout = self.holdtime
        else:
            if debug:
                print("[I][" + self.neighborip + "] Use Neighbor Holdtime.")
            self.holdtime = decData[22] * 256 + decData[23]
            self.timeout = self.holdtime
        if debug:
            print('===========================')
            print('# Recv OPEN Parameter [' + self.neighborip + ' #')
            print('Version: ' + str(decData[19]))
            print('ASN: ' + str(decData[20] * 256 + decData[21]))
            print('Router-ID: ' + str(decData[24]) + '.' + str(decData[25]) + '.' + str(decData[26]) + '.' + str(decData[27]))
            print('HoldTime: ' + str(decData[22] * 256 + decData[23]))
            print('Option: ' + str(decData[29]))
            print('===========================')
        if errorMsg:
            return False
        else:
            return True

    # UPDATE
    def recvUpdate(self, decData):
        global globalLock
        messageLength = decData[16] * 256 + decData[17]
        withdrawnLength = decData[19] * 256 + decData[20]
        # Withdrawn
        if withdrawnLength != 0:
            withdrawnStartByte = 21
            withdrawnRoute = []
            while withdrawnStartByte < 21 + withdrawnLength:
                prefixLength = decData[withdrawnStartByte]
                if prefixLength <= 8:
                    prefix_w = str(decData[withdrawnStartByte + 1]) + ".0.0.0/" + str(prefixLength)
                    withdrawnStartByte += 2
                elif prefixLength <= 16:
                    prefix_w = str(decData[withdrawnStartByte + 1]) + "." + str(decData[withdrawnStartByte + 2]) + ".0.0/" + str(prefixLength)
                    withdrawnStartByte += 3
                elif prefixLength <= 24:
                    prefix_w = str(decData[withdrawnStartByte + 1]) + "." + str(decData[withdrawnStartByte + 2]) + "." + str(decData[withdrawnStartByte + 3]) + ".0/" + str(prefixLength)
                    withdrawnStartByte += 4
                else:
                    prefix_w = str(decData[withdrawnStartByte + 1]) + "." + str(decData[withdrawnStartByte + 2]) + "." + str(decData[withdrawnStartByte + 3]) + "." + str(decData[withdrawnStartByte + 4]) + "/" + str(prefixLength)
                    withdrawnStartByte += 5
                if debug:
                    print("\033[31m","Receive UPDATE Withdrawn Prefix: ", prefix_w, "\033[0m")
                withdrawnRoute.append(prefix_w)
                globalLock.acquire()
                rw.del_from_bgptable(prefix_w, self.neighborip)
                globalLock.release()
            if debug:
                print('=======================')
                print('# Withdrawn #')
                print('Withdrawn Route Length: ' + str(withdrawnLength))
                for i in withdrawnRoute:
                    print('Withdrawn Routes: ' + i)
                print('=======================')

        # PathAttribute
        pathAttributeLength = decData[21 + withdrawnLength] * 256 + decData[22 + withdrawnLength]
        pathAttributeStartByte = 23 + withdrawnLength
        if pathAttributeLength != 0:
            pathAttrLenCnt = pathAttributeLength
            to_bgptable_array = {}
            while pathAttrLenCnt > 0:
                attributeFlag =  decData[pathAttributeStartByte]
                attributetype = decData[pathAttributeStartByte + 1]
                s = format(attributeFlag, '08b')
                # flag 3rd bit = AttrLen. 0 = 1byte, 1 = 2byte. 
                if int(s[3]) == 0:
                    # AttrLength = 1byte
                    attributelength = decData[pathAttributeStartByte + 2]
                    attributeArray = [attributeFlag, attributetype, attributelength]
                    for i in range(attributelength):
                        attributeArray.append(decData[pathAttributeStartByte + 3 + i])
                    pathAttributeStartByte += (3 + attributelength)
                    pathAttrLenCnt -= attributelength + 3
                else:
                    # AttrLength = 2byte
                    attributelength = decData[pathAttributeStartByte + 2] * 256 + decData[pathAttributeStartByte + 3]
                    attributeArray = [attributeFlag, attributetype, attributelength]
                    for i in range(attributelength):
                        attributeArray.append(decData[pathAttributeStartByte + 4 + i])
                    pathAttributeStartByte += (4 + attributelength)
                    pathAttrLenCnt -= attributelength + 4
                to_bgptable_array.update(self.selectPathAttribute(attributeArray))
        
        # NLRI
        nlriStartByte = 23 + withdrawnLength + pathAttributeLength
        while nlriStartByte < messageLength:
            prefixLength = decData[nlriStartByte]
            if prefixLength <= 8:
                prefix_n = str(decData[nlriStartByte + 1]) + ".0.0.0/" + str(prefixLength)
                nlriStartByte += 2
            elif prefixLength <= 16:
                prefix_n = str(decData[nlriStartByte + 1]) + "." + str(decData[nlriStartByte + 2]) + ".0.0/" + str(prefixLength)
                nlriStartByte += 3
            elif prefixLength <= 24:
                prefix_n = str(decData[nlriStartByte + 1]) + "." + str(decData[nlriStartByte + 2]) + "." + str(decData[nlriStartByte + 3]) + ".0/" + str(prefixLength)
                nlriStartByte += 4
            else:
                prefix_n = str(decData[nlriStartByte + 1]) + "." + str(decData[nlriStartByte + 2]) + "." + str(decData[nlriStartByte + 3]) + "." + str(decData[nlriStartByte + 4]) + "/" + str(prefixLength)
                nlriStartByte += 5
            print("\033[32m","Receive UPDATE NLRI Prefix: ", prefix_n, "\033[0m")
            globalLock.acquire()
            rw.into_bgptable(prefix_n, to_bgptable_array)
            globalLock.release()
        if debug:
            print("withdrawn Routes Length: ", withdrawnLength)

    def selectPathAttribute(self, attributeArray):
        attributeflag =  attributeArray[0]
        attributetype = attributeArray[1]
        attributelength = attributeArray[2]
        if debug:
            print("--------------------------")
            print("# PathAttribute info #")
            print("attributeflag:", format(attributeArray[0], '08b'))
            print(" Optional:", format(attributeArray[0], '08b')[0])
            print(" Transitive:", format(attributeArray[0], '08b')[1])
            print(" Partial:", format(attributeArray[0], '08b')[2])
            print(" Extended-Length:", format(attributeArray[0], '08b')[3])
            print("attributetype:", attributeArray[1])
            print("attributelength:", attributeArray[2])

        parameterArray = []
        for i in attributeArray[3:]:
            parameterArray.append(i)
        
        # ORIGIN
        if attributetype == BGP_PASSATTR_ORIGIN:
            if debug:
                print('# ORIGIN #')
                print('origin: ', parameterArray[0])
                print("--------------------------")
            return {'origin': parameterArray[0]}
        
        # ASPATH
        if attributetype == BGP_PASSATTR_AS_PATH:
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
                print("--------------------------")
            return {'as_path': as_path}
        
        # NEXT_HOP
        if attributetype == BGP_PASSATTR_NEXT_HOP:
            next_hop = str(parameterArray[0]) + "." + str(parameterArray[1]) + "." + str(parameterArray[2]) + "." + str(parameterArray[3])
            if debug:
                print('# NEXT_HOP #')
                print('next_hop: ', next_hop)
                print("--------------------------")
            return {'next_hop': next_hop}

        # MED
        if attributetype == BGP_PASSATTR_MED:
            med = parameterArray[0] * (256 ^ 4) + parameterArray[1] * (256 ^ 3) + parameterArray[2] * (256 ^ 2) + parameterArray[3]
            if debug:
                print('# MED #')
                print('med: ', med)
                print("--------------------------")
            return {'med': med}
        
        # LP
        if attributetype == BGP_PASSATTR_LP:
            lp = parameterArray[0] * (256 ^ 4) + parameterArray[1] * (256 ^ 3) + parameterArray[2] * (256 ^ 2) + parameterArray[3]
            if debug:
                print('# LP #')
                print('LP: ', lp) 
                print("--------------------------")

        # COMMUNITY
        if attributetype == BGP_PASSATTR_COMMUNITIES:
            community_f = parameterArray[0] * (256 ^ 2) + parameterArray[1]
            community_b = parameterArray[2] * (256 ^ 2) + parameterArray[3]
            community = str(community_f) + ':' + str(community_b)
            if debug:
                print('# COMMUNITY #')
                print('COMMUNITY: ', community)
                print("--------------------------")
            return {'community': community}

    def sendUpdate(self,s):
        msg = bgpformat.b_updateMsg(self.nexthop)
        s.sendall(msg)
        if debug:
            print(">>[" + self.neighborip + "] Send UPDATE")

    # NOTIFICATION

    # KEEPALIVE
    def sendKeepalive(self,s):
        msg = bgpformat.b_keepaliveMsg()
        s.sendall(msg)
        if debug:
            print(">>[" + self.neighborip + "] Send KEEPALIVE")
    
    def intervalKeepalive(self, s):
        global peer_state
        global exitflag
        if exitflag:
            if debug:
                print("[!][" + self.neighborip + "] intervalKeepalive down")
            sys.exit()
        while peer_state[self.neighborip] == BGP_STATE_ESTABLISHED:
            self.sendKeepalive(s)
            time.sleep(int(self.holdtime/3))


    # Other
    def convertBinToDec(self, data):
        data_digit_array = []
        for i, octet in enumerate(data):
            data_digit_array.append(octet)
            if debug:
                if i == MSGTYPE_CHECK_BIN:
                    if octet == BGP_MSG_OPEN:
                        print('<<[' + self.neighborip + '] Recv OPEN')
                    elif octet == BGP_MSG_UPDATE:
                        print('<<[' + self.neighborip + '] Recv UPDATE')
                    elif octet == BGP_MSG_NOTIFICATION:
                        print('<<[' + self.neighborip + '] Recv NOTIFICATION')
                    elif octet == BGP_MSG_KEEPALIVE:
                        print('<<[' + self.neighborip + '] Recv KEEPALIVE')
                    elif octet == BGP_MSG_ROUTEREFRESH:
                        print('<<[' + self.neighborip + '] Recv ROUTEREFRESH')
                    else:
                        print('<<[' + self.neighborip + '] Recv UNKNOWN')
        return data_digit_array

#def server():
    #print("### Responder mode ###")
    #with open('config.yaml', 'r') as yml:
    #    config = yaml.safe_load(yml)
    #NEIGHBORCONF = config['bgp']['neighbor']
    #ip = NEIGHBORCONF["IP"]
    #remoteAs = NEIGHBORCONF["Remote-as"]
    #state = StateMachine(ip, remoteAs, BGP_MODE_RESPONDER)
    #while True:
    #    state.stateMachine()

def client():
    global exitflag
    global peer_state
    global globalLock
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
            i = input()
            if i == "":
                print("[cmd]")
            elif i == "exit":
                print("# exitflag is True. wait...#")
                exitflag = True
                for i in range(len(th)):
                    th[i].join()
                globalLock.acquire()
                rw.del_all()
                globalLock.release()
                print("exit.")
                sys.exit()
            elif i == "show":
                for k, v in peer_state.items():
                    if v == 1: 
                        state = 'IDLE'
                    elif v == 2: 
                        state = 'CONNECT'
                    elif v == 3: 
                        state = 'ACTIVE'
                    elif v == 4: 
                        state = 'OPENSENT'
                    elif v == 5: 
                        state = 'OPENCONFIRM'
                    elif v == 6: 
                        state = 'ESTABLISHED'
                    print(str(k) + ': ' + state)
    except KeyboardInterrupt:
        exitflag = True
        print('# exitflag is True. wait...#')
        for i in range(len(th)):
            th[i].join()
        globalLock.acquire()
        rw.del_all()
        globalLock.release()
        print("exit.")
        sys.exit()

if __name__ == "__main__":
    if os.geteuid() == 0 and os.getuid() == 0 :
        pass
    else:
        print("Root Only!!!")
        sys.exit()
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
