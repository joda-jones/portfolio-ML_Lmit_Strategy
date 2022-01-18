import datetime
import pickle
import pytz
import asyncio
import os
import time
from pprint import pprint

import ccxt
import pybotters
from discordwebhook import Discord
from crypto_data_fetcher.bybit import BybitFetcher
import configparser
import joblib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

import seaborn as sns
import optuna.integration.lightgbm as lgb_o

import func
from candle_open import Candle

sns.set()

"""
初期設定の部分は要確認！

確認事項
・api
・webhook url
・file path
・features
・create_feature_df()
"""

# 初期設定
bot_name = "atr_limit_H1"
SYMBOL = "BTCUSDT"
base_lots = 0.015
max_pos = 3 # 片側の最大ポジション
mult_limit = 0.58 # 指値距離の倍率
horizon = 4 # 決済までの待機本数(1の時、次の足で決済)
buy_cut = 3 # 損切(%)  1の時１％の逆行で決済
sell_cut = 4 # 損切(%)  1の時１％の逆行で決済

# ロット処理
lots = base_lots

# discord通知用インスタンス作成
discord = Discord(url="")
discord.post(content=bot_name + "起動しました")

# APIを格納
conf = configparser.ConfigParser()
conf.read("config.ini")

apiKey = conf["bybit"]["access_key"]
secretKey = conf["bybit"]["secret_key"]

apis = {
    'bybit': [apiKey, secretKey]
}

# 特徴量のカラムの配列を設定
buy_features = ['D1_near_hi', 'D1_STOCHRSI_fastk', 'H4_hl_per_cl', 'H4_volume',
                'D1_BOP', 'NATR', 'M15_hl_per_cl', 'PPO', 'D1_TRANGE', 'H4_TRANGE',
                'H4_NATR', 'M15_NATR', 'bull_or_bear', 'D1_hl_per_cl',
                'H4_HT_PHASOR_quadrature', 'hl_per_cl']

sell_features = ['D1_BOP', 'D1_bull_or_bear', 'D1_near_hi', 'D1_hl_per_cl',
                 'D1_LINEARREG', 'D1_BETA', 'H4_SAREXT', 'H4_BBANDS_lowerband',
                 'D1_STDDEV', 'D1_volume', 'D1_CMO', 'D1_TRANGE',
                 'D1_HT_PHASOR_inphase', 'H4_STOCHRSI_fastd', 'H4_AROON_aroondown',
                 'TRIMA', 'H4_TEMA', 'H4_PLUS_DM', 'H4_ATR', 'D1_STOCHF_fastk',
                 'D1_RSI']

# modelをロード
buy_models = []
sell_models = []

#Kfoldの回数分モデルが作成されるため、モデルの数だけループして読み込む
for i in range(3):
    with open(f'models/trained_model_buy_H1_{i}.pkl', 'rb') as f:
        buy_models.append(pickle.load(f))

    with open(f'models/trained_model_sell_H1_{i}.pkl', 'rb') as f:
        sell_models.append(pickle.load(f))

# ろうそく足のオープン取得用
candle = Candle(3600, "prev_timestamp_H1.pkl")

# 通知用
candle_m5 = Candle(300, "prev_timestamp_M5.pkl")

async def main():
    while True:
        async with pybotters.Client(apis=apis, base_url='https://api.bybit.com') as client:
            
            # ろうそく足の更新を取得
            if not candle_m5.is_candle_open():
                time.sleep(1)
                continue

            # 資産履歴を記録
            r = await client.get("/v2/private/wallet/balance", params={"coin": "USDT"})

            now_equity_df = pd.DataFrame(dict(await r.json())["result"]).T
            jst = pytz.timezone('Asia/Tokyo')
            now_jst = datetime.datetime.now(tz=datetime.timezone.utc).astimezone(jst)
            now_equity_df["time"] = now_jst
            now_equity_df = now_equity_df.set_index("time")

            equity_df_file = "equity_df.pkl"
            if os.path.exists(equity_df_file):
                with open(equity_df_file, "rb") as f:    
                    equity_df = pickle.load(f)
            else:
                with open(equity_df_file, "wb") as f:
                    equity_df = now_equity_df
                    pickle.dump(now_equity_df, f)

            equity_df = pd.concat([equity_df, now_equity_df], axis=0)
            with open(equity_df_file, "wb") as f:
                pickle.dump(equity_df, f)

            # 資産曲線を描画
            equity_and_balance_file = "equity and balance.png"
            fig = plt.figure(figsize=(16, 8))
            equity_df[["equity", "wallet_balance"]] = equity_df[["equity", "wallet_balance"]].applymap(lambda x : int(x))
            equity_df["equity"].plot(label="equity")
            equity_df["wallet_balance"].plot(label="balance")
            plt.title("equity and balance")
            plt.legend()
            plt.savefig(equity_and_balance_file, bbox_inches='tight')

            with open(equity_and_balance_file, "rb") as f:
                discord.post(content=equity_and_balance_file, file={equity_and_balance_file: f })

            # ろうそく足の更新を取得
            if not candle.is_candle_open():
                time.sleep(1)
                continue
            
            # DF取得       
            memory = joblib.Memory('/tmp/bybit_fetcher_cache', verbose=0)
            bybit = ccxt.bybit()
            fetcher = BybitFetcher(ccxt_client=bybit)
            days = 33
            df = fetcher.fetch_ohlcv(
                start_time=int(time.time()) - days*3600*24,
                market='BTCUSDT', # 市場のシンボルを指定
                interval_sec=5 * 60, # 足の間隔を秒単位で指定。この場合は5分足
            )

            df.columns = ["op", "hi", "lo", "cl", "volume"]
            df = func.create_feature_df(df)

            # シグナル生成　pred>0でエントリー
            buy_pred = 0
            sell_pred = 0

            for (buy_model, sell_model) in zip(buy_models, sell_models):
                buy_pred += buy_model.predict(df[buy_features].iloc[-1])
                sell_pred += sell_model.predict(df[sell_features].iloc[-1])

            print(buy_pred, sell_pred)
            discord.post(content=f"buy_pred={buy_pred}    sell_pred={sell_pred}")

            # 指値価格設定
            limit_price = df["H4_hl_per_cl"][-1] * df["cl"][-1] * mult_limit
            buy_limit = round(df["cl"][-1] - limit_price, 1)
            sell_limit = round(df["cl"][-1] + limit_price, 1)

            buy_sl = round(buy_limit * (1 - buy_cut/100), 1)
            sell_sl = round(sell_limit * (1 + sell_cut/100), 1)

            print(f"sell_sl   {sell_sl}")

            # ポジションIDを取得　同時に　注文キャンセル
            resps = await asyncio.gather(client.post("/private/linear/order/cancel-all", data={'symbol': 'BTCUSDT'}),
                                         client.get('/private/linear/position/list', params={'symbol': 'BTCUSDT'}),
                                         client.get('/private/linear/trade/execution/list', params={'symbol': 'BTCUSDT'})
                                        )
            canceled, position, record = await asyncio.gather(*[r.json() for r in resps])

            df_pos = pd.DataFrame(dict(position)["result"])
            record_df = pd.DataFrame(dict(record)["result"]["data"])

            # 現在のポジションサイズを取得
            opening_buy_size = df_pos.loc[0]["size"]
            opening_sell_size = df_pos.loc[1]["size"]
            
            # 決済可能時間
            # timestampが、現在時刻（hour）になるように変換
            border_time = (time.time() // 3600) * 3600
            border_time -= (horizon - 1) * 3600
            
            if opening_buy_size > 0:
                # 買い
                # 履歴から、オープン注文を抽出
                record_df_buy_open = record_df.query("side=='Buy' & closed_size==0 & exec_type=='Trade'")
                # 執行されたsizeをcumsum
                record_df_buy_open["cumsum"] = record_df_buy_open["exec_qty"].cumsum()
                # cumsumが現在のポジション数になるところ 即ち、最も古いオープンポジションの執行からのDFを作成
                record_df_buy_open = record_df_buy_open[record_df_buy_open["cumsum"]<=opening_buy_size]
                # trade_timeカラムで抽出
                record_df_buy_open = record_df_buy_open[record_df_buy_open["trade_time"]<border_time]
                # 現在オープンしている注文の中で、決済注文を入れてもいいポジション数 決済可能なポジションがないときエラーになるので、処理を入れておく
                if record_df_buy_open.shape[0]==0:
                    opening_buy_size = 0
                else:
                    opening_buy_size = record_df_buy_open["cumsum"].iloc[-1]
            
            if opening_sell_size > 0:
                # 売り
                # 履歴から、オープン注文を抽出
                record_df_sell_open = record_df.query("side=='Sell' & closed_size==0 & exec_type=='Trade'")
                # 執行されたsizeをcumsum
                record_df_sell_open["cumsum"] = record_df_sell_open["exec_qty"].cumsum()
                # cumsumが現在のポジション数になるところ 即ち、最も古いオープンポジションの執行からのDFを作成
                record_df_sell_open = record_df_sell_open[record_df_sell_open["cumsum"]<=opening_sell_size]
                # trade_timeカラムで抽出
                record_df_sell_open = record_df_sell_open[record_df_sell_open["trade_time"]<border_time]
                # 現在オープンしている注文の中で、決済注文を入れてもいいポジション数 決済可能なポジションがないときエラーになるので、処理を入れておく
                if record_df_sell_open.shape[0]==0:
                    opening_sell_size = 0
                else:
                    opening_sell_size = record_df_sell_open["cumsum"].iloc[-1]
            
            # ポジション数保存
            buy_num = opening_buy_size / lots
            sell_num = opening_sell_size / lots

            print(f"buy_num={buy_num}   sell_num={sell_num}")
            
            # discord通知用変数
            contents = ""

            # 決済買い注文　→　現在の売りポジションのsizeを入力
            if opening_sell_size>0:
                contents += f"buy limit at {buy_limit} for close..........\n"
                close_buy_data = {'symbol': 'BTCUSDT',
                                  'side': "Buy",
                                  'order_type': 'Limit',
                                  'price': buy_limit,
                                  'qty': opening_sell_size,
                                  'close_on_trigger': False,
                                  'reduce_only': True,
                                  'time_in_force': "PostOnly"}

                r = await client.post('/private/linear/order/create', data=close_buy_data)

            # 決済売り注文　→　現在の買いポジションのsizeを入力
            if opening_buy_size>0:
                contents += f"sell limit at {sell_limit} for close..........\n"
                close_sell_data = {'symbol': 'BTCUSDT',
                                   'side': "Sell",
                                   'order_type': 'Limit',
                                   'price': sell_limit,
                                   'qty': opening_buy_size,
                                   'close_on_trigger': False,
                                   'reduce_only': True,
                                   'time_in_force': "PostOnly"}

                r = await client.post('/private/linear/order/create', data=close_sell_data)

            # 新規買い注文
            if buy_pred>0 and buy_num<max_pos:
                contents += f"new buy limit at {buy_limit} is posting..........\n"
                new_buy_data = {'symbol': 'BTCUSDT',
                                'side': "Buy",
                                'order_type': 'Limit',
                                'price': buy_limit,
                                'stop_loss': buy_sl,
                                'qty': lots,
                                'close_on_trigger': False,
                                'reduce_only': False,
                                'time_in_force': "PostOnly"}

                r = await client.post('/private/linear/order/create', data=new_buy_data)
                pprint(await r.json())

            # 新規売り注文
            if sell_pred>0 and sell_num<max_pos:
                contents += f"new sell limit at {sell_limit} is posting..........\n"
                new_sell_data = {'symbol': 'BTCUSDT',
                                 'side': "Sell",
                                 'order_type': 'Limit',
                                 'price': sell_limit,
                                 'stop_loss': sell_sl,
                                 'qty': lots,
                                 'close_on_trigger': False,
                                 'reduce_only': False,
                                 'time_in_force': "PostOnly"}

                r = await client.post('/private/linear/order/create', data=new_sell_data)
                pprint(await r.json())  

            discord.post(content=contents)

            # 待機(60秒)
            print(bot_name)
            await asyncio.sleep(60.0)


# 非同期メイン関数を実行(Ctrl+Cで終了)
if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass