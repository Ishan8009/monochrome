import os
import subprocess
import sys
import zipfile
import urllib.request
from pathlib import Path

GITHUB_WORKFLOW_CONTENT = """name: Build Desktop App

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
          npm install --save-exact @tauri-apps/api@~2.11.0 @tauri-apps/plugin-process@~2.3.0 @tauri-apps/plugin-updater@~2.10.0 @tauri-apps/plugin-opener@~2.5.0 @tauri-apps/plugin-dialog@~2.2.0 --legacy-peer-deps
          npm install --legacy-peer-deps

      - name: Build Tauri Desktop Installer
        run: npx tauri build

      - name: Upload Installer Artifacts
        uses: actions/upload-artifact@v4
        with:
          name: Monochrome-Desktop-Installer
          path: src-tauri/target/release/bundle/
"""

def ensure_git():
    """Checks for system git; if missing, downloads Portable Git automatically."""
    try:
        subprocess.run(["git", "--version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        return "git"
    except (subprocess.CalledProcessError, FileNotFoundError):
        print(" ⚠ System Git not found. Downloading Portable Git...")

    git_dir = Path.home() / ".portable_git"
    git_bin = git_dir / "cmd" / "git.exe"

    if not git_bin.exists():
        git_zip_url = "https://github.com/git-for-windows/git/releases/download/v2.44.0.windows.1/MinGit-2.44.0-64-bit.zip"
        zip_path = Path.home() / "mingit.zip"

        print(" [1/2] Downloading minimal Git package (~25MB)...")
        urllib.request.urlretrieve(git_zip_url, zip_path)

        print(" [2/2] Extracting Git binaries...")
        git_dir.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(git_dir)

        if zip_path.exists():
            zip_path.unlink()

    print(" ✓ Portable Git ready!")
    return str(git_bin)

def main():
    print("=== GitHub Actions Cloud Build Setup ===")
    
    # Resolve working directory
    working_dir = Path(".").resolve()
    if (working_dir / "desktop-app-2.0.17" / "package.json").exists() and not (working_dir / "package.json").exists():
        working_dir = working_dir / "desktop-app-2.0.17"

    os.chdir(working_dir)
    print(f"Working Directory: {working_dir.resolve()}")

    git_cmd = ensure_git()

    # 1. Configure default Git username & email if not set
    subprocess.run([git_cmd, "config", "user.email", "developer@local.com"], check=False)
    subprocess.run([git_cmd, "config", "user.name", "Developer"], check=False)

    # 2. Initialize Git repo if needed
    git_repo_check = subprocess.run([git_cmd, "rev-parse", "--is-inside-work-tree"], capture_output=True, text=True)
    if git_repo_check.returncode != 0:
        print("\nInitializing Git repository...")
        subprocess.run([git_cmd, "init"], check=True)
        subprocess.run([git_cmd, "branch", "-M", "main"], check=True)

    # 3. Ensure Remote Origin URL is set
    remote_check = subprocess.run([git_cmd, "remote", "get-url", "origin"], capture_output=True, text=True)
    if remote_check.returncode != 0 or not remote_check.stdout.strip():
        print("\n" + "="*50)
        repo_url = input("Enter your GitHub repository URL (e.g., https://github.com/username/repo.git): ").strip()
        if repo_url:
            subprocess.run([git_cmd, "remote", "add", "origin", repo_url], check=True)
        else:
            print("❌ Repository URL is required to push to GitHub.")
            sys.exit(1)

    # 4. Create .github/workflows/build.yml
    workflow_dir = working_dir / ".github" / "workflows"
    workflow_dir.mkdir(parents=True, exist_ok=True)
    workflow_file = workflow_dir / "build.yml"
    workflow_file.write_text(GITHUB_WORKFLOW_CONTENT, encoding="utf-8")
    print(f"\n ✓ Created GitHub workflow file: {workflow_file}")

    # 5. Commit and Push
    try:
        print("\nCommitting and pushing changes to GitHub...")
        subprocess.run([git_cmd, "add", "."], check=True)
        subprocess.run([git_cmd, "commit", "-m", "Add GitHub Actions workflow for desktop app build"], check=False)
        subprocess.run([git_cmd, "push", "-u", "origin", "main"], check=True)
        
        print("\n🎉 SETUP COMPLETE!")
        print("1. Open your GitHub repository in your browser.")
        print("2. Click on the 'Actions' tab.")
        print("3. Watch the 'Build Desktop App' workflow compile your application.")
        print("4. Download the generated .exe installer from 'Artifacts' when finished!")

    except subprocess.CalledProcessError as e:
        print(f"\n⚠ Push failed: {e}")
        print("Make sure you have created an empty repository on GitHub and entered the correct URL.")

if __name__ == "__main__":
    main()