import json
import ollama
import re

# ── Load schema ──────────────────────────────────────────────────────────────
def load_schema(schema_path="schema/schema.json"):
    with open(schema_path, "r") as f:
        return json.load(f)

# ── Clean and extract JSON from response ─────────────────────────────────────
def extract_json(text: str) -> dict:
    # Remove backticks and markdown
    text = text.strip()
    if "```" in text:
        parts = text.split("```")
        for part in parts:
            part = part.strip()
            if part.startswith("json"):
                part = part[4:].strip()
            if part.startswith("{"):
                text = part
                break

    # Find the first { and last } to extract clean JSON
    start = text.find("{")
    end = text.rfind("}") + 1
    if start == -1 or end == 0:
        raise ValueError("No JSON found in response")

    text = text[start:end]
    return json.loads(text)

# ── Call Ollama ───────────────────────────────────────────────────────────────
def ask_ollama(schema: dict) -> dict:

    # Only send table names and column names (smaller = better response)
    simplified = {}
    for table, columns in schema.items():
        simplified[table] = list(columns.keys()) if isinstance(columns, dict) else columns

    schema_text = json.dumps(simplified, indent=2)

    prompt = f"""You are a database analyst. Analyze this database schema.
Return ONLY a JSON object with NO extra text, NO markdown, NO backticks.

Use exactly this format:
{{
  "business_type": "Music Store",
  "business_description": "Short 2 sentence description.",
  "tables": {{
    "Album": {{
      "purpose": "Stores music albums",
      "important_columns": ["AlbumId", "Title"]
    }}
  }},
  "relationships": "One sentence about how tables connect.",
  "potential_insights": ["insight 1", "insight 2", "insight 3", "insight 4", "insight 5"]
}}

Schema to analyze:
{schema_text}

Return ONLY the JSON object:"""

    response = ollama.chat(
        model="llama3.2",
        messages=[{"role": "user", "content": prompt}],
        options={"temperature": 0}
    )

    raw_text = response["message"]["content"]
    return extract_json(raw_text)

# ── Save result ──────────────────────────────────────────────────────────────
def save_understanding(understanding: dict, output_path="schema/db_understanding.json"):
    with open(output_path, "w") as f:
        json.dump(understanding, f, indent=4)
    print(f"Saved to {output_path}")

# ── Print summary ────────────────────────────────────────────────────────────
def print_summary(understanding: dict):
    print("\n" + "="*50)
    print("AI DATABASE UNDERSTANDING")
    print("="*50)
    print(f"\nBusiness Type : {understanding['business_type']}")
    print(f"\nDescription   : {understanding['business_description']}")
    print(f"\nTables ({len(understanding['tables'])} found):")
    for name, info in understanding["tables"].items():
        print(f"   - {name}: {info['purpose']}")
    print(f"\nRelationships : {understanding['relationships']}")
    print(f"\nPotential Insights:")
    for i, insight in enumerate(understanding["potential_insights"], 1):
        print(f"   {i}. {insight}")
    print("\n" + "="*50)

# ── Main ─────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("Step 2: AI Schema Understanding (Running Locally via Ollama)")
    print("Loading schema...")
    schema = load_schema()
    print(f"Found {len(schema)} tables. Asking Llama3.2 to analyze...")
    print("Please wait 30-60 seconds...")
    understanding = ask_ollama(schema)
    print_summary(understanding)
    save_understanding(understanding)