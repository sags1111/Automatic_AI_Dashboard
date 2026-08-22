import json
import sqlite3
import pandas as pd
import plotly.express as px
import streamlit as st
import ollama
import os
import tempfile


st.set_page_config(
    page_title="AI Database Intelligence",
    page_icon="🧠",
    layout="wide"
)

def get_schema(conn):
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [row[0] for row in cursor.fetchall()]
    schema = {}
    for table in tables:
        cursor.execute(f"PRAGMA table_info({table});")
        columns = [{"name": row[1], "type": row[2]} for row in cursor.fetchall()]
        schema[table] = columns
    return schema

def analyze_data(conn, schema):
    analysis = {}
    for table in schema.keys():
        try:
            df = pd.read_sql_query(f"SELECT * FROM {table}", conn)
            analysis[table] = {
                "total_rows": len(df),
                "columns": list(df.columns),
                "sample": df.head(3).to_dict(orient="records"),
                "numeric_stats": {}
            }
            for col in df.select_dtypes(include=["number"]).columns:
                analysis[table]["numeric_stats"][col] = {
                    "min": round(float(df[col].min()), 2),
                    "max": round(float(df[col].max()), 2),
                    "avg": round(float(df[col].mean()), 2)
                }
        except:
            pass
    return analysis

def extract_json(text):
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
        return None
    try:
        return json.loads(text[start:end])
    except:
        return None

def ask_ollama_json(prompt):
    try:
        response = ollama.chat(
            model="llama3.2",
            messages=[{"role": "user", "content": prompt}],
            options={"temperature": 0}
        )
        return extract_json(response["message"]["content"])
    except Exception as e:
        st.error(f"Ollama error: {e}")
        return None

def ask_ollama_text(messages):
    try:
        response = ollama.chat(
            model="llama3.2",
            messages=messages,
            options={"temperature": 0.3}
        )
        return response["message"]["content"]
    except Exception as e:
        return f"Error: {e}"


st.title("🧠 AI Database Intelligence Platform")
st.markdown("Upload any SQLite database and get instant AI-powered insights and charts.")
st.divider()

uploaded_file = st.file_uploader(
    "📂 Upload your database file",
    type=["sqlite", "db", "sqlite3"],
    help="Upload any SQLite database file"
)


if uploaded_file:
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".sqlite")
    tmp.write(uploaded_file.read())
    tmp.close()
    db_path = tmp.name
    st.success(f"✅ Loaded: {uploaded_file.name}")
elif os.path.exists("Chinook_Sqlite.sqlite"):
    db_path = "Chinook_Sqlite.sqlite"
    st.info("Using default Chinook database. Upload your own above!")
else:
    st.warning("Please upload a SQLite database file to get started.")
    st.stop()


conn = sqlite3.connect(db_path)
schema = get_schema(conn)
analysis = analyze_data(conn, schema)

if not schema:
    st.error("No tables found in this database!")
    st.stop()


cache_key = f"understanding_{uploaded_file.name if uploaded_file else 'chinook'}"

if cache_key not in st.session_state:
    with st.spinner("🤖 AI is analyzing your database..."):
        simplified = {t: [c["name"] for c in cols] for t, cols in schema.items()}
        prompt = f"""Analyze this database schema and return ONLY raw JSON. No markdown. No backticks.

{{
  "business_type": "type of business",
  "business_description": "2 sentence description",
  "tables": {{
    "TableName": {{"purpose": "what it stores", "important_columns": ["col1", "col2"]}}
  }},
  "relationships": "how tables connect",
  "potential_insights": ["insight 1", "insight 2", "insight 3", "insight 4", "insight 5"]
}}

Schema: {json.dumps(simplified)}

JSON only:"""
        result = ask_ollama_json(prompt)
        st.session_state[cache_key] = result or {
            "business_type": "Unknown",
            "business_description": "Database loaded successfully.",
            "tables": {},
            "relationships": "",
            "potential_insights": []
        }

understanding = st.session_state[cache_key]


st.subheader(f"📌 {understanding.get('business_type', 'Database')}")
st.markdown(f"_{understanding.get('business_description', '')}_")
st.divider()

st.subheader("📊 Key Metrics")
total_rows = sum(t.get("total_rows", 0) for t in analysis.values())
cols = st.columns(len(schema) if len(schema) <= 4 else 4)
for i, (table, data) in enumerate(list(analysis.items())[:4]):
    cols[i].metric(table, f"{data['total_rows']:,} rows")
st.divider()


st.subheader("📈 Auto-Generated Charts")

charts_drawn = 0
table_list = list(schema.keys())

for table in table_list:
    if charts_drawn >= 6:
        break
    try:
        df = pd.read_sql_query(f"SELECT * FROM {table} LIMIT 500", conn)
        numeric_cols = df.select_dtypes(include=["number"]).columns.tolist()
        text_cols = df.select_dtypes(include=["object"]).columns.tolist()

        if len(numeric_cols) >= 1 and len(text_cols) >= 1:
            col1, col2 = st.columns(2)
            with col1:
                fig = px.bar(
                    df.groupby(text_cols[0])[numeric_cols[0]].sum().reset_index().head(10),
                    x=text_cols[0], y=numeric_cols[0],
                    title=f"{table}: {text_cols[0]} vs {numeric_cols[0]}"
                )
                fig.update_layout(xaxis_tickangle=-35)
                st.plotly_chart(fig, use_container_width=True)
                charts_drawn += 1
            with col2:
                fig2 = px.pie(
                    df.groupby(text_cols[0])[numeric_cols[0]].sum().reset_index().head(8),
                    names=text_cols[0], values=numeric_cols[0],
                    title=f"{table}: Distribution"
                )
                st.plotly_chart(fig2, use_container_width=True)
                charts_drawn += 1
    except:
        pass

st.divider()

st.subheader("🔍 Explore Tables")
selected_table = st.selectbox("Select a table:", table_list)
if selected_table:
    df = pd.read_sql_query(f"SELECT * FROM {selected_table} LIMIT 50", conn)
    st.markdown(f"Showing first 50 rows of **{selected_table}** ({analysis[selected_table]['total_rows']:,} total rows)")
    st.dataframe(df, use_container_width=True)

st.divider()

st.subheader("💬 Ask AI About Your Database")
st.markdown("Type any question in plain English — AI will answer it!")


if "messages" not in st.session_state:
    st.session_state.messages = []


for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])


if question := st.chat_input("Ask anything... e.g. 'Which artist sold the most?'"):

    
    st.session_state.messages.append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.markdown(question)

    
    schema_text = json.dumps(
        {t: [c["name"] for c in cols] for t, cols in schema.items()},
        indent=2
    )

    # Build messages for AI
    system_prompt = f"""You are a data analyst. The user has a database with this schema:
{schema_text}

When the user asks a question:
1. Write a SQLite SELECT query to answer it
2. Wrap the SQL in <sql> tags like this: <sql>SELECT ...</sql>
3. Then explain what you found in simple words

Always use valid SQLite syntax. Only use SELECT queries."""

    ai_messages = [{"role": "user", "content": system_prompt + "\n\nQuestion: " + question}]

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            ai_reply = ask_ollama_text(ai_messages)

        # Extract and run SQL if present
        if "<sql>" in ai_reply and "</sql>" in ai_reply:
            sql = ai_reply.split("<sql>")[1].split("</sql>")[0].strip()
            explanation = ai_reply.replace(f"<sql>{sql}</sql>", "").strip()

            try:
                result_df = pd.read_sql_query(sql, conn)
                st.markdown(explanation if explanation else "Here are the results:")
                st.dataframe(result_df, use_container_width=True)

                # Auto chart if results are chartable
                if len(result_df) > 1 and len(result_df.columns) >= 2:
                    num_cols = result_df.select_dtypes(include=["number"]).columns.tolist()
                    txt_cols = result_df.select_dtypes(include=["object"]).columns.tolist()
                    if num_cols and txt_cols:
                        fig = px.bar(result_df.head(15),
                                     x=txt_cols[0], y=num_cols[0],
                                     title="Query Result")
                        fig.update_layout(xaxis_tickangle=-35)
                        st.plotly_chart(fig, use_container_width=True)

                full_reply = explanation + f"\n\n```sql\n{sql}\n```"
            except Exception as e:
                st.markdown(ai_reply)
                st.warning(f"Could not run SQL: {e}")
                full_reply = ai_reply
        else:
            st.markdown(ai_reply)
            full_reply = ai_reply

    st.session_state.messages.append({"role": "assistant", "content": full_reply})

conn.close()