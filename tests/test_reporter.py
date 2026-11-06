
import pandas as pd
import pytest

from data_automation.reporter import (
    generate_summary,
    generate_quality_details,
    generate_column_statistics,
    build_report,
    export_quality_report,
)


@pytest.fixture
def original_dataframe():
    return pd.DataFrame({
        "name": ["John", "Jane", "John", None],
        "email": [
            "john@mail.com",
            "jane@mail.com",
            "john@mail.com",
            None,
        ],
        "age": [25, 30, 25, None],
    })


@pytest.fixture
def cleaned_dataframe():
    return pd.DataFrame({
        "name": ["John", "Jane"],
        "email": ["john@mail.com", "jane@mail.com"],
        "age": [25, 30],
    })


@pytest.fixture
def validation_report():
    return {
        "summary": {
            "total_rows": 2,
            "total_columns": 3,
            "total_issues": 2,
        },
        "issues": [
            {
                "type": "missing_values",
                "column": "age",
                "count": 1,
                "row_numbers": [2],
            },
            {
                "type": "invalid_emails",
                "column": "email",
                "count": 1,
                "row_numbers": [3],
            },
        ],
    }


# ---------------------------------------------------------
# Summary generation
# ---------------------------------------------------------

def test_generate_summary(
    original_dataframe,
    cleaned_dataframe,
    validation_report,
):
    summary = generate_summary(
        original_dataframe,
        cleaned_dataframe,
        validation_report,
    )

    metrics = dict(zip(summary["Metric"], summary["Value"]))

    assert metrics["Original rows"] == 4
    assert metrics["Cleaned rows"] == 2
    assert metrics["Removed rows"] == 2
    assert metrics["Original columns"] == 3
    assert metrics["Cleaned columns"] == 3
    assert metrics["Detected issues"] == 2


# ---------------------------------------------------------
# Quality details
# ---------------------------------------------------------

def test_generate_quality_details(validation_report):
    details = generate_quality_details(validation_report)

    assert len(details) == 2
    assert list(details.columns) == [
        "Issue type",
        "Column",
        "Count",
        "Affected rows",
    ]

    assert details.iloc[0]["Issue type"] == "missing_values"
    assert details.iloc[0]["Column"] == "age"
    assert details.iloc[0]["Count"] == 1
    assert details.iloc[0]["Affected rows"] == "2"


def test_generate_quality_details_without_issues():
    report = {"issues": []}

    details = generate_quality_details(report)

    assert details.empty
    assert "Issue type" in details.columns


def test_generate_quality_details_without_row_numbers():
    report = {
        "issues": [
            {
                "type": "empty_dataset",
                "count": 1,
            }
        ]
    }

    details = generate_quality_details(report)

    assert details.iloc[0]["Column"] == "N/A"
    assert details.iloc[0]["Affected rows"] == "N/A"


# ---------------------------------------------------------
# Column statistics
# ---------------------------------------------------------

def test_generate_column_statistics(cleaned_dataframe):
    statistics = generate_column_statistics(cleaned_dataframe)

    assert len(statistics) == 3

    name_stats = statistics[
        statistics["Column"] == "name"
    ].iloc[0]

    assert name_stats["Missing values"] == 0
    assert name_stats["Unique values"] == 2
    assert name_stats["Completeness (%)"] == 100.0


def test_column_statistics_with_missing_values():
    df = pd.DataFrame({
        "name": ["John", None, "Alice", None],
    })

    statistics = generate_column_statistics(df)

    name_stats = statistics.iloc[0]

    assert name_stats["Missing values"] == 2
    assert name_stats["Unique values"] == 2
    assert name_stats["Completeness (%)"] == 50.0


def test_column_statistics_with_empty_dataframe():
    df = pd.DataFrame(columns=["name", "age"])

    statistics = generate_column_statistics(df)

    assert len(statistics) == 2
    assert all(statistics["Completeness (%)"] == 0.0)


def test_column_statistics_with_no_columns():
    df = pd.DataFrame()

    statistics = generate_column_statistics(df)

    assert statistics.empty
    assert "Column" in statistics.columns


# ---------------------------------------------------------
# Complete report construction
# ---------------------------------------------------------

def test_build_report(
    original_dataframe,
    cleaned_dataframe,
    validation_report,
):
    report = build_report(
        original_dataframe,
        cleaned_dataframe,
        validation_report,
    )

    assert list(report.keys()) == [
        "Summary",
        "Data Quality",
        "Column Statistics",
    ]

    assert isinstance(report["Summary"], pd.DataFrame)
    assert isinstance(report["Data Quality"], pd.DataFrame)
    assert isinstance(report["Column Statistics"], pd.DataFrame)


def test_build_report_invalid_original_dataframe(
    cleaned_dataframe,
    validation_report,
):
    with pytest.raises(TypeError, match="original_df"):
        build_report(
            ["John", "Jane"],
            cleaned_dataframe,
            validation_report,
        )


def test_build_report_invalid_cleaned_dataframe(
    original_dataframe,
    validation_report,
):
    with pytest.raises(TypeError, match="cleaned_df"):
        build_report(
            original_dataframe,
            ["John", "Jane"],
            validation_report,
        )


def test_build_report_invalid_validation_report(
    original_dataframe,
    cleaned_dataframe,
):
    with pytest.raises(ValueError, match="summary"):
        build_report(
            original_dataframe,
            cleaned_dataframe,
            {},
        )


def test_build_report_incomplete_validation_summary(
    original_dataframe,
    cleaned_dataframe,
):
    report = {
        "summary": {"total_rows": 2},
        "issues": [],
    }

    with pytest.raises(ValueError, match="incomplete"):
        build_report(
            original_dataframe,
            cleaned_dataframe,
            report,
        )


# ---------------------------------------------------------
# Excel report export
# ---------------------------------------------------------

def test_export_quality_report(
    original_dataframe,
    cleaned_dataframe,
    validation_report,
    tmp_path,
):
    report = build_report(
        original_dataframe,
        cleaned_dataframe,
        validation_report,
    )

    output_path = tmp_path / "quality_report.xlsx"

    result = export_quality_report(report, output_path)

    assert result == output_path
    assert output_path.exists()

    excel_file = pd.ExcelFile(output_path)

    assert excel_file.sheet_names == [
        "Summary",
        "Data Quality",
        "Column Statistics",
    ]


def test_export_quality_report_prevents_overwriting(tmp_path):
    output_path = tmp_path / "quality_report.xlsx"
    output_path.write_text("existing file", encoding="utf-8")

    report = {
        "Summary": pd.DataFrame({"Metric": ["Rows"], "Value": [10]})
    }

    with pytest.raises(FileExistsError):
        export_quality_report(report, output_path)


def test_export_quality_report_allows_overwriting(tmp_path):
    output_path = tmp_path / "quality_report.xlsx"
    output_path.write_text("existing file", encoding="utf-8")

    report = {
        "Summary": pd.DataFrame({"Metric": ["Rows"], "Value": [10]})
    }

    result = export_quality_report(
        report,
        output_path,
        overwrite=True,
    )

    assert result == output_path
    assert pd.ExcelFile(output_path).sheet_names == ["Summary"]


def test_export_quality_report_rejects_csv(tmp_path):
    report = {
        "Summary": pd.DataFrame({"Metric": ["Rows"], "Value": [10]})
    }

    with pytest.raises(ValueError, match=".xlsx"):
        export_quality_report(
            report,
            tmp_path / "quality_report.csv",
        )


def test_export_quality_report_rejects_empty_report(tmp_path):
    with pytest.raises(ValueError, match="cannot be empty"):
        export_quality_report(
            {},
            tmp_path / "quality_report.xlsx",
        )


def test_export_quality_report_rejects_invalid_sheet_name(
    tmp_path,
):
    report = {
        "Invalid/Sheet": pd.DataFrame({"value": [1]})
    }

    with pytest.raises(ValueError, match="Invalid character"):
        export_quality_report(
            report,
            tmp_path / "quality_report.xlsx",
        )
