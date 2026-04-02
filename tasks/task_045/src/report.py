"""Report generation for ETL pipeline."""


def generate_report(records: list[dict], table_name: str,
                    total_raw: int, total_cleaned: int,
                    total_valid: int, total_loaded: int,
                    errors: list[str] = None) -> str:
    """Generate a text summary report of the ETL run.

    Args:
        records: The final loaded records.
        table_name: Name of the target table.
        total_raw: Number of raw records extracted.
        total_cleaned: Number after cleaning.
        total_valid: Number after validation.
        total_loaded: Number loaded into DB.
        errors: List of error messages encountered.

    Returns:
        A formatted report string.
    """
    lines = [
        "=" * 50,
        "ETL Pipeline Report",
        "=" * 50,
        f"Target Table: {table_name}",
        f"Records Extracted: {total_raw}",
        f"Records After Cleaning: {total_cleaned}",
        f"Records After Validation: {total_valid}",
        f"Records Loaded: {total_loaded}",
    ]
    if errors:
        lines.append(f"Errors: {len(errors)}")
        for err in errors:
            lines.append(f"  - {err}")
    else:
        lines.append("Errors: 0")
    lines.append("=" * 50)
    return "\n".join(lines)
