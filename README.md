# Photo Tools

Photo Tools is a lightweight Python utility suite for managing photos, validating a local image database, computing image hashes, and performing basic image processing tasks.

## Overview

The project is organized into several scripts under `src/` and a small supporting library under `src/lib/`.

Key capabilities:
- Create and use a SQLite image database
- Compute MD5 hashes and perceptual image hashes
- Check database consistency for unregistered or missing files
- Detect duplicate images using MD5
- Add single images or entire directories to the database
- Read EXIF creation timestamps for basic sorting

## Requirements

- Python 3.x
- `pip install -r requirements.txt`
- Additional dependency:
  - `Pillow` for EXIF and image processing

Example installation:

```bash
python3 -m pip install -r requirements.txt
python3 -m pip install Pillow
```

## Configuration

Default configuration file:

```text
./.cpig_config.json
```

Default settings from `src/lib/config.py`:

```json
{
  "db_path": "./cpig_database.db",
  "image_extensions": [".jpg", ".jpeg", ".png", ".bmp", ".gif"]
}
```

## User Interface

This project currently provides a command-line interface only. There is no graphical user interface.

The CLI is exposed through several launchable scripts in `src/`.

### General CLI behavior

- Each script uses `argparse` for command-line arguments.
- Most scripts accept a `--config` option to load a JSON config file.
- Output is printed directly to the terminal.
- `argcomplete` support is included for optional shell tab completion if configured.

## Main Scripts and Usage

### Create database

```bash
python3 src/create_db.py --config ./.cpig_config.json
```

### Add images

Add a single image:

```bash
python3 src/add_image.py --photo /path/to/image.jpg --config ./.cpig_config.json
```

Add all files from a directory recursively:

```bash
python3 src/add_image.py --dir /path/to/directory --config ./.cpig_config.json
```

Dry run mode (no filesystem or database changes):

```bash
python3 src/add_image.py --dir /path/to/directory --dryrun --config ./.cpig_config.json
```

### Check database consistency

```bash
python3 src/consistence_check.py --get-stats --check-doubles --config ./.cpig_config.json
```

Available options:
- `--get-stats`: print database statistics
- `--get-unregistered-files`: list files in the directory that are not registered in the database
- `--check-doubles`: detect duplicate images by MD5
- `--delete-doubles`: delete duplicate entries and remove duplicate files
- `-v/--verbose`: print more details

### Sort images by EXIF timestamp (prototype)

```bash
python3 src/sortin.py
```

This script reads `DateTimeOriginal` from EXIF data and prints planned target filenames. It is implemented as a prototype rather than a finished sorting tool.

### Generate MD5 hashes (experimental)

```bash
python3 src/gen_hashes.py /path/to/directory
```

This script is intended to generate MD5 hashes for all files in a directory tree.

## Architecture

### `src/lib/cpigdb.py`

The central database class `CPigDb` manages:
- an `images` table with `md5_hash`, `image_hash`, and `path`
- consistency checks for unregistered and missing files
- duplicate detection via MD5
- inserting images into the database

### `src/lib/image.py`

The image helper class `CImage` computes for a given file:
- MD5 hash (using `md5sum` if available, otherwise Python fallback)
- perceptual image hash via `imagehash.phash`
- EXIF creation timestamp

### `src/lib/config.py`

Handles configuration for the database path and allowed image extensions.

### `src/lib/notification.py`

Prints colored status and error messages to the terminal.

## Notes

- The scripts are partially prototype code and may contain issues.
- The database is created by default at `./cpig_database.db`.

## Project structure

- `src/add_image.py`
- `src/create_db.py`
- `src/consistence_check.py`
- `src/gen_hashes.py`
- `src/sortin.py`
- `src/lib/config.py`
- `src/lib/cpigdb.py`
- `src/lib/image.py`
- `src/lib/notification.py`

---

If you want, I can also add a "Known Limitations" section or a small usage example for each script.