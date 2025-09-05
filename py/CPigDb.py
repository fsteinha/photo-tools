import sqlite3

class CPigDb:
    KEY_MD5 = "md5_hash"
    KEY_IMAGE = "image_hash"
    KEY_PATH = "path" 

    def __init__(self, file_name: str):
        self.file_name = file_name
        self.conn = sqlite3.connect(self.file_name)
        self._create_table()

    def _create_table(self):
        with self.conn:
            sql="CREATE TABLE IF NOT EXISTS images (id INTEGER PRIMARY KEY AUTOINCREMENT,"
            sql+=f"{self.KEY_MD5} TEXT,"
            sql+=f"{self.KEY_IMAGE} TEXT,"
            sql+=f"{self.KEY_PATH} TEXT UNIQUE"
            sql+=")"
            self.conn.execute(sql)
            
    def insert_image(self, md5_hash: str, image_hash: str, path: str):
        with self.conn:
            self.conn.execute(f'''
                INSERT OR IGNORE INTO images ({self.KEY_MD5}, {self.KEY_IMAGE}, {self.KEY_PATH})
                VALUES (?, ?, ?)
            ''', (md5_hash, image_hash, path))

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