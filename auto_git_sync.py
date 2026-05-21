import subprocess
import time
import os
import datetime

# Configuration
INTERVAL_SECONDS = 30
BRANCH_NAME = "main"
REMOTE_NAME = "origin"

def run_command(cmd, cwd=None):
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            cwd=cwd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        return result.returncode, result.stdout.strip(), result.stderr.strip()
    except Exception as e:
        return -1, "", str(e)

def has_changes(project_dir):
    # Check if there are any untracked or modified files (excluding ignored ones)
    code, stdout, stderr = run_command("git status --porcelain", cwd=project_dir)
    if code == 0 and stdout:
        return True
    return False

def sync_to_github(project_dir):
    print(f"[{datetime.datetime.now()}] Changes detected. Starting sync...")
    
    # 1. Add all changes
    code, out, err = run_command("git add -A", cwd=project_dir)
    if code != 0:
        print(f"Error adding changes: {err}")
        return False
        
    # 2. Commit changes
    commit_msg = f"Auto-commit: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    code, out, err = run_command(f'git commit -m "{commit_msg}"', cwd=project_dir)
    if code != 0:
        print(f"Error committing changes: {err}")
        return False
    print(f"Committed: {commit_msg}")
        
    # 3. Check if remote is configured before pushing
    code, out, err = run_command(f"git remote get-url {REMOTE_NAME}", cwd=project_dir)
    if code != 0:
        print(f"Warning: Remote '{REMOTE_NAME}' is not configured yet. Skipping push. (Please set up your remote repository URL)")
        return True
        
    # 4. Push to remote
    code, out, err = run_command(f"git push {REMOTE_NAME} {BRANCH_NAME}", cwd=project_dir)
    if code != 0:
        print(f"Error pushing to GitHub: {err}")
        return False
        
    print("Successfully pushed to GitHub!")
    return True

def main():
    project_dir = os.path.dirname(os.path.abspath(__file__))
    print(f"Starting Auto Git Sync in: {project_dir}")
    print(f"Checking for changes every {INTERVAL_SECONDS} seconds...")
    
    while True:
        try:
            if has_changes(project_dir):
                sync_to_github(project_dir)
        except Exception as e:
            print(f"Unexpected error: {e}")
            
        time.sleep(INTERVAL_SECONDS)

if __name__ == "__main__":
    main()
