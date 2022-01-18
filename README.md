# portfolio ML_limit_Strategy  
![ダウンロード (1)](https://user-images.githubusercontent.com/84313334/149931807-0aab3744-b6a1-415f-82ea-77cbf8f7d60b.png)

機械学習モデルを用いて取引戦略のリターンを予測し､  
予測をもとに取引を行うpythonプログラムです｡   
上記の画像は､バックテスト結果となっております｡  
赤が予測あり､青が予測なしのときの結果です｡  
縦軸の単位は割合です｡  

<br>

# DEMO
現在(2022/1/18(火))の損益は以下の用になっております｡  
縦軸の単位は､USDT(≒USD)です｡  
![equity and balance](https://user-images.githubusercontent.com/84313334/149875672-5db28632-9315-41e7-8353-bf55aae98afb.png)  

<br>

ディスコードサーバーにはこのような形で送信されてきます｡
<img width="567" alt="スクリーンショット 2022-01-18 14 14 49" src="https://user-images.githubusercontent.com/84313334/149875689-ef84a77e-5d49-4321-bac7-f8cb2d3cc9a9.png">

# Features
* 自動売買  
[こちら](https://jodawithforce.hatenablog.com/entry/2022/01/07/204340)で作成したモデルの別バージョンを利用します｡  
時間軸が長いのでリターン自体は減っているのですが､  
独自のロジックですので収益機会がまだ残っているのではないかと考えております｡  
* 損益の可視化  
定期的に(デフォルトでは3分)ごとに､指定のディスコードサーバーに損益グラフを送信します｡  

<br>

# Requirement

* huga 3.5.2
* hogehuga 1.0.2

# Installation

Requirementで列挙したライブラリなどのインストール方法を説明する

```bash
pip install huga_package
```

# Usage

DEMOの実行方法など、"hoge"の基本的な使い方を説明する

```bash
git clone https://github.com/hoge/~
cd examples
python demo.py
```

# Note


# Author
* 松崎 優羅
* yura3yura@gmail.com
* ブログ -> https://jodawithforce.hatenablog.com/archive/category/%E4%B8%80%E8%A6%A7

# License
None  
ソフトウェアの複製、改変、（複製物または二次的著作物の）再頒布はご遠慮いただけますと幸いです｡
