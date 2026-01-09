import pandas as pd
import numpy as np
import akshare as ak

def calculate_industry_correlation(stock_df: pd.DataFrame, industry_name: str):
    """
    计算个股与行业的 Pearson 相关性
    """
    if stock_df.empty or not industry_name:
        return None
        
    try:
        # 获取行业历史行情
        ind_hist = ak.stock_board_industry_hist_em(symbol=industry_name, period="daily", adjust="qfq")
        if ind_hist.empty:
            return None
            
        # 合并数据进行相关性计算
        # 确保日期列格式一致
        stock_df['日期'] = pd.to_datetime(stock_df['日期']).dt.strftime('%Y-%m-%d')
        ind_hist['日期'] = pd.to_datetime(ind_hist['日期']).dt.strftime('%Y-%m-%d')
        
        merged = pd.merge(
            stock_df[['日期', '收盘']].rename(columns={'收盘': 'stock_close'}),
            ind_hist[['日期', '收盘']].rename(columns={'收盘': 'ind_close'}),
            on='日期'
        )
        
        if len(merged) < 30:
            return None
            
        # 计算对数收益率的相关性（比价格相关性更准确）
        merged['stock_ret'] = np.log(merged['stock_close'] / merged['stock_close'].shift(1))
        merged['ind_ret'] = np.log(merged['ind_close'] / merged['ind_close'].shift(1))
        
        # 取最近 150 天的数据计算相关性
        correlation = merged['stock_ret'].tail(150).corr(merged['ind_ret'].tail(150))
        return correlation
    except Exception:
        return None
