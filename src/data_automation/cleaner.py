import re
import unicodedata
from collections.abc import Iterable
import pandas as pd


def normalize_column_names(df: pd.DataFrame) -> pd.DataFrame:
    """
    Normalize column names into lowercase snake_case.

    Examples:
        "First Name" -> "first_name"
        "E-mail Address" -> "e_mail_address"
        "Age (Years)" -> "age_years"
    """
    cleaned_df = df.copy()

    normalized_names = []

    for column in cleaned_df.columns:
        name = str(column).strip()

        # Remove accents.
        name = unicodedata.normalize("NFKD", name)
        name = name.encode("ascii", "ignore").decode("ascii")

        # Convert to lowercase.
        name = name.lower()

        # Replace groups of non-alphanumeric characters with underscores.
        name = re.sub(r"[^a-z0-9]+", "_", name)

        # Remove leading and trailing underscores.
        name = name.strip("_")

        if not name:
            raise ValueError(
                f"Column name {column!r} becomes empty after normalization."
            )

        normalized_names.append(name)

    # Prevent accidental column name collisions.
    if len(normalized_names) != len(set(normalized_names)):
        raise ValueError(
            "Column name collision detected after normalization."
        )

    cleaned_df.columns = normalized_names

    return cleaned_df


def clean_text_values(
    df: pd.DataFrame,
    lowercase_columns: Iterable[str] | None = None,
) -> pd.DataFrame:
    """
    Remove leading/trailing whitespace from text values.

    Empty strings resulting from whitespace-only values are converted
    to pandas missing values.

    Optionally convert selected columns to lowercase.
    """
    cleaned_df = df.copy()

    for column in cleaned_df.columns:
        cleaned_df[column] = cleaned_df[column].map(
            lambda value: (
                pd.NA
                if isinstance(value, str) and not value.strip()
                else value.strip()
                if isinstance(value, str)
                else value
            )
        )

    if lowercase_columns is not None:
        for column in lowercase_columns:
            if column not in cleaned_df.columns:
                raise ValueError(
                    f"Column '{column}' does not exist in the dataset."
                )

            cleaned_df[column] = cleaned_df[column].map(
                lambda value: (
                    value.lower() if isinstance(value, str) else value
                )
            )

    return cleaned_df


def remove_empty_rows(df: pd.DataFrame) -> pd.DataFrame:
    """
    Remove rows where every column contains a missing value.
    """
    return df.dropna(how="all").copy()


def remove_duplicates(
    df: pd.DataFrame,
    keep: str = "first",
) -> pd.DataFrame:
    """
    Remove fully duplicated rows.

    Args:
        df: Dataset to clean.
        keep: Which duplicate occurrence to retain:
            - "first": keep the first occurrence.
            - "last": keep the last occurrence.
            - False: remove all duplicated occurrences.
    """
    if keep not in ("first", "last", False):
        raise ValueError(
            "keep must be 'first', 'last', or False."
        )

    return df.drop_duplicates(keep=keep).copy()


def clean_dataframe(
    df: pd.DataFrame,
    lowercase_columns: Iterable[str] | None = None,
    remove_duplicates_enabled: bool = True,
    remove_empty_rows_enabled: bool = True,
) -> pd.DataFrame:
    """
    Apply the standard cleaning pipeline to a DataFrame.

    The original DataFrame is never modified.
    """
    if not isinstance(df, pd.DataFrame):
        raise TypeError("Input must be a pandas DataFrame.")

    cleaned_df = normalize_column_names(df)

    cleaned_df = clean_text_values(
        cleaned_df,
        lowercase_columns=lowercase_columns,
    )

    if remove_empty_rows_enabled:
        cleaned_df = remove_empty_rows(cleaned_df)

    if remove_duplicates_enabled:
        cleaned_df = remove_duplicates(cleaned_df)

    return cleaned_df.reset_index(drop=True)
