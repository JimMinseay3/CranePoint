import json
import sys
import requests
import io
import argparse

# 强制设置标准输出为 UTF-8 编码
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def get_page_data(page, page_size):
    try:
        # 直接调用东方财富底层 API，速度比 akshare 快得多
        url = "http://push2.eastmoney.com/api/qt/clist/get"
        # 优化 fs 参数，确保覆盖 沪深京 A 股
        # m:0 t:6 (深A), m:0 t:80 (创业板), m:1 t:2 (沪A), m:1 t:23 (科创板), m:0 t:81+s:2048 (北交所)
        fs_parts = [
            "m:0+t:6",      # 深证A股
            "m:0+t:80",     # 创业板
            "m:1+t:2",      # 上证A股
            "m:1+t:23",     # 科创板
            "m:0+t:81+s:2048" # 北交所
        ]
        
        params = {
            "pn": page,
            "pz": page_size,
            "po": 0,
            "np": 1,
            "ut": "bd1d9ddb040897f1cf462c6f6e7a71f8",
            "fltt": 2,
            "invt": 2,
            "fid": "f12",
            "fs": ",".join(fs_parts),
            "fields": "f2,f3,f5,f6,f7,f8,f9,f10,f12,f14,f15,f16,f17,f18,f20,f21,f22,f23,f24,f25,f62,f115,f184"
        }
        
        print(f"PROGRESS: 30", flush=True)
        # 增加重试逻辑
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = requests.get(url, params=params, timeout=15)
                response.raise_for_status()
                data = response.json()
                if data.get('data') and data['data'].get('diff'):
                    break
                if attempt == max_retries - 1:
                    print(f"DEBUG: Page {page} returned no data after {max_retries} attempts", file=sys.stderr)
                    return []
            except Exception as e:
                if attempt == max_retries - 1:
                    raise e
                print(f"DEBUG: Retry {attempt+1} for page {page} due to {str(e)}", file=sys.stderr)
        
        if not data.get('data') or not data['data'].get('diff'):
            return []

        stocks = data['data']['diff']
        print(f"PROGRESS: 70", flush=True)
        
        result = []
        for stock in stocks:
            result.append({
                "code": str(stock.get('f12', '--')),
                "name": str(stock.get('f14', '--')),
                "price": float(stock.get('f2', 0)) if stock.get('f2') != '-' else 0,
                "change": float(stock.get('f3', 0)) if stock.get('f3') != '-' else 0,
                "volume": float(stock.get('f5', 0)) if stock.get('f5') != '-' else 0,
                "amount": float(stock.get('f6', 0)) if stock.get('f6') != '-' else 0,
                "amplitude": float(stock.get('f7', 0)) if stock.get('f7') != '-' else 0,
                "turnover": float(stock.get('f8', 0)) if stock.get('f8') != '-' else 0,
                "pe_dynamic": float(stock.get('f9', 0)) if stock.get('f9') != '-' else 0,
                "volume_ratio": float(stock.get('f10', 0)) if stock.get('f10') != '-' else 0,
                "high": float(stock.get('f15', 0)) if stock.get('f15') != '-' else 0,
                "low": float(stock.get('f16', 0)) if stock.get('f16') != '-' else 0,
                "open": float(stock.get('f17', 0)) if stock.get('f17') != '-' else 0,
                "prevClose": float(stock.get('f18', 0)) if stock.get('f18') != '-' else 0,
                "market_cap": float(stock.get('f20', 0)) if stock.get('f20') != '-' else 0,
                "circulating_market_cap": float(stock.get('f21', 0)) if stock.get('f21') != '-' else 0,
                "speed": float(stock.get('f22', 0)) if stock.get('f22') != '-' else 0,
                "pb": float(stock.get('f23', 0)) if stock.get('f23') != '-' else 0,
                "change_60d": float(stock.get('f24', 0)) if stock.get('f24') != '-' else 0,
                "change_ytd": float(stock.get('f25', 0)) if stock.get('f25') != '-' else 0,
                "main_inflow": float(stock.get('f62', 0)) if stock.get('f62') != '-' else 0,
                "pe_static": float(stock.get('f115', 0)) if stock.get('f115') != '-' else 0,
                "main_inflow_ratio": float(stock.get('f184', 0)) if stock.get('f184') != '-' else 0,
            })
            
        print(f"PROGRESS: 100", flush=True)
        return result
    except Exception as e:
        print(f"ERROR: {str(e)}", file=sys.stderr)
        return []

if __name__ == "__main__":
    try:
        parser = argparse.ArgumentParser()
        parser.add_argument('--page', type=int, default=1)
        parser.add_argument('--size', type=int, default=500)
        args = parser.parse_args()
        
        data = get_page_data(args.page, args.size)
        print(json.dumps(data, ensure_ascii=False))
    except Exception as e:
        print(f"ERROR: Main block exception: {str(e)}", file=sys.stderr)
        print("[]") # 兜底输出空数组，防止 Rust 解析失败
        sys.exit(1)
