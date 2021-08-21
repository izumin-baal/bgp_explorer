import pandas as pd
from pandas.core.frame import DataFrame

def into_bgptable(prefixaddr, next_hop=None, as_path=None, community=None):
    df = pd.read_csv('bgp_table.csv', dtype=object ,encoding='utf_8')
    flag = True
    address, prefix = prefixaddr.split('/')
    for i in df.itertuples():
        p = i.address +  '/' + i.prefix
        if prefixaddr == p:
            # 書き換え処理
            df.iloc[0] = [address, prefix, next_hop, as_path, community]
            df.to_csv('bgp_table.csv', mode='w', index=False)
            flag = False
            break
    if flag:
        #新規追加
        data = pd.DataFrame([[address, prefix, next_hop, as_path, community]], columns=['address', 'prefix', 'next_hop', 'as_path', 'community'])
        data.to_csv('bgp_table.csv', mode='a', index=False, header=False)

def del_from_bgptable(addrprefix):
    print('del()')
    df = pd.read_csv('bgp_table.csv', dtype=object ,encoding='utf_8')
    address, prefix = addrprefix.split('/')
    for cnt,i in enumerate(df.itertuples()):
        p = i.address +  '/' + i.prefix
        if addrprefix == p:
            # 削除処理
            print(cnt)
            df.drop(cnt,inplace=True)
            print(df)
            df.to_csv('bgp_table.csv', mode='w', index=False)
            print('match')
            break