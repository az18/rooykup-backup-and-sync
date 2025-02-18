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

# Creating folders if necessary
for directory in ['compressed', 'logs']:
    if not os.path.exists(directory):
        os.makedirs(directory)