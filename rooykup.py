import zipfile
import os
import stat
import argparse
import datetime
import time
import platform
import glob
import re
from colors import *
from config import *

today = datetime.date.today()

def get_backup_version(base_name, date_str):
    """Get the next version number for a backup on the given date"""
    pattern = f"{base_name}_{date_str}_v(\\d+).zip"
    existing = glob.glob(os.path.join("compressed", f"{base_name}_{date_str}_v*.zip"))
    versions = [int(re.search(pattern, f).group(1)) for f in existing if re.search(pattern, f)]
    return max(versions, default=0) + 1

def cleanup_old_backups(directory_config):
    """Remove backup files older than retention_days specified in config"""
    retention_days = get_retention_days(directory_config)
    cutoff = today - datetime.timedelta(days=retention_days)
    pattern = re.compile(r".*_(\d{4}-\d{2}-\d{2})_v\d+\.zip$")
    
    for file in glob.glob(os.path.join("compressed", "*.zip")):
        match = pattern.match(file)
        if match:
            backup_date = datetime.datetime.strptime(match.group(1), "%Y-%m-%d").date()
            if backup_date < cutoff:
                try:
                    os.remove(file)
                    print(BLUE + "[-] Removed old backup: " + RESET_ALL + os.path.basename(file))
                except Exception as e:
                    print(RED + "[-] Error removing old backup: " + RESET_ALL + str(e))

def system_shutdown():
    """Cross-platform system shutdown command"""
    if platform.system() == 'Darwin':  # macOS
        os.system("shutdown -h now")
    else:  # Linux
        os.system("shutdown now")

def get_size(start_path):
    total_size = 0
    for dirpath, dirnames, filenames in os.walk(start_path):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            total_size += os.path.getsize(fp)
    return total_size

def check_if_file_was_created_today(file_path):
    stat_info = os.stat(file_path)
    creation_time = stat_info.st_ctime
    return datetime.datetime.fromtimestamp(creation_time).date() == today

# Parsing arguments
parser = argparse.ArgumentParser(description='rooykup lets you backup and sync your data')
parser.add_argument('-s', '--shutdown', dest='shutdown', action='store_true', help='Shutdown after script is done')
parser.add_argument('-c', '--force-new-backup', dest='always_create_zip', action='store_true', help='Force creating a new backup even if one exists from today')
parser.set_defaults(shutdown=SHUTDOWN_AFTER, always_create_zip=ALLWAYS_CREATE_ZIP)
args = parser.parse_args()

# Override settings from command line arguments if provided
SHUTDOWN_AFTER = args.shutdown or SHUTDOWN_AFTER

# Start timer
started = time.time()

# Load exclude directories
exclude = toml_data['exclude']['directories']

for p in toml_data['pathAndDirName']:
    size_initial = get_size(p['path'])

    # Get zip name - use folder name if zipName not provided
    source_dir = p['path']
    zip_name_base = p.get('zipName', os.path.basename(source_dir.rstrip('/')))
    
    # Check if directory is empty or not found
    if size_initial == 0:
        string_to_log = f"- [ ] {zip_name_base} (0MB) - Directory empty or not found"
        print(string_to_log[:string_to_log.find("-")]+RED+string_to_log[string_to_log.find("-"):]+RESET_ALL)
        with open(os.path.join("logs", f"log-{str(today)}.md"), 'a') as f:
            f.write(string_to_log+"\n")
        continue

    # Get directory-specific settings
    force_new_backup = args.always_create_zip or get_force_new_backup(p)

    # Clean up old backups first (using directory-specific retention)
    cleanup_old_backups(p)

    # Size of directory
    size_initial_mb = size_initial/(1024*1024)
    date_str = today.strftime("%Y-%m-%d")
    
    # Debug info
    print(BLUE+"[-] Debug: forceNewBackup setting =", force_new_backup, RESET_ALL)
    
    # Check existing backups from today
    pattern = f"{zip_name_base}_{date_str}_v*.zip"
    existing_backups = glob.glob(os.path.join("compressed", pattern))
    
    print(BLUE+f"[-] Debug: Searching for: {pattern}", RESET_ALL)
    print(BLUE+f"[-] Debug: Found backups: {[os.path.basename(f) for f in existing_backups]}", RESET_ALL)
    
    if existing_backups:
        latest_version = get_backup_version(zip_name_base, date_str) - 1
        print(BLUE+f"[-] Debug: Latest version found: {latest_version}", RESET_ALL)
        
        if not force_new_backup:
            print(f"- [x] {zip_name_base}_{date_str}_v{latest_version}.zip "+GREEN+"(Already created today)"+RESET_ALL)
            continue
        print(BLUE+"[-] Debug: forceNewBackup=true, creating new version", RESET_ALL)
    
    # Create new versioned backup
    version = get_backup_version(zip_name_base, date_str)
    print(BLUE+f"[-] Creating version {version} for today"+RESET_ALL)
    zip_name = f"{zip_name_base}_{date_str}_v{version}.zip"
    zip_path = os.path.join("compressed", zip_name)
    
    archive = zipfile.ZipFile(zip_path, "w")

    for root, dirs, files in os.walk(source_dir):
        dirs[:] = [d for d in dirs if d not in exclude]
        for file in files:
            try:
                file_path = os.path.join(root, file)
                if get_preserve_full_path(p):
                    archive.write(file_path)  # Keep full path structure
                else:
                    # Remove the source_dir part from the path to only include target directory
                    rel_path = os.path.relpath(file_path, os.path.dirname(source_dir))
                    archive.write(file_path, rel_path)
            except Exception as e:
                print(RED+"[-] Error: "+RESET_ALL+f" Something went wrong with: {file} at {root} ({str(e)}) (Skipping)")
                continue
    archive.close()

    # Size of ZIP
    size_final = os.path.getsize(zip_path)/(1024*1024)
    reduction = (size_initial_mb - size_final) / size_initial_mb * 100 if size_initial_mb > 0 else 0
    out_str = f"- [x] {zip_name} ({size_initial_mb:.1f}MB => {size_final:.1f}MB, {reduction:.1f}% reduction)"

    print(out_str[:out_str.find("(")]+GREEN+out_str[out_str.find("("):]+RESET_ALL)

    with open(os.path.join("logs", f"log-{str(today)}.md"), 'a') as f:
        f.write(out_str+"\n")

print("-"*30)

path_compressed = os.path.join(os.getcwd(), "compressed")

def try_rclone_sync(path_compressed):
    """Attempt to sync with rclone if configured"""
    try:
        remote = toml_data['config'].get('remote')
        local = toml_data['config'].get('local')
        
        # Skip if rclone is not configured
        if not remote or not local:
            print(BLUE+"[-] Info:"+RESET_ALL+" Rclone sync skipped - remote/local not configured")
            return
            
        config_pass = os.environ.get('RCLONE_CONFIG_PASS')
        if config_pass is None:
            print(BLUE+"[-] Info:"+RESET_ALL+" Rclone sync skipped - RCLONE_CONFIG_PASS not set")
            return
        
        for r in remote:
            os.system(f"echo {config_pass} | rclone copy {os.path.join(local, path_compressed)} {r} -P")
            print(GREEN+"[+] "+RESET_ALL+"Uploaded to "+r)
            
    except Exception as e:
        print(RED+f"[-] Rclone sync error: {str(e)}"+RESET_ALL)

# Try to sync with rclone
try_rclone_sync(path_compressed)

# End timer
ended = time.time()

time_elapsed = ended-started
time_var = "seconds"

if time_elapsed > 60:
    time_elapsed = time_elapsed/60
    time_var = "minutes"

print("-"*30)
print(BLUE+" ==> "+f"Total time elapsed: {time_elapsed:.2f} {time_var}"+RESET_ALL)

log_file = os.path.join("logs", f"log-{str(today)}.md")
with open(log_file, 'a') as f:
    f.write("\n")
    f.write("----\n")
    f.write(f"## Time elapsed: {time_elapsed:.2f} {time_var}\n")

print("-"*30)

if SHUTDOWN_AFTER:
    system_shutdown()
