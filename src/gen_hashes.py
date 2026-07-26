#!/usr/bin/python3

import argparse
from pathlib import Path
irom PIL import Image
from CPigDb import CPigDb

from add_image import add_image

# main function
def main():
    args = parse_args()
    target_dir = Path(args.directory).resolve()

    if not target_dir.is_dir():
        print(f"Error: '{target_dir}' is not a valid directory.")
        exit(1)

    gen_hashes(target_dir)

# Arguments
def parse_args():
    parser = argparse.ArgumentParser(
        description="Generates MD5 hashes for all files in a directory tree using md5sum."
    )
    parser.add_argument(
        "directory",
        type=str,
        help="Target directory to scan"
    )
    return parser.parse_args()

# gen_hash_function
def gen_hashes(target_dir, hash_file="hashes.db"):
    db = CPigDb(hash_file)
 
    print(f"Generating MD5 hashes for: {target_dir}")
    all_files = get_all_files(target_dir)
    total = len(all_files)
    count = 0

    for file_path in all_files:
        if add_image(db, file_path, target_dir) is False:
            print(f"Error processing file: {file_path}")
            continue
        count += 1
        percent = int((count / total) * 100)
        print(f"Progress: {percent}% ({count}/{total})", end='\r')

    print(f"\nHashes saved to: {hash_file}")

# helper all files in tree
def get_all_files(target_dir):
    return [f for f in Path(target_dir).rglob('*') if f.is_file()]


if __name__ == "__main__":
    main()
