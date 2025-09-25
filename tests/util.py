import shutil
import contextlib as ctxlib


@ctxlib.contextmanager
def make_backup_file(filename):
    """Thanks to that this not gonna hurt your .bashrc file :)"""
    FN_BAK= f"{filename}.bak"
    try:  # make backup
        shutil.copyfile(filename, FN_BAK)
        yield
    finally:  # restore file
        if os.path.exists(FN_BAK):
            os.remove(filename)
            shutil.move(FN_BAK, filename)

