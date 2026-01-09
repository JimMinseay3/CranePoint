import requests
import pandas as pd
import argparse
import sys
import os
import json
import time
import re
from datetime import datetime
import akshare as ak

# 强制输出为 UTF-8
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def get_stock_info(symbol):
    """
    获取股票的正确代码和名称
    """
    try:
        stock_list = ak.stock_info_a_code_name()
        # 如果是纯数字，按代码匹配
        if symbol.isdigit():
            # 补全 6 位代码
            code = symbol.zfill(6)
            match = stock_list[stock_list['code'] == code]
            if not match.empty:
                return code, match.iloc[0]['name']
        else:
            # 按名称匹配
            match = stock_list[stock_list['name'] == symbol]
            if not match.empty:
                return match.iloc[0]['code'], match.iloc[0]['name']
    except Exception as e:
        print(f"WARNING: 获取股票列表失败: {str(e)}", file=sys.stderr)
    
    return symbol, symbol # 兜底返回原值

def get_cninfo_org_id(code):
    """
    通过巨潮搜索接口获取股票的 orgId
    """
    url = "http://www.cninfo.com.cn/new/information/topSearch/query"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    }
    params = {
        "keyWord": code,
        "maxNum": 10
    }
    try:
        res = requests.post(url, data=params, headers=headers, timeout=10)
        if res.status_code == 200:
            data = res.json()
            if not data:
                return None, None
            # 查找最匹配的项
            for item in data:
                # 巨潮搜索结果中的 code 可能是 "000981", 也可能是 "000981 sz"
                item_code = item.get('code', '')
                if code in item_code:
                    return item.get('orgId'), item.get('plate', 'szsh') # 默认 szsh
    except Exception as e:
        print(f"ERROR: 获取 orgId 失败: {str(e)}", file=sys.stderr)
    return None, None

def get_cninfo_reports(symbol, years, report_types, save_path):
    """
    从巨潮资讯获取财报 PDF 链接并下载
    """
    # 1. 准确获取代码和名称
    stock_code, stock_name = get_stock_info(symbol)
    print(f"INFO: 目标标的 - {stock_code} {stock_name}", file=sys.stderr)
    
    # 2. 获取巨潮内部 orgId
    org_id, plate = get_cninfo_org_id(stock_code)
    if not org_id:
        print(f"ERROR: 无法在巨潮获取 {stock_code} 的 orgId", file=sys.stderr)
        return

    print(f"PROGRESS: 20", flush=True)

    # 3. 准备基础保存目录 (第一级：代码_名称)
    base_target_dir = os.path.join(save_path, f"{stock_code}_{stock_name}")
    if not os.path.exists(base_target_dir):
        os.makedirs(base_target_dir)

    # 报表类型映射到分类码
    category_map = {
        "年报": "category_ndbg_szsh",
        "半年报": "category_bndbg_szsh",
        "一季报": "category_yjdbg_szsh",
        "三季报": "category_sjdbg_szsh"
    }
    
    # 报表类型映射到巨潮搜索关键词 (尝试多个关键词以提高成功率)
    search_keys_map = {
        "年报": ["年度报告", "年报"],
        "半年报": ["半年度报告", "半年报"],
        "一季报": ["一季度报告", "第一季度报告"],
        "三季报": ["三季度报告", "第三季度报告"]
    }

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "X-Requested-With": "XMLHttpRequest",
        "Referer": "http://www.cninfo.com.cn/new/commonUrl/pageOfSearch?url=hisAnnouncement/hisAnnouncement",
        "Origin": "http://www.cninfo.com.cn"
    }

    url = "http://www.cninfo.com.cn/new/hisAnnouncement/query"
    
    total_tasks = len(years) * len(report_types)
    completed_tasks = 0

    for year in years:
        # 准备第二级保存目录 (第二级：年份)
        year_dir = os.path.join(base_target_dir, str(year))
        if not os.path.exists(year_dir):
            os.makedirs(year_dir)

        for r_type in report_types:
            search_keys = search_keys_map.get(r_type, [r_type])
            found_for_this_type = False

            # 构建查询数据公共参数
            search_year = int(year)
            # 扩大搜索日期范围，确保能搜到 (例如 2023 年报可能在 2024 年 4 月发布)
            start_date = f"{search_year}-01-01"
            end_date = f"{search_year + 1}-06-30"
            
            # 自动判断市场 (CNINFO 搜索参数)
            # 实际上使用 szsh 通常最稳健，或者根据股票代码精确区分
            if stock_code.startswith(('60', '68', '90')):
                column = "shmb"; plate = "sh"
            elif stock_code.startswith(('00', '20')):
                column = "szmb"; plate = "sz"
            elif stock_code.startswith('30'):
                column = "szcy"; plate = "sz"
            elif stock_code.startswith(('43', '83', '87', '88')):
                column = "bj"; plate = "bj"
            else:
                column = ""; plate = "" # 留空通常可以搜索全市场

            for search_key in search_keys:
                if found_for_this_type: break

                data = {
                    "pageNum": "1",
                    "pageSize": "30",
                    "column": column,
                    "tabName": "fulltext",
                    "plate": plate,
                    "stock": f"{stock_code},{org_id}",
                    "searchkey": search_key,
                    "secid": "",
                    "category": "category_ndbg_szsh;" if r_type == "年报" else "category_bndbg_szsh;" if r_type == "半年报" else "category_yjdbg_szsh;" if r_type == "一季报" else "category_sjdbg_szsh;",
                    "trade": "",
                    "seDate": f"{start_date}~{end_date}"
                }

                try:
                    print(f"INFO: 正在搜索 {year} {r_type} (关键词: {search_key})...", file=sys.stderr)
                    response = requests.post(url, data=data, headers=headers, timeout=15)
                    if response.status_code != 200: continue

                    res_json = response.json()
                    announcements = res_json.get('announcements', [])
                    
                    if announcements:
                        for a in announcements:
                            title = a['announcementTitle']
                            # 必须包含年份关键词且排除“摘要”、“英文版”、“提示性”等
                            if str(year) in title and not any(k in title for k in ["摘要", "英文", "风险提示", "提示性", "更正"]):
                                pdf_url = "http://static.cninfo.com.cn/" + a['adjunctUrl']
                                adj_title = re.sub(r'[\\/:*?"<>|]', '_', title)
                                file_path = os.path.join(year_dir, f"{adj_title}.pdf")
                                
                                if os.path.exists(file_path):
                                    print(f"INFO: 跳过已存在: {adj_title}", file=sys.stderr)
                                    found_for_this_type = True
                                    break
                                    
                                print(f"Downloading: {adj_title}", file=sys.stderr)
                                pdf_res = requests.get(pdf_url, headers=headers, timeout=30)
                                if pdf_res.status_code == 200:
                                    with open(file_path, 'wb') as f:
                                        f.write(pdf_res.content)
                                    print(f"SUCCESS: 已保存 {file_path}", file=sys.stderr)
                                    found_for_this_type = True
                                    break
                    
                    time.sleep(1) # 增加延迟，避免被封

                except Exception as e:
                    print(f"WARNING: 搜索 {year} {r_type} 时出错: {str(e)}", file=sys.stderr)

            if not found_for_this_type:
                print(f"WARNING: 未能找到 {year} 年的 {r_type}。", file=sys.stderr)

            completed_tasks += 1
            progress = 20 + int((completed_tasks / total_tasks) * 80)
            print(f"PROGRESS: {progress}", flush=True)

    print(f"PROGRESS: 100", flush=True)
    print(f"SUCCESS: 财报处理流程结束")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='从巨潮资讯下载 A 股财报 PDF')
    parser.add_argument('--symbol', type=str, required=True, help='股票代码或名称')
    parser.add_argument('--years', type=str, required=True, help='年份，逗号分隔，如 2023,2022')
    parser.add_argument('--types', type=str, required=True, help='类型，逗号分隔，如 一季报,年报')
    parser.add_argument('--path', type=str, default='downloads/finance', help='保存路径')

    args = parser.parse_args()
    
    years_list = [y.strip() for y in args.years.split(',')]
    types_list = [t.strip() for t in args.types.split(',')]
    
    get_cninfo_reports(args.symbol, years_list, types_list, args.path)
