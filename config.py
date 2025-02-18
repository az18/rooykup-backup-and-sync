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
ALLWAYS_CREATE_ZIP = toml_data['config'].get('alwaysCompress', False)
SHUTDOWN_AFTER = toml_data['config'].get('shutDownAfterBackup', False)

# Creating folders if necessary
for directory in ['compressed', 'logs']:
    if not os.path.exists(directory):
        os.makedirs(directory)