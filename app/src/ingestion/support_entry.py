import json

from pydantic import BaseModel


class SupportEntry(BaseModel):
    name: str
    website: str | None
    emails: list[str]
    addresses: list[str]
    phone_numbers: list[str]
    description: str | None


SUPPORT_ENTRY_SCHEMA = json.dumps(SupportEntry.model_json_schema(), indent=2)
