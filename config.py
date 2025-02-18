import os
import platform
import toml
from colors import *

HOME = os.getenv('HOME')

# Use ~/rooykup for all platforms
CONFIG_DIR = os.path.join(HOME, 'rooykup')
CONFIG_FILE = os.path.join(CONFIG_DIR, 'config.toml')

# Use ~/backup for all platforms
DEFAULT_BACKUP_DIR = os.path.join(HOME, 'backup')

# Create necessary directories
if not os.path.exists(CONFIG_DIR):
    os.makedirs(CONFIG_DIR)

# Import config file
try:
    with open(CONFIG_FILE, 'r') as file:
        toml_data = toml.load(file)
    if len(toml_data) == 0:
        raise Exception("Config file is empty")
except Exception as e:
    print(RED + " ==> " + RESET_ALL + str(e))
    exit()

# Setting working directory
if toml_data['config'].get('workingDirectory'):
    working_directory = toml_data['config']['workingDirectory']
else:
    if not os.path.exists(DEFAULT_BACKUP_DIR):
        os.makedirs(DEFAULT_BACKUP_DIR)
    working_directory = DEFAULT_BACKUP_DIR

os.chdir(working_directory)

# Setting variables
ALLWAYS_CREATE_ZIP = bool(toml_data['config'].get('forceNewBackup', False))  # Ensure boolean conversion
SHUTDOWN_AFTER = bool(toml_data['config'].get('shutDownAfterBackup', False))
PRESERVE_FULL_PATH = bool(toml_data['config'].get('preserveFullPath', True))
RETENTION_DAYS = int(toml_data['config'].get('retentionDays', 7))  # Ensure integer conversion

def get_preserve_full_path(directory_config):
    """Get preserveFullPath setting for a directory, falling back to global setting"""
    return directory_config.get('preserveFullPath', PRESERVE_FULL_PATH)

def get_force_new_backup(directory_config):
    """Get forceNewBackup setting for a directory, falling back to global setting"""
    return directory_config.get('forceNewBackup', ALLWAYS_CREATE_ZIP)

def get_retention_days(directory_config):
    """Get retentionDays setting for a directory, falling back to global setting"""
    return directory_config.get('retentionDays', RETENTION_DAYS)

# Process autoBackup sections if present
if 'autoBackup' in toml_data:
    # Initialize pathAndDirName if not present
    if 'pathAndDirName' not in toml_data:
        toml_data['pathAndDirName'] = []
        
    # Get existing paths to avoid duplicates
    existing_paths = {p['path'] for p in toml_data['pathAndDirName']}
    
    # Process each autoBackup entry
    for auto_config in toml_data['autoBackup']:
        parent_path = auto_config['parentPath']
        if not os.path.exists(parent_path):
            print(RED + f" ==> Warning: autoBackup parent path not found: {parent_path}" + RESET_ALL)
            continue
            
        # Get immediate subfolders
        try:
            subfolders = [f.path for f in os.scandir(parent_path)
                         if f.is_dir() and not f.name.startswith('.')]
        except Exception as e:
            print(RED + f" ==> Error scanning {parent_path}: {str(e)}" + RESET_ALL)
            continue
            
        # Create virtual pathAndDirName entries for each subfolder
        for folder in subfolders:
            if folder not in existing_paths:
                # Get base folder name
                folder_name = os.path.basename(folder.rstrip('/'))
                # Apply prefix if specified
                zip_name = f"{auto_config.get('zipNamePrefix', '')}{folder_name}" if auto_config.get('zipNamePrefix') else folder_name
                
                entry = {
                    'path': folder,
                    'zipName': zip_name,
                    # Copy any override settings from autoBackup
                    'preserveFullPath': auto_config.get('preserveFullPath', PRESERVE_FULL_PATH),
                    'retentionDays': auto_config.get('retentionDays', RETENTION_DAYS),
                    'forceNewBackup': auto_config.get('forceNewBackup', ALLWAYS_CREATE_ZIP)
                }
                toml_data['pathAndDirName'].append(entry)
                existing_paths.add(folder)

# Creating folders if necessary
for directory in ['compressed', 'logs']:
    if not os.path.exists(directory):
        os.makedirs(directory)