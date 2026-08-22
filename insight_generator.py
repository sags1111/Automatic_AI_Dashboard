import json
import ollama
import os


def load_json(path):
    if not os.path.exists(path):
        print(f"ERROR: File not found: {path}")
        exit(1)
    with open(path, "r") as f:
        return json.load(f)

def extract_json(text: str) -> dict:
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
    start = text.find("{")
    end = text.rfind("}") + 1
    if start == -1 or end == 0:
        raise ValueError("No JSON found in response")
    return json.loads(text[start:end])



def build_summary(understanding: dict, analysis: dict) -> str:
    summary = {}
    summary["business_type"] = understanding.get("business_type", "Unknown")
    summary["business_description"] = understanding.get("business_description", "")
    summary["tables"] = {}
    for table, data in analysis.items():
        summary["tables"][table] = {
            "total_rows": data.get("total_rows", 0),
            "columns": data.get("columns", []),
            "numeric_stats": data.get("numeric_stats", {})
        }
    return json.dumps(summary, indent=2, default=str)

# ── Ask Ollama ────────────────────────────────────────────────────────────────
def generate_insights(understanding: dict, analysis: dict) -> dict:
    summary_text = build_summary(understanding, analysis)

    prompt = f"""You are a business analyst. Analyze this database and return ONLY raw JSON.
No markdown. No backticks. No explanation. Just JSON.

{{
  "executive_summary": "3 sentence overview",
  "key_metrics": {{
    "metric name": "value"
  }},
  "insights": [
    {{
      "title": "insight title",
      "description": "what this means",
      "importance": "high"
    }}
  ],
  "recommendations": ["rec 1", "rec 2", "rec 3"],
  "suggested_charts": [
    {{
      "chart_type": "bar",
      "title": "chart title",
      "x_axis": "column",
      "y_axis": "column",
      "table": "table name"
    }}
  ]
}}

Data:
{summary_text}

JSON only:"""

    print("Sending request to Ollama...")
    response = ollama.chat(
        model="llama3.2",
        messages=[{"role": "user", "content": prompt}],
        options={"temperature": 0}
    )
    print("Got response from Ollama!")

    raw_text = response["message"]["content"]
    print(f"Response length: {len(raw_text)} characters")

    return extract_json(raw_text)


def save_insights(insights: dict, output_path="schema/insights.json"):
    with open(output_path, "w") as f:
        json.dump(insights, f, indent=4)
    print(f"Saved to {output_path}")


def print_insights(insights: dict):
    print("\n" + "="*55)
    print("AI BUSINESS INSIGHTS")
    print("="*55)
    print(f"\nSUMMARY:\n{insights.get('executive_summary', '')}")
    print(f"\nINSIGHTS:")
    for i, insight in enumerate(insights.get("insights", []), 1):
        print(f"   {i}. {insight.get('title', '')}")
    print(f"\nRECOMMENDATIONS:")
    for i, rec in enumerate(insights.get("recommendations", []), 1):
        print(f"   {i}. {rec}")
    print("\n" + "="*55)

# ── Main ──────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    try:
        print("Step 4: AI Business Insight Generator")
        print("Loading files...")

        understanding = load_json("schema/db_understanding.json")
        print("Loaded db_understanding.json")

        analysis = load_json("schema/data_analysis.json")
        print("Loaded data_analysis.json")

        print("Asking Llama3.2 to generate insights (30-60 seconds)...")
        insights = generate_insights(understanding, analysis)

        print_insights(insights)
        save_insights(insights)
        print("Done!")

    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()