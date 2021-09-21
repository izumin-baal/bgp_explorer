import subprocess

def into_routingtable(addr, prefix, next_hop):
    addrprefix = addr + '/' + prefix
    args = ['ip', 'route', 'add', addrprefix, 'via', next_hop]
    print("\033[33m", "ip route add ", addrprefix, "via", next_hop, "\033[0m", 'proto', 'bgp')
    try:
        res = subprocess.check_output(args)
    except:
        print('ip route add error.')

def del_routingtable(addr, prefix, next_hop):
    addrprefix = addr + '/' + prefix
    args = ['ip', 'route', 'del', addrprefix, 'via', next_hop]
    print("\033[35m", "ip route del ", addrprefix, "via", next_hop, "\033[0m")
    try:
        res = subprocess.check_output(args)
    except:
        print('ip route del error.')

def into_routingtable_ecmp(addrprefix, ecmp_nexthop_array):
    try:
        subprocess.check_output(['ip', 'route', 'del', addrprefix])
    except:
        pass
    args = ['ip', 'route', 'add', addrprefix]
    for i in range(len(ecmp_nexthop_array)):
        args.extend(['nexthop', 'via', ecmp_nexthop_array[i]], 'proto', 'bgp')
    print("\033[33m", *args, "\033[0m")
    try:
        res = subprocess.check_output(args)
    except:
        print('ip route add(ecmp) error.')