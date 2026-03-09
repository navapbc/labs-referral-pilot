#!/usr/bin/env python3
"""
Re-test reviewed queries with updated prompts and add results as new columns.
"""

import json
import requests
import pandas as pd
from datetime import datetime
import sys

# API endpoint
API_BASE = "http://localhost:3000"

def call_referral_api(query: str, prompt_type: str, user_email: str = "test@example.com") -> dict:
    """Call the referral API and return the response."""
    # Map prompt_type to suffix
    # referral, referraltx -> suffix=centraltx
    # referralkeystone -> suffix=keystone

    endpoint = f"{API_BASE}/generate_referrals_rag/run"

    # Determine suffix based on prompt_type
    if prompt_type == "referralkeystone":
        suffix = "keystone"
    else:
        suffix = "centraltx"

    try:
        response = requests.post(
            endpoint,
            headers={"Content-Type": "application/json"},
            json={
                "query": query,
                "user_email": user_email,
                "suffix": suffix
            },
            timeout=180  # Increased timeout for LLM calls
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        return {"error": str(e)}


def extract_resources_summary(response: dict) -> str:
    """Extract a summary of resources from the API response."""
    try:
        if "error" in response:
            return f"ERROR: {response['error']}"

        replies = response.get("result", {}).get("llm", {}).get("replies", [])
        if not replies:
            return "No replies"

        text = replies[0].get("_content", [{}])[0].get("text", "")

        # Parse JSON to count resources
        try:
            data = json.loads(text)
            resources = data.get("resources", [])
            names = [r.get("name", "Unknown") for r in resources]

            # Check for availability_status in any resource
            has_availability = any(r.get("availability_status") for r in resources)

            summary = f"Resources: {len(resources)}"
            if has_availability:
                summary += " [has availability_status]"
            summary += f"\nNames: {', '.join(names[:5])}"
            if len(names) > 5:
                summary += f"... (+{len(names)-5} more)"

            return summary
        except json.JSONDecodeError:
            return f"Raw response (first 200 chars): {text[:200]}"

    except Exception as e:
        return f"Parse error: {str(e)}"


def format_readable_output(response: dict) -> str:
    """Format resources in a human-readable format matching the UI."""
    try:
        if "error" in response:
            return f"ERROR: {response['error']}"

        replies = response.get("result", {}).get("llm", {}).get("replies", [])
        if not replies:
            return "No resources found."

        text = replies[0].get("_content", [{}])[0].get("text", "")

        try:
            data = json.loads(text)
            resources = data.get("resources", [])

            if not resources:
                return "No resources found."

            output_lines = [f"=== {len(resources)} Resources Found ===\n"]

            for i, r in enumerate(resources, 1):
                # Type badge
                ref_type = r.get("referral_type", "")
                type_label = {
                    "goodwill": "[Goodwill]",
                    "government": "[Government]",
                    "external": "[Community]"
                }.get(ref_type, "[Other]")

                output_lines.append(f"--- Resource {i} {type_label} ---")
                output_lines.append(f"Name: {r.get('name', 'Unknown')}")

                # Address
                addresses = r.get("addresses", [])
                if addresses:
                    addr_str = " | ".join([a for a in addresses if a])
                    if addr_str:
                        output_lines.append(f"Address: {addr_str}")

                # Phone
                phones = r.get("phones", [])
                if phones:
                    phone_str = " | ".join([p for p in phones if p])
                    if phone_str:
                        output_lines.append(f"Phone: {phone_str}")

                # Email
                emails = r.get("emails", [])
                if emails:
                    email_str = " | ".join([e for e in emails if e])
                    if email_str:
                        output_lines.append(f"Email: {email_str}")

                # Website
                website = r.get("website", "")
                if website:
                    output_lines.append(f"Website: {website}")

                # Availability status (NEW field from prompt improvements)
                availability = r.get("availability_status", "")
                if availability:
                    output_lines.append(f"⚠️ Availability: {availability}")

                # Description
                description = r.get("description", "")
                if description:
                    # Truncate long descriptions
                    if len(description) > 300:
                        description = description[:297] + "..."
                    output_lines.append(f"Description: {description}")

                output_lines.append("")  # Blank line between resources

            return "\n".join(output_lines)

        except json.JSONDecodeError:
            return f"Error parsing response: {text[:500]}"

    except Exception as e:
        return f"Format error: {str(e)}"


def main():
    input_file = "/Users/ryan/Documents/Claude_Code/Phoenix Exports/sheets_sync/exports/reviewed_rows_2026-02-05.csv"
    output_file = "/Users/ryan/Documents/Claude_Code/Phoenix Exports/sheets_sync/exports/reviewed_rows_2026-02-05_retested.csv"

    print(f"Reading {input_file}...")
    df = pd.read_csv(input_file)
    print(f"Found {len(df)} rows")

    # Add new columns for retest results
    df['retest_timestamp'] = None
    df['retest_full_output'] = None
    df['retest_summary'] = None
    df['retest_has_availability_status'] = None
    df['retest_readable_output'] = None

    for idx, row in df.iterrows():
        query = row['natural_language_query']
        prompt_type = row['prompt_type']

        if pd.isna(query) or not query.strip():
            print(f"Row {idx}: Skipping empty query")
            continue

        print(f"\nRow {idx}: Testing '{prompt_type}' - {query[:60]}...")

        # Call API
        response = call_referral_api(query, prompt_type)

        # Store results
        df.at[idx, 'retest_timestamp'] = datetime.now().isoformat()
        df.at[idx, 'retest_full_output'] = json.dumps(response)

        # Extract summary
        summary = extract_resources_summary(response)
        df.at[idx, 'retest_summary'] = summary

        # Check for availability_status
        has_availability = "availability_status" in json.dumps(response)
        df.at[idx, 'retest_has_availability_status'] = has_availability

        # Format human-readable output (like UI)
        readable = format_readable_output(response)
        df.at[idx, 'retest_readable_output'] = readable

        print(f"  Result: {summary[:100]}...")

    # Save results
    print(f"\nSaving results to {output_file}...")
    df.to_csv(output_file, index=False)
    print("Done!")

    # Print summary
    print("\n=== Summary ===")
    print(f"Total rows: {len(df)}")
    print(f"Rows with availability_status: {df['retest_has_availability_status'].sum()}")


if __name__ == "__main__":
    main()
