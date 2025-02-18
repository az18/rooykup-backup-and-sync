# rooykup - Cross-platform Backup and Sync Tool

![EXAMPLE](rooykup_example.gif)

![IMG](https://img.shields.io/badge/Version-0.0.2-blue)

## Table of Contents

- [Platform Support](#platform-support)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [Contributing](#contributing)
- [License](#license)

## Platform Support

rooykup is compatible with both Linux and macOS systems. All directories are consistent across platforms:

### Directory Structure (All Platforms)
- Configuration directory: `~/rooykup/`
- Default backup directory: `~/backup`

## Installation

1. Clone this repository
2. Install the required Python dependencies:
```bash
pip install -r requirements.txt
```

## Configuration

### rclone

1. Download rclone from https://rclone.org/downloads/
2. Configure rclone with `rclone config`. Follow the instructions from https://rclone.org/docs/
3. Set a strong configuration password

### rooykup

1. Create a `config.toml` file at `~/rooykup/config.toml`. You can use the provided `config.example.toml` as a template, which includes detailed descriptions of all available options and their default values.

Configuration structure:
```toml
[config]
workingDirectory = "/path/to/working/directory" # Optional: Directory where compressed files and logs will be saved
shutDownAfterBackup = false
forceNewBackup = false  # Whether to create new backups even if one exists from today
preserveFullPath = true # Optional: Whether to maintain full directory structure in zip files
remote = ["remote:folder", "remote2:"]
local = "local:"

[exclude]
directories = [".git", "node_modules"] # If none leave it empty 

[[pathAndDirName]]
path = "/path/to/folder/to/backup"
zipName = "NameOfTheZipFile"  # Optional: If not provided, folder name will be used
```

You can add as many `[[pathAndDirName]]` sections as you want. For each section:
- `path`: (required) Full path to the directory you want to back up
- `zipName`: (optional) Name for the zip file. If not provided, the folder name from the path will be used

Example:
```toml
# With explicit zipName (creates "documents.zip")
[[pathAndDirName]]
path = "/home/user/documents"
zipName = "documents"

# Without zipName (automatically creates "documents.zip")
[[pathAndDirName]]
path = "/home/user/documents"
```

2. Set the environment variable for rclone configuration:
   - For Bash/Zsh, add to your `.bashrc` or `.zshrc`:
     ```bash
     export RCLONE_CONFIG_PASS="yourRcloneConfigPass"
     ```
   - For macOS, you can also add it to `~/.profile`

## Usage

### Basic Usage
Run the script:
```bash
python rooykup.py
```
Or use the executable from the [release page](https://github.com/Rooyca/rooykup-backup-and-sync/releases)

### Command Line Options
- `-s` or `--shutdown`: Shutdown the system after backup completion
- `-c` or `--force-new-backup`: Force creating a new backup even if one exists from today

### Setting Up Aliases
Add to your `.bashrc`, `.zshrc`, or `~/.profile`:
```bash
alias rooykup="python /path/to/rooykup.py"
```

### Automated Backups
- Linux: Use `cron` or `systemd`
- macOS: Use `launchd` or set up in System Preferences > Battery > Schedule

### Configuration Options
- `retentionDays`: Number of days to keep backup files (default: 7). Older backups are automatically deleted. Set this according to how long you want to retain your backup history.

- `forceNewBackup`: Controls how multiple backups on the same day are handled:
  * When false (default): Skip if a backup already exists from today
  * When true: Create a new versioned backup (e.g., `Documents_2024-02-18_v1.zip`, `Documents_2024-02-18_v2.zip`)
  * Can be overridden with `-c` command line option

- `shutDownAfterBackup`: Enable automatic shutdown after backup (can be overridden with `-s`)
- `workingDirectory`: Custom backup location (defaults to `~/backup` if not set)
- `preserveFullPath`: When set to true (default), maintains the full directory structure in the zip file. When false, only includes the target directory and its contents.

### Backup File Naming
Backups are now created with a versioned naming scheme:
- Format: `{name}_{date}_v{version}.zip`
- Example: `Documents_2024-02-18_v1.zip`

The version number automatically increments for multiple backups on the same day.

For example, with a backup path of `/home/user/documents/projects`:
- If `preserveFullPath = true`: The zip will contain the full path structure
- If `preserveFullPath = false`: The zip will only contain the "projects" directory structure

### Desktop Integration

#### Linux (Polybar module)
Add to your polybar config:
```ini
[module/bs]
type = custom/script
exec = echo " "
format-prefix = "  "
format-prefix-foreground = #000
format-background = #fb4934
click-left = alacritty --hold -e python /path/to/rooykup.py -s
```

#### macOS
You can create an Automator quick action or use the built-in Calendar app to schedule backups.

## Contributing

Any contributions you make are **greatly appreciated**. <3

## License

Distributed under the MIT License. See `LICENSE` for more information.
