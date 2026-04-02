def parse_csv(text):
    """Parse CSV text into a list of dictionaries.

    The first line is treated as the header row.
    Returns a list of dicts mapping header names to row values.
    Empty input should return an empty list.
    Rows with fewer fields than headers should pad with empty strings.
    """
    # BUG 1: splitlines then index 0 without checking for empty input
    lines = text.splitlines()
    headers = [h.strip() for h in lines[0].split(",")]  # IndexError on empty

    result = []
    for line in lines[1:]:
        stripped = line.strip()
        if not stripped:
            continue
        values = [v.strip() for v in stripped.split(",")]
        # BUG 2: strict length check raises instead of padding short rows
        # (trailing comma produces an extra empty field, making len(values) ==
        #  len(headers)+1, which triggers this error)
        if len(values) != len(headers):
            raise ValueError(
                f"Row has {len(values)} fields, expected {len(headers)}"
            )
        row = dict(zip(headers, values))
        result.append(row)

    return result
