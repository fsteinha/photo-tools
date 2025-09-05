#!/usr/bin/python3

import argparse
import subprocess
import hashlib
import os
from pathlib import Path
import shutil
from PIL import Image
import imagehash
from CPigDb import CPigDb

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

    if shutil.which("md5sum"):
        compute_md5 = compute_md5_md5sum
    else:
        compute_md5 = compute_md5_python

    for file_path in all_files:
        md5_hash = compute_md5(file_path)       
        #check if image
        try:
            image_hash = imagehash.phash(Image.open(file_path))    
        except:
            image_hash = None
            
        rel_path = file_path.relative_to(target_dir)
        db.insert_image(md5_hash, str(image_hash), str(rel_path))
        count += 1
        percent = int((count / total) * 100)
        print(f"Progress: {percent}% ({count}/{total})", end='\r')

    print(f"\nHashes saved to: {hash_file}")

# md5 checksum with extern tool
def compute_md5_md5sum(file_path):
    try:
        result = subprocess.run(
            ["md5sum", str(file_path)],
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout.split()[0]
    except subprocess.CalledProcessError as e:
        print(f"Error hashing {file_path}: {e}")
        return None

# md5 checksum with python    
def compute_md5_python(file_path):
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

# helper all files in tree
def get_all_files(target_dir):
    return [f for f in Path(target_dir).rglob('*') if f.is_file()]


if __name__ == "__main__":
    main()
