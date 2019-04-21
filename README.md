# Pixin wallet: Bitcoin, altcoin Wallet written in PyQt
A Bitcoin and altcoin wallet written in python and qt. The wallet use [Mixin Network](https://mixin.one) to hold many cryptocurrency and keep Mixin Network account key file on your PC intead of cloud. 

## Try to be "Batteries Included" 
### Having an instant cryptocurrency exchange
[ExinCore](https://github.com/ExinOne/ExinCore) is a secure and instant cryptocurrency exchange build on Mixin Network. Just pay to ExinCore, Exin will send asset to your wallet in 2 seconds.
### Having an decentralized exchange to list ANY asset
[OceanOne](http://github.com/mixinnetwork/oceanone) is a decentralized exchange build on Mixin Network. Pay to OceanOne to sell your asset, OceanOne will send asset to your wallet after matched your order.

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
