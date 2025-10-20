import sqlite3
from pathlib import Path
import os
from typing import List, Tuple

class CPigDb:
    KEY_MD5 = "md5_hash"
    KEY_IMAGE = "image_hash"
    KEY_PATH = "path" 
    
    VALUE_NONE = "None"

    ERROR_STAT_NONE = "ERROR_NONE"
    
    ERROR_DB_FILE = "ERROR_FILE"
    ERROR_DATABASE_INTEGRITY = "ERROR_DATABASE_INTEGRITY"
    ERROR_UNREGISTERED_FILES = "ERROR_UNREGISTERED_FILES"
    ERROR_FILES_LOST = "ERROR_FILES_LOST"
    ERROR_DOUBLE_FILES = "ERROR_DOUBLE_FILES"
    
    def __init__(self, file_name: str):
        self.file_name = file_name
        self.unregistered_files = []
        self.lost_files = []
        self.__init_error__()
        self.is_valid_db()
       
    def __init_error__(self):
        self.d_error = {
            self.ERROR_DB_FILE: None,
            self.ERROR_DATABASE_INTEGRITY: None,
            self.ERROR_UNREGISTERED_FILES: None,
            self.ERROR_FILES_LOST: None,
            self.ERROR_DOUBLE_FILES: None
        }

    def create_database(self):
        """Erstellt eine neue Datenbankdatei mit der erforderlichen Tabelle."""
        try:
            with sqlite3.connect(self.file_name) as conn:
                self.conn = conn
                self._create_table()
                self.d_error[self.ERROR_DB_FILE] = None  # Fehler zurücksetzen
        except sqlite3.DatabaseError:
            self.__set_error__(self.ERROR_DATABASE_INTEGRITY)
            
    def __set_error__(self, error_key: str):
        if error_key in self.d_error:
            self.d_error[error_key] = True  
        else:
            raise ValueError(f"Unknown error key: {error_key}")
    
    def get_error(self) -> str:
        for key, value in self.d_error.items():
            if value is not None:
                return key
        return self.ERROR_STAT_NONE

    def is_valid_db(self) -> bool:
        """Prüft, ob die Datei eine gültige SQLite-Datenbank mit Tabelle 'images' ist."""
        db_file_path = Path(self.file_name)
        
        if not db_file_path.exists():
            self.__set_error__(self.ERROR_DB_FILE)
            print (f"Database file {self.file_name} does not exist.")
            return False
        
        if db_file_path.stat().st_size < 100:
            self.__set_error__(self.ERROR_DB_FILE)
            print (f"Database file {self.file_name} is too small to be a valid database.")
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
                        if str(other_file) not in db_paths:
                            self.unregistered_files.append(str(other_file))
                    if self.unregistered_files:
                        self.__set_error__(self.ERROR_UNREGISTERED_FILES)
                        return False
            except sqlite3.DatabaseError:
                self.__set_error__(self.ERROR_DATABASE_INTEGRITY)
                return False

    def check_lost_files(self) -> bool:
        """Prüft, ob in der Datenbank Pfade zu Dateien existieren, die nicht mehr vorhanden sind."""
        try:
            with sqlite3.connect(self.file_name) as conn:
                cursor = conn.execute(f"SELECT {self.KEY_PATH} FROM images;")
                db_paths = {row[0] for row in cursor.fetchall()}
                self.lost_files = [path for path in db_paths if not Path(path).exists()]
                if lost_files:
                    self.error = self.ERROR_UNREGISTERED_FILES
                    return False
        except sqlite3.DatabaseError:
            self.__set_error__(self.ERROR_DATABASE_INTEGRITY)
            return False
        return True

    def get_stats(self) -> dict:
        """Gibt Statistiken über die Datenbank zurück."""
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
        """Findet Fotos basierend auf dem MD5-Hash."""
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
        """Prüft, ob ein Bild mit dem gegebenen MD5-Hash in der Datenbank vorhanden ist."""
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
        """Findet doppelte Einträge basierend auf dem MD5-Hash."""
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
        """Gibt eine Liste der unregistrierten Dateien zurück."""
        return self.unregistered_files

    def delete_file_entry(self, md5_hash: str, path: str) -> bool:
        """Löscht einen Eintrag aus der Datenbank basierend auf dem MD5-Hash und Pfad."""
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
            
    def insert_image(self, md5_hash: str, image_hash: str, path: str, b_check_exists: bool = True) -> bool:
        if b_check_exists:
            if self.is_image_in_db_by_md5(md5_hash):
                self.__set_error__(self.ERROR_DOUBLE_FILES)
                return False
        with self.conn:
            self.conn.execute(f'''
                INSERT OR IGNORE INTO images ({self.KEY_MD5}, {self.KEY_IMAGE}, {self.KEY_PATH})
                VALUES (?, ?, ?)
            ''', (md5_hash, image_hash, path))
        return True

    def update_hashes(self, path: str, md5_hash: str = None, image_hash: str = None):
        """Setzt nachträglich md5 und/oder image hash für einen gegebenen Pfad."""
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