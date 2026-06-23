import os
from pathlib import Path
import cv2
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from skimage.metrics import structural_similarity as ssim



REPO_ROOT = Path(__file__).resolve().parents[2]
VIDEO_DIR = REPO_ROOT / "hardware" / "usrp" / "media" / "videos"

ORIGINAL_VIDEO = str(VIDEO_DIR / "trans.ts")
RIS_VIDEO = str(VIDEO_DIR / "recv_with.mp4")
NO_RIS_VIDEO = str(VIDEO_DIR / "recv_without.mp4")

OUTPUT_DIR = REPO_ROOT / "outputs" / "video_quality"
FIG_NAME = "ssim_smoothness_score.png"
CSV_NAME = "quality_metrics.csv"

os.makedirs(OUTPUT_DIR, exist_ok=True)



def get_video_info(video_path):
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise FileNotFoundError(f"Cannot open video: {video_path}")

    fps = cap.get(cv2.CAP_PROP_FPS)
    frame_count = cap.get(cv2.CAP_PROP_FRAME_COUNT)
    duration = frame_count / fps if fps > 0 else 0

    cap.release()
    return fps, frame_count, duration


def read_frame_at_time(video_path, time_sec):
    """Read the closest decodable frame at a requested timestamp."""
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise FileNotFoundError(f"Cannot open video: {video_path}")

    cap.set(cv2.CAP_PROP_POS_MSEC, time_sec * 1000.0)
    ret, frame = cap.read()
    cap.release()

    if not ret or frame is None:
        return None

    return frame


def resize_to_reference(frame, ref_frame):
    """Resize a received frame to the reference resolution for SSIM."""
    h, w = ref_frame.shape[:2]
    return cv2.resize(frame, (w, h), interpolation=cv2.INTER_AREA)



def compute_ssim(ref_frame, test_frame):
    """Compute color-image SSIM on a 0-to-1 scale."""
    test_frame = resize_to_reference(test_frame, ref_frame)

    ref_rgb = cv2.cvtColor(ref_frame, cv2.COLOR_BGR2RGB)
    test_rgb = cv2.cvtColor(test_frame, cv2.COLOR_BGR2RGB)

    value = ssim(
        ref_rgb,
        test_rgb,
        channel_axis=2,
        data_range=255
    )

    return float(value)



def compute_blockiness(frame, block_size=8):
    """Estimate block artifacts from gradients at codec block boundaries."""
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY).astype(np.float32)
    h, w = gray.shape

    if h < block_size * 2 or w < block_size * 2:
        return 0.0

    diff_x = np.abs(np.diff(gray, axis=1))
    diff_y = np.abs(np.diff(gray, axis=0))

    cols = np.arange(1, w)
    boundary_cols = (cols % block_size == 0)
    inner_cols = ~boundary_cols

    rows = np.arange(1, h)
    boundary_rows = (rows % block_size == 0)
    inner_rows = ~boundary_rows

    if boundary_cols.sum() == 0 or boundary_rows.sum() == 0:
        return 0.0

    boundary_x = diff_x[:, boundary_cols].mean()
    inner_x = diff_x[:, inner_cols].mean()

    boundary_y = diff_y[boundary_rows, :].mean()
    inner_y = diff_y[inner_rows, :].mean()

    boundary_mean = 0.5 * (boundary_x + boundary_y)
    inner_mean = 0.5 * (inner_x + inner_y)

    blockiness = max(0.0, (boundary_mean - inner_mean) / (inner_mean + 1e-6))

    return float(blockiness)



def compute_freezing_penalty(
    prev_ref_frame,
    curr_ref_frame,
    prev_test_frame,
    curr_test_frame,
    motion_threshold=2.0,
    freeze_ratio_threshold=0.45
):
    """Return a 0-to-1 freeze penalty from relative inter-frame motion."""
    if prev_ref_frame is None or prev_test_frame is None:
        return 0.0

    curr_test_frame = resize_to_reference(curr_test_frame, curr_ref_frame)
    prev_test_frame = resize_to_reference(prev_test_frame, prev_ref_frame)

    prev_ref_gray = cv2.cvtColor(prev_ref_frame, cv2.COLOR_BGR2GRAY).astype(np.float32)
    curr_ref_gray = cv2.cvtColor(curr_ref_frame, cv2.COLOR_BGR2GRAY).astype(np.float32)

    prev_test_gray = cv2.cvtColor(prev_test_frame, cv2.COLOR_BGR2GRAY).astype(np.float32)
    curr_test_gray = cv2.cvtColor(curr_test_frame, cv2.COLOR_BGR2GRAY).astype(np.float32)

    ref_motion = np.mean(np.abs(curr_ref_gray - prev_ref_gray))
    test_motion = np.mean(np.abs(curr_test_gray - prev_test_gray))

    if ref_motion < motion_threshold:
        return 0.0

    motion_ratio = test_motion / (ref_motion + 1e-6)

    penalty = (freeze_ratio_threshold - motion_ratio) / freeze_ratio_threshold
    penalty = np.clip(penalty, 0.0, 1.0)

    return float(penalty)



def robust_normalize(values):
    """Normalize with the 5th and 95th percentiles for outlier resistance."""
    values = np.asarray(values, dtype=np.float32)

    low = np.percentile(values, 5)
    high = np.percentile(values, 95)

    if high - low < 1e-8:
        return np.zeros_like(values)

    norm = (values - low) / (high - low)
    return np.clip(norm, 0.0, 1.0)


def compute_smoothness_score(freeze_penalty, blockiness_penalty):
    """Combine freeze and block-artifact penalties into a 0-to-100 score."""
    score = 100.0 * (1.0 - 0.60 * freeze_penalty - 0.40 * blockiness_penalty)
    return float(np.clip(score, 0.0, 100.0))



def evaluate_pair(original_video, test_video, time_points):
    records = []

    prev_ref_frame = None
    prev_test_frame = None

    for t in time_points:
        ref_frame = read_frame_at_time(original_video, t)
        test_frame = read_frame_at_time(test_video, t)

        if ref_frame is None or test_frame is None:
            continue

        test_frame_resized = resize_to_reference(test_frame, ref_frame)

        ssim_value = compute_ssim(ref_frame, test_frame_resized)

        raw_blockiness = compute_blockiness(test_frame_resized)

        freeze_penalty = compute_freezing_penalty(
            prev_ref_frame,
            ref_frame,
            prev_test_frame,
            test_frame_resized
        )

        records.append({
            "time_sec": t,
            "ssim": ssim_value,
            "freeze_penalty": freeze_penalty,
            "raw_blockiness": raw_blockiness
        })

        prev_ref_frame = ref_frame
        prev_test_frame = test_frame_resized

    return pd.DataFrame(records)



def save_snapshot_grid(
    original_video,
    ris_video,
    no_ris_video,
    save_dir,
    times=(0, 6, 12, 18, 24)
):
    """Save timestamped frames and a reference/RIS/no-RIS comparison grid."""
    snapshot_dir = os.path.join(save_dir, "snapshots")
    os.makedirs(snapshot_dir, exist_ok=True)

    video_items = [
        ("Original", original_video),
        ("With RIS", ris_video),
        ("Without RIS", no_ris_video)
    ]

    all_rgb_frames = []

    for row_name, video_path in video_items:
        row_frames = []

        for t in times:
            frame = read_frame_at_time(video_path, t)
            if frame is None:
                raise RuntimeError(f"Cannot read frame from {video_path} at {t}s")

            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            row_frames.append(rgb)

            single_name = f"{row_name.replace(' ', '_')}_{int(t):02d}s.png"
            single_path = os.path.join(snapshot_dir, single_name)

            cv2.imwrite(single_path, frame)

        all_rgb_frames.append(row_frames)

    fig, axes = plt.subplots(
        nrows=3,
        ncols=len(times),
        figsize=(2.2 * len(times), 5.4),
        dpi=300
    )

    for r, (row_name, _) in enumerate(video_items):
        for c, t in enumerate(times):
            axes[r, c].imshow(all_rgb_frames[r][c])
            axes[r, c].axis("off")

            if r == 0:
                axes[r, c].set_title(f"{t}s", fontsize=10)

            if c == 0:
                axes[r, c].set_ylabel(row_name, fontsize=11)

    plt.tight_layout()
    grid_path = os.path.join(save_dir, "snapshot_grid.png")
    # plt.savefig(grid_path, dpi=600, bbox_inches="tight")
    plt.close()

    print(f"Saved snapshots to: {snapshot_dir}")
    print(f"Saved snapshot grid to: {grid_path}")



def plot_quality_curve(df, save_path):
    """Plot SSIM and smoothness for RIS-assisted and baseline videos."""

    ris = df[df["case"] == "With RIS"]
    no_ris = df[df["case"] == "Without RIS"]

    plt.rcParams["font.family"] = "Times New Roman"
    plt.rcParams["axes.linewidth"] = 1.0

    fig, ax1 = plt.subplots(figsize=(8.0, 4.6), dpi=300)
    ax2 = ax1.twinx()

    bar_width = 0.09

    ax2.bar(
        ris["time_sec"] - bar_width / 2,
        ris["smoothness_score"],
        width=bar_width,
        color="red",
        alpha=0.25,
        label="Smoothness score with RIS",
        zorder=1
    )

    ax2.bar(
        no_ris["time_sec"] + bar_width / 2,
        no_ris["smoothness_score"],
        width=bar_width,
        color="black",
        alpha=0.22,
        label="Smoothness score without RIS",
        zorder=1
    )

    ax1.plot(
        ris["time_sec"],
        ris["ssim"],
        color="red",
        linewidth=2.0,
        marker="o",
        markersize=3.0,
        markevery=4,
        label="SSIM with RIS",
        zorder=3
    )

    ax1.plot(
        no_ris["time_sec"],
        no_ris["ssim"],
        color="black",
        linewidth=2.0,
        marker="s",
        markersize=3.0,
        markevery=4,
        label="SSIM without RIS",
        zorder=3
    )

    # ax1.set_xlabel("Time (s)", fontsize=12)
    # ax1.set_ylabel("SSIM", fontsize=12)
    # ax2.set_ylabel("Smoothness score", fontsize=12)

    ax1.set_xlim(0, 30)
    ax1.set_ylim(0, 1.02)
    ax2.set_ylim(0, 105)

    ax1.set_xticks(np.arange(0, 31, 5))
    ax1.grid(True, linestyle="--", linewidth=0.6, alpha=0.35)

    ax1.tick_params(axis="both", labelsize=11)
    ax2.tick_params(axis="y", labelsize=11)

    lines_1, labels_1 = ax1.get_legend_handles_labels()
    lines_2, labels_2 = ax2.get_legend_handles_labels()

    # ax1.legend(
    #     lines_1 + lines_2,
    #     labels_1 + labels_2,
    #     loc="lower left",
    #     fontsize=9,
    #     frameon=False,
    #     ncol=1
    # )

    plt.tight_layout()
    # plt.savefig(save_path, dpi=600, bbox_inches="tight")
    plt.show()
    # plt.close()

    # print(f"Saved figure to: {save_path}")



def main():
    _, _, duration_ori = get_video_info(ORIGINAL_VIDEO)
    _, _, duration_ris = get_video_info(RIS_VIDEO)
    _, _, duration_no_ris = get_video_info(NO_RIS_VIDEO)

    duration = min(duration_ori, duration_ris, duration_no_ris, 30.0)

    sample_interval = 0.25
    time_points = np.arange(0, duration, sample_interval)

    print("Evaluating video with RIS...")
    df_ris = evaluate_pair(ORIGINAL_VIDEO, RIS_VIDEO, time_points)
    df_ris["case"] = "With RIS"

    print("Evaluating video without RIS...")
    df_no_ris = evaluate_pair(ORIGINAL_VIDEO, NO_RIS_VIDEO, time_points)
    df_no_ris["case"] = "Without RIS"

    df_all = pd.concat([df_ris, df_no_ris], ignore_index=True)

    df_all["blockiness_penalty"] = robust_normalize(df_all["raw_blockiness"].values)

    df_all["smoothness_score"] = [
        compute_smoothness_score(freeze, block)
        for freeze, block in zip(
            df_all["freeze_penalty"].values,
            df_all["blockiness_penalty"].values
        )
    ]

    csv_path = os.path.join(OUTPUT_DIR, CSV_NAME)
    df_all.to_csv(csv_path, index=False)
    print(f"Saved metrics to: {csv_path}")

    fig_path = os.path.join(OUTPUT_DIR, FIG_NAME)
    plot_quality_curve(df_all, fig_path)


    # save_snapshot_grid(
    #     original_video=ORIGINAL_VIDEO,
    #     ris_video=RIS_VIDEO,
    #     no_ris_video=NO_RIS_VIDEO,
    #     save_dir=OUTPUT_DIR,
    #     times=(6, 12, 18, 24, 30)
    # )


if __name__ == "__main__":
    main()
