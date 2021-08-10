import sys
import yaml

def b_msgHeader(upperMsgLen, type):
    b_marker = format(0xffffffffffffffffffffffffffffffff, '0128b')
    b_length = format(upperMsgLen + 19, '016b')
    b_type = format(type, '08b')
    return b_marker + b_length + b_type

def b_openformat():
    with open('config.yaml', 'r') as yml:
        config = yaml.safe_load(yml)
    PARAMETERCONF = config['bgp']['parameter'][0]
    version = PARAMETERCONF["Version"]
    asn = PARAMETERCONF["MyASN"]
    holdtime = PARAMETERCONF["HoldTime"]
    routerid = PARAMETERCONF["RouterID"]
    isoption = PARAMETERCONF["Option"]
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

def b_openMsg():
    b_openFormat = b_openformat()
    b_openMsg = b_msgHeader(int(len(b_openFormat)/8), 1)
    msg = b_openMsg + b_openFormat
    msgLen = int(len(msg)/8)
    int_msg = int(msg, 2)
    return int_msg.to_bytes(msgLen, 'big')

def b_notificateMsg():
    b_msg = b_msgHeader(0, 3) # 本来はNOTFICATEのエラーコードの長さをいれる
    msgLen = int(len(b_msg)/8)
    return int(b_msg, 2).to_bytes(msgLen, 'big')

def b_keepaliveMsg():
    b_msg = b_msgHeader(0, 4)
    msgLen = int(len(b_msg)/8)
    return int(b_msg, 2).to_bytes(msgLen, 'big')

def binaryVersion(version):
    if type(version) == int:
        version = int(version)
        if version == 4:
            return format(4, '08b')
        else:
            print("BGP Version is Incorrect")
            sys.exit()
    else:
        print("BGP Version is Incorrect")
        sys.exit()

def binaryASN(asn):
    if type(asn) == int:
        asn = int(asn)
        if asn < 1 or asn > 65535:
            print("BGP ASN is Incorrect")
            sys.exit()
        else:
            return format(asn, '016b')
    else:
        print("BGP ASN is Incorrect")
        sys.exit()

def binaryHoldtime(holdtime):
    if type(holdtime) == int:
        holdtime = int(holdtime)
        if holdtime < 0 or holdtime > 65535:
            print("BGP HoldTime is Incorrect")
            sys.exit()
        else:
            return format(holdtime, '016b')
    else:
        print("BGP HoldTime is Incorrect")
        sys.exit()

def binaryRouterID(routerid):
    if type(routerid) == str:
        splitValue = routerid.split(".")
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
