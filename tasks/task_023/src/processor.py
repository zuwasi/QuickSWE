"""Monolithic data processor with hardcoded pipeline steps."""

from typing import Any


class DataProcessor:
    """Processes data through a fixed pipeline: validate → transform → enrich → filter → aggregate."""

    def __init__(self, config=None):
        self.config = config or {}
        self.errors = []
        self.stats = {"processed": 0, "filtered": 0, "errors": 0}

    def process(self, data: Any) -> dict:
        """Run data through the full processing pipeline."""
        self.errors.clear()
        self.stats = {"processed": 0, "filtered": 0, "errors": 0}

        # Step 1: Validate
        validated = self._validate(data)
        if validated is None:
            return {"result": None, "errors": self.errors, "stats": self.stats}

        # Step 2: Transform
        transformed = self._transform(validated)

        # Step 3: Enrich
        enriched = self._enrich(transformed)

        # Step 4: Filter
        filtered = self._filter(enriched)

        # Step 5: Aggregate
        aggregated = self._aggregate(filtered)

        self.stats["processed"] = len(filtered) if isinstance(filtered, list) else 1
        return {"result": aggregated, "errors": self.errors, "stats": self.stats}

    def _validate(self, data: Any):
        """Validate incoming data structure."""
        if data is None:
            self.errors.append("Data cannot be None")
            self.stats["errors"] += 1
            return None

        if isinstance(data, list):
            valid_items = []
            for i, item in enumerate(data):
                if isinstance(item, dict):
                    if "id" in item:
                        valid_items.append(item)
                    else:
                        self.errors.append(f"Item {i} missing 'id' field")
                        self.stats["errors"] += 1
                elif isinstance(item, str):
                    if item.strip():
                        valid_items.append({"id": i, "value": item.strip()})
                    else:
                        self.errors.append(f"Item {i} is empty string")
                        self.stats["errors"] += 1
                elif isinstance(item, (int, float)):
                    valid_items.append({"id": i, "value": item})
                else:
                    self.errors.append(f"Item {i} has unsupported type: {type(item).__name__}")
                    self.stats["errors"] += 1
            return valid_items if valid_items else None

        elif isinstance(data, dict):
            if "id" in data:
                return [data]
            else:
                self.errors.append("Dict data missing 'id' field")
                self.stats["errors"] += 1
                return None

        elif isinstance(data, str):
            if data.strip():
                return [{"id": 0, "value": data.strip()}]
            else:
                self.errors.append("Empty string data")
                self.stats["errors"] += 1
                return None

        else:
            self.errors.append(f"Unsupported data type: {type(data).__name__}")
            self.stats["errors"] += 1
            return None

    def _transform(self, records: list) -> list:
        """Normalize and transform records."""
        transformed = []
        for record in records:
            new_record = {}
            for key, value in record.items():
                # Normalize string values
                if isinstance(value, str):
                    new_record[key.lower()] = value.strip().lower()
                elif isinstance(value, (int, float)):
                    new_record[key.lower()] = value
                elif isinstance(value, list):
                    new_record[key.lower()] = [
                        v.strip().lower() if isinstance(v, str) else v
                        for v in value
                    ]
                elif isinstance(value, dict):
                    new_record[key.lower()] = {
                        k.lower(): v.strip().lower() if isinstance(v, str) else v
                        for k, v in value.items()
                    }
                else:
                    new_record[key.lower()] = value

            # Add type classification
            if "value" in new_record:
                val = new_record["value"]
                if isinstance(val, str):
                    new_record["_type"] = "text"
                elif isinstance(val, (int, float)):
                    new_record["_type"] = "numeric"
                else:
                    new_record["_type"] = "other"

            transformed.append(new_record)
        return transformed

    def _enrich(self, records: list) -> list:
        """Add computed fields to records."""
        enriched = []
        for record in records:
            enriched_record = dict(record)

            # Add length for string values
            if "value" in enriched_record and isinstance(enriched_record["value"], str):
                enriched_record["_length"] = len(enriched_record["value"])

            # Add tags based on config
            tags = []
            if self.config.get("tag_prefix"):
                tags.append(self.config["tag_prefix"])

            if enriched_record.get("_type") == "numeric":
                val = enriched_record["value"]
                if isinstance(val, (int, float)):
                    if val > 100:
                        tags.append("high")
                    elif val > 10:
                        tags.append("medium")
                    else:
                        tags.append("low")

            if enriched_record.get("_type") == "text":
                text = enriched_record.get("value", "")
                if len(text) > 50:
                    tags.append("long_text")
                elif len(text) > 10:
                    tags.append("medium_text")
                else:
                    tags.append("short_text")

            if tags:
                enriched_record["_tags"] = tags

            enriched.append(enriched_record)
        return enriched

    def _filter(self, records: list) -> list:
        """Filter records based on config criteria."""
        if not self.config.get("filters"):
            return records

        filters = self.config["filters"]
        filtered = []
        for record in records:
            keep = True

            if "min_value" in filters:
                val = record.get("value")
                if isinstance(val, (int, float)) and val < filters["min_value"]:
                    keep = False

            if "max_value" in filters:
                val = record.get("value")
                if isinstance(val, (int, float)) and val > filters["max_value"]:
                    keep = False

            if "required_tags" in filters:
                record_tags = set(record.get("_tags", []))
                required = set(filters["required_tags"])
                if not required.issubset(record_tags):
                    keep = False

            if "exclude_types" in filters:
                if record.get("_type") in filters["exclude_types"]:
                    keep = False

            if keep:
                filtered.append(record)
            else:
                self.stats["filtered"] += 1

        return filtered

    def _aggregate(self, records: list) -> dict:
        """Compute summary statistics over records."""
        if not records:
            return {"count": 0, "items": []}

        result = {
            "count": len(records),
            "items": records,
        }

        # Compute numeric aggregations
        numeric_values = []
        for r in records:
            val = r.get("value")
            if isinstance(val, (int, float)):
                numeric_values.append(val)

        if numeric_values:
            result["numeric_summary"] = {
                "sum": sum(numeric_values),
                "min": min(numeric_values),
                "max": max(numeric_values),
                "avg": sum(numeric_values) / len(numeric_values),
                "count": len(numeric_values),
            }

        # Compute type distribution
        type_counts = {}
        for r in records:
            t = r.get("_type", "unknown")
            type_counts[t] = type_counts.get(t, 0) + 1
        result["type_distribution"] = type_counts

        # Collect all tags
        all_tags = set()
        for r in records:
            for tag in r.get("_tags", []):
                all_tags.add(tag)
        result["all_tags"] = sorted(all_tags)

        return result
