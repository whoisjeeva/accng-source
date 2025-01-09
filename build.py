import os
import py_compile
import subprocess
import sys
import shutil

from accng import Encoder
from util import log


class Build:
    def __init__(self):
        self.enc = Encoder("knbjhyugs567yhbj")

    def run(self):
        log.info("[ ENCRYPT ] modules...")
        self.encrypt_modules()

        log.info("[ ENCRYPT ] plugins...")
        self.encrypt_plugins()

        # log.info("[ COMPILE ] core...")
        # self.compile()

        pyinstaller_path = os.path.join('venv', 'Scripts', 'pyinstaller') if os.name == 'nt' else os.path.join('venv', 'bin', 'pyinstaller')
        # command = [
        #     pyinstaller_path,
        #     '--onefile',          # This flag creates a single executable file
        #     '--distpath', "dist",  # Specifies the output directory for the exe
        #     "accng.py"
        # ]
        command = [
            pyinstaller_path,
            "accng.spec"
        ]

        try:
            log.info("Generating exe...")
            subprocess.run(command, check=True)
            log.success("Executable created successfully.")
        except subprocess.CalledProcessError as e:
            print(f"Error occurred: {e}")
            sys.exit(1)

    
    def __compile(self, folder):
        mods = []
        for root, dirs, files in os.walk(f"{folder}"):
            root = root.replace("\\", "/")
            for f in files:
                rt = "/".join(root.split("/")[1:])
                if rt.strip():
                    path = "{}/{}".format(rt, f)
                else:
                    path = "{}".format(f)
                if path.endswith(".py"):
                    ms = ".".join(path.split(".")[:-1])
                    mods.append(ms)
        
        os.makedirs(f"dist/{folder}", exist_ok=True)
        for m in mods:
            log.info(f"Compiling {folder}/{m}...")
            py_compile.compile(f"{folder}/{m}.py", cfile=f"dist/{folder}/{m}.pyc")

    def compile(self):
        self.__compile("core")
        self.__compile("data")
        self.__compile("lib")
        self.__compile("util")

    def encrypt_plugins(self):
        plugins_string = []
        for root, dirs, files in os.walk("plugins"):
            if "__pycache__" in root:
                continue
            root = root.replace("\\", "/")
            for f in files:
                rt = "/".join(root.split("/")[1:])
                if rt.strip():
                    path = "{}/{}".format(rt, f)
                else:
                    path = "{}".format(f)
                if path.endswith(".py"):
                    ms = ".".join(path.split(".")[:-1])
                    plugins_string.append(ms)

        for m in plugins_string:
            with open(f"plugins/{m}.py", "rb") as f:
                code = f.read().decode("utf-8")
            encoded_code = self.enc.e(code)

            nodes = m.split("/")
            nodes.pop(-1)
            path = f"dist/plugins/{"/".join(nodes)}"

            os.makedirs(path, exist_ok=True)

            with open(f"dist/plugins/{m}.m", "w") as f:
                f.write(encoded_code)
            log.info(f"Encrypting plugins/{m}...")   

    def encrypt_modules(self):
        modules_string = []
        for root, dirs, files in os.walk("modules"):
            if "__pycache__" in root:
                continue
            root = root.replace("\\", "/")
            for f in files:
                rt = "/".join(root.split("/")[1:])
                if rt.strip():
                    path = "{}/{}".format(rt, f)
                else:
                    path = "{}".format(f)
                if path.endswith(".py"):
                    ms = ".".join(path.split(".")[:-1])
                    modules_string.append(ms)

        for m in modules_string:
            with open(f"modules/{m}.py", "rb") as f:
                code = f.read().decode("utf-8")
            encoded_code = self.enc.e(code)

            nodes = m.split("/")
            nodes.pop(-1)
            path = f"dist/modules/{"/".join(nodes)}"

            os.makedirs(path, exist_ok=True)

            with open(f"dist/modules/{m}.m", "w") as f:
                f.write(encoded_code)
            log.info(f"Encrypting modules/{m}...")        


if __name__ == "__main__":
    shutil.rmtree("dist/modules")
    shutil.rmtree("dist/plugins")

    with open("core/version.py", "r") as f:
        v = f.read().strip()
    version = int(v.split("=")[-1].strip())
    with open("core/version.py", "w") as f:
        f.write(f"VERSION = {version+1}")

    build = Build()
    with open("core/extension.py", "w") as f:
        f.write("EXTENSION = \"m\"")
    build.run()
    with open("core/extension.py", "w") as f:
        f.write("EXTENSION = \"py\"")
