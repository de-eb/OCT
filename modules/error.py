class ModuleError(Exception):
    """Base exception class for all modules.
    
    All exceptions thrown from the package inherit this.
    
    Attributes
    ----------
    msg : `str`
        Human readable string describing the exception.
    
    """

    def __init__(self, msg: str):
        """Set the error message.
    
        Parameters
        ----------
        msg : `str`
            Human readable string describing the exception.
        
        """
        self.msg = msg
    
    def __str__(self):
        """Return the error message."""
        return self.msg
