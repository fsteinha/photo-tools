#!/usr/bin/env python3
import argparse
import argcomplete

from CPigDb import CPigDb
from config import Config

def main():
    args = parse_args()
    
    
    if args.db_path and not args.config:
        config = Config()
        config.db_path = args.db_path
    elif args.db_path and args.config:
        config = Config(args.config)
        config.db_path = args.db_path
        config.save_config()
        config.print_config()
    else:
        config = Config(args.config)
        
    if args.create_db:
        db = CPigDb(config.get_db_path())
    
        if db.get_error() == db.ERROR_DB_FILE:
            print(f"Creating new database at {config.get_db_path()}")
            db.create_database()
        else:
            print(f"Database {config.get_db_path()} already exists.")
        exit(0)
        
    db = CPigDb(config.get_db_path())
    if db.get_error() != db.ERROR_STAT_NONE:
        print(f"Error opening database: {db.get_error()}")
        return
    
    if consistency_check(db) is False:
        print("Database consistency check failed.")
    else:
        print("Database is consistent.")
    
    if args.get_stats:
        get_stats(db, b_verbose=args.verbose)
    
    if args.get_unregistered_files:
        get_unregistered_files(db, b_verbose=args.verbose)
    
    if args.check_doubles:
        get_double_files(db, b_verbose=args.verbose)
        
    if args.delete_doubles:
        delete_double_files(db, b_verbose=args.verbose)


def parse_args():
    parser = argparse.ArgumentParser(description="Check database consistency.")
    parser.add_argument("--db-path", help="Path to the database file.")
    parser.add_argument("-v", "--verbose", action="store_true", help="verbose")
    parser.add_argument("--get-stats", action="store_true", help="Get database statistics.")
    parser.add_argument("--get-unregistered-files", action="store_true", help="Get unregistered files.") 
    parser.add_argument("--check-doubles", action="store_true", help="Check for doubles") 
    parser.add_argument("--delete-doubles", action="store_true", help="Generate a delete script for doubles") 
    parser.add_argument("--info", action="store_true", help="Print info messages.")
    parser.add_argument('--config', default=Config.VAL_DEFAULT_CONFIG_PATH, type=str, help='Path to configuration file')
    parser.add_argument('--create-db', action="store_true", help='Create default database if not exists')
    
    argcomplete.autocomplete(parser)
    return parser.parse_args()

def consistency_check(db:CPigDb) -> bool:
    if db.get_error() != db.ERROR_STAT_NONE:
        print(f"Error opening database: {db.get_error()}")
        return False
    db.check_unregistered_files()    
    return True

def get_stats(db:CPigDb, b_info:bool = True, b_verbose:bool = False):
    d_stats = db.get_stats()
    if not d_stats:
        if b_info:
            print("Failed to retrieve statistics.")
        return {}
    # print beauty d_stats
    if b_info:
        for key, value in d_stats.items():
            print(f"{key}: {value}")
    return d_stats

def get_unregistered_files(db:CPigDb, b_info = True, b_verbose = False):
    unregistered_files = db.get_unregistered_files()
    if not unregistered_files:
        if b_info:
            print("No unregistered files found.")
        return []
    
    # print info unregistered files
    if b_info:
        print(f"{len(unregistered_files)} unregistered files found.")
        
    if b_verbose:
        if unregistered_files:
            print("Unregistered files:")
            for file in unregistered_files:
                print(f" - {file}")
        else:
            print("No unregistered files found.")
    return unregistered_files

def get_double_files(db:CPigDb, b_info= True, b_verbose = False):
    double_files = db.find_doubles_by_md5()
    if not double_files:
        if b_info:
            print("No double files found.")
        return []
    
    if b_info:
        print (f"{len(double_files)} double files found.")
    
    if b_verbose:
        for file in double_files:
            print(f"{file}")
            
    return double_files

def delete_double_files(db:CPigDb, b_info= True, b_verbose = False):
    double_files = db.find_doubles_by_md5()
    if not double_files:
        if b_info:
            print("No double files found.")
        return []
    
    count_double_files = len(double_files)
    if b_info:
        print (f"{count_double_files} double files found.")
    
    deleted_files = 0
    for file_found in double_files:
        md5 = file_found[0]
        file_to_delete = file_found[1][0]
        for double_file in file_found[1]:
            if len(double_file) > len(file_to_delete):
                file_to_delete = double_file
        if b_verbose:
            deleted_files += 1
            print (f"Delete file({deleted_files}/{count_double_files}): {file_to_delete} with md5: {md5}")
            db.delete_file_entry(md5,double_file)
            
if __name__ == "__main__":
    main()