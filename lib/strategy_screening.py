import sys
import json
import argparse
import os
import pandas as pd
from datetime import datetime, timedelta
import concurrent.futures
import akshare as ak
from functools import lru_cache

# 添加模块路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import quant
from quant import calculators

# 简单的本地缓存目录
CACHE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "cache", "history")
if not os.path.exists(CACHE_DIR):
    os.makedirs(CACHE_DIR, exist_ok=True)

def get_cached_history(stock_code, days=60):
    """
    带有本地文件缓存的历史数据获取
    """
    today = datetime.now().strftime("%Y%m%d")
    cache_file = os.path.join(CACHE_DIR, f"{stock_code}_{today}.json")
    
    # 1. 尝试从缓存读取
    if os.path.exists(cache_file):
        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return pd.DataFrame(data)
        except:
            pass
            
    # 2. 缓存不存在或失效，从网络抓取
    df = quant.get_history_detail(stock_code, days=days)
    if not df.empty:
        # 存入缓存
        try:
            # 转换为字典列表存储
            df.to_json(cache_file, orient='records', force_ascii=False)
        except:
            pass
    return df

def screen_stock(stock_code, stock_name, volume_ratio, start_date=None, end_date=None):
    """
    对单个股票进行策略验证
    """
    try:
        # 获取历史数据 (优先使用缓存)
        df = get_cached_history(stock_code, days=60)
        if df.empty or len(df) < 30:
            return None
            
        # 按照日期升序排列以便计算指标
        df = df.sort_values('日期', ascending=True)

        # 检查 MACD “零下金叉” (仅保留金叉和零下判定)
        if not calculators.check_macd_zero_golden_cross(df):
            return None
        
        # 返回符合条件的结果
        return {
            "code": stock_code,
            "name": stock_name,
            "macd_status": "Zero-Cross"
        }
    except Exception as e:
        return None

def run_strategy_screening(stocks_json_path):
    """
    运行全市场筛选
    """
    print(f"INFO: 开始全市场 MACD 金叉筛选 (并发加速版)...", file=sys.stderr)
    
    try:
        # 加载实时快照数据
        with open(stocks_json_path, 'r', encoding='utf-8') as f:
            all_stocks = json.load(f)
            
        # 1. 初步筛选：涨跌幅过滤
        # 排除大跌中的金叉
        candidates = [
            s for s in all_stocks 
            if s.get('change', 0) > -5
        ]
        
        if not candidates and all_stocks:
            candidates = all_stocks[:100]
            print(f"INFO: 初筛无结果，自动选取前 100 只", file=sys.stderr)
        
        print(f"INFO: 初筛候选标的: {len(candidates)} 只", file=sys.stderr)
        
        results = []
        # 显著增加并发线程数。对于网络 I/O 密集型任务，30-50 个线程通常没问题
        max_workers = 30
        
        # 预先计算日期
        end_date = datetime.now().strftime("%Y%m%d")
        start_date = (datetime.now() - timedelta(days=120)).strftime("%Y%m%d")

        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_stock = {
                executor.submit(
                    screen_stock, 
                    s['code'], 
                    s['name'], 
                    s.get('volume_ratio', 0),
                    start_date,
                    end_date
                ): s for s in candidates
            }
            
            count = 0
            total = len(candidates)
            if total == 0:
                print(f"SUCCESS: []", file=sys.stderr)
                return

            for future in concurrent.futures.as_completed(future_to_stock):
                count += 1
                if count % 10 == 0 or count == total:
                    print(f"PROGRESS: {int(count/total * 100)}", file=sys.stderr)
                    
                try:
                    res = future.result()
                    if res:
                        # 合并实时快照中的其他数据
                        stock_data = future_to_stock[future]
                        res.update(stock_data)
                        results.append(res)
                except:
                    continue

        print(f"SUCCESS: {json.dumps(results, ensure_ascii=False)}", file=sys.stderr)
        
    except Exception as e:
        import traceback
        print(f"ERROR: {traceback.format_exc()}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='MACD Strategy Screening')
    parser.add_argument('--stocks_path', type=str, required=True, help='Path to stocks snapshot JSON')
    
    args = parser.parse_args()
    run_strategy_screening(args.stocks_path)
