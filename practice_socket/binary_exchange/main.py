import sys
import socket
import yaml

MSGTYPE = 1

def bgp():
    with open('config.yaml', 'r') as yml:
        config = yaml.safe_load(yml)
    if MSGTYPE == 1:
        # Open
        OPENCONF = config['open'][0]
        b_openmsg = openMsg(OPENCONF['version'], OPENCONF['MyASN'], OPENCONF['HoldTime'], OPENCONF['RouterID'], OPENCONF['Option'])
        b_msgheader = msgHeader(int(len(b_openmsg)/8), 1)
        msg = b_msgheader + b_openmsg
        return msg
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

def server(IPADDR, PORT):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((IPADDR, int(PORT)))
        s.listen()
        conn, addr = s.accept()
        with conn:
            print("Connected by ", addr)
            while True:
                data = conn.recv(1024)
                if not data: break
                conn.sendall(data)

def client(IPADDR, PORT, DATA):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((IPADDR, int(PORT)))
        s.sendall(DATA.encode())
        data = s.recv(1024)
    print('Received', repr(data))

def main():
    data = bgp()
    arg = sys.argv
    if 2 <= len(arg):
        cmd = arg[1]
        if cmd == "sv":
            if 4 <= len(arg):
                server(arg[2], arg[3])
        elif cmd == "cl":
            if 4 <= len(arg):
                client(arg[2], arg[3], data)
        else:
            print("Unexpected argument(sv or cl)")
    else:
        print("Requires an argument")

if __name__ == "__main__":
    main()
