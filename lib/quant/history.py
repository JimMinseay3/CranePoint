import akshare as ak
import pandas as pd
from datetime import datetime, timedelta

def get_history_detail(symbol: str, days: int = 30):
    """
    获取最近 30 个交易日的详细行情
    """
    try:
        end_date = datetime.now().strftime("%Y%m%d")
        start_date = (datetime.now() - timedelta(days=days*2)).strftime("%Y%m%d") # 多取一点以保证有30个交易日
        
        df = ak.stock_zh_a_hist(symbol=symbol, period="daily", start_date=start_date, end_date=end_date, adjust="qfq")
        if df.empty:
            return pd.DataFrame()
            
        # 仅保留最近 30 行
        df = df.tail(days).sort_values('日期', ascending=False)
        # 强制将日期转换为字符串，防止 JSON 序列化失败
        df['日期'] = df['日期'].astype(str)
        return df
    except Exception:
        return pd.DataFrame()
