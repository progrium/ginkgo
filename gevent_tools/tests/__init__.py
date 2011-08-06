import sys
import StringIO

class silencer:
    """Context manager that silences stdout and stderr"""
    
    def __enter__(self):
        self.old_stdout = sys.stdout
        self.old_stderr = sys.stderr
        sys.stdout = StringIO.StringIO()
        sys.stderr = StringIO.StringIO()
    
    def __exit__(self, type, value, traceback):
        sys.stdout = self.old_stdout
        sys.stderr = self.old_stderr
    
def mock_open(file_map, default=None):
    """Generates a function to replace `open` for testing file operations"""
    file_map.update({"/dev/null": ""})
    def open_mock(*args, **kwargs):
        path, mode = args[0:2]
        contents = file_map.get(path, default)
        if mode == 'r' and contents is None:
            raise IOError("File not found: %s" % path)
        elif mode == 'w':
            contents = ""
        return StringIO.StringIO(contents)
    return open_mock
