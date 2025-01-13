import os

# Lists all files in a directory
# TODO: limit to data subdir! Stop path traversal attacks.
# dir_path: directory to list
def list_files_in_dir(
        dir_path: str, 
        append_path: bool
        ) -> list:
    try:
        files = os.listdir(dir_path)
        # Format files with directory in front
        if append_path == True:
            for file in files:
                if dir_path[-1] != "/":
                    dir_path += "/"
                files[files.index(file)] = dir_path + file
    # TODO: Catch specific exception for no files existing
    except Exception as error:
        print("Could not list files:", error)
        files = []

    # TODO: fix this check and uncomment it
    # This removed odd-numbered files instead of non-files
    # as intended.
    """
    # Remove non-files from the list
    for item in files:
        if not os.path.isfile(os.path.join(ROOT_DATA_DIR, item)):
            files.remove(item)
    """
    return files

def iterate(cur_path,allFiles):
    # Iterate directory and subdirectories
    for item in os.listdir(cur_path):
        fullPath=os.path.join(cur_path, item)
        # check if current path is a file
        if os.path.isfile(fullPath):
            if os.path.basename(cur_path) == "power":
                allFiles.append(fullPath) # This is a file in the right place. Keep it.
        else:
            # This is a directory, not a file. We may need the files inside it.
            # Iterate through the subdirectory looking for power directories
            iterate(fullPath,allFiles)