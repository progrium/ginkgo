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
    
def mock_open(file_map, default=''):
    """Generates a function to replace `open` for testing file operations"""
    def open_mock(*args, **kwargs):
        return StringIO.StringIO(file_map.get(args[0], default))
    return open_mock