# Pixin wallet: Bitcoin, altcoin Wallet written in PyQt
A Bitcoin and altcoin wallet written in python and qt. The wallet use [Mixin Network](https://mixin.one) to hold many cryptocurrency and keep Mixin Network account key file on your PC intead of cloud. 

The generated account keyfile is a text file with filename "xxx.pixinkey". Your can import the content to [mixinlight](https://mixinlight.github.io) and [mixwallet](https://github.com/over140/mixwallet)

[Developer resource](https://github.com/awesome-mixin-network/mixin_network_sdk_resource) of Mixin Network.

## Try to be "Batteries Included" 
### Having an instant cryptocurrency exchange
[ExinCore](https://github.com/ExinOne/ExinCore) is a secure and instant cryptocurrency exchange build on Mixin Network. Just pay to ExinCore, Exin will send asset to your wallet in 2 seconds.
### Having a decentralized exchange
[OceanOne](http://github.com/mixinnetwork/oceanone) is a decentralized exchange build on Mixin Network. Pay to OceanOne to sell your asset, OceanOne will send asset to your wallet after matched your order.

OceanOne is great because: 
1. List any asset supported by Mixin Network. 13 blockchain asset, Any ERC20, EOS token, TRC10 token. 
2. Asset are sent to your wallet in 1 second. 
3. NO register process. NO KYC.
4. Open Source

## Clone repo to computer
```bash
git clone https://github.com/myrual/pixinwallet.git 
cd pixinwallet
```

## create python env

```bash
python3 -m venv ./
```

Active the env now
```bash
source ./bin/activate
```

## Install required packages by "virtual environment"

Use pip to upgrade pip itself, and install required packages.
```bash
pip install --upgrade pip
pip install -r requirements_wallet_api.txt
pip install -r requirements_pyqt.txt
```

Open wallet file
![](https://github.com/myrual/pixinwallet/raw/master/open_wallet_file.png)

Show balance
![](https://github.com/myrual/pixinwallet/blob/master/balance_screen.png)

Instant trade on ExinCore
![](https://github.com/myrual/pixinwallet/blob/master/exin_exchange_screen.png)
Trade asset on OceanOne
![](https://github.com/myrual/pixinwallet/raw/master/OceanOne_Screen.png)


### Generate standalone macOS app by pyinstaller
Install pyinstaller
```bash
pip install pyinstaller
```
Edit pixinwallet.spec version number

and generate standalone app in dist folder
```bash
pyinstaller --onefile --windowed pixinwallet.spec
```

