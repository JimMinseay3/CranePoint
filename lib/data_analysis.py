import sys
import json
import argparse
import os
import pandas as pd
from datetime import datetime

# 添加模块路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 导入模块化量化工具库
import quant

import numpy as np

# 自定义 JSON 编码器以处理 numpy 数据类型
class MyEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, (np.int64, np.int32, np.integer)):
            return int(obj)
        elif isinstance(obj, (np.float64, np.float32, np.floating)):
            if np.isnan(obj) or np.isinf(obj):
                return None
            return float(obj)
        elif isinstance(obj, (np.ndarray,)):
            return obj.tolist()
        elif hasattr(obj, 'to_dict'):
            return obj.to_dict()
        return super(MyEncoder, self).default(obj)

def run_analysis(symbol, base_path="data"):
    print(f"INFO: 启动分析任务，代码: {symbol}, 路径: {base_path}", file=sys.stderr)
    try:
        # 1. 初始化归档目录 (Data Organization)
        print(f"INFO: 正在初始化 {symbol} 的分析归档...", file=sys.stderr)
        target_dir, analysis_dir, name = quant.get_target_dir(symbol, base_dir=base_path)
        
        # 2. 数据采集 (History & Basic Info)
        print(f"INFO: 正在采集 {symbol} 的基础行情...", file=sys.stderr)
        hist_df = quant.get_history_detail(symbol, days=150) # 获取足够的数据用于计算
        stock_info = quant.get_stock_info(symbol)
        
        # 3. 市场风险与波动率 (Market Risk & Volatility)
        print("INFO: 正在计算波动率指标...", file=sys.stderr)
        hv20 = quant.calculate_hv(hist_df, 20)
        hv60 = quant.calculate_hv(hist_df, 60)
        
        # 4. 流动性与盘口深度 (Liquidity & Depth)
        print("INFO: 正在评估盘口流动性...", file=sys.stderr)
        liquidity = quant.analyze_liquidity(symbol)
        
        # 5. 资金流向分析 (Fund Flow Analysis)
        print("INFO: 正在执行深度资金流向分析...", file=sys.stderr)
        raw_flow = quant.get_fund_flow(symbol)
        flow_details = quant.analyze_flow_details(raw_flow)
        rose_data = quant.prepare_rose_chart_data(flow_details)
        
        # 6. 财务基本面 (Fundamental Financials)
        print("INFO: 正在获取财务核心指标...", file=sys.stderr)
        deduct_profit, report_period = quant.get_latest_profit(symbol)
        
        # 7. 行业共振与相关性 (Industry & Correlation)
        print("INFO: 正在计算行业相关性...", file=sys.stderr)
        try:
            industry_name = stock_info[stock_info['item'] == '行业']['value'].values[0]
            correlation = quant.calculate_industry_correlation(hist_df, industry_name)
        except:
            industry_name = "未知"
            correlation = 0.0
            
        # 整合最终结果
        result = {
            "symbol": symbol,
            "name": name,
            "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "risk": {
                "hv20": round(hv20 * 100, 2) if hv20 else 0,
                "hv60": round(hv60 * 100, 2) if hv60 else 0
            },
            "liquidity": liquidity,
            "fund_flow": {
                "details": flow_details.head(5).to_dict(orient='records') if not flow_details.empty else [],
                "rose_chart": rose_data,
                "weekly_main_net": round(flow_details['主力'].head(5).sum(), 2) if not flow_details.empty else 0
            },
            "fundamentals": {
                "deduct_net_profit": deduct_profit,
                "report_period": report_period
            },
            "industry": {
                "name": industry_name,
                "correlation": round(correlation, 4) if correlation else 0
            },
            "history": hist_df.head(30).to_dict(orient='records') if not hist_df.empty else []
        }
        
        # 8. 自动归档 (Data Organization)
        print("INFO: 正在生成归档文件...", file=sys.stderr)
        
        # 保存 JSON 结果
        json_path = os.path.join(analysis_dir, f"analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
        print(f"INFO: 正在保存 JSON 结果到 {json_path}", file=sys.stderr)
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=4, cls=MyEncoder)
            
        # 保存简要 CSV 报告
        csv_path = os.path.join(analysis_dir, f"report_summary.csv")
        print(f"INFO: 正在生成 CSV 报告...", file=sys.stderr)
        summary_df = pd.DataFrame([{
            "代码": symbol,
            "名称": name,
            "HV20": f"{result['risk']['hv20']}%",
            "主力一周净流入": f"{result['fund_flow']['weekly_main_net']}万",
            "扣非净利润": deduct_profit,
            "行业": industry_name,
            "行业相关性": result['industry']['correlation']
        }])
        summary_df.to_csv(csv_path, index=False, encoding="utf-8-sig")
        
        # 输出成功结果给 Tauri (必须输出到 stderr 才能被捕获)
        print(f"SUCCESS: {json.dumps(result, ensure_ascii=False, cls=MyEncoder)}", file=sys.stderr)
        print(f"INFO: 分析完成！", file=sys.stderr)
        
    except Exception as e:
        import traceback
        error_msg = traceback.format_exc()
        print(f"ERROR: {error_msg}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--symbol', type=str, required=True)
    parser.add_argument('--path', type=str, default='data')
    args = parser.parse_args()
    
    run_analysis(args.symbol, args.path)
