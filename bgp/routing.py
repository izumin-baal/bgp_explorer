import subprocess

def into_routingtable(addr, prefix, next_hop):
    addrprefix = addr + '/' + prefix
    args = ['ip', 'route', 'add', addrprefix, 'via', next_hop]
    print("\033[33m", "ip route add ", addrprefix, "via", next_hop, "\033[0m")
    try:
        res = subprocess.check_output(args)
    except:
        print('error.')

def del_routingtable(addr, prefix, next_hop):
    addrprefix = addr + '/' + prefix
    args = ['ip', 'route', 'del', addrprefix, 'via', next_hop]
    print("\033[35m", "ip route del ", addrprefix, "via", next_hop, "\033[0m")
    try:
        res = subprocess.check_output(args)
    except:
        print('error.')