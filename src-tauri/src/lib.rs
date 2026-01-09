use serde_json::{json, Value};
use std::process::Stdio;
use tokio::io::{AsyncBufReadExt, BufReader};
use tokio::process::Command;
use tauri::{AppHandle, Emitter};
use futures::future::join_all;
use std::collections::HashSet;

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_opener::init())
        .plugin(tauri_plugin_dialog::init())
        .plugin(tauri_plugin_fs::init())
        .invoke_handler(tauri::generate_handler![
            greet,
            get_stock_data,
            download_finance_data,
            list_downloaded_finance,
            open_folder,
            run_stock_analysis,
            list_analysis_archives,
            download_market_history
        ])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}

#[tauri::command]
fn greet(name: &str) -> String {
    format!("Hello, {}! You've been greeted from Rust!", name)
}

/// 直接从东方财富 API 获取单页股票数据
async fn fetch_stock_page(page: i32, page_size: i32) -> Result<Vec<Value>, String> {
    let client = reqwest::Client::new();
    let url = "http://push2.eastmoney.com/api/qt/clist/get";
    
    // 东方财富 API 参数
    let params = [
        ("pn", page.to_string()),
        ("pz", page_size.to_string()),
        ("po", "1".to_string()),
        ("np", "1".to_string()),
        ("ut", "bd1d9ddb04089700cf9c27f6f7426281".to_string()),
        ("fltt", "2".to_string()),
        ("invt", "2".to_string()),
        ("fid", "f3".to_string()),
        ("fs", "m:0+t:6,m:0+t:80,m:1+t:2,m:1+t:23,m:0+t:81+s:2048".to_string()), // 沪深 A 股
        ("fields", "f2,f3,f4,f5,f6,f7,f8,f9,f10,f12,f14,f15,f16,f17,f18,f20,f21,f22,f23,f37,f57,f58,f114,f115,f161,f162".to_string()),
    ];

    let response = client.get(url)
        .query(&params)
        .header("User-Agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
        .send()
        .await
        .map_err(|e| format!("请求失败: {}", e))?;

    let json_data: Value = response.json()
        .await
        .map_err(|e| format!("解析 JSON 失败: {}", e))?;

    // 提取并转换数据格式以适配前端
    let mut result = Vec::new();
    if let Some(diff) = json_data.get("data").and_then(|d| d.get("diff")).and_then(|diff| diff.as_array()) {
        for item in diff {
            // 字段映射逻辑
            let f12 = item.get("f12").and_then(|v| v.as_str()).unwrap_or("-");
            if f12 == "-" { continue; }

            // 彻底过滤北交所股票 (8, 4, 92 开头)
            if f12.starts_with('8') || f12.starts_with('4') || f12.starts_with("92") {
                continue;
            }

            // 过滤转债 (11, 12 开头)
            if f12.starts_with("11") || f12.starts_with("12") {
                continue;
            }

            let name = item.get("f14").and_then(|v| v.as_str()).unwrap_or("-");
            // 过滤退市股
            if name.contains("退") {
                continue;
            }

            let f2 = item.get("f2").and_then(|v| v.as_f64()).unwrap_or(0.0);
            if f2 == 0.0 || f2.is_nan() { continue; } // 过滤停牌或无价数据

            let prev_close = item.get("f18").and_then(|v| v.as_f64()).unwrap_or(0.0);
            
            // 彻底移除对 f51/f52 的依赖，完全根据 A 股规则动态计算
            let limit_ratio = if f12.starts_with("688") || f12.starts_with("30") {
                0.20 // 科创板、创业板 20%
            } else if item.get("f14").and_then(|v| v.as_str()).unwrap_or("").contains("ST") {
                0.05 // ST 股 5%
            } else {
                0.10 // 主板 10%
            };

            let limit_up = if prev_close > 0.0 { (prev_close * (1.0 + limit_ratio) * 100.0).round() / 100.0 } else { 0.0 };
            let limit_down = if prev_close > 0.0 { (prev_close * (1.0 - limit_ratio) * 100.0).round() / 100.0 } else { 0.0 };

            result.push(json!({
                "code": f12,
                "name": item.get("f14").and_then(|v| v.as_str()).unwrap_or("-"),
                "price": f2,
                "change": item.get("f3").and_then(|v| v.as_f64()).unwrap_or(0.0),
                "change_amount": item.get("f4").and_then(|v| v.as_f64()).unwrap_or(0.0),
                "volume": item.get("f5").and_then(|v| v.as_f64()).unwrap_or(0.0),
                "amount": item.get("f6").and_then(|v| v.as_f64()).unwrap_or(0.0),
                "amplitude": item.get("f7").and_then(|v| v.as_f64()).unwrap_or(0.0),
                "turnover": item.get("f8").and_then(|v| v.as_f64()).unwrap_or(0.0),
                "pe_dynamic": item.get("f9").and_then(|v| v.as_f64()).unwrap_or(0.0),
                "volume_ratio": item.get("f10").and_then(|v| v.as_f64()).unwrap_or(0.0),
                "high": item.get("f15").and_then(|v| v.as_f64()).unwrap_or(0.0),
                "low": item.get("f16").and_then(|v| v.as_f64()).unwrap_or(0.0),
                "open": item.get("f17").and_then(|v| v.as_f64()).unwrap_or(0.0),
                "prevClose": prev_close,
                "market_cap": item.get("f20").and_then(|v| v.as_f64()).unwrap_or(0.0),
                "circulating_market_cap": item.get("f21").and_then(|v| v.as_f64()).unwrap_or(0.0),
                "speed": item.get("f22").and_then(|v| v.as_f64()).unwrap_or(0.0),
                "pb": item.get("f23").and_then(|v| v.as_f64()).unwrap_or(0.0),
                "turnover_actual": item.get("f37").and_then(|v| v.as_f64()).unwrap_or(0.0),
                "limit_up": limit_up,
                "limit_down": limit_down,
                "total_shares": item.get("f57").and_then(|v| v.as_f64()).unwrap_or(0.0),
                "circulating_shares": item.get("f58").and_then(|v| v.as_f64()).unwrap_or(0.0),
                "pe_ttm": item.get("f114").and_then(|v| v.as_f64()).unwrap_or(0.0),
                "pe_static": item.get("f115").and_then(|v| v.as_f64()).unwrap_or(0.0),
                "outer_disc": item.get("f161").and_then(|v| v.as_f64()).unwrap_or(0.0),
                "inner_disc": item.get("f162").and_then(|v| v.as_f64()).unwrap_or(0.0),
            }));
        }
    }
    Ok(result)
}

#[tauri::command]
async fn get_stock_data(app: AppHandle) -> Result<Value, String> {
    let page_size = 100; // 接口实际限制每页 100 条
    let total_pages = 70;  // 70 页覆盖约 7000 只股票
    
    app.emit("refresh-progress", 10).ok();

    let mut tasks = vec![];
    for page in 1..=total_pages {
        tasks.push(fetch_stock_page(page, page_size));
    }

    let results = join_all(tasks).await;
    
    let mut all_data = Vec::new();
    let mut seen_codes = HashSet::new();
    let mut success_count = 0;

    for (i, res) in results.into_iter().enumerate() {
        match res {
            Ok(data) => {
                for item in data {
                    let code = item.get("code").and_then(|v| v.as_str()).unwrap_or("");
                    if !code.is_empty() && !seen_codes.contains(code) {
                        seen_codes.insert(code.to_string());
                        all_data.push(item);
                    }
                }
                success_count += 1;
                let progress = 10 + (success_count * 90 / total_pages);
                app.emit("refresh-progress", progress).ok();
            }
            Err(e) => {
                eprintln!("第 {} 页抓取失败: {}", i + 1, e);
            }
        }
    }

    // 默认按涨跌幅降序排序，确保数据有序
    all_data.sort_by(|a, b| {
        let a_val = a.get("change").and_then(|v| v.as_f64()).unwrap_or(0.0);
        let b_val = b.get("change").and_then(|v| v.as_f64()).unwrap_or(0.0);
        b_val.partial_cmp(&a_val).unwrap_or(std::cmp::Ordering::Equal)
    });

    println!("成功抓取并去重，共计 {} 条记录", all_data.len());
    
    app.emit("refresh-progress", 100).ok();
    Ok(Value::Array(all_data))
}

#[tauri::command]
async fn download_finance_data(
    app: AppHandle,
    symbol: String,
    years: String,
    types: String,
    path: String,
) -> Result<String, String> {
    let python_path = if cfg!(windows) {
        "../.venv/Scripts/python.exe"
    } else {
        "../.venv/bin/python"
    };

    println!("DEBUG: 正在启动 Python 分析脚本, 路径: {}, 目标股票: {}", python_path, symbol);

    let mut child = Command::new(python_path)
        .arg("../lib/finance_fetching.py")
        .arg("--symbol")
        .arg(symbol)
        .arg("--years")
        .arg(years)
        .arg("--types")
        .arg(types)
        .arg("--path")
        .arg(path)
        .env("PYTHONIOENCODING", "utf-8")
        .stdout(Stdio::piped())
        .stderr(Stdio::piped())
        .spawn()
        .map_err(|e| format!("无法启动财报下载脚本: {}", e))?;

    let stdout = child.stdout.take().ok_or("无法打开 stdout")?;
    let stderr = child.stderr.take().ok_or("无法打开 stderr")?;
    let mut stdout_reader = BufReader::new(stdout).lines();
    let mut stderr_reader = BufReader::new(stderr).lines();

    let app_handle = app.clone();
    let (tx, mut rx) = tauri::async_runtime::channel::<String>(1);

    // 处理 stdout (防止管道溢出)
    let stdout_task = tauri::async_runtime::spawn(async move {
        while let Ok(Some(_line)) = stdout_reader.next_line().await {
            // 暂时忽略 stdout 内容，主要为了防止阻塞
        }
    });

    // 处理 stderr 用于所有实时消息、进度和结果
    let stderr_task = tauri::async_runtime::spawn(async move {
        let mut last_success = String::from("同步结束");
        while let Ok(Some(line)) = stderr_reader.next_line().await {
            if line.starts_with("PROGRESS:") {
                if let Ok(p) = line.trim_start_matches("PROGRESS:").trim().parse::<i32>() {
                    let _ = app_handle.emit("download-progress", json!({
                        "progress": p,
                        "message": "正在同步数据..."
                    }));
                }
            } else if line.starts_with("INFO:") || line.starts_with("ERROR:") {
                let _ = app_handle.emit("download-progress", json!({
                    "progress": 0, // 保持当前进度或设为 0
                    "message": line.clone()
                }));
            } else if line.starts_with("WARNING:") {
                let _ = app_handle.emit("download-progress", json!({
                    "progress": 0,
                    "message": "同步警告",
                    "warning": line.trim_start_matches("WARNING:").trim().to_string()
                }));
            } else if line.starts_with("SUCCESS:") {
                last_success = line.trim_start_matches("SUCCESS:").trim().to_string();
            }
        }
        let _ = tx.send(last_success).await;
    });

    let final_result = rx.recv().await.unwrap_or_else(|| "下载完成".to_string());
    let _ = stderr_task.await;
    let _ = stdout_task.await;
    let status = child.wait().await.map_err(|e| e.to_string())?;
    if status.success() {
        Ok(final_result)
    } else {
        Err(format!("下载脚本执行失败 (退出码: {:?})。请检查标的代码是否正确或网络是否连接。", status.code()))
    }
}

#[tauri::command]
async fn run_stock_analysis(
    app: AppHandle,
    symbol: String,
    path: String,
) -> Result<String, String> {
    let python_path = if cfg!(windows) {
        "../.venv/Scripts/python.exe"
    } else {
        "../.venv/bin/python"
    };

    println!("DEBUG: 正在启动 Python 分析引擎, 目标股票: {}", symbol);

    let mut child = Command::new(python_path)
        .arg("../lib/data_analysis.py")
        .arg("--symbol")
        .arg(symbol)
        .arg("--path")
        .arg(path)
        .env("PYTHONIOENCODING", "utf-8")
        .stdout(Stdio::piped())
        .stderr(Stdio::piped())
        .spawn()
        .map_err(|e| format!("无法启动分析引擎: {}", e))?;

    let stdout = child.stdout.take().ok_or("无法打开 stdout")?;
    let stderr = child.stderr.take().ok_or("无法打开 stderr")?;
    let mut stdout_reader = BufReader::new(stdout).lines();
    let mut stderr_reader = BufReader::new(stderr).lines();

    let app_handle = app.clone();
    let (tx, mut rx) = tauri::async_runtime::channel::<String>(1);

    // 处理 stdout (防止管道溢出)
    let stdout_task = tauri::async_runtime::spawn(async move {
        while let Ok(Some(_line)) = stdout_reader.next_line().await {
            // 暂时忽略 stdout 内容
        }
    });

    let stderr_task = tauri::async_runtime::spawn(async move {
        let mut last_success = String::new();
        while let Ok(Some(line)) = stderr_reader.next_line().await {
            if line.starts_with("INFO:") {
                let _ = app_handle.emit("analysis-status", line.trim_start_matches("INFO:").trim());
            } else if line.starts_with("SUCCESS:") {
                last_success = line.trim_start_matches("SUCCESS:").trim().to_string();
            } else if line.starts_with("ERROR:") {
                let error_msg = line.trim_start_matches("ERROR:").trim();
                let _ = app_handle.emit("analysis-status", format!("错误: {}", error_msg));
                eprintln!("Python Error: {}", line);
            }
        }
        let _ = tx.send(last_success).await;
    });

    let final_result = rx.recv().await.unwrap_or_default();
    let _ = stderr_task.await;
    let _ = stdout_task.await;
    let status = child.wait().await.map_err(|e| e.to_string())?;
    
    if status.success() && !final_result.is_empty() {
        Ok(final_result)
    } else {
        Err(format!("分析脚本执行失败 (退出码: {:?})。请检查网络或代码输入是否正确。", status.code()))
    }
}

#[tauri::command]
async fn download_market_history(
    app: AppHandle,
    symbol: String,
    start_date: String,
    end_date: String,
    path: String,
    level: String,
    include_index: bool,
) -> Result<String, String> {
    let python_path = if cfg!(windows) {
        "../.venv/Scripts/python.exe"
    } else {
        "../.venv/bin/python"
    };

    println!("DEBUG: 正在启动 Python 导出引擎, 目标股票: {}, 范围: {} - {}, 等级: {}, 同步指数: {}", symbol, start_date, end_date, level, include_index);

    let mut child = Command::new(python_path)
        .arg("../lib/data_analysis.py")
        .arg("--mode")
        .arg("history")
        .arg("--symbol")
        .arg(symbol)
        .arg("--start")
        .arg(start_date)
        .arg("--end")
        .arg(end_date)
        .arg("--path")
        .arg(path)
        .arg("--level")
        .arg(level)
        .arg("--include_index")
        .arg(include_index.to_string())
        .env("PYTHONIOENCODING", "utf-8")
        .stdout(Stdio::piped())
        .stderr(Stdio::piped())
        .spawn()
        .map_err(|e| format!("无法启动导出引擎: {}", e))?;

    let stdout = child.stdout.take().ok_or("无法打开 stdout")?;
    let stderr = child.stderr.take().ok_or("无法打开 stderr")?;
    let mut stdout_reader = BufReader::new(stdout).lines();
    let mut stderr_reader = BufReader::new(stderr).lines();

    let app_handle = app.clone();
    
    // 异步读取 stdout 以获取最终结果 JSON
    let (tx, mut rx) = tauri::async_runtime::channel::<String>(1);
    let stdout_task = tauri::async_runtime::spawn(async move {
        let mut final_json = String::new();
        while let Ok(Some(line)) = stdout_reader.next_line().await {
            if line.starts_with('{') {
                final_json = line;
            }
        }
        let _ = tx.send(final_json).await;
    });

    // 异步读取 stderr 以获取状态更新
    let stderr_task = tauri::async_runtime::spawn(async move {
        while let Ok(Some(line)) = stderr_reader.next_line().await {
            if line.starts_with("INFO:") {
                let msg = line.trim_start_matches("INFO:").trim().to_string();
                let _ = app_handle.emit("history-status", msg);
            } else if line.starts_with("ERROR:") {
                let msg = line.trim_start_matches("ERROR:").trim().to_string();
                let _ = app_handle.emit("history-status", format!("错误: {}", msg));
            }
        }
    });

    let final_result = rx.recv().await.unwrap_or_default();
    let _ = stderr_task.await;
    let _ = stdout_task.await;
    let status = child.wait().await.map_err(|e| e.to_string())?;

    if status.success() && !final_result.is_empty() {
        Ok(final_result)
    } else {
        Err(format!("导出脚本执行失败 (退出码: {:?})", status.code()))
    }
}

#[tauri::command]
fn list_analysis_archives(path: String) -> Result<Vec<Value>, String> {
    let mut results = Vec::new();
    let dir = std::path::Path::new(&path);
    
    if !dir.exists() {
        return Ok(results);
    }

    // 遍历基础目录下的子目录 (股票代码目录)
    if let Ok(entries) = std::fs::read_dir(dir) {
        for entry in entries.flatten() {
            if let Ok(file_type) = entry.file_type() {
                if file_type.is_dir() {
                    let stock_dir = entry.path();
                    let analysis_dir = stock_dir.join("analysis");
                    
                    if analysis_dir.exists() {
                        let stock_name = entry.file_name().to_string_lossy().into_owned();
                        let metadata = analysis_dir.metadata().ok();
                        let updated_at = metadata
                            .and_then(|m| m.modified().ok())
                            .and_then(|t| t.duration_since(std::time::UNIX_EPOCH).ok())
                            .map(|d| d.as_secs())
                            .unwrap_or(0);
                        
                        results.push(json!({
                            "name": stock_name,
                            "updated_at": updated_at
                        }));
                    }
                }
            }
        }
    }
    
    results.sort_by(|a, b| {
        let b_time = b.get("updated_at").and_then(|v| v.as_u64()).unwrap_or(0);
        let a_time = a.get("updated_at").and_then(|v| v.as_u64()).unwrap_or(0);
        b_time.cmp(&a_time)
    });

    Ok(results)
}

#[tauri::command]
fn list_downloaded_finance(path: String) -> Result<Vec<Value>, String> {
    let mut results = Vec::new();
    let dir = std::path::Path::new(&path);
    
    if !dir.exists() {
        return Ok(results);
    }

    if let Ok(entries) = std::fs::read_dir(dir) {
        for entry in entries.flatten() {
            if let Ok(file_type) = entry.file_type() {
                if file_type.is_dir() {
                    let name = entry.file_name().to_string_lossy().into_owned();
                    let metadata = entry.metadata().ok();
                    let updated_at = metadata
                        .and_then(|m| m.modified().ok())
                        .and_then(|t| t.duration_since(std::time::UNIX_EPOCH).ok())
                        .map(|d| d.as_secs())
                        .unwrap_or(0);
                    
                    results.push(json!({
                        "name": name,
                        "updated_at": updated_at
                    }));
                }
            }
        }
    }
    
    // 按时间降序排序
    results.sort_by(|a, b| {
         let b_time = b.get("updated_at").and_then(|v| v.as_u64()).unwrap_or(0);
         let a_time = a.get("updated_at").and_then(|v| v.as_u64()).unwrap_or(0);
         b_time.cmp(&a_time).reverse()
     });
 
     Ok(results)
 }

#[tauri::command]
fn open_folder(path: String) -> Result<(), String> {
    let dir = std::path::Path::new(&path);
    if !dir.exists() {
        std::fs::create_dir_all(dir).map_err(|e| e.to_string())?;
    }

    #[cfg(target_os = "windows")]
    {
        std::process::Command::new("explorer")
            .arg(&path)
            .spawn()
            .map_err(|e| e.to_string())?;
    }
    #[cfg(target_os = "macos")]
    {
        std::process::Command::new("open")
            .arg(&path)
            .spawn()
            .map_err(|e| e.to_string())?;
    }
    #[cfg(target_os = "linux")]
    {
        std::process::Command::new("xdg-open")
            .arg(&path)
            .spawn()
            .map_err(|e| e.to_string())?;
    }
    Ok(())
}
