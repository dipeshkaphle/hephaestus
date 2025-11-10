from dataclasses import dataclass, asdict
from typing import Optional, List
import json


@dataclass
class TransformationRecord:
    """A record of a single transformation applied to the AST."""
    transformation_name: str
    target_node_id: str
    description: str
    original_type: Optional[str] = None
    new_type: Optional[str] = None
    # New fields for debugging type selection
    available_types_pool: Optional[List[str]] = None # All types available to choose from
    relevant_types_found: Optional[List[str]] = None # Super- and sub-types that were excluded
    candidate_pool: Optional[List[str]] = None       # The final list of "irrelevant" types to choose from



class TransformationTracker:
    """A class to track transformations applied to the AST."""
    def __init__(self, enabled: bool = True):
        self.enabled = enabled
        self.records: List[TransformationRecord] = []

    def record(self, record: TransformationRecord):
        """Adds a transformation record to the log."""
        if self.enabled:
            self.records.append(record)

    def get_records(self) -> List[TransformationRecord]:
        """Returns the list of recorded transformations."""
        return self.records

    def to_json_string(self) -> str:
        """Serializes the records to a JSON string."""
        return json.dumps([asdict(rec) for rec in self.records], indent=2)

    def clear(self):
        """Clears all recorded transformations."""
        self.records = []
