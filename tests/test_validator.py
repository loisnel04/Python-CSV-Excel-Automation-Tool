
import pandas as pd
import pytest
from data_automation.validator import validate_dataframe


def test_detect_missing_values():
    df = pd.DataFrame({
        "name": ["John", "Jane"],
        "age": [25, None],
    })

    report = validate_dataframe(df)

    issue = next(
        issue for issue in report["issues"]
        if issue["type"] == "missing_values"
    )

    assert issue["column"] == "age"
    assert issue["count"] == 1
    assert issue["row_numbers"] == [2]


def test_detect_multiple_missing_values():
    df = pd.DataFrame({
        "name": ["John", None, "Alice"],
        "age": [None, 30, None],
    })

    report = validate_dataframe(df)

    missing_issues = {
        issue["column"]: issue
        for issue in report["issues"]
        if issue["type"] == "missing_values"
    }

    assert missing_issues["name"]["count"] == 1
    assert missing_issues["age"]["count"] == 2


def test_missing_values_with_non_consecutive_index():
    df = pd.DataFrame(
        {"name": ["John", None, "Alice"]},
        index=[10, 20, 30],
    )

    report = validate_dataframe(df)

    issue = next(
        issue for issue in report["issues"]
        if issue["type"] == "missing_values"
    )

    # Row numbers represent DataFrame positions, not index labels.
    assert issue["row_numbers"] == [2]


def test_detect_empty_column():
    df = pd.DataFrame({
        "name": ["John", "Jane"],
        "phone": [None, None],
    })

    report = validate_dataframe(df)

    assert any(
        issue["type"] == "empty_column"
        and issue["column"] == "phone"
        for issue in report["issues"]
    )


def test_detect_empty_dataset():
    df = pd.DataFrame(columns=["name", "age"])

    report = validate_dataframe(df)

    assert report["summary"]["total_rows"] == 0

    assert any(
        issue["type"] == "empty_dataset"
        for issue in report["issues"]
    )


def test_detect_dataset_without_columns():
    df = pd.DataFrame(index=range(3))

    report = validate_dataframe(df)

    assert any(
        issue["type"] == "no_columns"
        for issue in report["issues"]
    )


def test_detect_invalid_emails():
    df = pd.DataFrame({
        "email": [
            "john@mail.com",
            "alice.mail.com",
            "jane@example.org",
        ]
    })

    report = validate_dataframe(
        df,
        email_columns=["email"],
    )

    issue = next(
        issue for issue in report["issues"]
        if issue["type"] == "invalid_emails"
    )

    assert issue["count"] == 1
    assert issue["column"] == "email"
    assert issue["row_numbers"] == [2]


def test_missing_emails_are_not_invalid_emails():
    df = pd.DataFrame({
        "email": ["john@mail.com", None, "jane@mail.com"]
    })

    report = validate_dataframe(
        df,
        email_columns=["email"],
    )

    invalid_email_issues = [
        issue for issue in report["issues"]
        if issue["type"] == "invalid_emails"
    ]

    assert len(invalid_email_issues) == 0


def test_unknown_email_column():
    df = pd.DataFrame({
        "name": ["John"]
    })

    with pytest.raises(ValueError, match="does not exist"):
        validate_dataframe(
            df,
            email_columns=["email"],
        )


def test_detect_duplicate_rows():
    df = pd.DataFrame({
        "name": ["John", "Jane", "John"],
        "age": [25, 30, 25],
    })

    report = validate_dataframe(df)

    issue = next(
        issue for issue in report["issues"]
        if issue["type"] == "duplicate_rows"
    )

    # Both rows participating in the duplicate group are reported.
    assert issue["count"] == 2
    assert issue["row_numbers"] == [1, 3]


def test_no_duplicate_rows():
    df = pd.DataFrame({
        "name": ["John", "Jane", "Alice"],
        "age": [25, 30, 32],
    })

    report = validate_dataframe(df)

    assert not any(
        issue["type"] == "duplicate_rows"
        for issue in report["issues"]
    )


def test_detect_negative_values():
    df = pd.DataFrame({
        "name": ["John", "Jane"],
        "age": [25, -5],
    })

    report = validate_dataframe(
        df,
        non_negative_columns=["age"],
    )

    issue = next(
        issue for issue in report["issues"]
        if issue["type"] == "negative_values"
    )

    assert issue["count"] == 1
    assert issue["column"] == "age"
    assert issue["row_numbers"] == [2]


def test_unknown_numeric_column():
    df = pd.DataFrame({
        "name": ["John"]
    })

    with pytest.raises(ValueError, match="does not exist"):
        validate_dataframe(
            df,
            non_negative_columns=["age"],
        )


def test_non_numeric_column():
    df = pd.DataFrame({
        "age": ["twenty-five", "30"]
    })

    with pytest.raises(TypeError, match="numeric"):
        validate_dataframe(
            df,
            non_negative_columns=["age"],
        )


def test_invalid_input_type():
    with pytest.raises(TypeError, match="pandas DataFrame"):
        validate_dataframe(["John", "Jane"])


def test_original_dataframe_is_not_modified():
    df = pd.DataFrame({
        "email": ["john@mail.com", "invalid-email"],
        "age": [25, -5],
    })

    original = df.copy(deep=True)

    validate_dataframe(
        df,
        email_columns=["email"],
        non_negative_columns=["age"],
    )

    pd.testing.assert_frame_equal(df, original)


def test_report_summary():
    df = pd.DataFrame({
        "name": ["John", "Jane"],
        "age": [25, None],
    })

    report = validate_dataframe(df)

    assert report["summary"]["total_rows"] == 2
    assert report["summary"]["total_columns"] == 2
    assert report["summary"]["total_issues"] == 1


def test_total_issues_counts_all_detected_anomalies():
    df = pd.DataFrame({
        "email": ["invalid-email", None],
        "age": [-5, 30],
    })

    report = validate_dataframe(
        df,
        email_columns=["email"],
        non_negative_columns=["age"],
    )

    # One missing value + one invalid email + one negative value.
    assert report["summary"]["total_issues"] == 3
