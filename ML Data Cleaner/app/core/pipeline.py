import os
import uuid
from dataclasses import dataclass, field

import pandas as pd

from .cleaner import DataCleaner
from .loader import detect_column_types
from .splitter import split_dataframe, save_splits


@dataclass
class PipelineResult:
    original_shape: tuple
    cleaned_df: pd.DataFrame
    train_df: pd.DataFrame
    test_df: pd.DataFrame
    log_entries: list
    summary_stats: dict
    session_id: str
    train_path: str
    test_path: str
    cleaned_path: str


class CleaningPipeline:
    def __init__(self, config: dict, output_folder: str = "outputs"):
        self.config = config
        self.output_folder = output_folder

    def run(self, df: pd.DataFrame) -> PipelineResult:
        original_shape = df.shape
        log_entries = []

        # Detect column types from the original df before any transformation
        col_types = detect_column_types(df)

        # Step 1: Drop duplicates
        df, log = DataCleaner.drop_duplicates(df)
        log_entries.append(log)

        # Step 2: Fill missing values
        df, log = DataCleaner.fill_missing(df, col_types)
        log_entries.append(log)

        # Step 3: Drop high-missing columns
        threshold = self.config.get("missing_col_threshold", 0.5)
        df, log = DataCleaner.drop_high_missing_cols(df, threshold=threshold)
        # Update col_types to remove dropped columns
        col_types = {c: t for c, t in col_types.items() if c in df.columns}
        log_entries.append(log)

        # Step 4: Cap outliers
        df, log = DataCleaner.cap_outliers_iqr(df, col_types)
        log_entries.append(log)

        # Step 5: Encode categoricals (optional)
        if self.config.get("do_encode", True):
            strategy = self.config.get("encode_strategy", "label")
            df, log = DataCleaner.encode_categoricals(df, col_types, strategy=strategy)
            log_entries.append(log)
        else:
            log_entries.append({
                "step": "Encode Categoricals",
                "rows_before": len(df), "rows_after": len(df),
                "cols_before": df.shape[1], "cols_after": df.shape[1],
                "detail": "Skipped (disabled in config).",
            })

        # Step 6: Scale numerics (optional)
        if self.config.get("do_scale", True):
            df, log, _ = DataCleaner.scale_numerics(df, col_types)
            log_entries.append(log)
        else:
            log_entries.append({
                "step": "Scale Numeric Features",
                "rows_before": len(df), "rows_after": len(df),
                "cols_before": df.shape[1], "cols_after": df.shape[1],
                "detail": "Skipped (disabled in config).",
            })

        # Step 7: Train/test split
        test_size = self.config.get("test_size", 0.2)
        random_state = self.config.get("random_state", 42)
        train_df, test_df = split_dataframe(df, test_size=test_size, random_state=random_state)

        split_log = {
            "step": "Train/Test Split",
            "rows_before": len(df),
            "rows_after": len(df),
            "cols_before": df.shape[1],
            "cols_after": df.shape[1],
            "detail": (
                f"Split {len(df)} rows → train: {len(train_df)}, test: {len(test_df)} "
                f"({int((1-test_size)*100)}/{int(test_size*100)})."
            ),
        }
        log_entries.append(split_log)

        # Save outputs
        session_id = str(uuid.uuid4())
        session_dir = os.path.join(self.output_folder, session_id)
        os.makedirs(session_dir, exist_ok=True)

        train_path = os.path.join(session_dir, "train.csv")
        test_path = os.path.join(session_dir, "test.csv")
        cleaned_path = os.path.join(session_dir, "cleaned.csv")

        save_splits(train_df, test_df, train_path, test_path)
        df.to_csv(cleaned_path, index=False)

        # Summary stats as a serializable dict
        summary_stats = df.describe().round(4).to_dict()

        return PipelineResult(
            original_shape=original_shape,
            cleaned_df=df,
            train_df=train_df,
            test_df=test_df,
            log_entries=log_entries,
            summary_stats=summary_stats,
            session_id=session_id,
            train_path=train_path,
            test_path=test_path,
            cleaned_path=cleaned_path,
        )
