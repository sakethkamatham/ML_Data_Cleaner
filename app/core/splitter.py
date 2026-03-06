import pandas as pd
from sklearn.model_selection import train_test_split


def split_dataframe(
    df: pd.DataFrame,
    test_size: float = 0.2,
    random_state: int = 42,
) -> tuple:
    train_df, test_df = train_test_split(df, test_size=test_size, random_state=random_state)
    return train_df.reset_index(drop=True), test_df.reset_index(drop=True)


def save_splits(
    train_df: pd.DataFrame,
    test_df: pd.DataFrame,
    train_path: str,
    test_path: str,
) -> None:
    train_df.to_csv(train_path, index=False)
    test_df.to_csv(test_path, index=False)
