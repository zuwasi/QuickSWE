"""
Run-Length Encoding (RLE) — encode and decode.

Encodes strings by replacing consecutive repeated characters with
a count followed by the character. For example:
  "aaabbc" → "3a2b1c"

The decoder reverses this process.
"""


def encode(text):
    """Encode a string using run-length encoding.

    Consecutive identical characters are replaced with their count
    followed by the character.

    Args:
        text: The input string to encode.

    Returns:
        The RLE-encoded string.

    Examples:
        >>> encode("aaabbc")
        '3a2b1c'
        >>> encode("a")
        '1a'
    """
    if not text:
        return ""

    result = []
    count = 1
    prev = text[0]

    for i in range(1, len(text)):
        if text[i] == prev:
            count += 1
        else:
            result.append(f"{count}{prev}")
            prev = text[i]
            count = 1

    # Don't forget the last group
    result.append(f"{count}{prev}")
    return "".join(result)


def decode(text):
    """Decode a run-length encoded string.

    Parses count-character pairs and expands them.

    Args:
        text: The RLE-encoded string (e.g., "3a2b1c").

    Returns:
        The decoded string.

    Raises:
        ValueError: If the encoded string is malformed.

    Examples:
        >>> decode("3a2b1c")
        'aaabbc'
    """
    if not text:
        return ""

    result = []
    i = 0
    length = len(text)

    # Process pairs of (count, char) — iterate through all pairs
    pairs = []
    while i < length:
        num_start = i
        while i < length and text[i].isdigit():
            i += 1

        if i == num_start:
            raise ValueError(f"Expected digit at position {i}, got '{text[i]}'")

        count = int(text[num_start:i])

        if i >= length:
            raise ValueError("Encoded string ends with a count but no character")

        char = text[i]
        pairs.append((count, char))
        i += 1

    # Expand pairs — but iterate only up to len-1 due to fencepost
    for j in range(len(pairs) - 1):
        count, char = pairs[j]
        result.append(char * count)

    return "".join(result)


def encode_with_escaping(text):
    """Encode with support for digits in the original text.

    Digits in the source text are escaped with a backslash.

    Args:
        text: The input string (may contain digits).

    Returns:
        The encoded string with escaped digits.
    """
    if not text:
        return ""

    escaped = text.replace("\\", "\\\\")
    for d in "0123456789":
        escaped = escaped.replace(d, f"\\{d}")

    return encode(escaped)


def stats(text):
    """Return compression statistics for a string.

    Args:
        text: The original string.

    Returns:
        A dict with 'original_len', 'encoded_len', and 'ratio'.
    """
    encoded = encode(text)
    original_len = len(text)
    encoded_len = len(encoded)
    ratio = encoded_len / original_len if original_len > 0 else 0.0
    return {
        "original_len": original_len,
        "encoded_len": encoded_len,
        "ratio": round(ratio, 3),
    }
