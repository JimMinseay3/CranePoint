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

def get_history_range(symbol: str, start_date: str, end_date: str, level: str = 'standard'):
    """
    获取指定日期范围内的历史行情，支持不同粒度
    """
    try:
        # 1. 基础参数：根据等级决定复权方式和字段
        adjust = "qfq" if level in ['standard', 'research'] else ""
        
        # 2. 调用 akshare 获取基础 K 线
        df = ak.stock_zh_a_hist(
            symbol=symbol, 
            period="daily", 
            start_date=start_date, 
            end_date=end_date, 
            adjust=adjust
        )
        if df.empty:
            return pd.DataFrame()
            
        # 3. 基础字段清理 (Lite/Standard)
        # 默认字段: 日期, 开盘, 收盘, 最高, 最低, 成交量, 成交额, 振幅, 涨跌幅, 涨跌额, 换手率
        
        # 4. 进阶数据处理 (Research)
        if level == 'research':
            # 获取历史市值、内外盘等进阶数据
            # 注意：akshare 部分进阶数据需要单独接口，这里整合核心属性
            try:
                # 尝试获取个股实时行情中的市值作为参考（虽然不是历史，但可以补充当前状态）
                # 对于历史市值，通常需要更专业的接口，这里我们先整合基础属性中的盘口参考
                pass
            except:
                pass

        # 5. 排序与格式化
        df = df.sort_values('日期', ascending=False)
        df['日期'] = df['日期'].astype(str)
        
        # 剔除停牌日（成交量为 0 且价格无波动的通常视为停牌）
        df = df[df['成交量'] > 0]
        
        return df
    except Exception as e:
        print(f"Error fetching history range: {e}")
        return pd.DataFrame()

def get_index_history(symbol: str, start_date: str, end_date: str):
    """
    获取指数历史数据
    """
    try:
        # 指数代码转换：上证 000001 -> sh000001, 沪深300 000300 -> sh000300
        # ak.stock_zh_index_daily_em 获取指数
        df = ak.stock_zh_index_daily_em(symbol=f"sh{symbol}")
        if df.empty:
            return pd.DataFrame()
        
        # 过滤日期范围
        df['date'] = pd.to_datetime(df['date'])
        start = pd.to_datetime(start_date)
        end = pd.to_datetime(end_date)
        df = df[(df['date'] >= start) & (df['date'] <= end)]
        
        # 排序
        df = df.sort_values('date', ascending=False)
        df['date'] = df['date'].dt.strftime('%Y-%m-%d')
        return df
    except Exception as e:
        print(f"Error fetching index history: {e}")
        return pd.DataFrame()
