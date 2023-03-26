class LogCategory(object):
    """
    Class regarding log message category.
    """
    # Define log message categories.
    USE     = 1 << 0
    DIAG    = 1 << 1
    EVENT   = 1 << 2
    PROBLEM = 1 << 3
    WARNING = 1 << 4
    BUG     = 1 << 5
    DEBUG   = 1 << 6
    VERBOSE = 1 << 7


    # Type v.s. text mapping.
    _TEXT = {USE:     'USE',
             DIAG:    'DIAG',
             EVENT:   'EVENT',
             PROBLEM: 'PROBLEM',
             WARNING: 'WARNING',
             BUG:     'BUG',
             DEBUG:   'DEBUG',
             VERBOSE: 'VERBOSE'}


    @classmethod
    def text(cls, category):
        """
        Mapping the given category type to corresponding text.

        'category' must be a valid category type.
        """
        return cls._TEXT[category]


    @classmethod
    def category(cls, text):
        """
        Mapping the given category text to corresponding type.

        'text' must be a valid category text name.
        """
        text = text.upper()

        if text == cls._TEXT[cls.USE]:
            return cls.USE
        elif text == cls._TEXT[cls.DIAG]:
            return cls.DIAG
        elif text == cls._TEXT[cls.EVENT]:
            return cls.EVENT
        elif text == cls._TEXT[cls.PROBLEM]:
            return cls.PROBLEM
        elif text == cls._TEXT[cls.WARNING]:
            return cls.WARNING
        elif text == cls._TEXT[cls.BUG]:
            return cls.BUG
        elif text == cls._TEXT[cls.DEBUG]:
            return cls.DEBUG
        else:
            # Must be verbose.
            return cls.VERBOSE




