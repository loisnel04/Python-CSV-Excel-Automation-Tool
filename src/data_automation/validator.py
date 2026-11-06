import re
import pandas as pd


EMAIL_PATTERN = re.compile(
    r"^[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]+"
    r"@[A-Za-z0-9](?:[A-Za-z0-9-]*[A-Za-z0-9])?"
    r"(?:\.[A-Za-z0-9](?:[A-Za-z0-9-]*[A-Za-z0-9])?)+$"
)


def _make_issue(
    issue_type: str,
    count: int,
    column: str | None = None,
    row_numbers: list[int] | None = None,
) -> dict:
    """Create a consistent quality issue entry."""
    issue = {
        "type": issue_type,
        "count": count,
    }

    if column is not None:
        issue["column"] = column

    if row_numbers is not None:
        issue["row_numbers"] = row_numbers

    return issue


def check_empty_dataset(df: pd.DataFrame) -> list[dict]:
    """Check whether the dataset contains any records or columns."""
    if len(df.columns) == 0:
        return [_make_issue("no_columns", 1)]

    if len(df.index) == 0:
        return [_make_issue("empty_dataset", 1)]

    return []


def check_missing_values(df: pd.DataFrame) -> list[dict]:
    """Report missing values in each column."""
    issues = []

    for column in df.columns:
        missing_mask = df[column].isna()
        count = int(missing_mask.sum())

        if count > 0:
            row_numbers = (
                missing_mask[missing_mask]
                .index.to_list()
            )

            issues.append(
                _make_issue(
                    "missing_values",
                    count,
                    column=str(column),
                    row_numbers=[
                        df.index.get_loc(index) + 1
                        for index in row_numbers
                    ],
                )
            )

    return issues


def check_empty_columns(df: pd.DataFrame) -> list[dict]:
    """Report columns containing no non-missing values."""
    issues = []

    for column in df.columns:
        if df[column].isna().all():
            issues.append(
                _make_issue(
                    "empty_column",
                    1,
                    column=str(column),
                )
            )

    return issues


def check_invalid_emails(
    df: pd.DataFrame,
    email_columns: list[str],
) -> list[dict]:
    """Report email addresses that do not match the basic email pattern."""
    issues = []

    for column in email_columns:
        if column not in df.columns:
            raise ValueError(
                f"Email column '{column}' does not exist in the dataset."
            )

        values = df[column]

        invalid_mask = values.notna() & ~values.map(
            lambda value: (
                bool(EMAIL_PATTERN.fullmatch(str(value).strip()))
                if isinstance(value, str)
                else False
            )
        )

        count = int(invalid_mask.sum())

        if count > 0:
            row_numbers = [
                position + 1
                for position, is_invalid in enumerate(invalid_mask)
                if is_invalid
            ]

            issues.append(
                _make_issue(
                    "invalid_emails",
                    count,
                    column=column,
                    row_numbers=row_numbers,
                )
            )

    return issues


def check_duplicates(df: pd.DataFrame) -> list[dict]:
    """Report all rows participating in exact duplicate groups."""
    duplicate_mask = df.duplicated(keep=False)
    count = int(duplicate_mask.sum())

    if count == 0:
        return []

    row_numbers = [
        position + 1
        for position, is_duplicate in enumerate(duplicate_mask)
        if is_duplicate
    ]

    return [
        _make_issue(
            "duplicate_rows",
            count,
            row_numbers=row_numbers,
        )
    ]


def check_negative_values(
    df: pd.DataFrame,
    non_negative_columns: list[str],
) -> list[dict]:
    """Report negative values in columns expected to be non-negative."""
    issues = []

    for column in non_negative_columns:
        if column not in df.columns:
            raise ValueError(
                f"Column '{column}' does not exist in the dataset."
            )

        if not pd.api.types.is_numeric_dtype(df[column]):
            raise TypeError(
                f"Column '{column}' must contain numeric values."
            )

        negative_mask = df[column] < 0
        count = int(negative_mask.sum())

        if count > 0:
            row_numbers = [
                position + 1
                for position, is_negative in enumerate(negative_mask)
                if is_negative
            ]

            issues.append(
                _make_issue(
                    "negative_values",
                    count,
                    column=column,
                    row_numbers=row_numbers,
                )
            )

    return issues


def validate_dataframe(
    df: pd.DataFrame,
    email_columns: list[str] | None = None,
    non_negative_columns: list[str] | None = None,
) -> dict:
    """
    Run data quality checks and return a structured report.

    The input DataFrame is never modified.

    Args:
        df: Dataset to validate.
        email_columns: Columns containing email addresses.
        non_negative_columns: Numeric columns where negative values
            should be flagged.

    Returns:
        Dictionary containing dataset statistics and detected issues.
    """
    if not isinstance(df, pd.DataFrame):
        raise TypeError("Input must be a pandas DataFrame.")

    email_columns = email_columns or []
    non_negative_columns = non_negative_columns or []

    issues = []

    issues.extend(check_empty_dataset(df))

    if not df.empty:
        issues.extend(check_missing_values(df))
        issues.extend(check_empty_columns(df))
        issues.extend(check_invalid_emails(df, email_columns))
        issues.extend(check_duplicates(df))
        issues.extend(
            check_negative_values(df, non_negative_columns)
        )

    total_issues = sum(issue["count"] for issue in issues)

    return {
        "summary": {
            "total_rows": len(df),
            "total_columns": len(df.columns),
            "total_issues": total_issues,
        },
        "issues": issues,
    }