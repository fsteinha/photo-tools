from glob import glob
import os
from stat import S_IFDIR
import time
from PIL import Image
from pathlib import Path
from typing import Union, List, Tuple
import PIL.Image
import PIL.ExifTags

# Location with subdirectories
def rm_dir_list(l_list:list, s_pattern:str) -> list:
    s_found = None
    for s_item in l_list:
        if s_pattern == s_item.replace(r"/","").replace(r".",""):
            s_found = s_item
            break

    if s_found != None:           
        l_list.remove(s_found) 

    return l_list


def get_exif(file_path: Path,
             search_list: Union[int, str, List, Tuple] = None,
             ignore_error=True
             ) -> Union[int, PIL.Image.Exif, List]:
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
        im: PIL.Image.Image = PIL.Image.open(str(file_path))
    except FileNotFoundError:
        if ignore_error:
            return -1
        else:
            raise FileNotFoundError(file_path)
    
    exif: PIL.Image.Exif = im.getexif()
    im.close()

    if not exif:
        if ignore_error:
            return -1
        else:
            raise ValueError("exif is None")
    if search_list is None:
        return exif
    tag_by_name = {tag_by_id[dec_value]: exif[dec_value] for dec_value in exif if dec_value in tag_by_id}
    result_list = []
    if not isinstance(search_list, (list, tuple)):
        search_list = [search_list]
    for key in search_list:
        if isinstance(key, int):
            result_list.append(exif.get(key, None))
            continue
        try:
            dec_value = int(key, 16)
            result_list.append(exif.get(dec_value, None))
            continue
        except ValueError:
            ...
        result_list.append(tag_by_name.get(key, None))
    return result_list if len(result_list) > 1 else result_list[0]

def sortin_files(l_files:list, s_dest_dir:str) -> None:
    for s_file in l_files:
        exif_get = get_exif(s_file, 'DateTimeOriginal')
        #im = Image.open(s_file)
        # exif = im.getexif()
        # exif_get=exif.get(36867)
        # im.close()
        try:
            creation_time = exif_get.replace(":","").replace(" ","_")
            s_new_file_name = f"{creation_time}_{os.path.basename(s_file)}"
            print (s_new_file_name) 

        except:
            creation_time = "None"
            print (f"Error in {exif_get} {os.path.basename(s_file)}")
        

def main(s_sortin_path:str = "data", s_search_path:str = ".", l_exclude = ["lost+found"]) -> None: 
    l_dirs = glob(f"{s_search_path}/*/", recursive = True)
    l_dirs = rm_dir_list(l_dirs, s_sortin_path)
    for s_exc in l_exclude:
        l_dirs = rm_dir_list(l_dirs, s_exc)
    
    print (f"Search in {l_dirs}")

    for s_dir in l_dirs:
        l_files = glob(s_dir + '/**/*.jpg', recursive=True)
        sortin_files(l_files, s_sortin_path)
    



if __name__ == "__main__":
    main()


'''
# Get List of all images
files = glob.glob(my_path + '/**/*.jpg', recursive=True)

# For each image
for file in files:
    # Get File name and extension
    filename = os.path.basename(file)
    # Copy the file with os.rename
    os.rename(
        file,
        main_dir + filename
'''