import sys
import socket
import yaml
import threading
import time


def bgp(type, direction, MsgArray=None):
    if type == 1:
        with open('config.yaml', 'r') as yml:
            config = yaml.safe_load(yml)
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
            print("Version: " + str(MsgArray[19]))
            if OPENCONF['version'] == MsgArray[19]:
                print("Version Match")
            else:
                print("Version Unmatch")
                errorMsg = notificateMsg()
            
            # ASN
            print("ASN: " + str(MsgArray[20] * 8 + MsgArray[21]))
            if OPENCONF['MyASN'] == (MsgArray[20] * 8 + MsgArray[21]):
                print("ASN Mastch(iBGP)")
            else:
                print("ASN Unmastch(eBGP)")
            
            # HoldTime
            print("HoldTime: " + str(MsgArray[22] * 8 + MsgArray[23]))
            if OPENCONF['HoldTime'] > (MsgArray[22] * 8 + MsgArray[23]):
                print("Use Neighber HoldTime ")
            else:
                print("Use My HoldTime")
            
            # RouterID
            print("Router-id: " + str(MsgArray[24]) + '.' + str(MsgArray[25]) + '.' + str(MsgArray[26]) + '.' + str(MsgArray[27]))
            if OPENCONF['RouterID'] == (str(MsgArray[24]) + '.' + str(MsgArray[25]) + '.' + str(MsgArray[26]) + '.' + str(MsgArray[27])):
                print("Duplication Router-ID")
                errorMsg = notificateMsg()
            else:
                print("Remote-AS OK")
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
    


def msgHeader(uppermsgLen, type):
    b_marker = format(0xffffffffffffffffffffffffffffffff, '0128b')
    b_length = format(uppermsgLen + 19, '016b')
    b_type = format(type, '08b')
    return b_marker + b_length + b_type

    

def openMsg(version, asn, holdtime, routerid, isoption):
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
    pass

def server(IPADDR, PORT):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("", int(PORT)))
        s.listen()
        flag = True
        while flag:
            conn, addr = s.accept()
            with conn:
                print("Connected by ", addr)
                data = conn.recv(4096)
                BgpMsgArray = []
                type = 0
                for i,bytes in enumerate(data, 1):
                    BgpMsgArray.append(bytes)
                    if i == 19:
                        # Type
                        if bytes == 1:
                            type = 1
                            print("receive OPEN Message")
                            KeepAlive()
                        elif bytes == 2:
                            type = 2
                            print("receive UPDATE Message")
                        elif bytes == 3:
                            type = 3
                            flag = False
                            print("receive NOTIFICATION Message")
                        elif bytes == 4:
                            type = 4
                            print("receive KEEPALIVE Message")
                        else:
                            print("Unknown")
                # Typeによる処理の変化
                if type == 1:
                    replydata = replyOpen(BgpMsgArray)
                    notificate = notificateJudg(replydata)
                    conn.send(replydata)
                    if notificate:
                        print("NOTIFICATION Error")
                        flag = False
                elif type == 2:
                    pass
                elif type == 3:
                    pass
                elif type == 4:
                    pass
                else:
                    pass
                #conn.send('Retry?(y|n)'.encode('utf-8'))


def client(IPADDR, PORT, DATA):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((IPADDR, int(PORT)))
        s.sendall(DATA)
        flag = True
        while flag:
            data = s.recv(4096)
            BgpMsgArray = []
            type = 0
            for i,bytes in enumerate(data, 1):
                BgpMsgArray.append(bytes)
                if i == 19:
                    # Type
                    if bytes == 1:
                        type = 1
                        print("receive OPEN Message")
                    elif bytes == 2:
                        type = 2
                        print("receive UPDATE Message")
                    elif bytes == 3:
                        type = 3
                        print("receive NOTIFICATION Message")
                        flag = False
                    elif bytes == 4:
                        type = 4
                        print("receive KEEPALIVE Message")
                    else:
                        print("Unknown")
            # Typeによる処理の変化
            if type == 1:
                pass
            elif type == 2:
                pass
            elif type == 3:
                pass
            elif type == 4:
                pass
            else:
                pass
    print('Received', repr(data))

def main():
    arg = sys.argv
    if 2 <= len(arg):
        cmd = arg[1]
        if cmd == "sv":
            if 4 <= len(arg):
                server(arg[2], arg[3])
        elif cmd == "cl":
            if 4 <= len(arg):
                data, msglen = bgp(1, 1)
                client(arg[2], arg[3], data.to_bytes(int(msglen), 'big'))
        else:
            print("Unexpected argument(sv or cl)")
    else:
        print("Requires an argument")

if __name__ == "__main__":
    main()
