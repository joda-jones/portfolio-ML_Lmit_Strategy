import os
import pickle
import time

class Candle:
    
    def __init__(self, timeframe: (int), file: (str)):
        #初期設定
        self.timeframe = timeframe
        self.file = file
        self.prev_ts = 0
        #ファイルからprev_tsを読み込む。ファイルがなければ作成する
        if not os.path.exists(self.file):
            with open(self.file, "wb") as f:
                self.prev_ts = 0
                pickle.dump(self.prev_ts, f)
        
    def is_candle_open(self):
        with open(self.file, "rb") as f:
            self.prev_ts = pickle.load(f)
        
        
        if time.time() > self.prev_ts + self.timeframe:
            self.prev_ts = (time.time() // self.timeframe) * self.timeframe
            with open(self.file, "wb") as f:
                pickle.dump(self.prev_ts, f)
            return True
        else:
            return False
