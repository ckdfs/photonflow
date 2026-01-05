#![cfg_attr(
  all(not(debug_assertions), target_os = "windows"),
  windows_subsystem = "windows"
)]

use tauri::{AppHandle, Emitter, Manager};
use tauri_plugin_shell::ShellExt;
use tauri_plugin_shell::process::{CommandEvent, CommandChild};
use serde::Serialize;
use std::sync::Mutex;

struct SidecarState {
    child: Mutex<Option<CommandChild>>,
}

#[derive(Clone, Serialize)]
struct LoadingProgress {
    stage: String,
}

#[derive(Clone, Serialize)]
struct LoadingError {
    message: String,
}

fn parse_loading_stage(line: &str) -> Option<String> {
    // 解析格式: STAGE:stagename
    if line.starts_with("STAGE:") {
        Some(line[6..].trim().to_string())
    } else {
        None
    }
}

fn switch_to_main_window(app: &AppHandle) {
    // 获取窗口引用
    if let Some(splash) = app.get_webview_window("splash") {
        if let Some(main) = app.get_webview_window("main") {
            // 显示主窗口
            let _ = main.show();
            let _ = main.set_focus();
            // 延迟关闭splash窗口，确保主窗口已显示
            std::thread::sleep(std::time::Duration::from_millis(300));
            let _ = splash.close();
        }
    }
}

fn main() {
  tauri::Builder::default()
    .plugin(tauri_plugin_shell::init())
    .setup(|app| {
      let app_handle = app.handle().clone();
      let exit_handle = app.handle().clone();
      
      // 发送初始化阶段
      let _ = app_handle.emit("loading-progress", LoadingProgress {
          stage: "init".to_string(),
      });

      // 启动Python后端sidecar
      let (mut rx, child) = app.shell().sidecar("server")
        .expect("failed to create server binary command")
        .spawn()
        .expect("Failed to spawn sidecar");

      // 保存 child 进程句柄到应用状态
      app.manage(SidecarState {
          child: Mutex::new(Some(child)),
      });

      tauri::async_runtime::spawn(async move {
        while let Some(event) = rx.recv().await {
          match event {
            CommandEvent::Stdout(line) => {
              let line_str = String::from_utf8_lossy(&line);
              println!("Server: {}", line_str);
              
              // 解析加载阶段
              if let Some(stage) = parse_loading_stage(&line_str) {
                  let _ = app_handle.emit("loading-progress", LoadingProgress {
                      stage: stage.clone(),
                  });
                  
                  // 当服务器ready时，切换窗口
                  if stage == "ready" {
                      let app_clone = app_handle.clone();
                      std::thread::spawn(move || {
                          switch_to_main_window(&app_clone);
                      });
                  }
              }
            }
            CommandEvent::Stderr(line) => {
              let line_str = String::from_utf8_lossy(&line);
              eprintln!("Server Error: {}", line_str);
            }
            CommandEvent::Error(err) => {
              eprintln!("Sidecar error: {}", err);
              let _ = app_handle.emit("loading-error", LoadingError {
                  message: err.to_string(),
              });
            }
            CommandEvent::Terminated(status) => {
              eprintln!("Server terminated with: {:?}", status);
            }
            _ => {}
          }
        }
      });

      // 监听窗口关闭事件
      if let Some(window) = app.get_webview_window("main") {
        window.on_window_event(move |event| {
          if let tauri::WindowEvent::CloseRequested { .. } = event {
            eprintln!("Main window close requested, killing sidecar...");
            if let Some(state) = exit_handle.try_state::<SidecarState>() {
              if let Ok(mut child_guard) = state.child.lock() {
                if let Some(child) = child_guard.take() {
                  let _ = child.kill();
                  eprintln!("Sidecar process killed");
                }
              }
            }
            // 强制退出应用
            std::process::exit(0);
          }
        });
      }

      Ok(())
    })
    .build(tauri::generate_context!())
    .expect("error while building tauri application")
    .run(|_app_handle, _event| {});
}
