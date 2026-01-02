use pyo3::prelude::*;
use pyo3::types::PyModule;
use pyo3::Bound;
use std::io::{self, Write};
use std::process::{Command, Stdio};
use std::env;
use std::path::PathBuf;
use std::fs;
use tempfile::NamedTempFile;
use rand::Rng;

/// Formats the sum of two numbers as a string.
#[pyfunction]
fn sum_as_string(a: usize, b: usize) -> PyResult<String> {
    Ok((a + b).to_string())
}

/// Generates a random 4-byte hex string for scoping.
/// This is optimized for speed to replace secrets.token_hex(4).
#[pyfunction]
fn generate_scope_id() -> PyResult<String> {
    let mut rng = rand::thread_rng();
    let mut bytes = [0u8; 4];
    rng.fill(&mut bytes);
    Ok(hex::encode(bytes))
}

fn get_platform_executable_name() -> Result<String, String> {
    let os = env::consts::OS;
    let arch = env::consts::ARCH;

    let platform = match (os, arch) {
        ("linux", "x86_64") => "tailwindcss-linux-x64",
        ("macos", "x86_64") => "tailwindcss-macos-x64",
        ("macos", "aarch64") => "tailwindcss-macos-arm64",
        ("windows", "x86_64") => "tailwindcss-windows-x64.exe",
        _ => return Err(format!("Unsupported platform: {}-{}", os, arch)),
    };
    Ok(platform.to_string())
}

fn get_executable_path() -> Result<PathBuf, String> {
    let cache_dir = dirs::cache_dir().ok_or("Could not find cache directory")?;
    let executable_name = get_platform_executable_name()?;
    let executable_path = cache_dir.join("syqlorix").join(executable_name);
    Ok(executable_path)
}

fn download_executable(executable_path: &PathBuf) -> Result<(), String> {
    let executable_name = get_platform_executable_name()?;
    let version = "v3.4.1"; // As used in tailwind-processor
    let url = format!(
        "https://github.com/tailwindlabs/tailwindcss/releases/download/{}/{}",
        version, executable_name
    );

    let response = reqwest::blocking::get(&url)
        .map_err(|e| format!("Failed to download executable: {}", e))?;

    if !response.status().is_success() {
        return Err(format!("Failed to download executable: status code {}", response.status()));
    }

    let bytes = response.bytes().map_err(|e| format!("Failed to read response bytes: {}", e))?;

    fs::create_dir_all(executable_path.parent().unwrap())
        .map_err(|e| format!("Failed to create directory for executable: {}", e))?;
    
    fs::write(executable_path, bytes)
        .map_err(|e| format!("Failed to write executable to disk: {}", e))?;
    
    #[cfg(not(target_os = "windows"))]
    {
        use std::os::unix::fs::PermissionsExt;
        let mut perms = fs::metadata(executable_path).map_err(|e| format!("Failed to get metadata: {}", e))?.permissions();
        perms.set_mode(0o755);
        fs::set_permissions(executable_path, perms).map_err(|e| format!("Failed to set permissions: {}", e))?;
    }

    Ok(())
}

#[pyfunction]
fn process_tailwind_css(html_content: String) -> PyResult<String> {
    let executable_path = get_executable_path().map_err(PyErr::new::<pyo3::exceptions::PyRuntimeError, _>)?;

    if !executable_path.exists() {
        download_executable(&executable_path).map_err(PyErr::new::<pyo3::exceptions::PyRuntimeError, _>)?;
    }

    let mut temp_file = NamedTempFile::new().map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(format!("Failed to create temp file: {}", e)))?;
    temp_file.write_all(html_content.as_bytes()).map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(format!("Failed to write to temp file: {}", e)))?;
    
    let temp_path = temp_file.path().to_str().ok_or_else(|| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>("Failed to get temp file path"))?;

    let output = Command::new(&executable_path)
        .arg("--content")
        .arg(temp_path)
        .stdin(Stdio::null())
        .stdout(Stdio::piped())
        .stderr(Stdio::piped())
        .output()
        .map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(format!("Failed to spawn tailwindcss process: {}", e)))?;

    if !output.status.success() {
        return Err(PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(format!(
            "tailwindcss process exited with non-zero status: {}\n{}",
            output.status,
            String::from_utf8_lossy(&output.stderr)
        )));
    }

    Ok(String::from_utf8(output.stdout).map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(format!("Failed to decode stdout as utf8: {}", e)))?)
}

/// A Python module implemented in Rust.
#[pymodule]
fn syqlorix_rust(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(sum_as_string, m)?)?;
    m.add_function(wrap_pyfunction!(process_tailwind_css, m)?)?;
    m.add_function(wrap_pyfunction!(generate_scope_id, m)?)?;
    Ok(())
}
