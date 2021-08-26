import pandas as pd
import routing as rt
from pandas.core.frame import DataFrame

debug = True

def into_bgptable(addrprefix, attributeArray):
    # 初期化
    address = None
    prefix = None
    next_hop = None
    as_path = None
    community = None
    df = pd.read_csv('data/bgp_table.csv', dtype=object ,encoding='utf_8')
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
        if addrprefix == p:
            # 書き換え処理
            df.at[cnt, 'address'] = address
            df.at[cnt, 'prefix'] = prefix
            df.at[cnt, 'next_hop'] = next_hop
            df.at[cnt, 'as_path'] = as_path
            df.at[cnt, 'community'] = community
            flag = False
            df.to_csv('data/bgp_table.csv', mode='w', index=False)
            # add route
            rt.into_routingtable(address, prefix, next_hop)
            break
    if flag:
        #新規追加
        data = pd.DataFrame([[address, prefix, next_hop, as_path, community]], columns=['address', 'prefix', 'next_hop', 'as_path', 'community'])
        data.to_csv('data/bgp_table.csv', mode='a', index=False, header=False)
        rt.into_routingtable(address, prefix, next_hop)
    if debug:
        print("######### BGP_TABLE.csv #########")
        df = pd.read_csv('data/bgp_table.csv', dtype=object ,encoding='utf_8')
        print(df)
        print("#################################")

def del_from_bgptable(addrprefix, ip):
    df = pd.read_csv('data/bgp_table.csv', dtype=object ,encoding='utf_8')
    address, prefix = addrprefix.split('/')
    for cnt,i in enumerate(df.itertuples()):
        p = i.address +  '/' + i.prefix
        if addrprefix == p:
            if str(ip) == str(i.next_hop):
                # 削除処理
                df.drop(cnt,inplace=True)
                df.to_csv('data/bgp_table.csv', mode='w', index=False)
                rt.del_routingtable(address, prefix, ip)
                break
    if debug:
        print("######### BGP_TABLE.csv #########")
        print(df)
        print("#################################")