#!/usr/bin/env python3
import argparse
import argcomplete
import imagehash
import subprocess
import hashlib
import os
import shutil
f

from cpigdb import CPigDb
from config import Config
from consistence_check import consistency_check

# library functions
def add_image(db, file_path, target_dir) -> bool:
    md5_hash = compute_md5(file_path)
    if md5_hash is None:
        return False
           
    image_hash = compute_image_hash(file_path)
    if image_hash is None:
        return False    
            
    rel_path = file_path.relative_to(target_dir)
    
    return db.insert_image(md5_hash, str(image_hash), str(rel_path))
    
def compute_image_hash(file_path):
    """Compute perceptual hash of an image."""
    try:
        image_hash = imagehash.phash(Image.open(file_path))    
    except:
        image_hash = None
    return str(image_hash)

def compute_md5(file_path):
    """Compute MD5 hash of a file."""
    global compute_md5 = None
    if compute_md5 is None:
        if shutil.which("md5sum"):
            compute_md5 = compute_md5_md5sum
        else:
            compute_md5 = compute_md5_python
    return compute_md5(file_path)

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



# Script entry point
def main():
    args = parse_args()
    config = Config(args.config)
    db_path = config.get_db_path()
    db = CPigDb(db_path)
    if not consistency_check(db):
        print("Consistency check failed.")
        exit(1)
    
    if args.photo:
        if (add_image(db, os.path.abspath(args.photo), os.path.dirname(os.path.abspath(db_path))) is False):
            print(f"Error adding photo: {args.photo}, {db.get_error}")
    
def parse_args():
    parser = argparse.ArgumentParser(description="Check database consistency.")
    parser.add_argument("--photo", help="Path to the photo which should insert.")
    #parser.add_argument("--dir", help="Path to the database file.")
    parser.add_argument('--config', default=Config.VAL_DEFAULT_CONFIG_PATH, type=str, help='Path to configuration file')
    
    argcomplete.autocomplete(parser)
    return parser.parse_args()
    
    
def parse_args():
    parser =
    