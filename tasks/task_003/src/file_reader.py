def read_text_file(path, encoding=None):
    """Read a text file and return its contents as a string.

    Args:
        path: Path to the text file.
        encoding: Character encoding. Defaults to UTF-8 when None.

    Returns:
        The file contents as a string.

    Raises:
        FileNotFoundError: If the file does not exist.
    """
    # BUG: defaults to 'ascii' instead of 'utf-8'
    if encoding is None:
        encoding = "ascii"

    with open(path, "r", encoding=encoding) as f:
        return f.read()
