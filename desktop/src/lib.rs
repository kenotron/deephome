use tauri::{AppHandle, Emitter};
use pyo3::prelude::*;
use std::sync::Arc;

// Define a struct to hold the AppHandle safely for Python callbacks
#[pyclass]
#[derive(Clone)]
struct AgentCallback {
    app: Arc<AppHandle>,
}

#[pymethods]
impl AgentCallback {
    fn __call__(&self, event_type: String, payload: String) {
        let _ = self.app.emit(&format!("agent-{}", event_type), payload);
    }
}

#[tauri::command]
async fn manifest_agent(app: AppHandle, prompt: String) -> Result<(), String> {
    println!("Agent received prompt: {}", prompt);
    
    let app_handle = Arc::new(app);
    
    // Offload Python work to a blocking thread to avoid freezing the async runtime
    tauri::async_runtime::spawn_blocking(move || {
        Python::with_gil(|py| {
             // 1. Setup path to include our local python folder
             let sys = py.import("sys").map_err(|e| e.to_string())?;
             let path = sys.getattr("path").map_err(|e| e.to_string())?;
             
             // Get resource path for "server"
             // In dev, assume we are in desktop/ and server is at ../server
             let current_dir = std::env::current_dir().unwrap();
             // If we are in desktop/, parent is root. join("server")
             // Trying relative path "../server" often works if CWD is correct
             let py_dir = current_dir.parent().unwrap().join("server");
             let py_dir_str = py_dir.to_string_lossy();
             path.call_method1("append", (py_dir_str,)).map_err(|e| e.to_string())?;

             // 2. Import agent module
             let agent = py.import("agent").map_err(|e| e.to_string())?;
             
             // 3. Create callback
             let callback = AgentCallback { app: app_handle };
             
             // 4. Call run_agent(prompt, callback)
             let args = (prompt, callback);
             agent.call_method1("run_agent", args).map_err(|e| e.to_string())?;
             
             Ok::<(), String>(())
        }).map_err(|e| e.to_string())
    });

    Ok(())
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
  pyo3::prepare_freethreaded_python();

  tauri::Builder::default()
    .setup(|app| {
      #[cfg(debug_assertions)]
      {
        let _ = app.handle().plugin(
          tauri_plugin_log::Builder::default()
            .level(log::LevelFilter::Info)
            .build(),
        );
      }
      Ok(())
    })
    .invoke_handler(tauri::generate_handler![manifest_agent])
    .run(tauri::generate_context!())
    .expect("error while running tauri application");
}
