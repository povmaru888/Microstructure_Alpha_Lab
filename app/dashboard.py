"""Read-only Streamlit research dashboard."""

import json
from pathlib import Path

import pandas as pd
import streamlit as st

PAGES = ("Market & Depth", "Features", "Model Evaluation", "Benchmark & Limitations")
REQUIRED_RUN = ("run_manifest.json",)
REQUIRED_DATA = ("quality_report.json", "features.parquet")
RESEARCH_NOTICE = (
    "Single-day research sample; not live trading and not evidence of tradable profit."
)


@st.cache_data
def load_run(run_dir_text: str, data_dir_text: str, fingerprint: str) -> dict:
    del fingerprint
    run_dir = Path(run_dir_text)
    data_dir = Path(data_dir_text)
    missing = [str(run_dir / name) for name in REQUIRED_RUN if not (run_dir / name).is_file()]
    missing.extend(
        str(data_dir / name) for name in REQUIRED_DATA if not (data_dir / name).is_file()
    )
    if missing:
        raise FileNotFoundError(f"missing run artifacts: {', '.join(missing)}")
    result = {
        "manifest": json.loads((run_dir / "run_manifest.json").read_text(encoding="utf-8")),
        "quality": json.loads((data_dir / "quality_report.json").read_text(encoding="utf-8")),
        "features": pd.read_parquet(data_dir / "features.parquet"),
    }
    for name in ("metrics.json", "benchmark_report.json"):
        if (run_dir / name).is_file():
            result[name.removesuffix(".json")] = json.loads(
                (run_dir / name).read_text(encoding="utf-8")
            )
    return result


def main() -> None:
    st.set_page_config(page_title="Microstructure Alpha Lab", layout="wide")
    st.title("Microstructure Alpha Lab")
    st.warning(RESEARCH_NOTICE)
    run_dir = Path(st.sidebar.text_input("Run directory", "artifacts/latest"))
    data_dir = Path(st.sidebar.text_input("Data artifacts", "artifacts/data"))
    fingerprint = st.sidebar.text_input("Run fingerprint", "")
    page = st.sidebar.radio("Page", PAGES)
    try:
        data = load_run(str(run_dir), str(data_dir), fingerprint)
    except (FileNotFoundError, ValueError) as error:
        st.error(str(error))
        st.code("python scripts/run_experiment.py --config configs/experiment.yaml --run-id <id>")
        return
    manifest = data["manifest"]
    quality = data["quality"]
    st.caption(
        f"dataset={manifest.get('dataset_id')} | run={manifest.get('run_id')} | "
        f"source={manifest.get('features_sha256', '')[:12]} | "
        f"eligible={quality.get('eligible_rows')} | schema={manifest.get('schema_version')}"
    )
    if page == "Market & Depth":
        st.subheader(page)
        st.line_chart(data["features"], x="event_index", y=["midprice", "microprice"])
    elif page == "Features":
        st.subheader(page)
        st.dataframe(data["features"].describe(include="all"))
    elif page == "Model Evaluation":
        st.subheader(page)
        st.json(data.get("metrics", {"status": "metrics.json missing"}))
    else:
        st.subheader(page)
        st.json(data.get("benchmark_report", {"status": "benchmark_report.json missing"}))


if __name__ == "__main__":
    main()
