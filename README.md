# ML Data Cleaner

A Flask web app for cleaning ML datasets — upload a CSV or Excel file, configure a cleaning pipeline through a browser UI, and download ready-to-use train/test splits.

---

## What It Does

ML Data Cleaner takes a raw tabular dataset and runs it through a 7-step automated cleaning pipeline:

1. Removes duplicate rows
2. Fills missing values (median for numerics, mode for categoricals)
3. Drops columns that are mostly missing (configurable threshold)
4. Caps outliers using IQR-based clipping
5. Encodes categorical columns (label encoding or one-hot)
6. Scales numeric columns with StandardScaler
7. Splits the cleaned data into train and test sets

All steps are logged and surfaced in the UI. When the pipeline finishes, you can download `train.csv`, `test.csv`, or the full `cleaned.csv`.

---

## Features

- Drag-and-drop file upload (CSV, XLSX, XLS — up to 100 MB)
- Configurable pipeline options via the UI (no code needed)
- Step-by-step log showing what changed at each stage
- Summary statistics table for the cleaned dataset
- One-click download of train, test, or cleaned output files

---

## Project Structure

```
ML Data Cleaner/
├── main.py                  # App entry point
├── requirements.txt         # Python dependencies
├── app/
│   ├── __init__.py          # Flask app factory
│   ├── routes.py            # Upload, run, and download endpoints
│   └── core/
│       ├── cleaner.py       # DataCleaner — all pipeline transformation steps
│       ├── loader.py        # File loading and column type detection
│       ├── pipeline.py      # CleaningPipeline — orchestrates steps and saves outputs
│       └── splitter.py      # Train/test split logic
├── templates/
│   └── index.html           # Single-page UI
└── static/
    ├── app.js               # Frontend logic
    └── style.css            # Styles
```

Uploaded files are stored in `uploads/`. Output files are saved to `outputs/<session_id>/`.

---

## Prerequisites

- Python 3.8+
- pip

---

## Installation & Setup

1. Navigate to the project directory:
   ```bash
   cd "ML Data Cleaner"
   ```

2. (Optional) Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate      # macOS/Linux
   venv\Scripts\activate         # Windows
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Start the server:
   ```bash
   python main.py
   ```

5. Open your browser at `http://localhost:5000`

---

## How to Use

1. **Upload a file** — drag and drop or click to browse. Supported formats: `.csv`, `.xlsx`, `.xls` (max 100 MB).
2. **Configure options** — adjust test split size, missing column threshold, encoding strategy, scaling, and random seed using the UI controls.
3. **Click "Run Pipeline"** — the app processes your file through all 7 steps.
4. **Review the results** — a step-by-step log and summary statistics table appear in the UI.
5. **Download outputs** — click to download `train.csv`, `test.csv`, or `cleaned.csv`.

---

## Cleaning Pipeline Steps

| # | Step | What It Does |
|---|------|--------------|
| 1 | Drop Duplicates | Removes exact duplicate rows |
| 2 | Fill Missing Values | Fills numeric columns with the column median; fills categorical columns with the column mode |
| 3 | Drop High-Missing Columns | Removes columns where more than `missing_col_threshold` of values are missing |
| 4 | Cap Outliers (IQR) | Clips numeric values to the IQR fence: `[Q1 - 1.5*IQR, Q3 + 1.5*IQR]` |
| 5 | Encode Categoricals | Converts categorical columns to integers via label encoding or one-hot encoding |
| 6 | Scale Numeric Features | Applies `StandardScaler` (zero mean, unit variance) to numeric columns |
| 7 | Train/Test Split | Randomly splits the cleaned data into training and test sets |

---

## Configuration Options

| Option | UI Label | Default | Description |
|--------|----------|---------|-------------|
| `test_size` | Test Split % | `0.2` | Fraction of rows reserved for the test set (0.0–1.0) |
| `missing_col_threshold` | Missing Threshold | `0.5` | Drop columns with a missing-value fraction above this value |
| `do_encode` | Encode Categoricals | `true` | Whether to encode categorical columns |
| `encode_strategy` | Encoding Strategy | `"label"` | `"label"` for label encoding, `"onehot"` for one-hot encoding |
| `do_scale` | Scale Numerics | `true` | Whether to apply StandardScaler to numeric columns |
| `random_state` | Random Seed | `42` | Seed for reproducible train/test splits |

---

## Supported File Formats

| Format | Extension |
|--------|-----------|
| Comma-Separated Values | `.csv` |
| Excel (modern) | `.xlsx` |
| Excel (legacy) | `.xls` |

Maximum file size: **100 MB**

---

## Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| `pandas` | >=1.5.0 | Data loading and manipulation |
| `openpyxl` | >=3.0.0 | Reading `.xlsx` files |
| `scikit-learn` | >=1.1.0 | Label encoding and StandardScaler |
| `flask` | >=2.2.0 | Web server and routing |
