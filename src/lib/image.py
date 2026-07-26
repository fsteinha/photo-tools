import subprocess
import hashlib
import shutil
import imagehash
import argparse
import PIL as PIL
import PIL.Image
import PIL.ExifTags
from PIL import Image
from pathlib import Path
from typing import Union, List, Tuple
import os

from .csingleton import CSingletonMeta

class CImageMD5(metaclass=CSingletonMeta):
    """Class to compute MD5 hash using an external tool."""
    def __init__(self):
        if shutil.which("md5sum"):
            self.hasher = self._compute_md5_md5sum
        else:
            self.hasher = self._compute_md5_python

    def compute(self, file_path):
        return self.hasher(file_path)

    def _compute_md5_md5sum(self, file_path):
        """ Compute MD5 hash using the md5sum command-line tool. """
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

    def _compute_md5_python(self, file_path):
        """ Compute MD5 hash using Python's hashlib. """
        hash_md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()

class CImageHash(metaclass=CSingletonMeta):
    """Class to compute perceptual image hash."""
    def __init__(self):
        pass
    
    @staticmethod
    def compute(file_path):
        """Compute perceptual hash of an image."""
        try:
            image_hash = imagehash.phash(Image.open(file_path))    
        except:
            image_hash = None
        return str(image_hash)

        pass


class CImageExif:    
    """Class to handle image EXIF data extraction."""
    def __init__(self, file_path):
        self.file_path = file_path
        self.exif_data = self._get_exif()


    def _get_exif(self, ignore_error=True) -> dict:
        """
        :param file_path: image path
        :param search_list: if you want to get some property, then you can pass the id or name, it will return by order.
        :param ignore_error:
        :return:
            int: -1 FileNotFoundError, or exif is None
            PIL.Image.Exif: when the `search_list` is None, return the whole Exif
        """
        tag_by_id: dict = PIL.ExifTags.TAGS
        
        try:
            im: PIL.Image.Image = PIL.Image.open(str(self.file_path))
        except FileNotFoundError:
            if ignore_error:
                return -1
            else:
                raise FileNotFoundError(self.file_path)
        
        exif: PIL.Image.Exif = im.getexif()
        im.close()

        if not exif:
            if ignore_error:
                return -1
            else:
                raise ValueError("exif is None")
        # Create a copy with tag names instead of decimal values
        copy_exif: dict = {}
        for dec_value in exif:
            if dec_value in tag_by_id:
                #change key from dec to name
                copy_exif[tag_by_id[dec_value]] = exif[dec_value]
            else:
                continue
        return copy_exif
    
    def __str__(self):
        return str(self.exif_data)
        
class CImageDatetime:
    """Class to handle image datetime extraction from EXIF."""
    def __init__(self, exif: CImageExif):
        self.exif_data = exif.exif_data
        self.date_time = self._get_creation_time()
        self.year = self._get_year()
        self.month = self._get_month()
        self.day = self._get_day()
        self.time = self._get_time()
            
        pass

    def _get_year(self) -> Union[str, None]:
        """Extract year from creation time."""
        return self.date_time[0:4]
    
    def _get_month(self) -> Union[str, None]:
        """Extract month from creation time."""
        return self.date_time[5:7]
    
    def _get_day(self) -> Union[str, None]:
        """Extract day from creation time."""
        return self.date_time[8:10]
            
    def _get_time(self) -> Union[str, None]:
        """Extract time from creation time."""
        return self.date_time[11:19]
    
    def _get_creation_time(self) -> Union[str, None]:
        """Get the creation time from EXIF data."""
        if 'DateTimeOriginal' in self.exif_data:      
            return self.exif_data.get('DateTimeOriginal', None)
        elif 'DateTimeDigitized' in self.exif_data:
            return self.exif_data.get('DateTimeDigitized', None)
        elif 'DateTime' in self.exif_data:
            return self.exif_data.get('DateTime', None) 
        else:
            return None
    
    def __str__(self):
        return self.date_time if self.date_time else "Unknown"

class CImage:
    """Class representing an image with its hashes and path."""
    def __init__(self, file_path):
        if os.path.exists(file_path) is False:
            raise FileNotFoundError(f"File {file_path} does not exist.")
        self.file_path = file_path
        self.md5_hash = CImageMD5().compute(file_path)
        self.image_hash = CImageHash().compute(file_path)
        if self.md5_hash is None or self.image_hash is None:
            raise ValueError(f"Could not compute hashes for {file_path}.")
        self.exif_data = CImageExif(self.file_path)
        self.creation_time = CImageDatetime(self.exif_data)
        
    def copy_to_new_path(self, new_path: str) -> bool:
        """Copy image to a new path based on creation time. 
           New_path should include the directory and the filename.
        """        
        if not os.path.exists(new_path):
            #copy image from to new path
            shutil.copy2(self.file_path, new_path)
            self.file_path = new_path
            return True
        return False
            
            
        
def main():
    args = parse_args()
    if not os.path.exists(args.image_path):
        print(f"File {args.image_path} does not exist.")
        return
    
    img = CImage(args.image_path)
    print(f"File Path: {img.file_path}")
    print(f"MD5: {img.md5_hash}")
    print(f"Image Hash: {img.image_hash}")
    print(f"Creation Time: {img.creation_time}")
    print(f"EXIF Data: {img.exif_data}")
    
    pass

def parse_args():
    parser = argparse.ArgumentParser(description="Image Hashing Tool")
    parser.add_argument("image_path", type=str, help="Path to the image file")
    return parser.parse_args()

if __name__ == "__main__":
    main()    
    