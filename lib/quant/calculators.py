import pandas as pd
import numpy as np

def calculate_macd(df, fast=12, slow=26, signal=9):
    """
    计算 MACD 指标
    """
    if len(df) < slow:
        return None
    
    # 计算 EMA
    exp1 = df['收盘'].ewm(span=fast, adjust=False).mean()
    exp2 = df['收盘'].ewm(span=slow, adjust=False).mean()
    
    macd = exp1 - exp2
    signal_line = macd.ewm(span=signal, adjust=False).mean()
    hist = macd - signal_line
    
    return pd.DataFrame({
        'macd': macd,
        'signal': signal_line,
        'hist': hist
    })

def check_macd_golden_cross(df):
    """
    检查今日是否发生 MACD 金叉
    金叉定义：昨日 MACD <= Signal 且 今日 MACD > Signal
    """
    if len(df) < 2:
        return False
        
    macd_data = calculate_macd(df)
    if macd_data is None:
        return False
        
    # 获取最后两日的数据
    curr_macd = macd_data['macd'].iloc[-1]
    curr_signal = macd_data['signal'].iloc[-1]
    prev_macd = macd_data['macd'].iloc[-2]
    prev_signal = macd_data['signal'].iloc[-2]
    
    # 金叉判定
    return prev_macd <= prev_signal and curr_macd > curr_signal

def check_macd_zero_golden_cross(df):
    """
    检查今日是否发生 MACD “零下金叉”
    判定条件：
    1. 金叉产生：昨日 DIFF <= DEA，且今日 DIFF > DEA
    2. 处于零下：今日的 DIFF 和 DEA 值都必须小于 0
    3. 柱状图翻红：MACD 柱状值 (Histogram) 由负转正
    """
    if len(df) < 2:
        return False
        
    macd_data = calculate_macd(df)
    if macd_data is None:
        return False
        
    # 获取最后两日的数据
    # diff -> macd, dea -> signal
    curr_diff = macd_data['macd'].iloc[-1]
    curr_dea = macd_data['signal'].iloc[-1]
    curr_hist = macd_data['hist'].iloc[-1]
    
    prev_diff = macd_data['macd'].iloc[-2]
    prev_dea = macd_data['signal'].iloc[-2]
    prev_hist = macd_data['hist'].iloc[-2]
    
    # 1. 金叉判定
    is_golden_cross = prev_diff <= prev_dea and curr_diff > curr_dea
    
    # 2. 零下判定
    is_below_zero = curr_diff < 0 and curr_dea < 0
    
    return is_golden_cross and is_below_zero

def check_ma_trend_up(df, window=5):
    """
    检查 MA5 是否勾头向上
    定义：今日 MA5 > 昨日 MA5
    """
    if len(df) < window + 1:
        return False
        
    ma = df['收盘'].rolling(window=window).mean()
    return ma.iloc[-1] > ma.iloc[-2]

def check_bottom_divergence(df, window=60):
    """
    检查是否存在底背离
    底背离定义：股价创新低，但 MACD 指标未创新低（甚至回升）
    简单逻辑：寻找最近两个波谷进行对比
    """
    if len(df) < window:
        return False
        
    macd_data = calculate_macd(df)
    if macd_data is None:
        return False
        
    macd = macd_data['macd']
    price = df['收盘']
    
    # 寻找局部低点 (波谷)
    def find_troughs(series, n=5):
        troughs = []
        for i in range(n, len(series) - n):
            if all(series.iloc[i] <= series.iloc[i-j] for j in range(1, n+1)) and \
               all(series.iloc[i] <= series.iloc[i+j] for j in range(1, n+1)):
                troughs.append(i)
        return troughs

    price_troughs = find_troughs(price)
    if len(price_troughs) < 2:
        return False
        
    # 获取最近两个价格波谷
    last_idx = price_troughs[-1]
    prev_idx = price_troughs[-2]
    
    # 底背离条件：
    # 1. 价格：当前波谷价格 < 前一波谷价格
    # 2. MACD：当前波谷 MACD > 前一波谷 MACD
    if price.iloc[last_idx] < price.iloc[prev_idx] and \
       macd.iloc[last_idx] > macd.iloc[prev_idx]:
        # 确保最近的波谷距离现在不要太远 (比如在最近 10 天内)
        if (len(df) - 1 - last_idx) <= 10:
            return True
            
    return False
