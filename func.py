import configparser

import numpy as np
import pandas as pd
import pytz
import talib
import pybotters


conf = configparser.ConfigParser()
conf.read("config.ini")

apiKey = conf["bybit"]["access_key"]
secretKey = conf["bybit"]["secret_key"]

apis = {
    'bybit': [apiKey, secretKey]
}

client = pybotters.Client(apis=apis, base_url='https://api.bybit.com')

def create_feature_df(df):
    """
    特徴量dfを作成する

    Returns
    -------
    dataframe
        features dataframe 
    """
  
    d_ohlc = {'op': 'first',
              'hi': 'max',
              'lo': 'min',
              'cl': 'last',
              'volume': 'sum'}

    M15_df = df.resample('15T').agg(d_ohlc)
    # M30_df = df.resample('30T').agg(d_ohlc)
    H1_df = df.resample('1H').agg(d_ohlc)
    H4_df = df.resample('4H').agg(d_ohlc)
    D1_df = df.resample('D').agg(d_ohlc)

    # 何本連続陽線か
    def count_continuous_values(df, column_name):
        y = df[column_name]
        df[column_name + "_counum"] = y.groupby((y != y.shift()).cumsum()).cumcount() + 1

        return df

    def cal_candle_features(df):
        df["hl_per_cl"] = (df["hi"] - df["lo"])/df["cl"]
        df["near_hi"] = np.where((df["hi"] - df["cl"])>(df["cl"] - df["lo"]), 1, 0)
        df["near_lo"] = np.where((df["hi"] - df["cl"])<(df["cl"] - df["lo"]), 1, 0)
        df["bull_or_bear"] = np.where((df["op"]<df["cl"]), 1, 0)
        df = count_continuous_values(df, "bull_or_bear")

    # cal_candle_features(df)
    cal_candle_features(M15_df)
    # cal_candle_features(M30_df)
    cal_candle_features(H1_df)
    cal_candle_features(H4_df)
    cal_candle_features(D1_df)

    def calc_features(df):
        op = df['op']
        high = df['hi']
        low = df['lo']
        close = df['cl']
        volume = df['volume']
        
        hilo = (df['hi'] + df['lo']) / 2
        df['BBANDS_upperband'], df['BBANDS_middleband'], df['BBANDS_lowerband'] = talib.BBANDS(close, timeperiod=15, nbdevup=2, nbdevdn=2, matype=0)
        df['BBANDS_lowerband'] -= hilo
        df['TEMA'] = talib.TEMA(close, timeperiod=30) - hilo
        df['TRIMA'] = talib.TRIMA(close, timeperiod=30) - hilo
        df['AROON_aroondown'], df['AROON_aroonup'] = talib.AROON(high, low, timeperiod=14)
        df['BOP'] = talib.BOP(op, high, low, close)
        df['PLUS_DM'] = talib.PLUS_DM(high, low, timeperiod=14)
        df['RSI'] = talib.RSI(close, timeperiod=14)
        df['STOCHF_fastk'], df['STOCHF_fastd'] = talib.STOCHF(high, low, close, fastk_period=5, fastd_period=3, fastd_matype=0)
        df['STOCHRSI_fastk'], df['STOCHRSI_fastd'] = talib.STOCHRSI(close, timeperiod=14, fastk_period=5, fastd_period=3, fastd_matype=0)
        df['ATR'] = talib.ATR(high, low, close, timeperiod=14)
        df['NATR'] = talib.NATR(high, low, close, timeperiod=14)
        df['HT_PHASOR_inphase'], df['HT_PHASOR_quadrature'] = talib.HT_PHASOR(close)
        df['TRANGE'] = talib.TRANGE(high, low, close)
        df['BETA'] = talib.BETA(high, low, timeperiod=5)
        df['LINEARREG'] = talib.LINEARREG(close, timeperiod=14) - close
        df['STDDEV'] = talib.STDDEV(close, timeperiod=5, nbdev=1)
        df["CMO"] = talib.CMO(close, timeperiod=14)
        df["ROC"] = talib.ROC(close, timeperiod=14)
        df["PPO"] = talib.PPO(close, fastperiod=12, slowperiod=26, matype=0)
        df["SAREXT"] = talib.SAREXT(high, low)
        
        return df
    
    # メインにするdf
    df = H1_df

    df = df.dropna()
    M15_df = M15_df.dropna()
    # M30_df = M30_df.dropna()
    # H1_df = H1_df.dropna() 
    H4_df = H4_df.dropna()
    D1_df = D1_df.dropna()

    drop_cols = ["op", "hi", "lo", "cl"]
    
    df = calc_features(df)
    M15_df = calc_features(M15_df).drop(drop_cols, axis=1).add_prefix("M15_")
    H4_df = calc_features(H4_df).drop(drop_cols, axis=1).add_prefix("H4_")
    D1_df = calc_features(D1_df).drop(drop_cols, axis=1).add_prefix("D1_")

    df = pd.merge(df, M15_df, how="left", left_index=True, right_index=True)
    df = pd.merge(df, H4_df, how="left", left_index=True, right_index=True)
    df = pd.merge(df, D1_df, how="left", left_index=True, right_index=True)

    df = df.fillna(method="ffill")

    # 曜日を特徴量に変換
    df["open_week"] = df.index
    df["open_week"] = df["open_week"].map(lambda x: pd.Timestamp(x.astimezone(pytz.timezone("Asia/Tokyo"))))
    df["open_week"] = df["open_week"].map(lambda x: x.strftime("%A"))
    df = pd.get_dummies(df, columns=["open_week"])
    
    return df