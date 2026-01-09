import akshare as ak
import pandas as pd

def get_latest_profit(symbol: str):
    """
    获取最新报告期的扣非净利润
    """
    try:
        # 使用同花顺财务摘要接口
        df = ak.stock_financial_abstract_ths(symbol=symbol, indicator="主要指标")
        if df.empty:
            return "N/A", "N/A"
        
        # 排除无效数据并按报告期排序
        df = df[df['扣非净利润'] != 'False']
        if df.empty:
            return "N/A", "N/A"
            
        df_sorted = df.sort_values('报告期', ascending=False)
        latest = df_sorted.iloc[0]
        
        value = str(latest['扣非净利润'])
        period = str(latest['报告期'])
        
        return value, period
    except Exception:
        return "N/A", "N/A"
