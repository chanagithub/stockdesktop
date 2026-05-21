
from pathlib import Path
import platform


class FindSavedDatafilePath:

    def __init__(self):
        self.system = platform.system()

    def get_pythonista_icloud_path(self):

        possible_paths = []

        # ---------- macOS ----------
        if self.system == "Darwin":

            possible_paths = [
                Path.home()
                / "Library/Mobile Documents/iCloud~com~omz-software~Pythonista3/stockfundios",

                Path.home()
                / "Library/Mobile Documents/iCloud~omz-software~Pythonista3/Documents/stockfundios",

                Path.home()
                / "Library/Mobile Documents/com~omz-software~Pythonista3/Documents/stockfundios",
            ]

        # ---------- Windows ----------
        elif self.system == "Windows":

            possible_paths = [
                Path.home()
                / "iCloudDrive/iCloud~com~omz-software~Pythonista3/stockfundios",

                Path.home()
                / "Apple/CloudDocs/Pythonista 3/stockfundios",

                Path.home()
                / "iCloudDrive/Pythonista 3/stockfundios",
            ]

        # ---------- Search ----------
        for path in possible_paths:
            if path.exists():
                return path

        # ---------- Deep Search ----------
        try:
            for path in Path.home().rglob("stockfundios"):

                path_str = str(path).lower()

                if (
                    path.is_dir()
                    and "icloud" in path_str
                    and "pythonista3" in path_str
                ):
                    return path

        except Exception as e:
            print(f"Search error: {e}")

        return None