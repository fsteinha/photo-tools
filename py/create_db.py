#!/usr/bin/env python3
import argparse
import argcomplete

from cpigdb import CPigDb
from config import Config


def main():
    args = get_args()
    config = Config(args.config)
    db_path = config.get_db_path()
    db = CPigDb(db_path)
    db.create_database()
    if db.get_error() == db.ERROR_STAT_NONE:
        print(f"Database created successfully at {db_path}.")
    else:
        print(f"Failed to create database. Error: {db.get_error()}")
        
def get_args():
    parser = argparse.ArgumentParser(description="Photo Tools Consistency Check")
    parser.add_argument('--config', default=Config.VAL_DEFAULT_CONFIG_PATH, type=str, help='Path to configuration file (default: %(default)s)')

    argcomplete.autocomplete(parser)
    return parser.parse_args()

if __name__ == "__main__":
    main()