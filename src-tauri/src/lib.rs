use serde_json::Value;
use std::process::Stdio;
use tokio::io::{AsyncBufReadExt, BufReader};
use tokio::process::Command;
use tauri::{AppHandle, Emitter};
use std::sync::{Arc, Mutex};
use std::collections::HashMap;
use tokio::sync::Semaphore;

// Learn more about Tauri commands at https://tauri.app/develop/calling-rust/
#[tauri::command]
fn greet(name: &str) -> String {
    format!("Hello, {}! You've been greeted from Rust!", name)
}

async fn fetch_page_data(
    page: i32,
    size: i32,
    python_path: &str,
    app_handle: AppHandle,
    progress_map: Arc<Mutex<HashMap<i32, i32>>>,
    total_shards: i32,
) -> Result<Vec<Value>, String> {
    let mut child = Command::new(python_path)
        .arg("lib/data_fetching.py")
        .arg("--page")
        .arg(page.to_string())
        .arg("--size")
        .arg(size.to_string())
        .env("PYTHONIOENCODING", "utf-8")
        .stdout(Stdio::piped())
        .stderr(Stdio::piped())
        .spawn()
        .map_err(|e| format!("无法启动分片 {}: {}", page, e))?;

    let stdout = child.stdout.take().ok_or("无法打开 stdout")?;
    let mut reader = BufReader::new(stdout).lines();
    let mut last_json = String::new();

    while let Some(line) = reader.next_line().await.map_err(|e| e.to_string())? {
        let trimmed = line.trim();
        if trimmed.is_empty() {
            continue;
        }
        
        if trimmed.starts_with("PROGRESS:") {
            if let Ok(p) = trimmed.trim_start_matches("PROGRESS:").trim().parse::<i32>() {
                let mut map = progress_map.lock().unwrap();
                map.insert(page, p);
                
                let total_p: i32 = map.values().sum();
                let avg_progress = total_p / total_shards;
                app_handle.emit("refresh-progress", avg_progress).unwrap();
            }
        } else if trimmed.starts_with('[') {
            // 只有以 [ 开头的行才被认为是 JSON 数据行
            last_json = trimmed.to_string();
        }
    }

    let _ = child.wait().await;
    
    let data: Value = serde_json::from_str(&last_json)
        .map_err(|e| format!("解析分片 {} 失败: {}", page, e))?;

    if let Some(arr) = data.as_array() {
        Ok(arr.clone())
    } else {
        Ok(vec![])
    }
}

#[tauri::command]
async fn get_stock_data(app: AppHandle) -> Result<Value, String> {
    let python_path = if cfg!(windows) {
        "../.venv/Scripts/python.exe"
    } else {
        "../.venv/bin/python"
    };

    let shard_size = 100; // 东方财富 API 限制每页最多 100 条
    let total_shards = 65; // 65 个分片 * 100 = 6500 只，足以覆盖全量 A 股
    let progress_map = Arc::new(Mutex::new(HashMap::new()));
    let semaphore = Arc::new(Semaphore::new(10)); // 限制并发数为 10，避免被封禁
    
    for i in 1..=total_shards {
        progress_map.lock().unwrap().insert(i, 0);
    }

    let mut tasks = vec![];
    for i in 1..=total_shards {
        let app_clone = app.clone();
        let p_path = python_path.to_string();
        let p_map = Arc::clone(&progress_map);
        let sem = Arc::clone(&semaphore);
        
        tasks.push(tokio::spawn(async move {
            let _permit = sem.acquire().await.unwrap(); // 获取信号量许可
            let res = fetch_page_data(i, shard_size, &p_path, app_clone, p_map, total_shards).await;
            if let Err(ref e) = res {
                eprintln!("分片 {} 获取失败: {}", i, e);
            }
            res
        }));
    }

    let mut all_data = vec![];
    let mut success_count = 0;
    for task in tasks {
        match task.await {
            Ok(Ok(result)) => {
                all_data.extend(result);
                success_count += 1;
            }
            Ok(Err(e)) => {
                eprintln!("获取分片数据出错: {}", e);
            }
            Err(e) => {
                eprintln!("任务执行出错: {}", e);
            }
        }
    }

    println!("成功获取 {}/{} 个分片的数据，总计 {} 条记录", success_count, total_shards, all_data.len());

    app.emit("refresh-progress", 100).unwrap();
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
    let mut stderr_reader = BufReader::new(stderr).lines();

    let app_handle = app.clone();
    let (tx, mut rx) = tauri::async_runtime::channel::<String>(1);

    // 处理 stderr 用于所有实时消息、进度和结果
    let stderr_task = tauri::async_runtime::spawn(async move {
        let mut last_success = String::from("同步结束");
        while let Ok(Some(line)) = stderr_reader.next_line().await {
            if line.starts_with("PROGRESS:") {
                if let Ok(p) = line.trim_start_matches("PROGRESS:").trim().parse::<i32>() {
                    app_handle.emit("download-progress", p).unwrap();
                }
            } else if line.starts_with("INFO:") || line.starts_with("ERROR:") {
                app_handle.emit("download-status", line.clone()).unwrap();
            } else if line.starts_with("SUCCESS:") {
                last_success = line.trim_start_matches("SUCCESS:").trim().to_string();
            }
        }
        let _ = tx.send(last_success).await;
    });

    let final_result = rx.recv().await.unwrap_or_else(|| "下载完成".to_string());
    let _ = stderr_task.await;
    let status = child.wait().await.map_err(|e| e.to_string())?;
    if status.success() {
        Ok(final_result)
    } else {
        Err(format!("下载脚本执行失败 (退出码: {:?})。请检查标的代码是否正确或网络是否连接。", status.code()))
    }
}

#[derive(serde::Serialize)]
struct DownloadedItem {
    name: String,
    updated_at: u64,
}

#[tauri::command]
fn list_downloaded_finance(path: String) -> Result<Vec<DownloadedItem>, String> {
    let mut entries = Vec::new();
    let dir = std::path::Path::new(&path);
    
    if !dir.exists() {
        return Ok(entries);
    }

    if let Ok(read_dir) = std::fs::read_dir(dir) {
        for entry in read_dir {
            if let Ok(entry) = entry {
                if entry.file_type().map(|t| t.is_dir()).unwrap_or(false) {
                    let metadata = entry.metadata().map_err(|e| e.to_string())?;
                    let modified = metadata.modified().map_err(|e| e.to_string())?
                        .duration_since(std::time::UNIX_EPOCH)
                        .map_err(|e| e.to_string())?
                        .as_secs();

                    if let Some(name) = entry.file_name().to_str() {
                        entries.push(DownloadedItem {
                            name: name.to_string(),
                            updated_at: modified,
                        });
                    }
                }
            }
        }
    }
    
    // 按修改时间倒序排列，最新的在前
    entries.sort_by(|a, b| b.updated_at.cmp(&a.updated_at));
    Ok(entries)
}

#[tauri::command]
fn open_folder(path: String) -> Result<(), String> {
    let dir = std::path::Path::new(&path);
    if !dir.exists() {
        std::fs::create_dir_all(dir).map_err(|e| e.to_string())?;
    }

    #[cfg(target_os = "windows")]
    {
        Command::new("explorer")
            .arg(path)
            .spawn()
            .map_err(|e| e.to_string())?;
    }

    #[cfg(target_os = "macos")]
    {
        Command::new("open")
            .arg(path)
            .spawn()
            .map_err(|e| e.to_string())?;
    }

    #[cfg(target_os = "linux")]
    {
        Command::new("xdg-open")
            .arg(path)
            .spawn()
            .map_err(|e| e.to_string())?;
    }

    Ok(())
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_opener::init())
        .invoke_handler(tauri::generate_handler![
            greet, 
            get_stock_data,
            download_finance_data,
            list_downloaded_finance,
            open_folder
        ])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
