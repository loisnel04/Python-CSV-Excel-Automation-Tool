import pandas as pd
import pytest

from data_automation.cleaner import (
    clean_dataframe,
    normalize_column_names,
    clean_text_values,
    remove_empty_rows,
    remove_duplicates,
)


def test_normalize_column_names():
    df = pd.DataFrame({
        "First Name": ["John"],
        "E-mail Address": ["john@mail.com"],
        "Age (Years)": [25],
    })

    result = normalize_column_names(df)

    assert list(result.columns) == [
        "first_name",
        "e_mail_address",
        "age_years",
    ]


def test_column_name_collision():
    df = pd.DataFrame({
        "First Name": ["John"],
        "first-name": ["Jane"],
    })

    with pytest.raises(ValueError, match="collision"):
        normalize_column_names(df)


def test_clean_text_values():
    df = pd.DataFrame({
        "name": [" John Smith ", "Jane Doe"],
        "email": [" JOHN@MAIL.COM ", "jane@mail.com"],
    })

    result = clean_text_values(
        df,
        lowercase_columns=["email"],
    )

    assert result.iloc[0]["name"] == "John Smith"
    assert result.iloc[0]["email"] == "john@mail.com"


def test_whitespace_only_values_become_missing():
    df = pd.DataFrame({
        "name": ["John", "   "],
    })

    result = clean_text_values(df)

    assert pd.isna(result.iloc[1]["name"])


def test_remove_empty_rows():
    df = pd.DataFrame({
        "name": ["John", None, "Jane"],
        "age": [25, None, 30],
    })

    result = remove_empty_rows(df)

    assert len(result) == 2


def test_remove_duplicates():
    df = pd.DataFrame({
        "name": ["John", "Jane", "John"],
        "age": [25, 30, 25],
    })

    result = remove_duplicates(df)

    assert len(result) == 2


def test_clean_dataframe():
    df = pd.DataFrame({
        "First Name": [" John ", "Jane", " John "],
        "Email": [
            " JOHN@MAIL.COM ",
            "jane@mail.com",
            " JOHN@MAIL.COM ",
        ],
        "Age": [25, 30, 25],
    })

    result = clean_dataframe(
        df,
        lowercase_columns=["email"],
    )

    assert list(result.columns) == ["first_name", "email", "age"]
    assert len(result) == 2
    assert result.iloc[0]["first_name"] == "John"
    assert result.iloc[0]["email"] == "john@mail.com"


def test_original_dataframe_is_not_modified():
    df = pd.DataFrame({
        "First Name": [" John "],
    })

    original = df.copy(deep=True)

    clean_dataframe(df)

    pd.testing.assert_frame_equal(df, original)


def test_missing_lowercase_column():
    df = pd.DataFrame({"name": ["John"]})

    with pytest.raises(ValueError, match="does not exist"):
        clean_text_values(df, lowercase_columns=["email"])