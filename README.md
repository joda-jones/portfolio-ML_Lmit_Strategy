# portfolio ML_limit_Strategy  
![ダウンロード (1)](https://user-images.githubusercontent.com/84313334/149931807-0aab3744-b6a1-415f-82ea-77cbf8f7d60b.png)  

機械学習モデルを用いて取引戦略のリターンを予測し､  
予測をもとに取引を行うpythonプログラムです｡   
上記の画像は､バックテスト結果となっております｡  
赤が予測あり､青が予測なしのときの結果です｡  
縦軸の単位は割合です｡  

独学未経験が作成したものですので､お見苦しい部分が多々あると思いますが､  
選考にお役立ていただければ幸いです｡  

<br>

# Features
* 自動売買  
[こちら](https://jodawithforce.hatenablog.com/entry/2022/01/07/204340)で作成したモデルの別バージョンを利用します｡  
時間軸が長いのでリターン自体は減っているのですが､  
独自のロジックですので収益機会がまだ残っているのではないかと考えております｡  
* 損益の可視化  
定期的に(デフォルトでは3分)ごとに､指定のディスコードサーバーに損益グラフを送信します｡  

<br>

# DEMO
現在(2022/1/18(火))の損益は以下の用になっております｡  
縦軸の単位は､USDT(≒USD)です｡  
![equity and balance](https://user-images.githubusercontent.com/84313334/149875672-5db28632-9315-41e7-8353-bf55aae98afb.png)  

<br>

ディスコードサーバーにはこのような形で送信されてきます｡  
<img width="567" alt="スクリーンショット 2022-01-18 14 14 49" src="https://user-images.githubusercontent.com/84313334/149875689-ef84a77e-5d49-4321-bac7-f8cb2d3cc9a9.png">

<br>

# environment & Requirement  
#### environment  
windows10   
anacondaのbase環境をコピーした仮想環境を利用しました｡  

#### Requirement  
* ccxt 1.66.50  
* discordwebhook 1.0.3  
* crypto-data-fetcher 0.0.17  
* TA-Lib 0.4.23  
* pybotters 0.9.0   
* seaborn 0.11.2  

```
pip install -r requirements.txt
```

不可能な場合は､以下をお試しください｡  
```
pip install ccxt
pip install discordwebhook
pip install pybotters
pip install seaborn  
pip install "git+https://github.com/richmanbtc/crypto_data_fetcher.git@v0.0.17#egg=crypto_data_fetcher"
```
talibに関しては､OSごとにインストールが異なり､少し煩雑ですので､[こちら](https://qiita.com/ConnieWild/items/cb50f36425a683c914d2)をご参照ください｡  


# Usage   
* bybitのapiを作成､config.iniに記述します｡  
* 環境構築
* python main.py


# Note  
### 各ファイルの概要

#### config.ini  
apiKey､apiSecretを記述するファイルです｡  

#### candle_open.py  
設定した時間足のオープンを判定するクラスを記述しています｡

#### func.py  
指定されたフォーマットのohlcvデータを渡すと､  
特徴量を作成したDFを返します｡  

#### main.py  
メインコードです｡  
* 初期設定  
    以下ループ  
* 時間足のオープン判定  
* 損益グラフ送信  
* データ取得  
* 特徴量作成  
* モデルによる予測  
* API操作による取引

[anaconda仮想環境を起動､.pyファイルをrunするバッチファイル作成方法](https://jodawithforce.hatenablog.com/)  


# Author
* 松崎 優羅
* yura3yura@gmail.com
* ブログ -> https://jodawithforce.hatenablog.com/archive/category/%E4%B8%80%E8%A6%A7

# License
None  
エッジ保護のため､ 
ソフトウェアの複製、改変、（複製物または二次的著作物の）再頒布はご遠慮いただけますと幸いです｡  
