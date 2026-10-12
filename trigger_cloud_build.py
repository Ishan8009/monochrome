import os
import subprocess
import sys
from pathlib import Path

# Path to the local Portable Git executable
PORTABLE_GIT = r"C:\Users\ishan\.portable_git\cmd\git.exe"
REMOTE_REPO_URL = "https://github.com/Ishan8009/monochrome.git"

def run_git(args, allow_failure=False):
    """Executes a git command using Portable Git."""
    cmd = [PORTABLE_GIT] + args
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0 and not allow_failure:
        print(f"❌ Error running 'git {' '.join(args)}':\n{result.stderr.strip()}")
    return result

def main():
    print("=== Automated GitHub Cloud Build Trigger ===")

    # 1. Resolve project directory containing package.json
    working_dir = Path(".").resolve()
    if (working_dir / "desktop-app-2.0.17" / "package.json").exists() and not (working_dir / "package.json").exists():
        working_dir = working_dir / "desktop-app-2.0.17"

    os.chdir(working_dir)
    print(f"Working Directory: {working_dir.resolve()}\n")

    # 2. Check for Portable Git
    if not Path(PORTABLE_GIT).exists():
        print(f"❌ Portable Git binary not found at: {PORTABLE_GIT}")
        sys.exit(1)

    # 3. Configure local Git identity
    print("[1/5] Configuring Git user identity...")
    run_git(["config", "user.email", "ishan@monochrome.local"])
    run_git(["config", "user.name", "Ishan"])

    # 4. Initialize repository if needed
    print("[2/5] Checking Git repository initialization...")
    repo_check = run_git(["rev-parse", "--is-inside-work-tree"], allow_failure=True)
    if repo_check.returncode != 0:
        run_git(["init"])
        print(" ✓ Initialized new local Git repository.")

    # 5. Set Remote Origin URL
    print("[3/5] Setting remote repository origin...")
    run_git(["remote", "remove", "origin"], allow_failure=True)
    run_git(["remote", "add", "origin", REMOTE_REPO_URL])
    print(f" ✓ Remote set to: {REMOTE_REPO_URL}")

    # 6. Stage files and create initial commit
    print("[4/5] Staging files and creating initial commit...")
    run_git(["add", "."])
    commit_res = run_git(["commit", "-m", "Add custom download location prompt and GitHub Actions workflow"], allow_failure=True)
    if commit_res.returncode == 0:
        print(" ✓ Created commit successfully.")
    else:
        print(" ℹ Files already committed or clean state.")

    # Ensure branch name is main
    run_git(["branch", "-M", "main"])

    # 7. Push to GitHub
    print("[5/5] Pushing changes to GitHub...")
    push_res = run_git(["push", "-u", "origin", "main", "--force"])

    if push_res.returncode == 0:
        print("\n🎉 SUCCESS! Project successfully pushed to GitHub.")
        print("=" * 60)
        print("1. Open https://github.com/Ishan8009/monochrome in your browser.")
        print("2. Click on the 'Actions' tab.")
        print("3. Watch the 'Build Desktop App' workflow compile your executable.")
        print("4. Download the ready-to-use .exe installer from 'Artifacts' when completed!")
        print("=" * 60)
    else:
        print("\n❌ Push failed. If Windows opens a credential prompt, please sign in to GitHub to authorize the push.")

if __name__ == "__main__":
    main()