import os
import re
import glob
from pathlib import Path
import numpy as np
import pandas as pd


REPO_ROOT = Path(__file__).resolve().parents[2]
BASE_ROOT = REPO_ROOT / "data"

SCENE1_DIR = os.path.join(BASE_ROOT, "workplace")
SCENE2_DIR = os.path.join(BASE_ROOT, "residential_apartment")
SCENE3_DIR = os.path.join(BASE_ROOT, "multistory_corridor")


def natural_key(path):
    """Sort numbered CSV files naturally rather than lexicographically."""
    name = os.path.basename(path)
    return [int(s) if s.isdigit() else s.lower() for s in re.split(r"(\d+)", name)]


def to_float(value):
    """Convert a CSV cell to float, returning NaN for invalid values."""
    try:
        return float(pd.to_numeric(value, errors="coerce"))
    except Exception:
        return np.nan


def list_csv_files(folder_path):
    files = sorted(glob.glob(os.path.join(folder_path, "*.csv")), key=natural_key)
    if len(files) == 0:
        print(f"[Warning] No CSV files found in: {folder_path}")
    return files


def read_power_first_cell(file_path):
    """Read power from the first CSV cell."""
    df = pd.read_csv(file_path, header=None)
    return to_float(df.iloc[0, 0])


def read_power_scene2_measured(file_path):
    """Read the measured residential-apartment power from row 2, column 3."""
    df = pd.read_csv(file_path, header=None)
    return to_float(df.iloc[1, 2])


def read_ber_log10(file_path, col_name="Log10_BER"):
    """Read log10(BER); the caller converts it to linear BER when needed."""
    df = pd.read_csv(file_path)

    if col_name in df.columns:
        return to_float(df[col_name].mean())

    return to_float(df.iloc[:, 1].mean())


def load_series(folder_path, reader_func):
    values = []
    for file_path in list_csv_files(folder_path):
        try:
            values.append(reader_func(file_path))
        except Exception as e:
            print(f"[Warning] Error reading {file_path}: {e}")
            values.append(np.nan)
    return np.array(values, dtype=float)


def mean_sd_str(values, decimals=2):
    """Format mean and sample standard deviation."""
    arr = np.asarray(values, dtype=float)
    arr = arr[np.isfinite(arr)]

    if len(arr) == 0:
        return "nan +/- nan"

    mean = np.mean(arr)
    sd = np.std(arr, ddof=1) if len(arr) > 1 else 0.0
    return f"{mean:.{decimals}f} +/- {sd:.{decimals}f}"


def sci_str(value):
    """Format BER in scientific notation."""
    if value is None or not np.isfinite(value):
        return "nan"
    return f"{value:.3e}"


def percent_str(value):
    if value is None or not np.isfinite(value):
        return "nan"
    return f"{value:.2f}%"


def willmott_ioa(measured, simulated):
    """
    Willmott index of agreement, IOA.
    measured: measured power
    simulated: simulated power
    """
    meas = np.asarray(measured, dtype=float)
    sim = np.asarray(simulated, dtype=float)

    mask = np.isfinite(meas) & np.isfinite(sim)
    meas = meas[mask]
    sim = sim[mask]

    if len(meas) == 0:
        return np.nan

    mean_meas = np.mean(meas)
    numerator = np.sum((sim - meas) ** 2)
    denominator = np.sum((np.abs(sim - mean_meas) + np.abs(meas - mean_meas)) ** 2)

    if denominator == 0:
        return 1.0

    return 1 - numerator / denominator


def sample_points_str(point_ids):
    """Format a compact sample-point range."""
    point_ids = np.asarray(point_ids, dtype=int)

    if len(point_ids) == 0:
        return "None"

    if len(point_ids) == 1:
        return f"{point_ids[0]} (n=1)"

    if np.all(np.diff(point_ids) == 1):
        return f"{point_ids[0]}-{point_ids[-1]} (n={len(point_ids)})"

    return f"{point_ids.tolist()} (n={len(point_ids)})"


def build_scene_dataframe(
    scene_dir,
    measured_power_reader,
    simulated_power_reader=read_power_first_cell,
    tail_points=None,
):
    """Load per-sample power and BER values for one experimental scene."""

    ber_dir = os.path.join(scene_dir, "BER_data")
    power_dir = os.path.join(scene_dir, "Power_data")

    power_no_meas = load_series(
        os.path.join(power_dir, "no_ris"),
        measured_power_reader
    )
    power_with_meas = load_series(
        os.path.join(power_dir, "with_ris"),
        measured_power_reader
    )
    power_no_sim = load_series(
        os.path.join(power_dir, "no_ris_sim"),
        simulated_power_reader
    )
    power_with_sim = load_series(
        os.path.join(power_dir, "with_ris_sim"),
        simulated_power_reader
    )

    ber_no_log10 = load_series(
        os.path.join(ber_dir, "no_ris"),
        lambda f: read_ber_log10(f, "Log10_BER")
    )
    ber_with_log10 = load_series(
        os.path.join(ber_dir, "with_ris"),
        lambda f: read_ber_log10(f, "Log10_BER")
    )

    min_len = min(
        len(power_no_meas),
        len(power_with_meas),
        len(power_no_sim),
        len(power_with_sim),
        len(ber_no_log10),
        len(ber_with_log10),
    )

    if min_len == 0:
        raise ValueError(f"No valid data found in scene folder: {scene_dir}")

    df = pd.DataFrame({
        "point_id": np.arange(1, min_len + 1),

        "power_no_meas": power_no_meas[:min_len],
        "power_with_meas": power_with_meas[:min_len],
        "power_no_sim": power_no_sim[:min_len],
        "power_with_sim": power_with_sim[:min_len],

        "ber_no_log10": ber_no_log10[:min_len],
        "ber_with_log10": ber_with_log10[:min_len],
    })

    df["gain_meas"] = df["power_with_meas"] - df["power_no_meas"]
    df["gain_sim"] = df["power_with_sim"] - df["power_no_sim"]

    df["ber_no"] = 10 ** df["ber_no_log10"]
    df["ber_with"] = 10 ** df["ber_with_log10"]

    if tail_points is not None:
        df = df.tail(tail_points).copy()

    return df


def summarize_subset(scene_label, subset_label, df_subset):
    if len(df_subset) == 0:
        return None

    ber_no_mean = np.nanmean(df_subset["ber_no"])
    ber_with_mean = np.nanmean(df_subset["ber_with"])

    if np.isfinite(ber_no_mean) and ber_no_mean != 0:
        ber_reduction_rate = (ber_no_mean - ber_with_mean) / ber_no_mean * 100
    else:
        ber_reduction_rate = np.nan

    ber_log10_reduction = np.nanmean(
        df_subset["ber_no_log10"] - df_subset["ber_with_log10"]
    )

    ioa_no = willmott_ioa(
        measured=df_subset["power_no_meas"],
        simulated=df_subset["power_no_sim"]
    )

    ioa_with = willmott_ioa(
        measured=df_subset["power_with_meas"],
        simulated=df_subset["power_with_sim"]
    )

    return {
        "Scene": scene_label,
        "Subset": subset_label,
        "Sample points": sample_points_str(df_subset["point_id"].values),

        "No-RIS simulated power (dBm)": mean_sd_str(df_subset["power_no_sim"]),
        "RIS simulated power (dBm)": mean_sd_str(df_subset["power_with_sim"]),
        "No-RIS measured power (dBm)": mean_sd_str(df_subset["power_no_meas"]),
        "RIS measured power (dBm)": mean_sd_str(df_subset["power_with_meas"]),

        "Simulated RIS gain (dB)": mean_sd_str(df_subset["gain_sim"]),
        "Measured RIS gain (dB)": mean_sd_str(df_subset["gain_meas"]),

        "No-RIS IOA": f"{ioa_no:.4f}" if np.isfinite(ioa_no) else "nan",
        "RIS IOA": f"{ioa_with:.4f}" if np.isfinite(ioa_with) else "nan",

        "No-RIS measured BER": sci_str(ber_no_mean),
        "RIS measured BER": sci_str(ber_with_mean),
        "BER reduction rate": percent_str(ber_reduction_rate),

        "BER reduction (log10 orders)": f"{ber_log10_reduction:.2f}"
        if np.isfinite(ber_log10_reduction) else "nan",
    }


def print_summary_table(title, rows):
    rows = [r for r in rows if r is not None]
    if len(rows) == 0:
        print(f"\n{title}: No valid rows.")
        return

    result_df = pd.DataFrame(rows)

    print("\n" + "=" * 120)
    print(title)
    print("=" * 120)
    print(result_df.to_string(index=False))
    print("=" * 120 + "\n")


def main():
    # --------------------------------------------------------
    # --------------------------------------------------------
    scene1_df = build_scene_dataframe(
        scene_dir=SCENE1_DIR,
        measured_power_reader=read_power_first_cell,
        simulated_power_reader=read_power_first_cell,
        tail_points=None
    )

    scene1_rows = []

    scene1_rows.append(
        summarize_subset(
            scene_label="Scene 1",
            subset_label="Total",
            df_subset=scene1_df
        )
    )

    for area_idx in range(5):
        start = area_idx * 12
        end = (area_idx + 1) * 12

        scene1_rows.append(
            summarize_subset(
                scene_label="Scene 1",
                subset_label=f"Area {area_idx + 1}",
                df_subset=scene1_df.iloc[start:end]
            )
        )

    print_summary_table(
        title="Scene 1: Total and five Areas",
        rows=scene1_rows
    )

    # --------------------------------------------------------
    # --------------------------------------------------------
    scene2_df = build_scene_dataframe(
        scene_dir=SCENE2_DIR,
        measured_power_reader=read_power_scene2_measured,
        simulated_power_reader=read_power_first_cell,
        tail_points=None
    )

    scene2_rows = [
        summarize_subset(
            scene_label="Scene 2",
            subset_label="Area 2",
            df_subset=scene2_df.iloc[:20]
        )
    ]

    print_summary_table(
        title="Scene 2: Area 2",
        rows=scene2_rows
    )

    # --------------------------------------------------------
    # --------------------------------------------------------
    scene3_df = build_scene_dataframe(
        scene_dir=SCENE3_DIR,
        measured_power_reader=read_power_first_cell,
        simulated_power_reader=read_power_first_cell,
        tail_points=20
    )

    scene3_rows = [
        summarize_subset(
            scene_label="Scene 3",
            subset_label="Selected last 20 points",
            df_subset=scene3_df
        )
    ]

    print_summary_table(
        title="Scene 3: Last 20 sampling points",
        rows=scene3_rows
    )


if __name__ == "__main__":
    main()
