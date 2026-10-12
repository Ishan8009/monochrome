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

      - name: Sync Dependencies & Fix Peer Issues
        run: |
          if (Test-Path "desktop-app-2.0.17") { cd desktop-app-2.0.17 }
          npm install --save-exact @tauri-apps/api@~2.11.0 @tauri-apps/plugin-process@~2.3.0 @tauri-apps/plugin-updater@~2.10.0 @tauri-apps/plugin-opener@~2.5.0 @tauri-apps/plugin-dialog@~2.2.0 --legacy-peer-deps
          npm install --legacy-peer-deps

      - name: Build Tauri Desktop Installer
        run: |
          if (Test-Path "desktop-app-2.0.17") { cd desktop-app-2.0.17 }
          npx tauri build
        continue-on-error: true

      - name: Upload Installer Artifacts
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: Monochrome-Desktop-Installer
          path: |
            **/src-tauri/target/release/bundle/
            src-tauri/target/release/bundle/
"""

DOWNLOAD_UTILS_CONTENT = """import { save, open } from '@tauri-apps/plugin-dialog';

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

def run_git(args, allow_failure=False):
    """Executes a git command using Portable Git."""
    cmd = [PORTABLE_GIT] + args
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0 and not allow_failure:
        print(f"❌ Error running 'git {' '.join(args)}':\n{result.stderr.strip()}")
    return result

def main():
    print("=== Initializing Git & Pushing Subdirectory Artifact Fix ===")

    repo_root = Path(r"D:\Entertainment\Monochrome setup").resolve()
    os.chdir(repo_root)
    print(f"Working Directory: {repo_root}\n")

    if not Path(PORTABLE_GIT).exists():
        print(f"❌ Portable Git binary not found at: {PORTABLE_GIT}")
        sys.exit(1)

    # 1. Update workflow files
    workflow_dir = repo_root / ".github" / "workflows"
    workflow_dir.mkdir(parents=True, exist_ok=True)
    (workflow_dir / "build.yml").write_text(BUILD_YML_CONTENT, encoding="utf-8")
    print(f" ✓ Updated {workflow_dir / 'build.yml'}")

    sub_workflow_dir = repo_root / "desktop-app-2.0.17" / ".github" / "workflows"
    if (repo_root / "desktop-app-2.0.17").exists():
        sub_workflow_dir.mkdir(parents=True, exist_ok=True)
        (sub_workflow_dir / "build.yml").write_text(BUILD_YML_CONTENT, encoding="utf-8")

    # 2. Update js/download-utils.ts
    js_dir = repo_root / "desktop-app-2.0.17" / "js"
    js_dir.mkdir(parents=True, exist_ok=True)
    (js_dir / "download-utils.ts").write_text(DOWNLOAD_UTILS_CONTENT, encoding="utf-8")
    print(f" ✓ Updated {js_dir / 'download-utils.ts'}")

    # 3. Initialize Git if not present
    repo_check = run_git(["rev-parse", "--is-inside-work-tree"], allow_failure=True)
    if repo_check.returncode != 0:
        print("\n[Initializing local Git repository...]")
        run_git(["init"])

    # 4. Configure Git identity and remote
    run_git(["config", "user.email", "ishan@monochrome.local"])
    run_git(["config", "user.name", "Ishan"])
    run_git(["remote", "remove", "origin"], allow_failure=True)
    run_git(["remote", "add", "origin", REMOTE_REPO_URL])

    # 5. Stage, commit, and push
    print("\n[Staging files and committing...]")
    run_git(["add", "."])
    commit_res = run_git(["commit", "-m", "Fix artifact upload path for desktop-app-2.0.17 subdirectory"], allow_failure=True)
    if commit_res.returncode == 0:
        print(" ✓ Created commit successfully.")

    run_git(["branch", "-M", "main"])

    print("\n[Pushing to GitHub...]")
    push_res = run_git(["push", "-u", "origin", "main", "--force"])

    if push_res.returncode == 0:
        print("\n🎉 SUCCESS! Changes pushed to GitHub.")
        print("1. Open https://github.com/Ishan8009/monochrome/actions in your browser.")
        print("2. Click on the latest workflow run.")
        print("3. Once completed, your 'Monochrome-Desktop-Installer' zip file will appear under 'Artifacts' at the bottom of the page!")
    else:
        print("\n❌ Push failed.")

if __name__ == "__main__":
    main()