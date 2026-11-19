import re
from .config import OPENAI_API_KEY, MOCK_LLM, MODEL

SYSTEM = (
    "You write pandas code. A DataFrame named `df` already exists; `pd` is imported. "
    "Return ONLY Python code, no markdown, no explanations. Do not import anything. "
    "Assign the final answer to a variable named `result` (a DataFrame, Series or scalar). "
    "Never touch files, network or the OS."
)


def _clean(code: str) -> str:
    code = re.sub(r"^```(?:python)?\s*|\s*```$", "", code.strip())
    return code.strip()


def _column_name(column):
    return re.sub(r"[^a-z0-9]+", " ", str(column).lower()).strip()


def _pick_column(columns, question, candidates, fallback=None):
    normalized = {column: _column_name(column) for column in columns}
    for column, name in normalized.items():
        if name and re.search(rf"\b{re.escape(name)}\b", question):
            return column
    for column, name in normalized.items():
        if any(word in name for word in candidates):
            return column
    return fallback


def suggest_questions(columns, dtypes, sample_values=None):
    numeric = [
        column for column, dtype in zip(columns, dtypes)
        if any(kind in dtype.lower() for kind in ("int", "float", "decimal"))
    ]
    categorical = [column for column in columns if column not in numeric]
    preferred_categories = ("category", "region", "product", "author", "owner", "user", "department")
    categorical = sorted(
        categorical,
        key=lambda column: (
            not any(word in _column_name(column) for word in preferred_categories),
            columns.index(column),
        ),
    )
    suggestions = ["How many rows are there?", "Show the columns in this file"]
    if numeric:
        metric = numeric[0]
        suggestions.extend([
            f"What is the total {metric}?",
            f"What is the average {metric}?",
            f"Which are the top 5 rows by {metric}?",
        ])
    elif columns:
        suggestions.append("Show the first 5 rows")
    if numeric and categorical:
        suggestions.append(f"Show total {numeric[0]} by {categorical[0]}")
    if sample_values:
        for column in categorical:
            values = sample_values.get(column, [])
            if values:
                suggestions.append(f"How many rows are done by {values[0]}?")
                break
    return suggestions[:7]


def _mock(columns, dtypes, question):
    q = _column_name(question)
    numeric = [
        column for column, dtype in zip(columns, dtypes)
        if any(kind in dtype.lower() for kind in ("int", "float", "decimal"))
    ]
    numeric_target = _pick_column(
        numeric,
        q,
        ("sales", "revenue", "amount", "price", "cost", "profit", "quantity", "total"),
        None,
    )
    if numeric_target is None and numeric and not any(
        word in q for word in ("sales", "revenue", "amount", "price", "cost", "profit", "quantity", "total")
    ):
        numeric_target = numeric[0]
    categories = [column for column in columns if column not in numeric]
    category_target = _pick_column(
        categories,
        q,
        ("category", "region", "product", "item", "name", "department", "date", "month"),
        categories[0] if categories else None,
    )
    quoted_numeric = repr(numeric_target)
    quoted_category = repr(category_target)

    author_match = re.search(
        r"\b(?:done|created|written|managed|owned|posted|made)\s+by\s+([a-z0-9][a-z0-9 _-]*)",
        q,
    )
    if author_match:
        value = repr(author_match.group(1).strip())
        return (
            "mask = df.astype(str).apply("
            f"lambda col: col.str.contains({value}, case=False, na=False)"
            ").any(axis=1)\n"
            "result = df.loc[mask]"
        )

    if "row count" in q or "how many rows" in q or "number of rows" in q:
        return "result = pd.DataFrame({'Rows': [len(df)]})"
    if "column" in q or "header" in q:
        return "result = pd.DataFrame({'Columns': list(df.columns)})"

    if any(word in q for word in ("average", "avg", "mean")):
        return f"result = pd.DataFrame({{'Average': [df[{quoted_numeric}].mean()]}})"
    if any(word in q for word in ("minimum", "minimum value", "lowest", "smallest", "min")):
        return f"result = pd.DataFrame({{'Minimum': [df[{quoted_numeric}].min()]}})"
    if any(word in q for word in ("maximum", "maximum value", "highest", "largest", "max")):
        return f"result = pd.DataFrame({{'Maximum': [df[{quoted_numeric}].max()]}})"

    top_match = re.search(r"\b(top|first|best)\s+(\d+)", q)
    bottom_match = re.search(r"\b(bottom|last|worst)\s+(\d+)", q)
    if top_match or bottom_match:
        match = top_match or bottom_match
        ascending = "False" if top_match else "True"
        if not numeric_target:
            return f"result = df.head({int(match.group(2))})"
        return (
            f"result = df.sort_values({quoted_numeric}, ascending={ascending})"
            f".head({int(match.group(2))})"
        )

    if not numeric_target:
        return "result = df.head(10)"

    group_words = ("by", "per", "each", "group")
    if category_target and any(word in q.split() for word in group_words):
        if any(word in q for word in ("average", "avg", "mean")):
            aggregate = "mean"
        elif any(word in q for word in ("count", "how many")):
            return f"result = df.groupby({quoted_category}).size().reset_index(name='Count')"
        else:
            aggregate = "sum"
        return (
            f"result = df.groupby({quoted_category})[{quoted_numeric}]"
            f".{aggregate}().reset_index()"
        )

    if any(word in q for word in ("total", "sum", "add up")):
        return f"result = pd.DataFrame({{'Total': [df[{quoted_numeric}].sum()]}})"
    return f"result = df.sort_values({quoted_numeric}, ascending=False).head(10)"


def generate_code(columns, dtypes, question: str) -> str:
    if MOCK_LLM or not OPENAI_API_KEY:
        if not MOCK_LLM:
            raise RuntimeError("OPENAI_API_KEY is not set on the server.")
        return _mock(columns, dtypes, question)
    from openai import OpenAI

    client = OpenAI(api_key=OPENAI_API_KEY)
    cols = ", ".join(f"{c} ({t})" for c, t in zip(columns, dtypes))
    resp = client.chat.completions.create(
        model=MODEL,
        temperature=0,
        messages=[
            {"role": "system", "content": SYSTEM},
            {"role": "user", "content": f"Columns: {cols}\nQuestion: {question}"},
        ],
    )
    return _clean(resp.choices[0].message.content)
