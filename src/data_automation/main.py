import pandas as pd
from pathlib import Path

from data_automation.reader import (
    SUPPORTED_EXTENSIONS,
    read_file,
)

from data_automation.cleaner import (
    clean_dataframe,
    normalize_column_names
    )

from data_automation.validator import validate_dataframe

from data_automation.reporter import (
    build_report,
    export_quality_report,
)

from data_automation.exporter import export_dataframe

# Project directories
PROJECT_ROOT = Path(__file__).resolve().parents[2]
INPUT_DIR = PROJECT_ROOT / "data" / "input"
OUTPUT_DIR = PROJECT_ROOT / "data" / "output"


def display_menu() -> None:
    """Display the application's main menu."""
    print("\n" + "=" * 45)
    print("       PYTHON CSV & EXCEL AUTOMATION")
    print("=" * 45)
    print("\nPlease select a processing mode:")
    print("1. Individual processing")
    print("2. Merge processing")
    print("0. Exit")
    print("=" * 45)


def get_user_choice() -> str:
    """Get the user's menu selection."""
    return input("Your choice: ").strip()


def get_input_files() -> list[Path]:
    """Return all supported files from the input directory."""

    if not INPUT_DIR.exists():
        print(f"[WARNING] Input directory not found: {INPUT_DIR}")
        return []

    if not INPUT_DIR.is_dir():
        print(f"[ERROR] Input path is not a directory: {INPUT_DIR}")
        return []

    all_files = sorted(
        path for path in INPUT_DIR.iterdir()
        if path.is_file()
    )

    supported_files = [
        path for path in all_files
        if path.suffix.lower() in SUPPORTED_EXTENSIONS
    ]

    unsupported_files = [
        path for path in all_files
        if path.suffix.lower() not in SUPPORTED_EXTENSIONS
    ]

    for file_path in unsupported_files:
        print(f"[WARNING] Unsupported file skipped: {file_path.name}")

    return supported_files


def run_individual_processing() -> None:
    """Process each input file individually."""

    print("\n[INFO] Starting individual processing...")

    input_files = get_input_files()

    if not input_files:
        print("[WARNING] No supported files found in the input directory.")
        return

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    print(f"\n[INFO] {len(input_files)} file(s) detected.")

    successful_files = 0
    failed_files = 0

    for file_path in input_files:

        print("\n" + "-" * 45)
        print(f"[INFO] Processing: {file_path.name}")
        print("-" * 45)

        try:
            # Step 1: Read the original file
            original_df = read_file(file_path)

            print(
                f"[INFO] Loaded {len(original_df)} rows "
                f"and {len(original_df.columns)} columns."
            )

            # Step 2: Clean the dataset
            cleaned_df = clean_dataframe(original_df)

            print("[INFO] Data cleaning completed.")

            # Step 3: Validate the cleaned dataset
            validation_report = validate_dataframe(cleaned_df)

            print(
                f"[INFO] Detected "
                f"{validation_report['summary']['total_issues']} issue(s)."
            )

            # Step 4: Generate the quality report
            report = build_report(
                original_df,
                cleaned_df,
                validation_report,
            )

            # Step 5: Prepare output paths
            cleaned_file_path = (
                OUTPUT_DIR / f"{file_path.stem}_cleaned{file_path.suffix.lower()}"
            )

            report_file_path = (
                OUTPUT_DIR / f"{file_path.stem}_quality_report.xlsx"
            )

            # Step 6: Export cleaned dataset
            export_dataframe(
                cleaned_df,
                cleaned_file_path,
                overwrite=True,
            )

            # Step 7: Export quality report
            export_quality_report(
                report,
                report_file_path,
                overwrite=True,
            )

            print("[SUCCESS] File processed successfully.")
            print(f"[OUTPUT] Cleaned data: {cleaned_file_path.name}")
            print(f"[OUTPUT] Quality report: {report_file_path.name}")

            successful_files += 1

        except Exception as error:
            print(f"[ERROR] Failed to process {file_path.name}: {error}")
            failed_files += 1

    # Final processing summary
    print("\n" + "=" * 45)
    print("          PROCESSING SUMMARY")
    print("=" * 45)
    print(f"Total files:      {len(input_files)}")
    print(f"Successful:       {successful_files}")
    print(f"Failed:           {failed_files}")
    print("=" * 45)


def run_merge_processing() -> None:
    """Merge compatible input files before processing."""

    print("\n[INFO] Starting merge processing...")

    input_files = get_input_files()

    if len(input_files) < 2:
        print(
            "[WARNING] Merge processing requires at least "
            "two supported input files."
        )
        return

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    print(f"\n[INFO] {len(input_files)} file(s) detected.")

    dataframes = []
    reference_columns = None

    try:
        # Step 1: Read and normalize all input files
        for file_path in input_files:
            print(f"\n[INFO] Reading: {file_path.name}")

            dataframe = read_file(file_path)
            dataframe = normalize_column_names(dataframe)

            print(
                f"[INFO] Loaded {len(dataframe)} rows "
                f"and {len(dataframe.columns)} columns."
            )

            current_columns = list(dataframe.columns)

            # The first file defines the reference schema
            if reference_columns is None:
                reference_columns = current_columns
                print("[INFO] Reference schema established.")

            else:
                missing_columns = sorted(
                    set(reference_columns) - set(current_columns)
                )
                extra_columns = sorted(
                    set(current_columns) - set(reference_columns)
                )

                if missing_columns or extra_columns:
                    print(
                        f"\n[ERROR] Incompatible schema in "
                        f"{file_path.name}."
                    )

                    if missing_columns:
                        print(
                            "[ERROR] Missing columns: "
                            f"{missing_columns}"
                        )

                    if extra_columns:
                        print(
                            "[ERROR] Unexpected columns: "
                            f"{extra_columns}"
                        )

                    print(
                        "[WARNING] Merge cancelled. "
                        "No output files were generated."
                    )
                    return

                # Align column order with the reference schema
                dataframe = dataframe[reference_columns]

            dataframes.append(dataframe)

        # Step 2: Merge all compatible DataFrames
        print("\n[INFO] All file schemas are compatible.")

        merged_df = pd.concat(
            dataframes,
            ignore_index=True,
        )

        print(
            f"[INFO] Merge completed: {len(merged_df)} rows "
            f"and {len(merged_df.columns)} columns."
        )

        # Step 3: Clean the merged dataset
        cleaned_df = clean_dataframe(merged_df)

        print("[INFO] Data cleaning completed.")

        # Step 4: Validate the cleaned dataset
        validation_report = validate_dataframe(cleaned_df)

        print(
            f"[INFO] Detected "
            f"{validation_report['summary']['total_issues']} issue(s)."
        )

        # Step 5: Generate the quality report
        report = build_report(
            merged_df,
            cleaned_df,
            validation_report,
        )

        # Step 6: Define output paths
        cleaned_file_path = OUTPUT_DIR / "merged_cleaned.xlsx"
        report_file_path = OUTPUT_DIR / "merged_quality_report.xlsx"

        # Step 7: Export merged dataset
        export_dataframe(
            cleaned_df,
            cleaned_file_path,
            overwrite=True,
        )

        # Step 8: Export quality report
        export_quality_report(
            report,
            report_file_path,
            overwrite=True,
        )

        print("\n[SUCCESS] Merge processing completed.")
        print(f"[OUTPUT] Cleaned data: {cleaned_file_path.name}")
        print(f"[OUTPUT] Quality report: {report_file_path.name}")

        # Final summary
        print("\n" + "=" * 45)
        print("          MERGE PROCESSING SUMMARY")
        print("=" * 45)
        print(f"Input files:      {len(input_files)}")
        print(f"Original rows:    {len(merged_df)}")
        print(f"Cleaned rows:     {len(cleaned_df)}")
        print(f"Output columns:   {len(cleaned_df.columns)}")
        print("=" * 45)

    except Exception as error:
        print(f"\n[ERROR] Merge processing failed: {error}")
        print("[WARNING] No complete merge result was generated.")


def main() -> None:
    """Run the main application loop."""
    print("\nWelcome to the CSV & Excel Automation Tool!")

    while True:
        display_menu()
        choice = get_user_choice()

        if choice == "1":
            run_individual_processing()

        elif choice == "2":
            run_merge_processing()

        elif choice == "0":
            print("\nThank you for using the application. Goodbye!")
            break

        else:
            print(
                "\n[WARNING] Invalid selection. "
                "Please enter 1, 2 or 0."
            )


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n[INFO] Application interrupted by user.")
