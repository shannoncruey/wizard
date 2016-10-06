"""
Shared globals for this cast.
"""

import vars

TMPDIR = "/tmp"
DEFAULT_TIMEOUT = 60

VARS = vars.Vars()

class log():
    """
    The (to be expanded) central logging function.
    """
    @staticmethod
    def debug(msg):
        print("DEBUG: %s" % (msg))
    
    @staticmethod
    def info(msg):
        print("INFO: %s" % (msg))
    
    @staticmethod
    def warning(msg):
        print("WARNING: %s" % (msg))
    
    @staticmethod
    def error(msg):
        print("ERROR: %s" % (msg))
        
        
def uuid():
    return str(uuid.uuid4())


def replace_variables(s):
    """
    Parse the provided string, and replace any escaped variables accordingly.
    """
    # for the moment does nothing
    return s