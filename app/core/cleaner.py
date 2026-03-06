import pandas as pd
import numpy as np
from sklearn.preprocessing import LabelEncoder, StandardScaler


class DataCleaner:

    @staticmethod
    def drop_duplicates(df: pd.DataFrame):
        rows_before = len(df)
        cleaned = df.drop_duplicates()
        removed = rows_before - len(cleaned)
        log = {
            "step": "Drop Duplicates",
            "rows_before": rows_before,
            "rows_after": len(cleaned),
            "cols_before": df.shape[1],
            "cols_after": cleaned.shape[1],
            "detail": f"{removed} duplicate row(s) removed.",
        }
        return cleaned.reset_index(drop=True), log

    @staticmethod
    def fill_missing(df: pd.DataFrame, col_types: dict):
        rows_before = len(df)
        cleaned = df.copy()
        numeric_filled = 0
        categorical_filled = 0

        for col, ctype in col_types.items():
            if col not in cleaned.columns:
                continue
            missing = cleaned[col].isnull().sum()
            if missing == 0:
                continue
            if ctype == "numeric":
                cleaned[col] = cleaned[col].fillna(cleaned[col].median())
                numeric_filled += missing
            else:
                mode = cleaned[col].mode()
                if not mode.empty:
                    cleaned[col] = cleaned[col].fillna(mode[0])
                    categorical_filled += missing

        log = {
            "step": "Fill Missing Values",
            "rows_before": rows_before,
            "rows_after": len(cleaned),
            "cols_before": df.shape[1],
            "cols_after": cleaned.shape[1],
            "detail": (
                f"{numeric_filled} numeric cell(s) filled with median; "
                f"{categorical_filled} categorical cell(s) filled with mode."
            ),
        }
        return cleaned, log

    @staticmethod
    def drop_high_missing_cols(df: pd.DataFrame, threshold: float = 0.5):
        missing_frac = df.isnull().mean()
        to_drop = missing_frac[missing_frac > threshold].index.tolist()
        cleaned = df.drop(columns=to_drop)
        detail = (
            f"Dropped {len(to_drop)} column(s) with >{int(threshold*100)}% missing: "
            + (", ".join(to_drop) if to_drop else "none")
        )
        log = {
            "step": "Drop High-Missing Columns",
            "rows_before": len(df),
            "rows_after": len(cleaned),
            "cols_before": df.shape[1],
            "cols_after": cleaned.shape[1],
            "detail": detail,
        }
        return cleaned, log

    @staticmethod
    def cap_outliers_iqr(df: pd.DataFrame, col_types: dict):
        cleaned = df.copy()
        total_capped = 0
        col_details = []

        for col, ctype in col_types.items():
            if col not in cleaned.columns or ctype != "numeric":
                continue
            q1 = cleaned[col].quantile(0.25)
            q3 = cleaned[col].quantile(0.75)
            iqr = q3 - q1
            lower = q1 - 1.5 * iqr
            upper = q3 + 1.5 * iqr
            capped = ((cleaned[col] < lower) | (cleaned[col] > upper)).sum()
            if capped > 0:
                cleaned[col] = cleaned[col].clip(lower=lower, upper=upper)
                total_capped += capped
                col_details.append(f"{col} ({int(capped)})")

        detail = f"{total_capped} value(s) capped across {len(col_details)} column(s)."
        if col_details:
            detail += " Columns: " + ", ".join(col_details)

        log = {
            "step": "Cap Outliers (IQR)",
            "rows_before": len(df),
            "rows_after": len(cleaned),
            "cols_before": df.shape[1],
            "cols_after": cleaned.shape[1],
            "detail": detail,
        }
        return cleaned, log

    @staticmethod
    def encode_categoricals(df: pd.DataFrame, col_types: dict, strategy: str = "label"):
        cleaned = df.copy()
        cat_cols = [c for c, t in col_types.items() if t == "categorical" and c in cleaned.columns]

        if not cat_cols:
            log = {
                "step": "Encode Categoricals",
                "rows_before": len(df),
                "rows_after": len(cleaned),
                "cols_before": df.shape[1],
                "cols_after": cleaned.shape[1],
                "detail": "No categorical columns to encode.",
            }
            return cleaned, log

        if strategy == "onehot":
            cleaned = pd.get_dummies(cleaned, columns=cat_cols, drop_first=True)
            detail = (
                f"One-hot encoded {len(cat_cols)} column(s): {', '.join(cat_cols)}. "
                f"New shape: {cleaned.shape[1]} columns."
            )
        else:
            le = LabelEncoder()
            for col in cat_cols:
                cleaned[col] = le.fit_transform(cleaned[col].astype(str))
            detail = f"Label encoded {len(cat_cols)} column(s): {', '.join(cat_cols)}."

        log = {
            "step": "Encode Categoricals",
            "rows_before": len(df),
            "rows_after": len(cleaned),
            "cols_before": df.shape[1],
            "cols_after": cleaned.shape[1],
            "detail": detail,
        }
        return cleaned, log

    @staticmethod
    def scale_numerics(df: pd.DataFrame, col_types: dict):
        cleaned = df.copy()
        # Scale only columns that were originally numeric and still exist
        num_cols = [c for c, t in col_types.items() if t == "numeric" and c in cleaned.columns]

        if not num_cols:
            log = {
                "step": "Scale Numeric Features",
                "rows_before": len(df),
                "rows_after": len(cleaned),
                "cols_before": df.shape[1],
                "cols_after": cleaned.shape[1],
                "detail": "No numeric columns to scale.",
            }
            return cleaned, log, None

        scaler = StandardScaler()
        cleaned[num_cols] = scaler.fit_transform(cleaned[num_cols])
        detail = f"StandardScaler applied to {len(num_cols)} column(s): {', '.join(num_cols)}."

        log = {
            "step": "Scale Numeric Features",
            "rows_before": len(df),
            "rows_after": len(cleaned),
            "cols_before": df.shape[1],
            "cols_after": cleaned.shape[1],
            "detail": detail,
        }
        return cleaned, log, scaler
