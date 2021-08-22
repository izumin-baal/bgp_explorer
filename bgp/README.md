## memo
- IOSはnetworkコマンドを打った直後にUPDATEが走るのでconsoleで入力しても経路をまとめて送ることができない点に違和感。IOS-XRはcommitが必要なのでまとめてUPDATEできるので良い。
- Ping通るところまで
    - netlink: 低レイヤー
    - pyroute2: いい感じにラッパーしてるやつ
    - executeで直 #簡単なので採用!!
    