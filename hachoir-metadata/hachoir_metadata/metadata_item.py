from hachoir_core.tools import makeUnicode, normalizeNewline

MIN_PRIORITY = 100
MAX_PRIORITY = 999
MAX_STR_LENGTH = 300              # 300 characters

class DataValue:
    def __init__(self, value, text):
        self.value = value
        self.text = text

class Data:
    def __init__(self, metadata, key, priority, description,  text_handler=None, type=None, filter=None):
        """
        handler is only used if value is not string nor unicode, prototype:
           def handler(value) -> str/unicode
        """
        assert MIN_PRIORITY <= priority <= MAX_PRIORITY
        assert isinstance(description, unicode)
        self.metadata = metadata
        self.key = key
        self.description = description
        self.values = []
        self.type = type
        self.text_handler = text_handler
        self.filter = filter
        self.priority = priority

    def _createItem(self, value, text=None):
        if text is None:
            if isinstance(value, unicode):
                text = value
            elif self.text_handler:
                text = self.text_handler(value)
                assert isinstance(text, unicode)
            else:
                text = makeUnicode(value)
        return DataValue(value, text)

    def add(self, value):
        if isinstance(value, tuple):
            if len(value) != 2:
                raise ValueError("Data.add() only accept tuple of 2 elements: (value,text)")
            value, text = value
        else:
            text = None

        # Skip value 'None'
        if value is None:
            return

        assert not self.type or isinstance(value, self.type), \
            "Value %r is not of type %r" % (value, self.type)

        # Convert string to Unicode string using charset ISO-8859-1
        if isinstance(value, str):
            value = unicode(value, "ISO-8859-1")

        # Skip empty strings
        if isinstance(value, unicode):
            value = value.strip(" \t\v\n\r\0")
            if not value:
                return
            value = normalizeNewline(value)
            if MAX_STR_LENGTH < len(value):
                value = value[:MAX_STR_LENGTH] + "(...)"

        # Skip duplicates
        if value in self:
            return

        # Use filter
        if self.filter and not self.filter(value):
            self.metadata.warning("Skip value %s=%r (filter)" % (self.key, value))
            return

        # For string, if you have "verlongtext" and "verylo",
        # keep the longer value
        if isinstance(value, unicode):
            for index, item in enumerate(self.values):
                if not isinstance(item, unicode):
                    continue
                if value.startswith(item):
                    # Find longer value, replace the old one
                    self.values[index] = self._createItem(value, text)
                    return
                if item.startswith(value):
                    # Find truncated value, skip it
                    return

        # Add new value
        self.values.append(self._createItem(value, text))

    def __len__(self):
        return len(self.values)

    def __getitem__(self, index):
        return self.values[index]

    def __contains__(self, value):
        for item in self.values:
            if value == item.value:
                return True
        return False

    def __cmp__(self, other):
        return cmp(self.priority, other.priority)
