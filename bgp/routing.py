import subprocess

def into_routingtable(addr, prefix, next_hop):
    addrprefix = addr + '/' + prefix
    args = ['ip', 'route', 'add', addrprefix, 'via', next_hop]
    try:
        res = subprocess.check_output(args)
    except:
        print('error.')

def del_routingtable(addr, prefix, next_hop):
    addrprefix = addr + '/' + prefix
    args = ['ip', 'route', 'del', addrprefix, 'via', next_hop]
    try:
        res = subprocess.check_output(args)
    except:
        print('error.')