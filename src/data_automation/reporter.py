
from pathlib import Path

import pandas as pd

from data_automation.exporter import validate_output_path


def generate_summary(
    original_df: pd.DataFrame,
    cleaned_df: pd.DataFrame,
    validation_report: dict,
) -> pd.DataFrame:
    """
    Generate a high-level summary of the cleaning process.

    The number of removed rows is calculated by comparing
    the original and cleaned datasets.
    """
    original_rows = len(original_df)
    cleaned_rows = len(cleaned_df)

    removed_rows = max(original_rows - cleaned_rows, 0)

    summary = {
        "Metric": [
            "Original rows",
            "Cleaned rows",
            "Removed rows",
            "Original columns",
            "Cleaned columns",
            "Detected issues",
        ],
        "Value": [
            original_rows,
            cleaned_rows,
            removed_rows,
            len(original_df.columns),
            len(cleaned_df.columns),
            validation_report["summary"]["total_issues"],
        ],
    }

    return pd.DataFrame(summary)


def generate_quality_details(validation_report: dict) -> pd.DataFrame:
    """
    Convert validation issues into a tabular format.

    Each issue becomes one row in the resulting DataFrame.
    """
    issues = validation_report.get("issues", [])

    columns = [
        "Issue type",
        "Column",
        "Count",
        "Affected rows",
    ]

    if not issues:
        return pd.DataFrame(columns=columns)

    records = []

    for issue in issues:
        row_numbers = issue.get("row_numbers", [])

        records.append({
            "Issue type": issue["type"],
            "Column": issue.get("column", "N/A"),
            "Count": issue["count"],
            "Affected rows": ", ".join(
                str(number) for number in row_numbers
            ) if row_numbers else "N/A",
        })

    return pd.DataFrame(records, columns=columns)


def generate_column_statistics(
    df: pd.DataFrame,
) -> pd.DataFrame:
    """
    Generate statistics for each column.

    Completeness represents the percentage of non-missing values.
    """
    total_rows = len(df)
    statistics = []

    for column in df.columns:
        missing_count = int(df[column].isna().sum())

        if total_rows > 0:
            completeness = (
                (total_rows - missing_count) / total_rows
            ) * 100
        else:
            completeness = 0.0

        statistics.append({
            "Column": str(column),
            "Data type": str(df[column].dtype),
            "Total values": total_rows,
            "Missing values": missing_count,
            "Unique values": int(df[column].nunique(dropna=True)),
            "Completeness (%)": round(completeness, 2),
        })

    return pd.DataFrame(
        statistics,
        columns=[
            "Column",
            "Data type",
            "Total values",
            "Missing values",
            "Unique values",
            "Completeness (%)",
        ],
    )


def build_report(
    original_df: pd.DataFrame,
    cleaned_df: pd.DataFrame,
    validation_report: dict,
) -> dict[str, pd.DataFrame]:
    """
    Build all quality report sections.

    Returns a dictionary where keys represent Excel sheet names
    and values are DataFrames.
    """
    if not isinstance(original_df, pd.DataFrame):
        raise TypeError("original_df must be a pandas DataFrame.")

    if not isinstance(cleaned_df, pd.DataFrame):
        raise TypeError("cleaned_df must be a pandas DataFrame.")

    if not isinstance(validation_report, dict):
        raise TypeError("validation_report must be a dictionary.")

    if not isinstance(validation_report.get("summary"), dict):
        raise ValueError("Validation report must contain a summary.")

    if not isinstance(validation_report.get("issues"), list):
        raise ValueError("Validation report must contain an issues list.")

    required_summary_fields = {
        "total_rows",
        "total_columns",
        "total_issues",
    }

    if not required_summary_fields.issubset(
        validation_report["summary"]
    ):
        raise ValueError("Validation report summary is incomplete.")

    report = {
        "Summary": generate_summary(
            original_df,
            cleaned_df,
            validation_report,
        ),
        "Data Quality": generate_quality_details(
            validation_report,
        ),
        "Column Statistics": generate_column_statistics(
            cleaned_df,
        ),
    }

    return report


def export_quality_report(
    report: dict[str, pd.DataFrame],
    file_path: str | Path,
    overwrite: bool = False,
) -> Path:
    """
    Export the quality report into a multi-sheet Excel workbook.

    Args:
        report: Dictionary of sheet names and DataFrames.
        file_path: Destination Excel file.
        overwrite: Whether an existing file can be replaced.

    Returns:
        Path to the generated Excel report.
    """
    if not isinstance(report, dict):
        raise TypeError("report must be a dictionary.")

    if not report:
        raise ValueError("Report cannot be empty.")

    for sheet_name, dataframe in report.items():
        if not isinstance(sheet_name, str) or not sheet_name.strip():
            raise ValueError("Sheet names must be non-empty strings.")

        if len(sheet_name) > 31:
            raise ValueError(
                f"Sheet name '{sheet_name}' exceeds 31 characters."
            )

        if any(character in sheet_name for character in r"[]:*?/\\"):
            raise ValueError(
                f"Invalid character in sheet name: {sheet_name}"
            )

        if not isinstance(dataframe, pd.DataFrame):
            raise TypeError(
                f"Sheet '{sheet_name}' must contain a DataFrame."
            )

    path = Path(file_path)

    if path.suffix.lower() != ".xlsx":
        raise ValueError("Quality reports must use the .xlsx format.")

    path = validate_output_path(path, overwrite=overwrite)

    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        for sheet_name, dataframe in report.items():
            dataframe.to_excel(
                writer,
                sheet_name=sheet_name,
                index=False,
            )

    return path
