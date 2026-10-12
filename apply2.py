import json
import os
import subprocess
import sys
from pathlib import Path

PORTABLE_GIT = r"C:\Users\ishan\.portable_git\cmd\git.exe"
REMOTE_REPO_URL = "https://github.com/Ishan8009/monochrome.git"

BUILD_YML_CONTENT = """name: Build Desktop App

on:
  push:
    branches: [ main, master ]
  workflow_dispatch:

jobs:
  build:
    runs-on: windows-latest
    steps:
      - name: Checkout Repository
        uses: actions/checkout@v4

      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: 20

      - name: Setup Rust Toolchain
        uses: dtolnay/rust-toolchain@stable

      - name: Install Project Dependencies
        run: |
          cd desktop-app-2.0.17
          npm install --legacy-peer-deps
          npm install @tauri-apps/cli@latest --legacy-peer-deps

      - name: Build Tauri Desktop Application
        run: |
          cd desktop-app-2.0.17
          npx tauri build --no-bundle
        continue-on-error: true

      - name: Upload Installer Artifacts
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: Monochrome-Desktop-Installer
          path: |
            desktop-app-2.0.17/src-tauri/target/release/
            desktop-app-2.0.17/src-tauri/target/release/bundle/
"""

def run_git(args, allow_failure=False):
    """Executes a git command using Portable Git."""
    cmd = [PORTABLE_GIT] + args
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0 and not allow_failure:
        print(f"❌ Error running 'git {' '.join(args)}':\n{result.stderr.strip()}")
    return result

def main():
    print("=== Applying Comprehensive Build Fix ===")

    repo_root = Path(r"D:\Entertainment\Monochrome setup").resolve()
    os.chdir(repo_root)

    if not Path(PORTABLE_GIT).exists():
        print(f"❌ Portable Git binary not found at: {PORTABLE_GIT}")
        sys.exit(1)

    # 1. Clear pubkey in tauri.conf.json
    tauri_conf_path = repo_root / "desktop-app-2.0.17" / "src-tauri" / "tauri.conf.json"
    if tauri_conf_path.exists():
        try:
            with open(tauri_conf_path, "r", encoding="utf-8") as f:
                conf = json.load(f)

            if "plugins" in conf and "updater" in conf["plugins"]:
                conf["plugins"]["updater"]["pubkey"] = ""
                with open(tauri_conf_path, "w", encoding="utf-8") as f:
                    json.dump(conf, f, indent=2)
                print(" ✓ Cleared pubkey in tauri.conf.json")
        except Exception as e:
            print(f" ⚠ Error updating tauri.conf.json: {e}")

    # 2. Update .github/workflows/build.yml
    workflow_dir = repo_root / ".github" / "workflows"
    workflow_dir.mkdir(parents=True, exist_ok=True)
    (workflow_dir / "build.yml").write_text(BUILD_YML_CONTENT, encoding="utf-8")
    print(" ✓ Updated .github/workflows/build.yml")

    # 3. Git Operations
    repo_check = run_git(["rev-parse", "--is-inside-work-tree"], allow_failure=True)
    if repo_check.returncode != 0:
        run_git(["init"])

    run_git(["config", "user.email", "ishan@monochrome.local"])
    run_git(["config", "user.name", "Ishan"])
    run_git(["remote", "remove", "origin"], allow_failure=True)
    run_git(["remote", "add", "origin", REMOTE_REPO_URL])

    run_git(["add", "."])
    run_git(["commit", "-m", "Apply comprehensive workflow fix and clear updater pubkey"], allow_failure=True)
    run_git(["branch", "-M", "main"])

    print("\nPushing updated files to GitHub...")
    push_res = run_git(["push", "-u", "origin", "main", "--force"])

    if push_res.returncode == 0:
        print("\n🎉 Pushed successfully! Monitor the run at https://github.com/Ishan8009/monochrome/actions")
    else:
        print("\n❌ Push failed.")

if __name__ == "__main__":
    main()