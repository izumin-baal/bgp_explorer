import pandas as pd
from pandas.core.frame import DataFrame

debug = True

def into_bgptable(addrprefix, next_hop=None, as_path=None, community=None):
    df = pd.read_csv('bgp_table.csv', dtype=object ,encoding='utf_8')
    flag = True
    address, prefix = addrprefix.split('/')
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
            df.to_csv('bgp_table.csv', mode='w', index=False)
            print('match')
            break
    if flag:
        #新規追加
        data = pd.DataFrame([[address, prefix, next_hop, as_path, community]], columns=['address', 'prefix', 'next_hop', 'as_path', 'community'])
        data.to_csv('bgp_table.csv', mode='a', index=False, header=False)
    if debug:
        print("######### BGP_TABLE.csv #########")
        df = pd.read_csv('bgp_table.csv', dtype=object ,encoding='utf_8')
        print(df)
        print("#################################")

def del_from_bgptable(addrprefix):
    df = pd.read_csv('bgp_table.csv', dtype=object ,encoding='utf_8')
    address, prefix = addrprefix.split('/')
    for cnt,i in enumerate(df.itertuples()):
        p = i.address +  '/' + i.prefix
        if addrprefix == p:
            # 削除処理
            df.drop(cnt,inplace=True)
            df.to_csv('bgp_table.csv', mode='w', index=False)
            break
    if debug:
        print("######### BGP_TABLE.csv #########")
        print(df)
        print("#################################")