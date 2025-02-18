import zipfile
import os
import stat
import argparse
import datetime
import time
import platform
from colors import *
from config import *

today = datetime.date.today()

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
parser.add_argument('-c', '--always-create-zip', dest='always_create_zip', action='store_true', help='Create zip even if it already exists')
parser.set_defaults(shutdown=SHUTDOWN_AFTER, always_create_zip=ALLWAYS_CREATE_ZIP)
args = parser.parse_args()

if args.always_create_zip:
    ALLWAYS_CREATE_ZIP = not ALLWAYS_CREATE_ZIP

if args.shutdown:
    SHUTDOWN_AFTER = not SHUTDOWN_AFTER

# Start timer
started = time.time()

# Load exclude directories
exclude = toml_data['exclude']['directories']

for p in toml_data['pathAndDirName']:
    size_initial = get_size(p['path'])

    # Check if directory is empty or not found
    if size_initial == 0:
        string_to_log = f"- [ ] {p['zipName']} (0MB) - Directory empty or not found"
        print(string_to_log[:string_to_log.find("-")]+RED+string_to_log[string_to_log.find("-"):]+RESET_ALL)
        with open(os.path.join("logs", f"log-{str(today)}.md"), 'a') as f:
            f.write(string_to_log+"\n")
        continue

    # Size of directory
    size_initial_mb = size_initial/(1024*1024)
    source_dir = p['path']
    zip_name = p['zipName']+".zip"
    zip_path = os.path.join("compressed", zip_name)

    if not ALLWAYS_CREATE_ZIP:
        if os.path.isfile(zip_path):
            if check_if_file_was_created_today(zip_path):
                print(f"- [x] {zip_name} "+GREEN+"(Already created today)"+RESET_ALL)
                continue

    archive = zipfile.ZipFile(zip_path, "w")

    for root, dirs, files in os.walk(source_dir):
        dirs[:] = [d for d in dirs if d not in exclude]
        for file in files:
            try:
                file_path = os.path.join(root, file)
                if PRESERVE_FULL_PATH:
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
    out_str = f"- [x] {zip_name} ({size_initial_mb:.1f}MB => {size_final:.1f}MB)"

    print(out_str[:out_str.find("(")]+GREEN+out_str[out_str.find("("):]+RESET_ALL)

    with open(os.path.join("logs", f"log-{str(today)}.md"), 'a') as f:
        f.write(out_str+"\n")

print("-"*30)

path_compressed = os.path.join(os.getcwd(), "compressed")

try:
    remote = toml_data['config']['remote']
    local = toml_data['config']['local']
except KeyError:
    print(RED+"[-] Error"+RESET_ALL+" - add 'remote' and 'local' to config file")
    exit()

try:
    config_pass = os.environ.get('RCLONE_CONFIG_PASS')
    if config_pass is None:
        raise EnvironmentError("RCLONE_CONFIG_PASS environment variable not set")
    
    for r in remote:
        os.system(f"echo {config_pass} | rclone copy {os.path.join(local, path_compressed)} {r} -P")
        print(GREEN+"[+] "+RESET_ALL+"Uploaded to "+r)

except Exception as e:
    print(RED+f"Uploading error: {str(e)}"+RESET_ALL)

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
