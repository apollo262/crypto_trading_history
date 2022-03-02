# これは何？
ブロックチェーンエクスプローラーから取引履歴をまとめて抽出するツールです。
yuk_t様のコードを参考にさせていただきました。
https://qiita.com/yuk_t/items/578c5e6d0dad4acc10e5
# setup
```
python3 -m venv venv/ &&
source venv/bin/activate &&
pip install --upgrade pip &&
pip install -r requirements.txt
```
# config
```
etherscan = 'xxxxxxxxxxxxxxx' # etherscanのAPIキー
polygonscan = 'xxxxxxxxxxxxx' # polygonscanのAPIキー
addresses = ['xxxxxxxxxxxxx'] # 情報が欲しいアドレスを入れる
alladdrs = addresses+['xxxx'] # 自分のウォレットのアドレスを全部入れる（自分のウォレット間取引判定用）
bridge = ['xxxxxxxxxxxxxxxx'] # ブリッジコントラクトとのトランザクション特定用
```
# run
```
python crypto_trading_history.py
```
# todo
- なぜかテストネットに接続しようとするとエラーになってしまいます。
- blockscout.comにERC20のリクエストを投げると落ちてしまう場合があるためコメントアウトしています。
