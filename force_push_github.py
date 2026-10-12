import os
import subprocess
import sys
from pathlib import Path

PORTABLE_GIT = r"C:\Users\ishan\.portable_git\cmd\git.exe"

def run_git(args):
    """Executes a git command using the local Portable Git binary."""
    cmd = [PORTABLE_GIT] + args
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"⚠ Git Warning ({' '.join(args)}):\n{result.stderr.strip()}")
    else:
        print(f" ✓ {' '.join(args)}")
    return result

def main():
    print("=== Temporary GitHub Push Script ===")

    # 1. Resolve project directory containing package.json
    working_dir = Path(".").resolve()
    if (working_dir / "desktop-app-2.0.17" / "package.json").exists() and not (working_dir / "package.json").exists():
        working_dir = working_dir / "desktop-app-2.0.17"

    os.chdir(working_dir)
    print(f"Working Directory: {working_dir.resolve()}\n")

    if not Path(PORTABLE_GIT).exists():
        print(f"❌ Portable Git not found at: {PORTABLE_GIT}")
        sys.exit(1)

    # 2. Configure local Git identity (temporary for this repo only)
    run_git(["config", "user.email", "developer@monochrome.local"])
    run_git(["config", "user.name", "Ishan"])

    # 3. Stage all source files and workflows
    print("\nStaging files and creating initial commit...")
    run_git(["add", "."])
    run_git(["commit", "-m", "Initial commit: Add download prompts and GitHub build workflow"])

    # 4. Set branch to main
    run_git(["branch", "-M", "main"])

    # 5. Push to GitHub
    print("\nPushing repository to GitHub...")
    push_res = run_git(["push", "-u", "origin", "main", "--force"])

    if push_res.returncode == 0:
        print("\n🎉 SUCCESS! Your repository has been pushed to GitHub.")
        print("1. Open https://github.com/Ishan8009/monochrome in your browser.")
        print("2. Click on the 'Actions' tab.")
        print("3. Watch the 'Build Desktop App' workflow compile your executable.")
        print("4. Download the ready-to-use .exe installer from 'Artifacts' when finished!")
    else:
        print("\n❌ Push failed. If prompted, please authenticate with your GitHub credentials in the terminal.")

if __name__ == "__main__":
    main()