import numpy as np
import pandas as pd
import akshare as ak

def calculate_hv(df: pd.DataFrame, window: int = 20):
    """
    计算历史年化波动率 (HV)
    """
    if df is None or len(df) < window + 1:
        return None
    try:
        # 确保收盘价是数值型
        prices = pd.to_numeric(df['收盘'], errors='coerce').dropna()
        # 计算对数收益率
        log_returns = np.log(prices / prices.shift(1))
        # 计算滚动标准差并年化
        vol = log_returns.rolling(window=window).std() * np.sqrt(252)
        return vol.iloc[-1]
    except Exception:
        return None

def analyze_liquidity(symbol: str):
    """
    分析流动性与盘口深度
    """
    try:
        # 获取五档委买委卖
        tick_data = ak.stock_bid_ask_em(symbol=symbol)
        
        ask_vols = [f'sell_{i}_vol' for i in range(1, 6)]
        bid_vols = [f'buy_{i}_vol' for i in range(1, 6)]
        
        total_ask = tick_data[tick_data['item'].isin(ask_vols)]['value'].sum()
        total_bid = tick_data[tick_data['item'].isin(bid_vols)]['value'].sum()
        
        # 评分逻辑：挂单量大于 10000 手视为充裕（根据实际市场情况可调整）
        assessment = "充裕" if (total_ask + total_bid) > 20000 else "中/低"
        
        return {
            "bid_depth": int(total_bid),
            "ask_depth": int(total_ask),
            "score": assessment
        }
    except Exception:
        return {
            "total_ask_depth": 0,
            "total_bid_depth": 0,
            "assessment": "未知"
        }
