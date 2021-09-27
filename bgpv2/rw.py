from numpy import add
import random
import time
import pandas as pd
import routing as rt
import yaml
from pandas.core.frame import DataFrame

debug = True

with open('config.yaml', 'r') as yml:
    config = yaml.safe_load(yml)
MYASN = config['bgp']['parameter']['MyASN']

def into_bgptable(addrprefix, attributeArray):
    # 初期化
    address = None
    prefix = None
    next_hop = None
    as_path = None
    community = None
    df = pd.read_csv('../data/bgp_table.csv', dtype=object ,encoding='utf_8')
    flag = True
    address, prefix = addrprefix.split('/')
    if 'next_hop' in attributeArray:
        next_hop = attributeArray['next_hop']
    if 'as_path' in attributeArray:
        as_path = " ".join([str(_) for _ in attributeArray['as_path']])
    if 'community' in attributeArray:
        community = attributeArray['community']
    for cnt,i in enumerate(df.itertuples()):
        p = i.address +  '/' + i.prefix
        n = i.next_hop
        if addrprefix == p:
            if next_hop == n:
                # 書き換え処理
                df.at[cnt, 'address'] = address
                df.at[cnt, 'prefix'] = prefix
                df.at[cnt, 'next_hop'] = next_hop
                df.at[cnt, 'as_path'] = as_path
                df.at[cnt, 'community'] = community
                flag = False
                df.to_csv('../data/bgp_table.csv', mode='w', index=False)
                # add route
                Flaginto = True
                for asn in as_path.split(" "):
                    # BGPLOOP
                    if int(asn) == MYASN:
                        if debug:
                            print("!!!!!!!!!!!!!!!!!!")
                            print("Loop route")
                            print("!!!!!!!!!!!!!!!!!!")
                        Flaginto = False
                if Flaginto:
                    check_ecmp(addrprefix)
                break
    if flag:
        #新規追加
        data = pd.DataFrame([[address, prefix, next_hop, as_path, community]], columns=['address', 'prefix', 'next_hop', 'as_path', 'community'])
        Flaginto = True
        for asn in as_path.split(" "):
            # BGPLOOP
            if int(asn) == MYASN:
                if debug:
                    print("!!!!!!!!!!!!!!!!!!")
                    print("Loop route")
                    print("!!!!!!!!!!!!!!!!!!")
                Flaginto = False
        if Flaginto:
            data.to_csv('../data/bgp_table.csv', mode='a', index=False, header=False)
            check_ecmp(addrprefix)
    if debug:
        print("######### BGP_TABLE.csv #########")
        df = pd.read_csv('../data/bgp_table.csv', dtype=object ,encoding='utf_8')
        print(df)
        print("#################################")

def del_from_bgptable(addrprefix, ip):
    df = pd.read_csv('../data/bgp_table.csv', dtype=object ,encoding='utf_8')
    address, prefix = addrprefix.split('/')
    for cnt,i in enumerate(df.itertuples()):
        p = i.address +  '/' + i.prefix
        if addrprefix == p:
            if str(ip) == str(i.next_hop):
                # 削除処理
                df.drop(cnt,inplace=True)
                df.to_csv('../data/bgp_table.csv', mode='w', index=False)
                check_ecmp(addrprefix)
                break
    if debug:
        print("######### BGP_TABLE.csv #########")
        print(df)
        print("#################################")

def del_all():
    print("############# init #############")
    df = pd.read_csv('../data/bgp_table.csv', dtype=object ,encoding='utf_8')
    for cnt,i in enumerate(df.itertuples()):
        # 削除処理
        addrprefix = str(df.at[cnt, 'address']) + '/' + str(df.at[cnt, 'prefix'])
        rt.del_routingtable(addrprefix)
        df.drop(cnt,inplace=True)
        df.to_csv('../data/bgp_table.csv', mode='w', index=False)
    print("################################")

def check_ecmp(addrprefix):
    time.sleep(random.random(2))
    df = pd.read_csv('../data/bgp_table.csv', dtype=object ,encoding='utf_8')
    ecmp_nexthop_array = []
    for cnt,i in enumerate(df.itertuples()):
        p = i.address +  '/' + i.prefix
        if addrprefix == p:
            ecmp_nexthop_array.append(i.next_hop)
    if len(ecmp_nexthop_array) > 1:
        rt.into_routingtable_ecmp(addrprefix, ecmp_nexthop_array)
    elif len(ecmp_nexthop_array) == 1:
        rt.into_routingtable(addrprefix, ecmp_nexthop_array[0])
    else:
        rt.del_routingtable(addrprefix)