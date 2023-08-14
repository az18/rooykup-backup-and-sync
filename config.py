import os, toml
from colors import *

HOME = os.getenv('HOME')

if not os.path.exists(HOME+'/.config/rooykup'):
	os.makedirs(HOME+'/.config/rooykup')

# Import config file
try:
	with open(HOME+'/.config/rooykup/config.toml', 'r') as file:
	    toml_data = toml.load(file)
	if len(toml_data) == 0:
		raise Exception("Config file is empty")
except Exception as e:
	print(RED+" ==> "+RESET_ALL+str(e))
	exit()

# Setting working directory
if toml_data['config']['workingDirectory']:
	working_directory = toml_data['config']['workingDirectory']
else:
	if not os.path.exists(HOME+"/backup"):
		os.makedirs(HOME+"/backup")
	working_directory = HOME+"/backup"

os.chdir(working_directory)

# Setting variables
if toml_data['config']['alwaysCompress']:
	ALLWAYS_CREATE_ZIP = toml_data['config']['alwaysCompress']
else:
	ALLWAYS_CREATE_ZIP = False

if toml_data['config']['shutDownAfterBackup']:
	SHUTDOWN_AFTER = toml_data['config']['shutDownAfterBackup']
else:
	SHUTDOWN_AFTER = False

# Creating folders if necessary
if not os.path.exists("compressed"):
	os.makedirs("compressed")

if not os.path.exists("logs"):
	os.makedirs("logs")