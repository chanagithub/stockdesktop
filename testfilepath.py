from find_saved_datafile_path import FindSavedDatafilePath


finder = FindSavedDatafilePath()

path = finder.get_pythonista_icloud_path()


if path is None:
    print("Cannot find Pythonista iCloud folder")

else:
    print("FOUND PATH:")
    print(path)