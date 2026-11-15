"""


Extrae los posteos publicados de Revista Anfibia desde el dump SQL de WordPress.

Procesa el volcado por streaming y conserva solo las tablas editoriales necesarias,
evitando tablas de usuarios, newsletters o seguridad con datos personales u operativos.


"""

from __future__ import annotations

import argparse
import html
import json
import re
from collections import Counter
from pathlib import Path
from typing import Iterable

import pandas as pd
from lxml import html as lxml_html

# DEFAULT_DUMP = Path("revistaanfibia_prod_database_2026-06-17.sql")
# DEFAULT_OUTPUT_DIR = Path("output")
# Rutas estándar del proyecto
BASE_DIR = Path(__file__).resolve().parent.parent
RAW_DATA_PATH = BASE_DIR / "data" / "raw"
PROCESSED_DATA_PATH = BASE_DIR / "data" / "processed"

DEFAULT_DUMP = RAW_DATA_PATH / "revistaanfibia_prod_database_2026-06-17.sql"
DEFAULT_OUTPUT_DIR = PROCESSED_DATA_PATH
DUMP_DATE = pd.Timestamp("2026-06-17")

CREATE_RE = re.compile(r"^CREATE TABLE `([^`]+)` \(")
COLUMN_RE = re.compile(r"^\s+`([^`]+)`\s+(.+?)(?:,)?$")
INSERT_RE = re.compile(r"^INSERT INTO `([^`]+)` VALUES\s*(.*)$")
SHORTCODE_RE = re.compile(r"\[(?:/?)[A-Za-z][^\]]*\]")
GUTENBERG_COMMENT_RE = re.compile(r"<!--\s*/?wp:[^>]*-->")
HTML_TAG_RE = re.compile(
    r"</?(?:a|abbr|article|aside|blockquote|br|caption|cite|code|div|em|figcaption|figure|footer|h[1-6]|header|hr|iframe|img|li|main|ol|p|pre|section|span|strong|table|tbody|td|th|thead|tr|ul)\b[^>]*>",
    re.IGNORECASE,
)
EMAIL_RE = re.compile(r"[\w.+-]+@[\w.-]+\.\w+")
MYSQL_ESCAPES = {"0": "\0", "b": "\b", "n": "\n", "r": "\r", "t": "\t", "Z": "\x1a"}

WANTED_TABLES = {
    "wp_posts",
    "wp_postmeta",
    "wp_terms",
    "wp_term_taxonomy",
    "wp_term_relationships",
}

META_KEYS = {
    "wpcf-copete": "copete",
    "wpcf-tagline": "tagline",
    "autor_ids": "autor_ids_raw",
    "_autor_ids": "autor_ids_field",
    "illustrator_ids": "illustrator_ids_raw",
    "_illustrator_ids": "illustrator_ids_field",
    "_thumbnail_id": "thumbnail_id",
    "_yoast_wpseo_metadesc": "yoast_metadesc",
    "_yoast_wpseo_focuskw": "yoast_focuskw",
    "_yoast_wpseo_estimated-reading-time-minutes": "yoast_reading_time_minutes",
}

CURATED_COLUMNS = [
    "title_text",
    "body_text",
    "copete",
    "tagline",
    "autor_names",
    "post_date",
    "category",
    "text_type",
]


def iter_insert_payloads(
    path: Path, wanted: set[str] | None = None
) -> Iterable[tuple[str, str]]:
    """Yield (table, VALUES payload) without loading the dump into memory."""
    table: str | bool | None = None
    parts: list[str] = []
    with path.open(encoding="utf-8", errors="replace") as handle:
        for line in handle:
            if table is None:
                match = INSERT_RE.match(line)
                if not match:
                    continue
                candidate, first = match.groups()
                if wanted is not None and candidate not in wanted:
                    table = False
                else:
                    table = candidate
                    parts = [first]
            elif table is not False:
                parts.append(line)

            if table is not None and line.rstrip().endswith(";"):
                if table is not False:
                    payload = "".join(parts).rstrip()
                    yield str(table), payload[:-1] if payload.endswith(";") else payload
                table, parts = None, []


def parse_values(payload: str) -> list[list[str | None]]:
    """Parse one MariaDB VALUES payload into Python rows."""
    rows: list[list[str | None]] = []
    row: list[str | None] = []
    token: list[str] = []
    quoted = escaped = field_was_quoted = False
    depth = 0

    def finish_field() -> None:
        nonlocal field_was_quoted
        raw = "".join(token)
        row.append(None if not field_was_quoted and raw.upper() == "NULL" else raw)
        token.clear()
        field_was_quoted = False

    for char in payload:
        if escaped:
            token.append(MYSQL_ESCAPES.get(char, char))
            escaped = False
        elif quoted and char == "\\":
            escaped = True
        elif char == "'":
            quoted = not quoted
            field_was_quoted = True
        elif not quoted and char == "(" and depth == 0:
            depth = 1
            row, token = [], []
        elif not quoted and depth == 1 and char == ",":
            finish_field()
        elif not quoted and char == ")" and depth == 1:
            finish_field()
            rows.append(row)
            depth = 0
        elif depth:
            token.append(char)
    return rows


def extract_schemas(path: Path) -> dict[str, list[str]]:
    schemas: dict[str, list[str]] = {}
    current: str | None = None
    with path.open(encoding="utf-8", errors="replace") as handle:
        for line in handle:
            match = CREATE_RE.match(line)
            if match:
                current = match.group(1)
                schemas[current] = []
            elif current and line.startswith(") ENGINE="):
                current = None
            elif current:
                match = COLUMN_RE.match(line)
                if match:
                    schemas[current].append(match.group(1))
    return schemas


def clean_wordpress_text(value: object) -> str:
    """Convert stored WordPress HTML/blocks/shortcodes to compact visible text."""
    if value is None or pd.isna(value):
        return ""
    text = html.unescape(str(value))
    text = GUTENBERG_COMMENT_RE.sub(" ", text)
    text = SHORTCODE_RE.sub(" ", text)
    if "<" in text and ">" in text:
        try:
            fragment = lxml_html.fromstring(f"<div>{text}</div>")
            text = fragment.text_content()
        except Exception:
            text = re.sub(r"<[^>]+>", " ", text)
    text = SHORTCODE_RE.sub(" ", html.unescape(text))
    return re.sub(r"\s+", " ", text).strip()


def redact_emails(value: object) -> object:
    if value is None or pd.isna(value):
        return value
    return EMAIL_RE.sub("[EMAIL_REDACTED]", str(value))


def normalize_plain_text(value: object) -> str:
    if value is None or pd.isna(value):
        return ""
    text = html.unescape(str(value))
    text = EMAIL_RE.sub("[EMAIL_REDACTED]", text)
    return re.sub(r"\s+", " ", text).strip()


def parse_php_id_list(value: object) -> list[int]:
    """Extract numeric IDs from the simple PHP serialized arrays used by ACF."""
    if value is None or pd.isna(value):
        return []
    value = str(value)
    if not value or value.startswith("field_"):
        return []
    ids = [int(match) for match in re.findall(r's:\d+:"(\d+)";', value)]
    if ids:
        return ids
    if value.isdigit():
        return [int(value)]
    return []


def make_site_url(row: pd.Series) -> str:
    slug = str(row.get("post_name") or "").strip("/")
    guid = str(row.get("guid") or "")
    if slug:
        return f"https://www.revistaanfibia.com/{slug}/"
    return guid.replace(
        "http://stage.revistaanfibia.com", "https://www.revistaanfibia.com"
    )


def load_tables(
    dump_path: Path,
) -> tuple[dict[str, list[str]], dict[str, pd.DataFrame]]:
    schemas = extract_schemas(dump_path)
    collected = {table: [] for table in WANTED_TABLES}
    for table, payload in iter_insert_payloads(dump_path, WANTED_TABLES):
        collected[table].extend(parse_values(payload))
    frames = {
        table: pd.DataFrame(rows, columns=schemas[table])
        for table, rows in collected.items()
    }
    return schemas, frames


def prepare_posts(posts: pd.DataFrame) -> pd.DataFrame:
    posts = posts.copy()
    for column in ["ID", "post_author", "post_parent", "comment_count"]:
        posts[column] = pd.to_numeric(posts[column], errors="coerce").astype("Int64")
    for column in ["post_date", "post_date_gmt", "post_modified", "post_modified_gmt"]:
        posts[column] = pd.to_datetime(posts[column], errors="coerce")
    return posts


def build_taxonomy_lists(frames: dict[str, pd.DataFrame]) -> pd.DataFrame:
    terms = frames["wp_terms"][["term_id", "name", "slug"]].copy()
    tax = frames["wp_term_taxonomy"][["term_taxonomy_id", "term_id", "taxonomy"]].copy()
    rel = frames["wp_term_relationships"][["object_id", "term_taxonomy_id"]].copy()
    for frame, columns in [
        (terms, ["term_id"]),
        (tax, ["term_taxonomy_id", "term_id"]),
        (rel, ["object_id", "term_taxonomy_id"]),
    ]:
        for column in columns:
            frame[column] = pd.to_numeric(frame[column], errors="coerce").astype(
                "Int64"
            )

    post_terms = rel.merge(tax, on="term_taxonomy_id", how="left").merge(
        terms, on="term_id", how="left"
    )
    term_lists = (
        post_terms.dropna(subset=["taxonomy", "name"])
        .groupby(["object_id", "taxonomy"])["name"]
        .agg(
            lambda values: sorted(
                set(str(value) for value in values if str(value).strip())
            )
        )
        .unstack(fill_value=[])
    )
    return term_lists


def build_meta_wide(postmeta: pd.DataFrame) -> pd.DataFrame:
    postmeta = postmeta.copy()
    postmeta["post_id"] = pd.to_numeric(postmeta["post_id"], errors="coerce").astype(
        "Int64"
    )
    selected = postmeta[postmeta["meta_key"].isin(META_KEYS)].copy()
    selected["field"] = selected["meta_key"].map(META_KEYS)
    selected = selected.drop_duplicates(["post_id", "field"], keep="last")
    wide = selected.pivot(index="post_id", columns="field", values="meta_value")
    return wide


def build_author_lookup(posts: pd.DataFrame) -> dict[int, str]:
    authors = posts[
        (posts["post_type"].eq("autor")) & (posts["post_status"].eq("publish"))
    ].copy()
    return {
        int(row.ID): clean_wordpress_text(row.post_title)
        for row in authors.itertuples(index=False)
        if pd.notna(row.ID) and clean_wordpress_text(row.post_title)
    }


def join_name_list(ids: list[int], lookup: dict[int, str]) -> str:
    names = [lookup[item] for item in ids if item in lookup]
    return "; ".join(dict.fromkeys(names))


def add_temporal_fields(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["post_date_calendar"] = df["post_date"].dt.date.astype("string")
    df["post_year"] = df["post_date"].dt.year.astype("Int64")
    df["post_month"] = df["post_date"].dt.month.astype("Int64")
    df["post_year_month"] = df["post_date"].dt.to_period("M").astype("string")
    df["post_quarter"] = df["post_date"].dt.quarter.astype("Int64")
    df["post_year_quarter"] = df["post_date"].dt.to_period("Q").astype("string")
    df["post_weekday"] = df["post_date"].dt.day_name()
    df["days_to_modified"] = (
        df["post_modified"] - df["post_date"]
    ).dt.total_seconds() / 86400
    return df


def build_dataset(
    frames: dict[str, pd.DataFrame],
) -> tuple[pd.DataFrame, dict[str, object]]:
    posts = prepare_posts(frames["wp_posts"])
    term_lists = build_taxonomy_lists(frames)
    meta_wide = build_meta_wide(frames["wp_postmeta"])
    author_lookup = build_author_lookup(posts)

    type_status_counts = (
        posts.groupby(["post_type", "post_status"], dropna=False)
        .size()
        .rename("rows")
        .reset_index()
        .sort_values("rows", ascending=False)
    )
    published_type_counts = posts[posts["post_status"].eq("publish")][
        "post_type"
    ].value_counts()

    dataset = posts[
        (posts["post_type"].eq("post")) & (posts["post_status"].eq("publish"))
    ].copy()
    dataset["source_url"] = dataset.apply(make_site_url, axis=1)
    dataset["post_title"] = dataset["post_title"].map(redact_emails)
    dataset["post_excerpt"] = dataset["post_excerpt"].map(redact_emails)
    dataset["post_content"] = dataset["post_content"].map(redact_emails)
    dataset["title_text"] = dataset["post_title"].map(clean_wordpress_text)
    dataset["body_text"] = dataset["post_content"].map(clean_wordpress_text)
    dataset["excerpt_text"] = dataset["post_excerpt"].map(clean_wordpress_text)
    dataset["document_text"] = (
        dataset["title_text"] + ". " + dataset["body_text"]
    ).str.strip(" .")
    dataset["word_count"] = (
        dataset["document_text"].str.findall(r"(?u)\b\w+\b").str.len().astype("Int64")
    )
    dataset = add_temporal_fields(dataset)

    dataset = dataset.merge(term_lists, left_on="ID", right_index=True, how="left")
    taxonomy_columns = [
        column for column in term_lists.columns if column in dataset.columns
    ]
    for column in taxonomy_columns:
        dataset[column] = dataset[column].map(
            lambda value: value if isinstance(value, list) else []
        )

    dataset = dataset.merge(meta_wide, left_on="ID", right_index=True, how="left")
    for column in ["copete", "tagline", "yoast_metadesc"]:
        if column in dataset:
            dataset[column] = (
                dataset[column].map(redact_emails).map(clean_wordpress_text)
            )
    for column in ["yoast_focuskw"]:
        if column in dataset:
            dataset[column] = dataset[column].map(redact_emails)

    for source, target in [
        ("autor_ids_raw", "autor_ids"),
        ("illustrator_ids_raw", "illustrator_ids"),
    ]:
        if source in dataset:
            dataset[target] = dataset[source].map(parse_php_id_list)
        else:
            dataset[target] = [[] for _ in range(len(dataset))]
    dataset["autor_names"] = dataset["autor_ids"].map(
        lambda ids: join_name_list(ids, author_lookup)
    )
    dataset["illustrator_names"] = dataset["illustrator_ids"].map(
        lambda ids: join_name_list(ids, author_lookup)
    )
    dataset["autor_id_list"] = dataset["autor_ids"].map(
        lambda values: ";".join(str(value) for value in values)
    )
    dataset["illustrator_id_list"] = dataset["illustrator_ids"].map(
        lambda values: ";".join(str(value) for value in values)
    )

    if "yoast_reading_time_minutes" in dataset:
        dataset["yoast_reading_time_minutes"] = pd.to_numeric(
            dataset["yoast_reading_time_minutes"], errors="coerce"
        ).astype("Int64")
    if "thumbnail_id" in dataset:
        dataset["thumbnail_id"] = pd.to_numeric(
            dataset["thumbnail_id"], errors="coerce"
        ).astype("Int64")

    ordered_base = [
        "ID",
        "source_url",
        "guid",
        "post_name",
        "post_title",
        "title_text",
        "post_status",
        "post_type",
        "post_author",
        "post_date",
        "post_date_gmt",
        "post_modified",
        "post_modified_gmt",
        "post_date_calendar",
        "post_year",
        "post_month",
        "post_year_month",
        "post_quarter",
        "post_year_quarter",
        "post_weekday",
        "days_to_modified",
        "comment_count",
        "post_excerpt",
        "excerpt_text",
        "post_content",
        "body_text",
        "document_text",
        "word_count",
        "copete",
        "tagline",
        "autor_ids",
        "autor_id_list",
        "autor_names",
        "illustrator_ids",
        "illustrator_id_list",
        "illustrator_names",
        "thumbnail_id",
        "yoast_metadesc",
        "yoast_focuskw",
        "yoast_reading_time_minutes",
    ]
    ordered = [column for column in ordered_base if column in dataset.columns]
    ordered += sorted(column for column in taxonomy_columns if column not in ordered)
    ordered += sorted(column for column in dataset.columns if column not in ordered)
    dataset = dataset[ordered].sort_values(["post_date", "ID"]).reset_index(drop=True)

    adjunct = posts[
        posts["post_status"].eq("publish")
        & posts["post_type"].isin(["especial", "web-story"])
    ].copy()
    adjunct["title_text"] = adjunct["post_title"].map(clean_wordpress_text)
    adjunct["body_text"] = adjunct["post_content"].map(clean_wordpress_text)
    adjunct["word_count"] = (
        (adjunct["title_text"] + ". " + adjunct["body_text"])
        .str.findall(r"(?u)\b\w+\b")
        .str.len()
    )

    diagnostics = {
        "rows": int(len(dataset)),
        "type_status_counts": type_status_counts.head(60).to_dict(orient="records"),
        "published_type_counts": published_type_counts.to_dict(),
        "taxonomy_columns": taxonomy_columns,
        "adjunct_counts": adjunct["post_type"].value_counts().to_dict(),
        "adjunct_word_stats": adjunct.groupby("post_type")["word_count"]
        .agg(["count", "median", "mean", "max"])
        .round(2)
        .to_dict(orient="index"),
    }
    return dataset, diagnostics


def run_checks(dataset: pd.DataFrame) -> dict[str, int]:
    privacy_text_columns = [
        column
        for column in [
            "source_url",
            "guid",
            "post_title",
            "title_text",
            "post_excerpt",
            "excerpt_text",
            "post_content",
            "body_text",
            "document_text",
            "copete",
            "tagline",
            "autor_names",
            "illustrator_names",
            "yoast_metadesc",
            "yoast_focuskw",
        ]
        if column in dataset.columns
    ]
    email_like_rows = int(
        dataset[privacy_text_columns]
        .fillna("")
        .astype(str)
        .apply(lambda row: bool(EMAIL_RE.search(" ".join(row))), axis=1)
        .sum()
    )
    checks = {
        "non_publish_rows": int(dataset["post_status"].ne("publish").sum()),
        "non_post_rows": int(dataset["post_type"].ne("post").sum()),
        "duplicate_ids": int(dataset["ID"].duplicated().sum()),
        "exact_duplicate_document_text_rows": int(
            dataset["document_text"].duplicated().sum()
        ),
        "empty_titles": int(dataset["title_text"].eq("").sum()),
        "missing_dates": int(dataset["post_date"].isna().sum()),
        "dates_after_dump_date": int((dataset["post_date"] > DUMP_DATE).sum()),
        "temporal_year_mismatches": int(
            (dataset["post_year"] != dataset["post_date"].dt.year).fillna(False).sum()
        ),
        "html_like_body_text_rows": int(
            dataset["body_text"].str.contains(HTML_TAG_RE, regex=True, na=False).sum()
        ),
        "email_like_rows": email_like_rows,
    }
    return checks


def write_outputs(
    dataset: pd.DataFrame, diagnostics: dict[str, object], output_dir: Path
) -> dict[str, object]:
    output_dir.mkdir(parents=True, exist_ok=True)
    csv_path = output_dir / "posteos_anfibia.csv"
    curated_csv_path = output_dir / "posteos_anfibia_minimo_curado.csv"
    parquet_path = output_dir / "posteos_anfibia.parquet"
    diagnostics_path = output_dir / "posteos_anfibia_diagnostics.json"

    csv_dataset = dataset.copy()
    for column in csv_dataset.columns:
        if csv_dataset[column].map(lambda value: isinstance(value, list)).any():
            csv_dataset[column] = csv_dataset[column].map(
                lambda value: (
                    "; ".join(map(str, value)) if isinstance(value, list) else value
                )
            )
    csv_dataset.to_csv(csv_path, index=False, encoding="utf-8-sig")

    curated_dataset = csv_dataset[CURATED_COLUMNS].copy()
    for column in [
        "title_text",
        "body_text",
        "copete",
        "tagline",
        "autor_names",
        "category",
        "text_type",
    ]:
        curated_dataset[column] = curated_dataset[column].map(normalize_plain_text)
    curated_dataset["post_date"] = pd.to_datetime(
        curated_dataset["post_date"], errors="coerce"
    ).dt.strftime("%Y-%m-%d %H:%M:%S")
    curated_dataset.to_csv(curated_csv_path, index=False, encoding="utf-8-sig")

    parquet_status: dict[str, object]
    try:
        dataset.to_parquet(parquet_path, index=False)
        parquet_status = {"written": True, "path": str(parquet_path)}
    except Exception as exc:
        parquet_status = {
            "written": False,
            "path": str(parquet_path),
            "reason": f"{type(exc).__name__}: {exc}",
        }

    diagnostics = dict(diagnostics)
    diagnostics["checks"] = run_checks(dataset)
    diagnostics["curated_minimal"] = {
        "rows": int(len(curated_dataset)),
        "columns": CURATED_COLUMNS,
        "missing_or_empty": {
            column: int(
                curated_dataset[column].fillna("").astype(str).str.strip().eq("").sum()
            )
            for column in CURATED_COLUMNS
        },
    }
    diagnostics["exports"] = {
        "csv": str(csv_path),
        "curated_minimal_csv": str(curated_csv_path),
        "parquet": parquet_status,
        "diagnostics": str(diagnostics_path),
    }
    diagnostics_path.write_text(
        json.dumps(diagnostics, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return diagnostics


def print_summary(diagnostics: dict[str, object]) -> None:
    print(f"Rows exported: {diagnostics['rows']:,}")
    print("Checks:")
    for key, value in diagnostics["checks"].items():
        print(f"  {key}: {value}")
    print("Exports:")
    print(f"  csv: {diagnostics['exports']['csv']}")
    print(f"  curated minimal csv: {diagnostics['exports']['curated_minimal_csv']}")
    parquet = diagnostics["exports"]["parquet"]
    if parquet["written"]:
        print(f"  parquet: {parquet['path']}")
    else:
        print(f"  parquet: not written ({parquet['reason']})")
    print(f"  diagnostics: {diagnostics['exports']['diagnostics']}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--dump",
        type=Path,
        default=DEFAULT_DUMP,
        help="Path to the WordPress SQL dump.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help="Directory for extracted outputs.",
    )
    args = parser.parse_args()

    if not args.dump.exists():
        raise FileNotFoundError(f"SQL dump not found: {args.dump}")

    _, frames = load_tables(args.dump)
    dataset, diagnostics = build_dataset(frames)
    diagnostics = write_outputs(dataset, diagnostics, args.output_dir)
    print_summary(diagnostics)

    hard_failures = {
        key: value
        for key, value in diagnostics["checks"].items()
        if key
        in {
            "non_publish_rows",
            "non_post_rows",
            "duplicate_ids",
            "dates_after_dump_date",
            "temporal_year_mismatches",
            "html_like_body_text_rows",
            "email_like_rows",
        }
        and value
    }
    if hard_failures:
        raise SystemExit(f"Extraction checks failed: {hard_failures}")


if __name__ == "__main__":
    main()
