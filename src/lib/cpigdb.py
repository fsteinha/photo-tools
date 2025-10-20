import sqlite3
from pathlib import Path
import os
from typing import List, Tuple
import inspect

from .image import CImage
from .notification import Notification

class CPigDb:
    # class constants
    KEY_MD5 = "md5_hash"
    KEY_IMAGE = "image_hash"
    KEY_PATH = "path" 
    
    VALUE_NONE = "None"

    ERROR_STAT_NONE = "ERROR_NONE"
    
    ERROR_DB_NOT_FOUND = "ERROR_DB_NOT_FOUND"
    ERROR_DB_INVALID = "ERROR_DB_INVALID"
    ERROR_IMAGE_PATH = "ERROR_IMAGE_PATH"
    ERROR_DATABASE_INTEGRITY = "ERROR_DATABASE_INTEGRITY"
    ERROR_UNREGISTERED_FILES = "ERROR_UNREGISTERED_FILES"
    ERROR_FILES_LOST = "ERROR_FILES_LOST"
    ERROR_DOUBLE_FILES = "ERROR_DOUBLE_FILES"
    ERROR_HASH_COMPUTE_MD5 = "ERROR_HASH_COMPUTE_MD5"
    ERROR_HASH_COMPUTE_IMAGE = "ERROR_HASH_COMPUTE_IMAGE"
    
    IMAGE_EXTERNSIONS_DEFAULT = [".jpg", ".jpeg", ".png", ".bmp", ".gif", ".tiff"]
    
    def __init__(self, file_name: str):
        """init the database object and check if the database is valid"""
        self.file_name = file_name
        self.unregistered_files = []
        self.lost_files = []
        self.__init_error__()
        self.notify = Notification()
        self.image_extensions = self.IMAGE_EXTERNSIONS_DEFAULT
        
        if (self.is_valid_db()):
            self.db_path = os.path.abspath(file_name)
        elif self.get_error() == self.ERROR_DB_NOT_FOUND:
            raise FileNotFoundError(f"Database file {file_name} is invalid or missing.")
        elif self.get_error() == self.ERROR_DB_INVALID:
            raise sqlite3.DatabaseError(f"Database file {file_name} is invalid.")
        else:
            raise Exception(f"Unknown error with database file {file_name}.")
              
    def __init_error__(self):
        """Init the error dictionary."""
        self.d_error = {
            self.ERROR_DB_NOT_FOUND: None,
            self.ERROR_IMAGE_PATH: None,
            self.ERROR_DATABASE_INTEGRITY: None,
            self.ERROR_UNREGISTERED_FILES: None,
            self.ERROR_FILES_LOST: None,
            self.ERROR_DOUBLE_FILES: None
        }

    def create_database(self):
        """Create the database file and the images table if not exists"""
        try:
            with sqlite3.connect(self.file_name) as conn:
                self.conn = conn
                self._create_table()
                self.d_error[self.ERROR_DB_NOT_FOUND] = None  # Fehler zurücksetzen
        except sqlite3.DatabaseError:
            self.__set_error__(self.ERROR_DATABASE_INTEGRITY)
            
    def __set_error__(self, error_key: str):
        """set an error in the error dictionary"""
        if error_key in self.d_error:
            self.d_error[error_key] = True 
            filename, line_number = Notification._caller_filename_lineno()
 
            self.notify.__error__(f"Error set: {error_key}", filename=filename, lineno=line_number)
        else:
            raise ValueError(f"Unknown error key: {error_key}")
    
    def get_error(self) -> str:
        """get the current error status"""
        for key, value in self.d_error.items():
            if value is not None:
                return key
        return self.ERROR_STAT_NONE

    def is_valid_db(self) -> bool:
        """Check is the database valid"""
        db_file_path = Path(self.file_name)
        
        if not db_file_path.exists():
            self.__set_error__(self.ERROR_DB_NOT_FOUND)
            return False
        
        if db_file_path.stat().st_size < 100:
            self.__set_error__(self.ERROR_DB_INVALID)
            return False
        
        try:
            with sqlite3.connect(self.file_name) as conn:
                cursor = conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name='images';"
                )
                return cursor.fetchone() is not None
        except sqlite3.DatabaseError:
            self.error = self.ERROR_DATABASE_INTEGRITY
            return False

    def check_unregistered_files(self) -> bool:
        """Checks for files in the database directory that are not registered in the database."""
        db_file_path = Path(self.file_name)
        db_file_path_str = str(db_file_path.parent)
        # get all files in the directory
        files_in_dir = list(Path(db_file_path_str).glob('*'))
        # filter out the database file itself
        other_files = [f for f in files_in_dir if f != db_file_path]
        #filter only files (not directories)
        other_files = [f for f in other_files if f.is_file()]
        # check if there are any other files and check if they are in the database
        self.unregistered_files = []
        if other_files:
            try:
                with sqlite3.connect(self.file_name) as conn:
                    cursor = conn.execute(f"SELECT {self.KEY_PATH} FROM images;")
                    db_paths = {row[0] for row in cursor.fetchall()}
                    for other_file in other_files:
                        if str(other_file) not in db_paths and\
                            str(other_file).endswith(tuple(self.image_extensions)):
                            self.unregistered_files.append(str(other_file))
                    if self.unregistered_files:
                        self.__set_error__(self.ERROR_UNREGISTERED_FILES)
                        self.notify.__error__(f"Unregistered files found: {self.unregistered_files}")
                        return False
            except sqlite3.DatabaseError:
                self.__set_error__(self.ERROR_DATABASE_INTEGRITY)
                self.notify.__error__(f"Database integrity error while checking for unregistered files: {self.get_error()}")
                return False
        return True

    def check_lost_files(self) -> bool:
        """Checks whether the database contains paths to files that no longer exist."""
        try:
            with sqlite3.connect(self.file_name) as conn:
                cursor = conn.execute(f"SELECT {self.KEY_PATH} FROM images;")
                db_paths = {row[0] for row in cursor.fetchall()}
                self.lost_files = []
                
                for path in db_paths:
                    full_path = f"{os.path.dirname(self.db_path)}/{path}"
                    if not os.path.exists(full_path):
                        self.lost_files.append(path)
                if self.lost_files:
                    self.error = self.ERROR_UNREGISTERED_FILES
                    return False
        except sqlite3.DatabaseError:
            self.__set_error__(self.ERROR_DATABASE_INTEGRITY)
            return False
        return True

    def consistency_check(self) -> bool:
        if self.get_error() != self.ERROR_STAT_NONE:
            self.notify.__error__(f"Consistency check failed: {self.get_error()}")
            return False
        if not self.check_unregistered_files():
            self.notify.__error__(f"Consistency check failed: {self.get_error()}")
            return False
        if not self.check_lost_files():
            self.notify.__error__(f"Consistency check failed: {self.get_error()}")
            return False
            
        return True
    def get_stats(self) -> dict:
        """Returns statistics about the database."""
        stats = {
            "total_images": 0,
            "images_with_md5": 0,
            "images_with_image_hash": 0,
            "images_with_both_hashes": 0,
            "unregistered_files": len(self.unregistered_files),
            "double_files": len(self.find_doubles_by_md5())
        }
        try:
            with sqlite3.connect(self.file_name) as conn:
                cursor = conn.execute(f"SELECT {self.KEY_MD5}, {self.KEY_IMAGE} FROM images;")
                rows = cursor.fetchall()
                stats["total_images"] = len(rows)
                for md5, img_hash in rows:
                    if md5 and md5 != self.VALUE_NONE:
                        stats["images_with_md5"] += 1
                    if img_hash and img_hash != self.VALUE_NONE:
                        stats["images_with_image_hash"] += 1
                    if md5 and img_hash and md5 != self.VALUE_NONE and img_hash != self.VALUE_NONE:
                        stats["images_with_both_hashes"] += 1
        except sqlite3.DatabaseError:
            self.__set_error__(self.ERROR_DATABASE_INTEGRITY)
        return stats

    def find_photo_by_md5(self, md5_hash: str) -> List[Tuple[str, str]]:
        """Finds photos based on the MD5 hash."""
        results = []
        try:
            with sqlite3.connect(self.file_name) as conn:
                cursor = conn.execute(f'''
                    SELECT {self.KEY_PATH}, {self.KEY_IMAGE}
                    FROM images
                    WHERE {self.KEY_MD5}=?
                ''', (md5_hash,))
                results = cursor.fetchall()
        except sqlite3.DatabaseError:
            self.__set_error__(self.ERROR_DATABASE_INTEGRITY)
        return results
    
    def is_image_in_db_by_md5(self, md5_hash: str) -> bool:
        """Checks whether an image with the given MD5 hash exists in the database."""
        try:
            with sqlite3.connect(self.file_name) as conn:
                cursor = conn.execute(f'''
                    SELECT 1 FROM images WHERE {self.KEY_MD5}=? LIMIT 1;
                ''', (md5_hash,))
                return cursor.fetchone() is not None
        except sqlite3.DatabaseError:
            self.__set_error__(self.ERROR_DATABASE_INTEGRITY)
            return False
        
    def find_doubles_by_md5(self) -> list:
        """Finds duplicate entries based on the MD5 hash."""
        doubles = []
        try:
            with sqlite3.connect(self.file_name) as conn:
                cursor = conn.execute(f'''
                    SELECT {self.KEY_MD5}, COUNT(*) as count
                    FROM images
                    WHERE {self.KEY_MD5} IS NOT NULL AND {self.KEY_MD5} != '{self.VALUE_NONE}'
                    GROUP BY {self.KEY_MD5}
                    HAVING count > 1;
                ''')
                rows = cursor.fetchall()
                for md5, count in rows:
                    cursor2 = conn.execute(f'''
                        SELECT {self.KEY_PATH} FROM images WHERE {self.KEY_MD5}=?;
                    ''', (md5,))
                    paths = [row[0] for row in cursor2.fetchall()]
                    doubles.append((md5, paths))
        except sqlite3.DatabaseError:
            self.__set_error__(self.ERROR_DATABASE_INTEGRITY)
        return doubles
    
    def get_unregistered_files(self) -> list:
        """Returns a list of unregistered files."""
        return self.unregistered_files

    def delete_file_entry(self, md5_hash: str, path: str) -> bool:
        """Deletes an entry from the database based on the MD5 hash and path."""
        try:
            with sqlite3.connect(self.file_name) as conn:
                conn.execute(f'''
                    DELETE FROM images WHERE {self.KEY_MD5}=? AND {self.KEY_PATH}=?
                ''', (md5_hash, path))
            # delete file in dir
            file_path = f"{os.path.dirname(self.file_name)}/{Path(path)}"
            try:
                #print(file_path)
                os.remove(file_path)
            except OSError:
                pass
            return True
        except sqlite3.DatabaseError:
            self.__set_error__(self.ERROR_DATABASE_INTEGRITY)
            return False

    def _create_table(self):
        with self.conn:
            sql="CREATE TABLE IF NOT EXISTS images (id INTEGER PRIMARY KEY AUTOINCREMENT,"
            sql+=f"{self.KEY_MD5} TEXT,"
            sql+=f"{self.KEY_IMAGE} TEXT,"
            sql+=f"{self.KEY_PATH} TEXT UNIQUE"
            sql+=")"
            self.conn.execute(sql)
            
    def insert_image(self, image_path: str, b_check_exists: bool = True, dryrun: bool = False) -> bool:
        
        extension = os.path.splitext(image_path)[1].lower()
        if extension not in self.image_extensions:
            self.notify.__error__(f"Unsupported file extension: {extension} for file {image_path}")
            self.__set_error__(self.ERROR_IMAGE_PATH)
            return False
        
        try:
            image = CImage(image_path)
        except Exception:
            self.notify.__error__(f"Failed to process image: {image_path}")
            self.__set_error__(self.ERROR_IMAGE_PATH)
            return False
       
        if b_check_exists:
            if self.is_image_in_db_by_md5(image.md5_hash):
                exist_image = self.find_photo_by_md5(image.md5_hash)
                self.notify.__info__(f"Image already exists in database: {image_path} as {exist_image[0][0]}")
                return False
            
        image_path_year = f"{image.creation_time.year}"
        image_path_month = f"{image_path_year}/{image.creation_time.year}-{image.creation_time.month}"
        
        full_image_path_month = f"{os.path.dirname(self.db_path)}/{image_path_month}"    
        if os.path.exists(full_image_path_month) is False:
            if not dryrun:
                os.makedirs(full_image_path_month)
            else:
                self.notify.__info__(f"Dry run: Would create directory {full_image_path_month}") 
                
        new_file_name = f"{str(image.creation_time).replace(':', '_').replace(' ', '__')}.{image.file_path.split('.')[-1]}"
        new_file_path = f"{image_path_month}/{new_file_name}"
        full_new_file_path = f"{os.path.dirname(self.db_path)}/{new_file_path}"
        
        if os.path.exists(f"{full_new_file_path}"):
            new_file_name = f"{new_file_name.rsplit('.', 1)[0]}_{image.md5_hash[:8]}.{new_file_name.rsplit('.', 1)[1]}"        

        if not dryrun:
            image.copy_to_new_path(f"{full_new_file_path}")
        else:
            self.notify.__info__(f"Dry run: Would copy {image.file_path} to {full_new_file_path}")
        
        if not dryrun:
            with sqlite3.connect(self.file_name) as conn:
                conn.execute(f'''
                    INSERT OR IGNORE INTO images ({self.KEY_MD5}, {self.KEY_IMAGE}, {self.KEY_PATH})
                    VALUES (?, ?, ?)
                ''', (image.md5_hash, image.image_hash, new_file_path))
        else:
            self.notify.__info__(f"Dry run: Would insert into database: MD5={image.md5_hash}, ImageHash={image.image_hash}, OldPath={image.file_path}, NewPath={new_file_path}")
        return True

    def update_hashes(self, path: str, md5_hash: str = None, image_hash: str = None):
        """Sets/updates the md5 and/or image hash for a given path."""
        fields = []
        values = []
        if md5_hash is not None:
            fields.append(f"{self.KEY_MD5}=?")
            values.append(md5_hash)
        if image_hash is not None:
            fields.append(f"{self.KEY_IMAGE}=?")
            values.append(image_hash)
        if not fields:
            return  # Nichts zu aktualisieren
        values.append(path)
        with self.conn:
            self.conn.execute(
                f"UPDATE images SET {', '.join(fields)} WHERE {self.KEY_PATH}=?",
                values
            )
    
    def diagnose(self, b_print=False) -> dict:
        """Performs a consistency check and returns a report."""
        report = {
            "consistency_check": self.consistency_check(),
            "unregistered_files": self.get_unregistered_files(),
            "lost_files": self.lost_files,
            "double_files": self.find_doubles_by_md5(),
            "stats": self.get_stats(),
            "error": self.get_error()
        }
        if b_print:
            print("Database Consistency Report:")
            print(f"  Consistency Check: {'Passed' if report['consistency_check'] else 'Failed'}")
            print(f"  Unregistered Files: {len(report['unregistered_files'])}")
            for file in report['unregistered_files']:
                print(f"    - {file}")
            print(f"  Lost Files: {len(report['lost_files'])}")
            for file in report['lost_files']:
                print(f"    - {file}")
            print(f"  Double Files: {len(report['double_files'])}")
            for md5, paths in report['double_files']:
                print(f"    - MD5: {md5}, Paths: {paths}")
            print("  Stats:")
            for key, value in report['stats'].items():
                print(f"    - {key}: {value}")
            print(f"  Error Status: {report['error']}")
        return report