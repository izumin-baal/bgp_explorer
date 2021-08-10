import sys
import socket
import yaml
import threading
import time
import random

#
# STATE
# Idle: 1 
# Connect: 2
# Active: 3
# OpenSent: 4
# OpenConfirm: 5
# Established: 6
#

# init
state = 0

def bgp(type, direction, MsgArray=None):
    with open('config.yaml', 'r') as yml:
        config = yaml.safe_load(yml)
    if type == 1:
        # Open
        OPENCONF = config['open'][0]
        if direction == 1:
            # OPEN req
            b_openmsg = openMsg(OPENCONF['version'], OPENCONF['MyASN'], OPENCONF['HoldTime'], OPENCONF['RouterID'], OPENCONF['Option'])
            b_msgheader = msgHeader(int(len(b_openmsg)/8), 1)
            msg = b_msgheader + b_openmsg
            msglen = int(len(msg)/8)
            return int(msg, 2), msglen 
        else:
            # OPEN res
            # version
            #print("Version: " + str(MsgArray[19]))
            if OPENCONF['version'] == MsgArray[19]:
                #print("Version Match")
                pass
            else:
                #print("Version Unmatch")
                errorMsg = notificateMsg()
            
            # ASN
            #print("ASN: " + str(MsgArray[20] * 8 + MsgArray[21]))
            if OPENCONF['MyASN'] == (MsgArray[20] * 8 + MsgArray[21]):
                #print("ASN Mastch(iBGP)")
                pass
            else:
                #print("ASN Unmastch(eBGP)")
                pass
            
            # HoldTime
            #print("HoldTime: " + str(MsgArray[22] * 8 + MsgArray[23]))
            if OPENCONF['HoldTime'] > (MsgArray[22] * 8 + MsgArray[23]):
                #print("Use Neighber HoldTime ")
                pass
            else:
                #print("Use My HoldTime")
                pass
            
            # RouterID
            #print("Router-id: " + str(MsgArray[24]) + '.' + str(MsgArray[25]) + '.' + str(MsgArray[26]) + '.' + str(MsgArray[27]))
            if OPENCONF['RouterID'] == (str(MsgArray[24]) + '.' + str(MsgArray[25]) + '.' + str(MsgArray[26]) + '.' + str(MsgArray[27])):
                #print("Duplication Router-ID")
                errorMsg = notificateMsg()
            else:
                #print("Remote-AS OK")
                pass
            if 'errorMsg' in locals():
                msglen = int(len(errorMsg)/8)
                return int(errorMsg, 2), msglen
            else:
                b_openmsg = openMsg(OPENCONF['version'], OPENCONF['MyASN'], OPENCONF['HoldTime'], OPENCONF['RouterID'], OPENCONF['Option'])
                b_msgheader = msgHeader(int(len(b_openmsg)/8), 1)
                msg = b_msgheader + b_openmsg
                msglen = int(len(msg)/8)
                return int(msg, 2), msglen 
    else:
        pass

def bgpCheck(MsgArray):
    with open('config.yaml', 'r') as yml:
        config = yaml.safe_load(yml)
    OPENCONF = config['open'][0]
    #print("Version: " + str(MsgArray[19]))
    if OPENCONF['version'] == MsgArray[19]:
        #print("Version Match")
        pass
    else:
        #print("Version Unmatch")
        errorMsg = notificateMsg()
    
    # ASN
    #print("ASN: " + str(MsgArray[20] * 8 + MsgArray[21]))
    if OPENCONF['MyASN'] == (MsgArray[20] * 8 + MsgArray[21]):
        #print("ASN Mastch(iBGP)")
        pass
    else:
        #print("ASN Unmastch(eBGP)")
        pass
    
    # HoldTime
    #print("HoldTime: " + str(MsgArray[22] * 8 + MsgArray[23]))
    if OPENCONF['HoldTime'] > (MsgArray[22] * 8 + MsgArray[23]):
        #print("Use Neighber HoldTime ")
        pass
    else:
        #print("Use My HoldTime")
        pass
    
    # RouterID
    #print("Router-id: " + str(MsgArray[24]) + '.' + str(MsgArray[25]) + '.' + str(MsgArray[26]) + '.' + str(MsgArray[27]))
    if OPENCONF['RouterID'] == (str(MsgArray[24]) + '.' + str(MsgArray[25]) + '.' + str(MsgArray[26]) + '.' + str(MsgArray[27])):
        #print("Duplication Router-ID")
        errorMsg = notificateMsg()
    else:
        #print("Remote-AS OK")
        pass
    if 'errorMsg' in locals():
        return True
    else:
        return False

def msgHeader(uppermsgLen, type):
    b_marker = format(0xffffffffffffffffffffffffffffffff, '0128b')
    b_length = format(uppermsgLen + 19, '016b')
    b_type = format(type, '08b')
    return b_marker + b_length + b_type

def openMsg():
    with open('config.yaml', 'r') as yml:
        config = yaml.safe_load(yml)
    NEIGHBORCONF = config['bgp']['parameter']
    version = NEIGHBORCONF["Version"]
    asn = NEIGHBORCONF["MyASN"]
    holdtime = NEIGHBORCONF["HoldTime"]
    routerid = NEIGHBORCONF["RouterID"]
    isoption = NEIGHBORCONF["Option"]
    b_version = binaryVersion(version)
    b_asn = binaryASN(asn)
    b_holdtime = binaryHoldtime(holdtime)
    b_routerid = binaryRouterID(routerid)
    if isoption:
        # 仮
        b_optlen = format(255, '08b')
        pass
    else:
        b_optlen = format(0, '08b')
    return b_version + b_asn + b_holdtime + b_routerid + b_optlen

def notificateMsg():
    return msgHeader(0, 3) # 本来はNOTFICATEのエラーコードの長さをいれる

def keepaliveMsg():
    return msgHeader(0, 4)

def binaryVersion(value):
    if type(value) == int:
        version = int(value)
        if version == 4:
            return format(4, '08b')
        else:
            print("BGP Version is Incorrect")
            sys.exit()
    else:
        print("BGP Version is Incorrect")

def binaryASN(value):
    if type(value) == int:
        asn = int(value)
        if asn < 1 or asn > 65535:
            print("BGP ASN is Incorrect")
            sys.exit()
        else:
            return format(value, '016b')
    else:
        print("BGP ASN is Incorrect")
        sys.exit()

def binaryHoldtime(value):
    if type(value) == int:
        holdtime = int(value)
        if holdtime < 0 or holdtime > 65535:
            print("BGP HoldTime is Incorrect")
            sys.exit()
        else:
            return format(value, '016b')
    else:
        print("BGP HoldTime is Incorrect")
        sys.exit()

def binaryRouterID(value):
    if type(value) == str:
        splitValue = value.split(".")
        if len(splitValue) == 4:
            binRouteid = ""
            for i in splitValue:
                if int(i) < 1 or int(i) > 255:
                    print("BGP Router-ID is Incorrect")
                    sys.exit()
                else:
                    binRouteid += format(int(i), '08b')
            return binRouteid
        else:
            print("BGP Router-ID is Incorrect")
            sys.exit()        
    else:
        print("BGP RouterID is Incorrect")
        sys.exit()

def replyOpen(MsgArray):
    data, msglen = bgp(1,2, MsgArray)
    return data.to_bytes(int(msglen), 'big')

def notificateJudg(data):
    for i,bytes in enumerate(data, 1):
                    if i == 19:
                        # Type
                        if bytes == 3:
                            return True
                        else:
                            return False

def KeepAlive():
    print("KEEPALIVE")
    t = threading.Timer(10, KeepAlive)
    t.start()

def HoldTime(time):
    t = threading.Timer(time, KeepAlive)
    t.start()
    print("TimeOut")

def Idle():
    state = 1
    # data, msglen = bgp(1, 1)
    while state == 1:
        pass

def checkMessage(type):
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

def State():
    # init
    # config読み込み
    with open('config.yaml', 'r') as yml:
        config = yaml.safe_load(yml)
    NEIGHBORCONF = config['neighbor'][0]
    ip = NEIGHBORCONF['IP']
    remoteAs = NEIGHBORCONF['remote-as']
    # Idle
    state = 1
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(("", 179))
    s.listen()
    while state == 1:
        s.settimeout(random.randint(1,5))
        try:
            conn, addr = s.accept()
            print("!! Connected by ", addr, " !!")
            state = 4 # OpenSent
            s.settimeout(None)
            with conn:
                data = conn.recv(4096)
                BgpMsgArray = []
                type = 0
                for i,bytes in enumerate(data, 1):
                    BgpMsgArray.append(bytes)
                    if i == 19:
                        type = checkMessage(bytes)
                if type == 1:
                    # recv Open
                    replydata = replyOpen(BgpMsgArray)
                    notificate = notificateJudg(replydata)
                    conn.sendall(replydata)
                    state = 5
                    if notificate:
                        print(">> Send NOTIFICATION Message")
                        state = 1
                    else:
                        print(">> Send OPEN Message")
                elif type == 2:
                    # recv UPDATE
                    pass
                elif type == 3:
                    # recv KEEP
                    state = 1
                elif type == 4:
                    # recv NOTI
                    pass
                else:
                    pass
                if state == 5: # OpenConfirm
                    conn.settimeout(10)
                    try:
                        data = conn.recv(4096) # KEEPALIVE待ち
                        conn.settimeout(None)
                        BgpMsgArray = []
                        for i,bytes in enumerate(data, 1):
                            BgpMsgArray.append(bytes)
                            if i == 19:
                                type = checkMessage(bytes)
                        if type == 4: #KEEPALIVE
                            state = 6 # Established
                            print(">> Send KEEPALIVE Message")
                            sendmsg = keepaliveMsg()
                            msglen = int(len(sendmsg)/8)
                            senddata = int(sendmsg, 2).to_bytes(int(msglen), 'big')
                            conn.sendall(senddata)
                            print("Established!!!")
                        elif type == 3: # NOTIFICATE
                            state = 1
                    except:
                        print("例外発生!!!")
                        state = 1
        except socket.timeout:
            # クライアント側となる処理
            print("##### Access #####")
            print("try: " + ip)
            senddata, msglen = bgp(1, 1)
            s.close()
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            try:
                s.connect((ip, 179))
                s.sendall(senddata.to_bytes(int(msglen), 'big')) # Open送信
                print(">> Send Open Message")
                state = 4 # Opensent
                while state == 4 or state == 5:
                    s.settimeout(20)
                    try:
                        data = s.recv(4096)
                        s.settimeout(None)
                        BgpMsgArray = []
                        for i,bytes in enumerate(data, 1):
                            BgpMsgArray.append(bytes)
                            if i == 19:
                                type = checkMessage(bytes)
                        if type == 1: # Open受信
                            check = bgpCheck(BgpMsgArray)
                            if check:
                                print("enter True")
                                errorMsg = notificateMsg()
                                msglen = int(len(errorMsg)/8)
                                senddata = int(errorMsg, 2).to_bytes(int(msglen), 'big')
                                s.sendall(senddata)
                                s.close()
                                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                                s.bind(("", 179))
                                s.listen()
                                print(">> Send NOTIFICATION MESSAGE")
                            else:
                                msg = keepaliveMsg()
                                msglen = int(len(msg)/8)
                                senddata = int(msg, 2).to_bytes(int(msglen), 'big')
                                s.sendall(senddata) # KEEPALIVE送信
                                print(">> Send KEEPALIVE Message")
                                state = 5
                        elif type == 3: # NOTIFICATE受信
                            state = 1
                        elif type == 4: # KEEPALIVE受信
                            if state == 5:
                                state = 6 # Established
                                print("Established!!!")
                    except:
                        print("例外発生！")
                        errorMsg = notificateMsg()
                        msglen = int(len(errorMsg)/8)
                        senddata = int(errorMsg, 2).to_bytes(int(msglen), 'big')
                        s.sendall(senddata)
                        state = 1
            except:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.bind(("", 179))
                s.listen()

def server():
    print("#### Listen ####")
    with open('config.yaml', 'r') as yml:
        config = yaml.safe_load(yml)
    NEIGHBORCONF = config['neighbor'][0]
    ip = NEIGHBORCONF['IP']
    remoteAs = NEIGHBORCONF['remote-as']
    # Idle
    state = 1
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(("", 179))
    s.listen()
    print("Listen: 179")
    while state == 1:
        conn, addr = s.accept()
        print("!! Connected by ", addr, " !!")
        state = 4 # OpenSent
        s.settimeout(None)
        with conn:
            data = conn.recv(4096)
            BgpMsgArray = []
            type = 0
            for i,bytes in enumerate(data, 1):
                BgpMsgArray.append(bytes)
                if i == 19:
                    type = checkMessage(bytes)
            if type == 1:
                # recv Open
                replydata = replyOpen(BgpMsgArray)
                notificate = notificateJudg(replydata)
                conn.sendall(replydata)
                state = 5
                if notificate:
                    print(">> Send NOTIFICATION Message")
                    state = 1
                else:
                    print(">> Send OPEN Message")
            elif type == 2:
                # recv UPDATE
                pass
            elif type == 3:
                # recv NOTI
                state = 1
            elif type == 4:
                # recv KEEP
                pass
            else:
                pass
            if state == 5: # OpenConfirm
                conn.settimeout(10)
                try:
                    data = conn.recv(4096) # KEEPALIVE待ち
                    conn.settimeout(None)
                    BgpMsgArray = []
                    for i,bytes in enumerate(data, 1):
                        BgpMsgArray.append(bytes)
                        if i == 19:
                            type = checkMessage(bytes)
                    if type == 4: #KEEPALIVE
                        state = 6 # Established
                        print(">> Send KEEPALIVE Message")
                        sendmsg = keepaliveMsg()
                        msglen = int(len(sendmsg)/8)
                        senddata = int(sendmsg, 2).to_bytes(int(msglen), 'big')
                        conn.sendall(senddata)
                        print("Established!!!")
                    elif type == 3: # NOTIFICATE
                        state = 1
                except:
                    print("例外発生!!!")
                    state = 1

def client():
    with open('config.yaml', 'r') as yml:
        config = yaml.safe_load(yml)
    NEIGHBORCONF = config['neighbor'][0]
    ip = NEIGHBORCONF['IP']
    remoteAs = NEIGHBORCONF['remote-as']
    # Idle
    state = 1
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(("", 179))
    s.connect((ip, 179))
    print("##### Access #####")
    print("try: " + ip)
    senddata, msglen = bgp(1, 1)
    s.sendall(senddata.to_bytes(int(msglen), 'big')) # Open送信
    print(">> Send Open Message")
    state = 4 # Opensent
    while state == 4 or state == 5:
        try:
            data = s.recv(4096)
            BgpMsgArray = []
            for i,bytes in enumerate(data, 1):
                BgpMsgArray.append(bytes)
                if i == 19:
                    type = checkMessage(bytes)
            if type == 1: # Open受信
                check = bgpCheck(BgpMsgArray)
                if check:
                    print("enter True")
                    errorMsg = notificateMsg()
                    msglen = int(len(errorMsg)/8)
                    senddata = int(errorMsg, 2).to_bytes(int(msglen), 'big')
                    s.sendall(senddata)
                    s.close()
                    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    s.bind(("", 179))
                    s.listen()
                    print(">> Send NOTIFICATION MESSAGE")
                else:
                    msg = keepaliveMsg()
                    msglen = int(len(msg)/8)
                    senddata = int(msg, 2).to_bytes(int(msglen), 'big')
                    s.sendall(senddata) # KEEPALIVE送信
                    print(">> Send KEEPALIVE Message")
                    state = 5
            elif type == 3: # NOTIFICATE受信
                state = 1
            elif type == 4: # KEEPALIVE受信
                if state == 5:
                    state = 6 # Established
                    print("Established!!!")
        except:
            print("例外発生！")
            errorMsg = notificateMsg()
            msglen = int(len(errorMsg)/8)
            senddata = int(errorMsg, 2).to_bytes(int(msglen), 'big')
            s.sendall(senddata)
            state = 1


def main():
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

if __name__ == "__main__":
    main()
