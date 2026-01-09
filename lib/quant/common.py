import os
import akshare as ak
import pandas as pd
from datetime import datetime, timedelta

def get_target_dir(symbol: str, symbol_name: str = "", base_dir: str = "data"):
    """
    获取或创建标的的归档目录：base_dir/代码_简称
    """
    if not symbol_name:
        # 如果没提供名称，尝试实时获取
        try:
            info = ak.stock_individual_info_em(symbol=symbol)
            name_res = info[info['item'] == '股票简称']['value'].values
            symbol_name = name_res[0] if len(name_res) > 0 else "Unknown"
        except:
            symbol_name = "Unknown"
            
    folder_name = f"{symbol}_{symbol_name}"
    target_path = os.path.join(base_dir, folder_name)
    
    if not os.path.exists(target_path):
        os.makedirs(target_path)
        
    # 同时创建分析子目录
    analysis_path = os.path.join(target_path, "analysis")
    if not os.path.exists(analysis_path):
        os.makedirs(analysis_path)
        
    return target_path, analysis_path, symbol_name

def get_stock_info(symbol: str):
    """获取股票基本信息"""
    try:
        return ak.stock_individual_info_em(symbol=symbol)
    except:
        return pd.DataFrame()
