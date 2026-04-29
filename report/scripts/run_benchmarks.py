#!/usr/bin/env python3
import csv
import statistics
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
RESULTS_FILE = ROOT / "report" / "results.csv"
FIGURES_DIR = ROOT / "report" / "figures"

PROBLEM_SIZES = [100000000, 200000000, 300000000]
PARALLEL_PROCESSES_FOR_SIZE_TEST = 5
FIXED_N = 200000000
PROCESS_COUNTS = [3, 5, 10, 15]
REPEATS = 1


def parse_program_output(output):
    values = {}
    for line in output.strip().splitlines():
        key, value = line.split(",", 1)
        values[key] = value
    return values


def run_command(command, cwd):
    completed = subprocess.run(
        command,
        cwd=cwd,
        check=True,
        text=True,
        capture_output=True,
    )
    return parse_program_output(completed.stdout)


def run_measurement(mode, n, processes):
    times = []
    prime_count = None

    for _ in range(REPEATS):
        if mode == "sequential":
            output = run_command(["./prime_sequential", str(n)], ROOT / "sequential")
        else:
            output = run_command(
                ["mpirun", "--oversubscribe", "-np", str(processes), "./prime_parallel", str(n)],
                ROOT / "parallel",
            )

        times.append(float(output["time_seconds"]))
        prime_count = int(output["prime_count"])

    return {
        "mode": mode,
        "n": n,
        "processes": processes,
        "prime_count": prime_count,
        "time_seconds": statistics.median(times),
    }


def write_results(rows):
    RESULTS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with RESULTS_FILE.open("w", newline="") as csv_file:
        writer = csv.DictWriter(
            csv_file,
            fieldnames=["mode", "n", "processes", "prime_count", "time_seconds"],
        )
        writer.writeheader()
        writer.writerows(rows)


def svg_bar_chart(title, labels, series, ylabel, output_path, baseline=None):
    width = 900
    height = 520
    margin_left = 80
    margin_right = 30
    margin_top = 70
    margin_bottom = 90
    plot_width = width - margin_left - margin_right
    plot_height = height - margin_top - margin_bottom
    colors = ["#2563eb", "#16a34a", "#f97316", "#9333ea"]

    all_values = [value for _, values in series for value in values]
    if baseline is not None:
        all_values.append(baseline[1])
    max_value = max(all_values) if all_values else 1.0
    max_value = max(max_value * 1.15, 0.000001)

    def y(value):
        return margin_top + plot_height - (value / max_value) * plot_height

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="white"/>',
        f'<text x="{width / 2}" y="32" text-anchor="middle" font-family="Arial" font-size="22" font-weight="700">{title}</text>',
        f'<text x="22" y="{height / 2}" text-anchor="middle" font-family="Arial" font-size="14" transform="rotate(-90 22 {height / 2})">{ylabel}</text>',
        f'<line x1="{margin_left}" y1="{margin_top}" x2="{margin_left}" y2="{margin_top + plot_height}" stroke="#111827"/>',
        f'<line x1="{margin_left}" y1="{margin_top + plot_height}" x2="{margin_left + plot_width}" y2="{margin_top + plot_height}" stroke="#111827"/>',
    ]

    for tick in range(6):
        value = max_value * tick / 5
        tick_y = y(value)
        parts.append(f'<line x1="{margin_left - 5}" y1="{tick_y:.2f}" x2="{margin_left + plot_width}" y2="{tick_y:.2f}" stroke="#e5e7eb"/>')
        parts.append(f'<text x="{margin_left - 10}" y="{tick_y + 4:.2f}" text-anchor="end" font-family="Arial" font-size="12">{value:.6f}</text>')

    group_width = plot_width / len(labels)
    bar_gap = 10
    bar_width = (group_width - 2 * bar_gap) / len(series)

    for series_index, (name, values) in enumerate(series):
        for label_index, value in enumerate(values):
            x = margin_left + label_index * group_width + bar_gap + series_index * bar_width
            bar_y = y(value)
            bar_height = margin_top + plot_height - bar_y
            parts.append(f'<rect x="{x:.2f}" y="{bar_y:.2f}" width="{bar_width - 4:.2f}" height="{bar_height:.2f}" fill="{colors[series_index % len(colors)]}"/>')
            parts.append(f'<text x="{x + (bar_width - 4) / 2:.2f}" y="{bar_y - 5:.2f}" text-anchor="middle" font-family="Arial" font-size="11">{value:.6f}</text>')

    if baseline is not None:
        baseline_name, baseline_value = baseline
        baseline_y = y(baseline_value)
        parts.append(f'<line x1="{margin_left}" y1="{baseline_y:.2f}" x2="{margin_left + plot_width}" y2="{baseline_y:.2f}" stroke="#dc2626" stroke-width="2" stroke-dasharray="8 6"/>')
        parts.append(f'<text x="{margin_left + plot_width - 8}" y="{baseline_y - 8:.2f}" text-anchor="end" font-family="Arial" font-size="13" fill="#dc2626">{baseline_name}: {baseline_value:.6f}s</text>')

    for index, label in enumerate(labels):
        x = margin_left + index * group_width + group_width / 2
        parts.append(f'<text x="{x:.2f}" y="{height - 45}" text-anchor="middle" font-family="Arial" font-size="13">{label}</text>')

    legend_x = margin_left
    for index, (name, _) in enumerate(series):
        x = legend_x + index * 190
        parts.append(f'<rect x="{x}" y="45" width="14" height="14" fill="{colors[index % len(colors)]}"/>')
        parts.append(f'<text x="{x + 20}" y="57" font-family="Arial" font-size="13">{name}</text>')

    parts.append("</svg>")

    output_path.write_text("\n".join(parts))


def generate_figures(rows):
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)

    sequential_by_n = {
        row["n"]: row["time_seconds"]
        for row in rows
        if row["mode"] == "sequential" and row["n"] in PROBLEM_SIZES
    }
    parallel_by_n = {
        row["n"]: row["time_seconds"]
        for row in rows
        if row["mode"] == "parallel"
        and row["processes"] == PARALLEL_PROCESSES_FOR_SIZE_TEST
        and row["n"] in PROBLEM_SIZES
    }

    svg_bar_chart(
        "Comparatie timp executie in functie de n",
        [str(n) for n in PROBLEM_SIZES],
        [
            ("Secvential", [sequential_by_n[n] for n in PROBLEM_SIZES]),
            (f"Paralel ({PARALLEL_PROCESSES_FOR_SIZE_TEST} procese)", [parallel_by_n[n] for n in PROBLEM_SIZES]),
        ],
        "Timp (secunde)",
        FIGURES_DIR / "timp_in_functie_de_n.svg",
    )

    parallel_by_processes = {
        row["processes"]: row["time_seconds"]
        for row in rows
        if row["mode"] == "parallel" and row["n"] == FIXED_N
    }
    sequential_baseline = next(
        row["time_seconds"]
        for row in rows
        if row["mode"] == "sequential" and row["n"] == FIXED_N
    )

    svg_bar_chart(
        f"Scalare pentru n={FIXED_N}",
        [str(processes) for processes in PROCESS_COUNTS],
        [("Paralel", [parallel_by_processes[processes] for processes in PROCESS_COUNTS])],
        "Timp (secunde)",
        FIGURES_DIR / "timp_in_functie_de_procese.svg",
        baseline=("Secvential", sequential_baseline),
    )


def main():
    rows = []

    for n in PROBLEM_SIZES:
        rows.append(run_measurement("sequential", n, 1))
        rows.append(run_measurement("parallel", n, PARALLEL_PROCESSES_FOR_SIZE_TEST))

    for processes in PROCESS_COUNTS:
        if processes != PARALLEL_PROCESSES_FOR_SIZE_TEST:
            rows.append(run_measurement("parallel", FIXED_N, processes))

    rows.sort(key=lambda row: (row["n"], row["mode"], row["processes"]))
    write_results(rows)
    generate_figures(rows)

    print(f"Rezultatele au fost scrise in {RESULTS_FILE}")
    print(f"Graficele au fost scrise in {FIGURES_DIR}")


if __name__ == "__main__":
    main()
