# BGP Format
## Common Message format
- Marker: 16byte
    - OPENメッセージ,または認証が含まれていない場合は全て1
- Length: 2byte
    - BGPメッセージ全体の長さ。
    - 符号なし整数でメッセージの全長
    - 19-4096を入れる必要がある。
    - 19-byteはKEEPALIVEでCommon Message formatのみ
- Type: 1byte
    - 1-OPEN
    - 2-UPDATE
    - 3-NOTIFICATION
    - 4-KEEPALIVE

## Open Message format
- Version: 1-byte
    - BGPバージョン。お互いがサポートする最大となるまでセッションをリセットする。
- My AS: 2-byte
    -スピーカのASN
- Hold time: 2-byte
    - 符号なし整数。0からインクリメントしていく。
    - KEEPALIVE, UPDATEを受け取ると0になる
    - お互いの短い値が採用される。
    - 0の場合はリセットされないため、常に有効とされる。
- BGP Identifier: 4-byte
    - 符号なし整数
    - CiscoではRouter-IDとされる
- Opt Len: 1-byte
    - オプションの全長を表す符号なし整数。
    - 0はオプションがないことを表す
- Optional Parameteres: variable
    - オプションのパラメータリスト