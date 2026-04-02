"""Monolithic ETL function — needs refactoring into declarative pipeline.

This file contains the original procedural extract_transform_load function
and should eventually contain the refactored Step/Pipeline classes.
"""

from .file_io import read_source
from .database import MockDatabase
from .report import generate_report


def extract_transform_load(source: str, db: MockDatabase,
                           table_name: str = "records") -> str:
    """Monolithic ETL function that does everything in one go.

    Reads source data, cleans it, validates it, transforms it,
    loads it into the database, and generates a report.

    Args:
        source: CSV-formatted string data.
        db: MockDatabase instance.
        table_name: Target table name.

    Returns:
        Report string.
    """
    errors = []

    # --- EXTRACT ---
    raw_records = read_source(source)
    total_raw = len(raw_records)

    # --- CLEAN ---
    cleaned = []
    for record in raw_records:
        clean_record = {}
        skip = False
        for key, value in record.items():
            if value is None or value.strip() == "" or value.strip().lower() == "null":
                if key in ("name", "id"):
                    skip = True
                    errors.append(f"Missing required field '{key}' in record")
                    break
                clean_record[key] = None
            else:
                clean_record[key] = value.strip()
        if not skip:
            cleaned.append(clean_record)
    total_cleaned = len(cleaned)

    # --- VALIDATE ---
    validated = []
    for record in cleaned:
        valid = True
        if "age" in record and record["age"] is not None:
            try:
                age_val = int(record["age"])
                if age_val < 0 or age_val > 150:
                    valid = False
                    errors.append(f"Invalid age {age_val} for record {record.get('name', '?')}")
            except (ValueError, TypeError):
                valid = False
                errors.append(f"Non-numeric age '{record['age']}' for record {record.get('name', '?')}")
        if "email" in record and record["email"] is not None:
            if "@" not in record["email"]:
                valid = False
                errors.append(f"Invalid email '{record['email']}' for record {record.get('name', '?')}")
        if "salary" in record and record["salary"] is not None:
            try:
                salary_val = float(record["salary"])
                if salary_val < 0:
                    valid = False
                    errors.append(f"Negative salary {salary_val}")
            except (ValueError, TypeError):
                valid = False
                errors.append(f"Non-numeric salary '{record['salary']}'")
        if valid:
            validated.append(record)
    total_valid = len(validated)

    # --- TRANSFORM ---
    transformed = []
    for record in validated:
        new_record = dict(record)
        # Type conversions
        if "age" in new_record and new_record["age"] is not None:
            new_record["age"] = int(new_record["age"])
        if "salary" in new_record and new_record["salary"] is not None:
            new_record["salary"] = float(new_record["salary"])
        # Derived fields
        if "salary" in new_record and new_record["salary"] is not None:
            salary = new_record["salary"]
            if salary > 100000:
                new_record["salary_band"] = "high"
            elif salary > 50000:
                new_record["salary_band"] = "medium"
            else:
                new_record["salary_band"] = "low"
        if "name" in new_record and new_record["name"] is not None:
            new_record["name_upper"] = new_record["name"].upper()
        transformed.append(new_record)

    # --- LOAD ---
    db.create_table(table_name)
    for record in transformed:
        db.insert(table_name, record)
    total_loaded = len(transformed)

    # --- REPORT ---
    report = generate_report(
        records=transformed,
        table_name=table_name,
        total_raw=total_raw,
        total_cleaned=total_cleaned,
        total_valid=total_valid,
        total_loaded=total_loaded,
        errors=errors if errors else None,
    )
    return report
