import pandas as pd
import akshare as ak
import os
from datetime import datetime

def get_fund_flow(symbol: str):
    """获取个股资金流向数据"""
    # 自动识别市场
    if symbol.startswith('6'):
        market = "sh"
    elif symbol.startswith('0') or symbol.startswith('3'):
        market = "sz"
    elif symbol.startswith('8') or symbol.startswith('4'):
        market = "bj"
    else:
        market = "sh"
        
    try:
        return ak.stock_individual_fund_flow(stock=symbol, market=market)
    except:
        return pd.DataFrame()

def analyze_flow_details(df: pd.DataFrame):
    """
    深度分析资金流向明细：计算日增量（环比）
    """
    if df.empty:
        return pd.DataFrame()
        
    # 筛选近一周 (5个交易日) 的明细数据
    week_flow = df.head(5).copy()
    
    # 动态匹配列名 (处理不同接口可能的列名差异)
    cols_map = {
        '日期': '日期',
        '超大单': [c for c in week_flow.columns if '超大单' in c and '净额' in c][0],
        '大单': [c for c in week_flow.columns if '大单' in c and '净额' in c][0],
        '中单': [c for c in week_flow.columns if '中单' in c and '净额' in c][0],
        '小单': [c for c in week_flow.columns if '小单' in c and '净额' in c][0],
        '主力': [c for c in week_flow.columns if '主力净流入' in c and '净额' in c][0]
    }
    
    analysis_df = week_flow[list(cols_map.values())].copy()
    analysis_df.columns = list(cols_map.keys())
    
    # 强制将日期转换为字符串，防止 JSON 序列化失败
    analysis_df['日期'] = analysis_df['日期'].astype(str)
    
    numeric_cols = ['超大单', '大单', '中单', '小单', '主力']
    for col in numeric_cols:
        analysis_df[col] = analysis_df[col] / 10000 # 转为万元
        
    # 计算每日变化量 (环比增量)
    analysis_df = analysis_df.sort_values('日期')
    for col in numeric_cols:
        analysis_df[f'{col}日增量'] = analysis_df[col].diff().fillna(0)
    
    return analysis_df.sort_values('日期', ascending=False)

def prepare_rose_chart_data(df: pd.DataFrame):
    """
    为前端 ECharts 极坐标饼图准备数据
    """
    if df.empty:
        return []
        
    # 取最新一天的数据
    latest = df.iloc[0]
    
    size_order = ['小单', '中单', '大单', '超大单']
    results = []
    
    for size in size_order:
        val = latest[size]
        results.append({
            "name": f"{size}({'流入' if val >= 0 else '流出'})",
            "value": abs(float(val)),
            "raw": float(val),
            "type": "inflow" if val >= 0 else "outflow"
        })
        
    # 按流入/流出分组，并按规模从小到大排序（符合用户要求的视觉效果）
    inflows = [i for i in results if i['type'] == 'inflow']
    outflows = [i for i in results if i['type'] == 'outflow']
    
    return inflows + outflows
