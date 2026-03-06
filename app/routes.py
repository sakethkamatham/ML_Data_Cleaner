import os
import uuid

from flask import Blueprint, render_template, request, jsonify, send_file, current_app

from .core.loader import load_file
from .core.pipeline import CleaningPipeline

bp = Blueprint("main", __name__)


@bp.route("/")
def index():
    return render_template("index.html")


@bp.route("/upload", methods=["POST"])
def upload():
    if "file" not in request.files:
        return jsonify({"error": "No file provided."}), 400

    f = request.files["file"]
    if f.filename == "":
        return jsonify({"error": "No file selected."}), 400

    ext = os.path.splitext(f.filename)[1].lower()
    if ext not in (".csv", ".xlsx", ".xls"):
        return jsonify({"error": "Unsupported file type. Use .csv, .xlsx, or .xls."}), 400

    upload_folder = current_app.config["UPLOAD_FOLDER"]
    os.makedirs(upload_folder, exist_ok=True)

    file_id = str(uuid.uuid4())
    filename = file_id + ext
    filepath = os.path.join(upload_folder, filename)
    f.save(filepath)

    try:
        df = load_file(filepath)
    except Exception as e:
        os.remove(filepath)
        return jsonify({"error": f"Could not read file: {e}"}), 400

    return jsonify({
        "file_id": file_id,
        "filename": f.filename,
        "rows": df.shape[0],
        "cols": df.shape[1],
        "columns": list(df.columns),
        "filepath": filepath,
    })


@bp.route("/run", methods=["POST"])
def run_pipeline():
    data = request.get_json()
    filepath = data.get("filepath")

    if not filepath or not os.path.exists(filepath):
        return jsonify({"error": "File not found. Please re-upload."}), 400

    config = {
        "test_size": float(data.get("test_size", 0.2)),
        "do_scale": bool(data.get("do_scale", True)),
        "do_encode": bool(data.get("do_encode", True)),
        "encode_strategy": data.get("encode_strategy", "label"),
        "missing_col_threshold": float(data.get("missing_col_threshold", 0.5)),
        "random_state": int(data.get("random_state", 42)),
    }

    try:
        df = load_file(filepath)
        pipeline = CleaningPipeline(config, output_folder=current_app.config["OUTPUT_FOLDER"])
        result = pipeline.run(df)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    return jsonify({
        "session_id": result.session_id,
        "original_rows": result.original_shape[0],
        "original_cols": result.original_shape[1],
        "cleaned_rows": len(result.cleaned_df),
        "cleaned_cols": result.cleaned_df.shape[1],
        "train_rows": len(result.train_df),
        "test_rows": len(result.test_df),
        "log_entries": result.log_entries,
        "summary_stats": result.summary_stats,
    })


@bp.route("/download/<session_id>/<filetype>")
def download(session_id, filetype):
    if filetype not in ("train", "test", "cleaned"):
        return jsonify({"error": "Invalid file type."}), 400

    output_folder = current_app.config["OUTPUT_FOLDER"]
    path = os.path.join(output_folder, session_id, f"{filetype}.csv")

    if not os.path.exists(path):
        return jsonify({"error": "File not found."}), 404

    return send_file(path, as_attachment=True, download_name=f"{filetype}.csv")
