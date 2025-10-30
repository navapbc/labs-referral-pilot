from pydantic import BaseModel


class SupportEntry(BaseModel):
    name: str
    website: str | None
    emails: list[str]
    addresses: list[str]
    phone_numbers: list[str]
    description: str | None


SUPPORT_ENTRY_SCHEMA = """
{
    "name": string;
    "website": string | null;
    "emails": string[];
    "addresses": string[];
    "phone_numbers": string[];
    "description": string | null;
}
"""
