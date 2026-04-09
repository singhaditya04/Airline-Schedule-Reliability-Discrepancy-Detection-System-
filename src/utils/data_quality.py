"""Data quality profiling utilities."""
import pandas as pd


class DataQualityReport:
    """Generate data quality summary for a DataFrame."""

    def __init__(self, df: pd.DataFrame, name: str = "Dataset"):
        self.df = df
        self.name = name

    def nulls_summary(self) -> pd.DataFrame:
        """Return null counts per column."""
        nulls = self.df.isnull().sum()
        nulls_pct = (nulls / len(self.df) * 100).round(2)
        return pd.DataFrame({
            "column": nulls.index,
            "null_count": nulls.values,
            "null_percent": nulls_pct.values,
        })

    def duplicates_summary(self) -> dict:
        """Return duplicate row information."""
        total_rows = len(self.df)
        duplicate_rows = self.df.duplicated().sum()
        return {
            "total_rows": total_rows,
            "duplicate_rows": duplicate_rows,
            "duplicate_percent": round(duplicate_rows / total_rows * 100, 2) if total_rows > 0 else 0,
        }

    def value_counts(self, column: str, top_n: int = 5) -> pd.Series:
        """Return top N value counts for a column."""
        return self.df[column].value_counts().head(top_n)

    def print_summary(self) -> None:
        """Print a comprehensive data quality summary."""
        print(f"\n{'='*60}")
        print(f"Data Quality Report: {self.name}")
        print(f"{'='*60}")
        print(f"Shape: {self.df.shape[0]} rows, {self.df.shape[1]} columns\n")

        print("Null Values Summary:")
        print(self.nulls_summary().to_string(index=False))

        print(f"\nDuplicate Rows Summary:")
        dup_summary = self.duplicates_summary()
        for key, val in dup_summary.items():
            print(f"  {key}: {val}")

        print(f"\nData Types:")
        print(self.df.dtypes)
        print(f"{'='*60}\n")
