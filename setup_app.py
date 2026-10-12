import os
import subprocess
import sys
from pathlib import Path

def check_command(cmd):
    """Check if a CLI tool is available in the PATH."""
    return subprocess.call(f"which {cmd}" if os.name != "nt" else f"where {cmd}", 
                           shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL) == 0

def setup_and_run():
    print("=== Desktop Application Setup ===")

    # 1. Detect working directory
    working_dir = Path(".")
    if not (working_dir / "package.json").exists() and (working_dir / "desktop-app-2.0.17" / "package.json").exists():
        working_dir = working_dir / "desktop-app-2.0.17"

    os.chdir(working_dir)
    print(f"Working directory set to: {working_dir.resolve()}")

    # 2. Determine package manager (prefer bun, fallback to pnpm or npm)
    pkg_mgr = None
    if check_command("bun"):
        pkg_mgr = "bun"
    elif check_command("pnpm"):
        pkg_mgr = "pnpm"
    elif check_command("npm"):
        pkg_mgr = "npm"
    else:
        print("Error: Neither Bun, pnpm, nor npm was found in your PATH.")
        print("Please install Node.js (https://nodejs.org) or Bun (https://bun.sh).")
        sys.exit(1)

    print(f"Using package manager: {pkg_mgr}")

    # 3. Install Tauri Dialog Plugin
    print("\nInstalling Tauri dialog plugin...")
    if pkg_mgr == "npm":
        add_cmd = [pkg_mgr, "install", "@tauri-apps/plugin-dialog", "--legacy-peer-deps"]
    elif pkg_mgr == "pnpm":
        add_cmd = [pkg_mgr, "add", "@tauri-apps/plugin-dialog"]
    else:
        add_cmd = [pkg_mgr, "add", "@tauri-apps/plugin-dialog"]

    subprocess.run(add_cmd, check=True, shell=(os.name == "nt"))

    # 4. Install project dependencies
    print("\nInstalling project dependencies...")
    install_cmd = [pkg_mgr, "install", "--legacy-peer-deps"] if pkg_mgr == "npm" else [pkg_mgr, "install"]
    subprocess.run(install_cmd, check=True, shell=(os.name == "nt"))

    # 5. Prompt user to run or build
    print("\nSetup complete! Select an option to proceed:")
    print("1) Run Application in Development Mode")
    print("2) Build Production Installers")
    choice = input("Enter choice (1/2) [default: 1]: ").strip()

    run_cmd = [pkg_mgr, "run", "build"] if choice == "2" else [pkg_mgr, "run", "dev"]
    print(f"\nExecuting: {' '.join(run_cmd)}")
    subprocess.run(run_cmd, check=True, shell=(os.name == "nt"))

if __name__ == "__main__":
    setup_and_run()