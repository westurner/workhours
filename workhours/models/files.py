import tempfile
import shutil
import os
import codecs
import glob


class TempDir(object):
    def __init__(self, path=None, create=True, dir="tmp", prefix="whtmp-"):
        if not path:
            if create:
                self.path = tempfile.mkdtemp(suffix="", prefix=prefix, dir=dir)
            else:
                self.path = os.path.join(dir, "whtmp")
        else:
            self.path = os.path.expanduser(path)
            if create:
                if not os.path.exists(self.path):
                    os.mkdir(self.path, 0o700)
        return

    def copy_here(self, filename, dest_path=None):
        if dest_path:
            dest = os.path.join(self.path, dest_path)
        else:
            dest = self.path
        dest_path = os.path.join(dest, os.path.basename(filename))

        with self.get_log() as f:
            f.writelines(
                (self.format_path(filename, dest_path).replace(self.path, ""))
            )

        if "*" in filename:
            import glob

            filenames = glob.glob(filename)
        else:
            filenames = [filename]
        for filename in filenames:
            shutil.copy2(filename, dest_path)
        return dest_path

    def format_path(self, path, source):
        return "%s = %s" % (path, source)

    def get_log(self):
        return codecs.open(
            os.path.join(os.path.dirname(self.path), "SOURCES"),
            "w+",
            encoding="utf-8",
        )

    def mkdir(self, path):

        with self.get_log() as f:
            f.writelines(path)
        mkpath = os.path.join(self.path, path)
        if not os.path.exists(mkpath):
            os.mkdir(mkpath)
        return TempDir(path=mkpath, create=False)

    def add_path(self, path, source):
        with self.get_log() as f:
            f.writelines(self.format_path(path, source))
        return os.path.join(self.path, path)

    # def __del__(self):
    # if managed:
    #     shutil.rmtree(self.path)
    #    pass


def initialize_fs(*args, **kwargs):
    return TempDir(*args, create=True, **kwargs)
