import requests,json,datetime,time,re
import pandas as pd

etherscan = '' # etherscanのAPIキー
polygonscan = '' # polygonscanのAPIキー
addresses = [''] # 情報が欲しいアドレスを入れる
alladdrs = addresses+[] # 自分のウォレットのアドレスを全部入れる（自分のウォレット間取引判定用）
bridge = [] # ブリッジコントラクトとのトランザクション特定用

networks = [
    {
        'chain': 'ether',
        'token': 'ETH',
        'endpoint': 'https://api.etherscan.io/api',
        #'endpoint': 'https://api-rinkeby.etherscan.io/api',
        #'endpoint': 'https://api-ropsten.etherscan.io/api',
        'params': {
            'default': {
                'module': 'account',
                'startblock': 0, 'endblock': 99999999, 'page': 1, 'offset': 999, 'sort': 'asc',
                'apikey': etherscan,
            },
            'normal': {'action': 'txlist'},
            'erc20': {'action': 'tokentx'},
            'internal': {'action': 'txlistinternal'},
        },
    },
    {
        'chain': 'polygon',
        'token': 'MATIC',
        'endpoint': 'https://api.polygonscan.com/api',
        'params': {
            'default': {
                'module': 'account',
                'startblock': 0, 'endblock': 99999999, 'page': 1, 'offset': 999, 'sort': 'asc',
                'apikey': polygonscan,
            },
            'normal': {'action': 'txlist'},
            'erc20': {'action': 'tokentx'},
            'internal': {'action': 'txlistinternal'},
        },
    },
    # {
    #     'chain': 'xdai',
    #     'token': 'DAI',
    #     'endpoint': 'https://blockscout.com/xdai/mainnet/api',
    #     'params': {
    #         'default': {
    #             'module': 'account'
    #         },
    #         'normal': {'action': 'txlist'},
    #         'erc20': {'action': 'tokentx'},
    #         'internal': None,
    #     },
    # },
]

required_keys = ['hash', 'timeStamp', 'from', 'to', 'tokenSymbol', 'value', '_in', '_out', 'TransactionFee', 'wallet', 'chain', 'notes']

def api_call(network, action, address):
    if network['params'][action] is None:
        return None

    params = dict(network['params']['default'])
    params.update(network['params'][action])
    params['address'] = address

    while True:
        response = requests.get(network['endpoint'], params=params)
        if response.ok:
            response = json.loads(response.text)
            if response['status'] != '0':
                return pd.DataFrame(response['result'])
            else:
                return None
        time.sleep(1)

def transaction_fee(df):
    fee = df['gasPrice'].astype(int) * df['gasUsed'].astype(int)
    return fee.astype('float128')/pow(10,18)

def append_required_keys(df):
    for key in required_keys:
        if key not in df.columns:
            df[key] = 0
    return df

def safe_token_symbol(k):
    return re.sub(r'[^a-zA-Z0-9]', '_', k) if k is not None else '_'

def is_myaddr(x):
    return x.lower() in list(map(lambda y: y.lower(), alladdrs))

def is_mybridge(x):
    return x.lower() in list(map(lambda y: y.lower(), bridge))

def normal_txns(network, address, txns):
    df = api_call(network, 'normal', address)
    if df is not None:
        df = append_required_keys(df.assign(
            tokenSymbol=network['token'],
            value=df['value'].astype('float128')/pow(10, 18),
            TransactionFee=transaction_fee(df),
            wallet=address, chain=network['chain']
        ))
        txns = pd.concat([txns, df.loc[:, required_keys]])
    return txns

def erc20_txns(network, address, txns):
    df = api_call(network, 'erc20', address)
    if df is not None:
        df = append_required_keys(df.assign(
            tokenSymbol=df['tokenSymbol'].apply(safe_token_symbol),
            value=df['value'].astype('float128')/pow(10, df['tokenDecimal'].astype('float128')),
            wallet=address, chain=network['chain']
        ))
        txns = pd.concat([txns, df.loc[:, required_keys]])
    return txns

def internal_txns(network, address, txns):
    df = api_call(network, 'internal', address)
    if df is not None:
        df = append_required_keys(df.assign(
            tokenSymbol=network['token'],
            value=df['value'].astype('float128')/pow(10, 18),
            wallet=address, chain=network['chain']
        ))
        txns = pd.concat([txns, df.loc[:, required_keys]])
    return txns

def all_txns(address):
    df = pd.DataFrame()
    for network in networks:
        df = normal_txns(network, address, df)
        df = erc20_txns(network, address, df)
        df = internal_txns(network, address, df)

    if df.empty == False :
        from_me = df['from'] == address
        to_me = df['to'] == address

        df.loc[from_me, '_out'] = df.loc[from_me, 'value']
        df.loc[to_me, '_in'] = df.loc[to_me, 'value']
        df.loc[to_me, 'TransactionFee'] = 0
        df.loc[df['from'].apply(is_myaddr) & df['to'].apply(is_myaddr), 'notes'] = 'Both are my wallets'
        df.loc[df['to'].apply(is_mybridge), 'notes'] = 'bridge'

        df['timeStamp'] = pd.to_datetime(df['timeStamp'].astype(int)+9*60*60, unit='s')
        df = df.sort_values(by='timeStamp', ascending=True)

    return df

def main():
    for address in addresses:
        address = address.lower()
        df = all_txns(address)

        with pd.ExcelWriter(address+'.xlsx') as excel:
            df.to_excel(excel, sheet_name='Sheet', index=False)
            if not df.empty:
                for token in list(set(df['tokenSymbol'].tolist())):
                    df_token = df[df['tokenSymbol'] == token]
                    df_token.to_excel(excel, sheet_name=token, index=False)
            excel.save()

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        pass
