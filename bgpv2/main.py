import sys
import socket
import yaml
import threading
import time
import bgpformat
import rw
import os

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

peer_state = {}

class peerState(threading.Thread):
    def __init__(self, neighborip, remoteas, nexthop):
            self.neighborip = neighborip
            self.remoteas = remoteas
            self.state = BGP_STATE_IDLE
            #self.mode = mode

    def run(self):
        while True:
            self.stateMachine()

    def stateMachine(self):
        if self.state == BGP_STATE_IDLE:
            self.tcpNego()
        elif self.state == BGP_STATE_CONNECT:
            self.open()
        elif self.state == BGP_STATE_ACTIVE:
            print('Neighbor ' + self.neighborip + ' State Active...')
            time.sleep(20)
            pass
        elif self.state == BGP_STATE_OPENSENT:
            self.opensent()
        elif self.state == BGP_STATE_OPENCONFIRM:
            self.openconfirm()
        elif self.state == BGP_STATE_ESTABLISHED:
            self.established()
        else:
            pass

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
        th[i] = peerState(neighborip, remoteas, nexthop)
    try:
        while True:
            pass
    except KeyboardInterrupt:
        rw.del_all()
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
