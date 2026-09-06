// desktop/src-tauri/src/main.rs

#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

use std::io::{Write, BufRead, BufReader};
use std::net::TcpStream;
use std::process::{Command, Stdio, Child};
use std::sync::Mutex;
use std::time::Duration;
use serde_json::json;
use tauri::{Manager, Emitter};

// ─── State ────────────────────────────────────────────────────────────

struct AppState {
    backend_ready: Mutex<bool>,
    backend_pid: Mutex<Option<u32>>,
}

impl Default for AppState {
    fn default() -> Self {
        Self {
            backend_ready: Mutex::new(false),
            backend_pid: Mutex::new(None),
        }
    }
}

// ─── Commands ─────────────────────────────────────────────────────────

#[tauri::command]
fn start_backend(app: tauri::AppHandle) -> Result<String, String> {
    let base_path = std::path::PathBuf::from("C:/Users/DaveH/Navi-G8/agent");
    let python_path = base_path.join(".venv").join("Scripts").join("python.exe");

    if !python_path.exists() {
        return Err(format!("Python not found at: {:?}", python_path));
    }

    println!("🔧 Starting backend at: {:?}", base_path);
    println!("🔧 Python: {:?}", python_path);

    // ─── Spawn backend with piped output (so we can capture logs) ──
    let mut child = Command::new(&python_path)
        .arg("-m")
        .arg("navi_agent")
        .arg("--mode")
        .arg("daemon")
        .current_dir(&base_path)
        .stdin(Stdio::piped())   // we might not need stdin, but keep it
        .stdout(Stdio::piped())
        .stderr(Stdio::piped())
        .spawn()
        .map_err(|e| format!("Failed to start backend: {}", e))?;

    let pid = child.id();
    println!("✅ Backend PID: {}", pid);

    // ─── Store PID in state ──────────────────────────────────────────
    let state = app.state::<AppState>();
    {
        let mut guard = state.backend_pid.lock().unwrap();
        *guard = Some(pid);
    }

    // ─── Spawn threads to capture stdout and stderr ──────────────────
    let stdout = child.stdout.take().expect("Failed to take stdout");
    let stderr = child.stderr.take().expect("Failed to take stderr");

    std::thread::spawn(move || {
        let reader = BufReader::new(stdout);
        for line in reader.lines() {
            if let Ok(line) = line {
                println!("[BACKEND stdout] {}", line);
            }
        }
    });

    std::thread::spawn(move || {
        let reader = BufReader::new(stderr);
        for line in reader.lines() {
            if let Ok(line) = line {
                eprintln!("[BACKEND stderr] {}", line);
            }
        }
    });

    // ─── Wait for socket to be ready ──────────────────────────────────
    println!("⏳ Waiting for backend to be ready...");
    let mut attempts = 0;
    let max_attempts = 50;
    let mut ready = false;

    while attempts < max_attempts {
        // Check if the process is still alive
        match child.try_wait() {
            Ok(Some(status)) => {
                return Err(format!("Backend exited early with status: {}", status));
            }
            Ok(None) => {
                // still running
            }
            Err(e) => {
                println!("⚠️ Error checking process: {}", e);
            }
        }

        // Try to connect to the socket
        if let Ok(_) = TcpStream::connect("127.0.0.1:9876") {
            ready = true;
            break;
        }

        std::thread::sleep(Duration::from_millis(200));
        attempts += 1;
    }

    if !ready {
        // If not ready, check if process is still alive and dump logs
        if let Ok(Some(status)) = child.try_wait() {
            return Err(format!("Backend exited with status: {} before becoming ready", status));
        } else {
            // Process is still running but socket never became ready – kill it
            let _ = child.kill();
            return Err("Backend started but never became ready. Check logs above.".to_string());
        }
    }

    // ─── Store ready state ──────────────────────────────────────────
    {
        let mut guard = state.backend_ready.lock().unwrap();
        *guard = true;
    }

    println!("✅ Backend is ready");
    Ok("Backend started".to_string())
}

#[tauri::command]
fn send_query(query: String, app: tauri::AppHandle) -> Result<String, String> {
    println!("📨 Received query: {}", query);

    let state = app.state::<AppState>();
    let guard = state.backend_ready.lock().unwrap();
    if !*guard {
        return Err("Backend not ready".to_string());
    }

    // Connect to the backend socket
    let mut stream = TcpStream::connect("127.0.0.1:9876")
        .map_err(|e| format!("Failed to connect to backend: {}", e))?;

    let request = json!({ "type": "query", "query": query });
    let data = request.to_string();

    writeln!(stream, "{}", data)
        .map_err(|e| format!("Failed to send query: {}", e))?;
    stream.flush()
        .map_err(|e| format!("Failed to flush: {}", e))?;

    // Read response
    let mut reader = BufReader::new(stream);
    let mut response_line = String::new();
    reader.read_line(&mut response_line)
        .map_err(|e| format!("Failed to read response: {}", e))?;

    println!("📤 Backend response: {}", response_line);

    // Forward to frontend via event
    app.emit("field_event", response_line.as_str()).ok();

    Ok("Query sent".to_string())
}

#[tauri::command]
fn get_state(app: tauri::AppHandle) -> Result<String, String> {
    println!("📨 State requested");

    let state = app.state::<AppState>();
    let guard = state.backend_ready.lock().unwrap();
    if !*guard {
        return Err("Backend not ready".to_string());
    }

    let mut stream = TcpStream::connect("127.0.0.1:9876")
        .map_err(|e| format!("Failed to connect to backend: {}", e))?;

    let request = json!({ "type": "state" });
    let data = request.to_string();

    writeln!(stream, "{}", data)
        .map_err(|e| format!("Failed to send state request: {}", e))?;
    stream.flush()
        .map_err(|e| format!("Failed to flush: {}", e))?;

    let mut reader = BufReader::new(stream);
    let mut response_line = String::new();
    reader.read_line(&mut response_line)
        .map_err(|e| format!("Failed to read state response: {}", e))?;

    println!("📤 State response: {}", response_line);

    app.emit("field_event", response_line.as_str()).ok();

    Ok("State requested".to_string())
}

// ─── Main ─────────────────────────────────────────────────────────────

fn main() {
    tauri::Builder::default()
        .manage(AppState::default())
        .invoke_handler(tauri::generate_handler![
            start_backend,
            send_query,
            get_state
        ])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}