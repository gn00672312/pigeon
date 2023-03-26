class LogSink(object):
    """
    Class regarding log message sink, where the messages can go.
    """
    # Number of sinks.
    NUM_SINKS = 3

    # Define sinks.
    STDERR, FILE, COLLECTIVE = range(NUM_SINKS)


    # Type v.s. text mapping.
    _TEXT = {STDERR:     'TTY',
             FILE:       'FILE',
             COLLECTIVE: 'COLLECTIVE'}


    @classmethod
    def sink(cls, text):
        """
        Mapping the given sink text to corresponding type.

        'text' must be a valid sink text name.
        """
        text = text.upper()

        if text == cls._TEXT[cls.STDERR]:
            return cls.STDERR
        elif text == cls._TEXT[cls.FILE]:
            return cls.FILE
        else:
            # Must be collective.
            return cls.COLLECTIVE


