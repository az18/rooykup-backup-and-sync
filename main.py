import json
import colorama
import zipfile
import os, stat, argparse
import datetime, time

colorama.init()
today = datetime.date.today()
ALLWAYS_CREATE_ZIP = SHUTDOWN_AFTER = False

# Parsing arguments
parser = argparse.ArgumentParser(description='Process some integers.')
parser.add_argument('-s', '--shutdown', dest='shutdown', action='store_true', help='Shutdown after script is done')
parser.add_argument('-acz', '--allways-create-zip', dest='allways_create_zip', action='store_true', help='Create zip even if it already exists')
parser.set_defaults(shutdown=SHUTDOWN_AFTER, allways_create_zip=ALLWAYS_CREATE_ZIP)
args = parser.parse_args()

if args.allways_create_zip:
	ALLWAYS_CREATE_ZIP = True

if args.shutdown:
	SHUTDOWN_AFTER = True

# Creating folders if necessary
if not os.path.exists("compressed"):
	os.makedirs("compressed")

if not os.path.exists("logs"):
	os.makedirs("logs")

# Importing path from json file
with open('path.json') as json_file:
	data = json.load(json_file)

# Importing exclude folders from .dirignore
with open('.dirignore') as f:
	exclude = f.readlines()
	exclude = [x.strip() for x in exclude]

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
  today = datetime.date.today()

  return datetime.datetime.fromtimestamp(creation_time).date() == today

# Start timer
started = time.time()

for p in data['pathAndDirName']:
	size_initial = get_size(p['path'])
	if size_initial == 0:
		string_to_log = f"- [ ] {p['zipName']} (0MB) - Directory empty or not found"
		print(string_to_log[:string_to_log.find("-")]+colorama.Fore.RED+string_to_log[string_to_log.find("-"):]+colorama.Style.RESET_ALL)
		with open(f"log-{str(today)}.md", 'a') as f:
			f.write(string_to_log+"\n")
		continue
	size_inital_mb = size_initial/(1024*1024)
	source_dir = p['path']
	zipName = p['zipName']+".zip"

	if not ALLWAYS_CREATE_ZIP:
		is_file = "compressed/" + zipName
		if os.path.isfile(is_file):
			if check_if_file_was_created_today(is_file):
				print(f"- [x] {zipName} "+colorama.Fore.GREEN+"(Already created today)"+colorama.Style.RESET_ALL)
				continue

	archive = zipfile.ZipFile(zipName, "w")

	for root, dirs, files in os.walk(source_dir):
		dirs[:] = [d for d in dirs if d not in exclude]
		for file in files:
			archive.write(os.path.join(root, file))

	archive.close()

	size_final = os.path.getsize(zipName)/(1024*1024)
	out_str = f"- [x] {zipName} ({size_inital_mb:.1f}MB => {size_final:.1f}MB)"

	print(out_str[:out_str.find("(")]+colorama.Fore.GREEN+out_str[out_str.find("("):]+colorama.Style.RESET_ALL)
	with open(f"log-{str(today)}.md", 'a') as f:
		f.write(out_str+"\n")

print("-"*30)
os.system("mv *.zip compressed")

path = os.getcwd() + "/compressed"
os.system(f"rclone sync arch:{path} bipbop:enc -P < confp")

ended = time.time()

time_elapsed = ended-started
time_var = "seconds"

if time_elapsed > 60:
	time_elapsed = time_elapsed/60
	time_var = "minutes"

print("-"*30)
print(colorama.Fore.BLUE+" ==> "+f"Total time elapsed: {time_elapsed:.2f} {time_var}"+colorama.Style.RESET_ALL)

with open(f"log-{str(today)}.md", 'a') as f:
	f.write("\n")
	f.write("----\n")
	f.write(f"## Time elapsed: {time_elapsed:.2f} {time_var}\n")


os.system("mv log-*.md logs")
print("-"*30)

if SHUTDOWN_AFTER:
	os.system("shutdown")
