#!/usr/bin/env python3
import argparse
from datetime import datetime
import argcomplete
import os

from lib.cpigdb import CPigDb
from lib.config import Config


# library functions
def add_image(db:CPigDb, image_file_path: str, dryrun: bool = False) -> bool:
    return db.insert_image(str(image_file_path), dryrun=dryrun)
   

# ############################################################################
# Script entry point
##############################################################################
def main():
    args = parse_args()
    config = Config(args.config)
    config.print_config()
    db_path = config.get_db_path()
    db = CPigDb(db_path)
    if not db.consistency_check():
        print("Consistency check failed.")
        db.diagnose(b_print=True)
        exit(1)
    
    file_log = open(f"add_image{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.log", "w")
    
        
    if args.photo:
        if not (add_image(db, os.path.abspath(args.photo), args.dryrun)):
            log = (f"Error adding photo: {args.photo}, {db.get_error()}")
        else:
            log = (f"Photo added successfully: {args.photo}")

        file_log.write(log + "\n")
        print(log)
    
    if args.dir:
        for root, dirs, files in os.walk(args.dir):
            for file in files:
                file_path = os.path.join(root, file)
                if not (add_image(db, os.path.abspath(file_path), args.dryrun)):
                    log = (f"Error adding photo: {file_path}, {db.get_error()}")
                else:
                    log = (f"Photo added successfully: {file_path}")
                file_log.write(log + "\n")
                print(log)

def parse_args():
    parser = argparse.ArgumentParser(description="Check database consistency.")
    parser.add_argument("--photo", help="Path to the photo which should insert.")
    parser.add_argument("--dir", help="Path to the directory containing photos.")
    parser.add_argument('--config', default=Config.VAL_DEFAULT_CONFIG_PATH, type=str, help='Path to configuration file')
    parser.add_argument('--dryrun', action='store_true', help='Perform a dry run without making any changes to the database')
    argcomplete.autocomplete(parser)
    return parser.parse_args()
    
if __name__ == "__main__":
    main()