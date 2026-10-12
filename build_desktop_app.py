import os
import json
import subprocess
import sys
from pathlib import Path

# Inject Cargo into PATH if present
user_cargo_bin = Path.home() / ".cargo" / "bin"
if user_cargo_bin.exists():
    cargo_str = str(user_cargo_bin)
    if cargo_str not in os.environ["PATH"]:
        os.environ["PATH"] = f"{cargo_str}{os.pathsep}{os.environ['PATH']}"

def check_command(cmd):
    return subprocess.call(
        f"which {cmd}" if os.name != "nt" else f"where {cmd}",
        shell=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    ) == 0

def fix_tauri_conf(base_dir, pkg_mgr):
    """Updates tauri.conf.json beforeBuildCommand to match installed package manager."""
    tauri_conf_path = base_dir / "src-tauri" / "tauri.conf.json"
    if tauri_conf_path.exists():
        try:
            content = json.loads(tauri_conf_path.read_text(encoding="utf-8"))
            build_cmd = f"{pkg_mgr} run build"
            
            if content.get("build", {}).get("beforeBuildCommand") != build_cmd:
                content["build"]["beforeBuildCommand"] = build_cmd
                tauri_conf_path.write_text(json.dumps(content, indent=2), encoding="utf-8")
                print(f" ✓ Updated tauri.conf.json beforeBuildCommand to '{build_cmd}'")
        except Exception as e:
            print(f" ⚠ Could not update tauri.conf.json: {e}")

def apply_download_modifications(base_dir):
    print("\n[Step 1/3] Applying download location prompt modifications...")
    
    download_utils_path = base_dir / "js" / "download-utils.ts"
    downloads_path = base_dir / "js" / "downloads.js"

    # 1. Modify js/download-utils.ts (with strict duplication check)
    if download_utils_path.exists():
        content = download_utils_path.read_text(encoding="utf-8")
        
        # Strip out duplicate function additions if they exist from previous runs
        if "export async function getCustomSavePath" in content:
            content = content.split("export async function getCustomSavePath")[0].strip()

        if "@tauri-apps/plugin-dialog" not in content:
            content = "import { save, open } from '@tauri-apps/plugin-dialog';\n" + content

        helper_code = """

export async function getCustomSavePath(defaultFilename: string): Promise<string | null> {
  try {
    const filePath = await save({
      title: 'Select Download Location',
      defaultPath: defaultFilename,
    });
    return filePath;
  } catch (e) {
    console.error('Error selecting file path:', e);
    return null;
  }
}

export async function getCustomFolder(): Promise<string | null> {
  try {
    const folderPath = await open({
      directory: true,
      multiple: false,
      title: 'Select Folder for Bulk Downloads',
    });
    return folderPath ? (Array.isArray(folderPath) ? folderPath[0] : folderPath) : null;
  } catch (e) {
    console.error('Error selecting folder:', e);
    return null;
  }
}
"""
        download_utils_path.write_text(content + helper_code, encoding="utf-8")
        print(f" ✓ Cleaned and Updated: {download_utils_path}")

    # 2. Modify js/downloads.js (with duplication check)
    if downloads_path.exists():
        content = downloads_path.read_text(encoding="utf-8")
        
        if "window.__getDownloadPathPrompt" in content:
            content = content.split("// Interceptor to always ask for download directory")[0].strip()

        wrapper_code = """

// Interceptor to always ask for download directory/file location
if (typeof window !== 'undefined') {
  window.__getDownloadPathPrompt = async function(defaultName, isBulk = false) {
    try {
      const { save, open } = await import('@tauri-apps/plugin-dialog');
      if (isBulk) {
        const folder = await open({
          directory: true,
          multiple: false,
          title: 'Choose Destination Folder for Bulk Download'
        });
        return folder ? (Array.isArray(folder) ? folder[0] : folder) : null;
      } else {
        const filePath = await save({
          title: 'Save Audio File',
          defaultPath: defaultName
        });
        return filePath || null;
      }
    } catch (err) {
      console.warn('Dialog closed or unavailable:', err);
      return null;
    }
  };
}
"""
        downloads_path.write_text(content + wrapper_code, encoding="utf-8")
        print(f" ✓ Cleaned and Updated: {downloads_path}")

def run_build():
    print("=== Complete Desktop App Build Script ===")

    working_dir = Path(".").resolve()
    if (working_dir / "desktop-app-2.0.17" / "package.json").exists() and not (working_dir / "package.json").exists():
        working_dir = working_dir / "desktop-app-2.0.17"

    os.chdir(working_dir)
    print(f"Working Directory: {working_dir.resolve()}")

    if not check_command("cargo"):
        print("\n❌ Error: Rust/Cargo compiler was not found in your system PATH.")
        sys.exit(1)

    pkg_mgr = "bun" if check_command("bun") else ("npm" if check_command("npm") else None)
    if not pkg_mgr:
        print("\n❌ Error: Neither npm nor Bun was found in your PATH.")
        sys.exit(1)

    print(f"Using Package Manager: {pkg_mgr}")

    # Fix beforeBuildCommand in tauri.conf.json
    fix_tauri_conf(working_dir, pkg_mgr)

    # Step 1: Apply source modifications safely
    apply_download_modifications(working_dir)

    # Step 2: Sync exact matching Tauri package versions
    print("\n[Step 2/3] Syncing Tauri NPM dependencies...")
    
    tauri_matching_pkgs = [
        "@tauri-apps/api@~2.11.0",
        "@tauri-apps/plugin-process@~2.3.0",
        "@tauri-apps/plugin-updater@~2.10.0",
        "@tauri-apps/plugin-opener@~2.5.0",
        "@tauri-apps/plugin-dialog@~2.2.0"
    ]

    if pkg_mgr == "npm":
        install_matched = [pkg_mgr, "install", "--save-exact"] + tauri_matching_pkgs + ["--legacy-peer-deps"]
        install_all = [pkg_mgr, "install", "--legacy-peer-deps"]
    else:
        install_matched = [pkg_mgr, "add", "--exact"] + tauri_matching_pkgs
        install_all = [pkg_mgr, "install"]

    subprocess.run(install_matched, check=True, shell=(os.name == "nt"))
    subprocess.run(install_all, check=True, shell=(os.name == "nt"))

    # Step 3: Build production app
    print("\n[Step 3/3] Compiling Tauri Desktop Application (this will take a few minutes)...")
    build_cmd = ["npx", "tauri", "build"] if pkg_mgr == "npm" else ["bun", "run", "tauri", "build"]
    
    res = subprocess.run(build_cmd, shell=(os.name == "nt"))

    if res.returncode == 0:
        bundle_path = working_dir / "src-tauri" / "target" / "release" / "bundle"
        print("\n🎉 BUILD SUCCESSFUL!")
        print(f"Your installers are ready at:\n{bundle_path.resolve()}")
    else:
        print("\n❌ Build failed. Please check the output above for compiler errors.")

if __name__ == "__main__":
    run_build()