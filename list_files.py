from os import listdir
import os.path
from config import ROOT_DATA_DIR

# Lists all files in a directory
# TODO: limit to data subdir! Stop path traversal attacks.
# dir_path: directory to list
def list_files_in_dir(dir_path, append_path):
    try:
        files = listdir(dir_path)
        # Format files with directory in front
        if append_path == True:
            for file in files:
                if dir_path[-1] != "/":
                    dir_path += "/"
                files[files.index(file)] = dir_path + file
    # TODO: Catch specific exception for no files existing
    except:
        print("Could not list files.")
    # TODO: fix this check and uncomment it
    # This removed odd-numbered files instead of non-files
    # as intended.

    # Remove non-files from the list
    #for item in files:
        #if not os.path.isfile(os.path.join(ROOT_DATA_DIR, item)):
        #    files.remove(item)
    return files
