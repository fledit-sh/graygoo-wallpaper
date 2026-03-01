import argparse
import json
import os
from dataclasses import dataclass

DEFAULT_ROWS_PER_COLUMN = 24
MIN_ROWS_PER_COLUMN = 5


@dataclass
class GridDimensions:
    columns: int
    rows: int
    column_width: float
    row_spacing: float


def env_int(name: str, default: int) -> int:
    value = os.getenv(name)
    if value is None:
        return default
    try:
        return int(value)
    except ValueError as exc:
        raise ValueError(f"Environment variable {name} must be an integer, got {value!r}.") from exc


def load_config(path: str | None) -> dict:
    if not path:
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def compute_max_rows(height: int, font_size: int) -> int:
    # Keep enough vertical space to avoid overlap while allowing dense layouts.
    min_safe_spacing = max(1, font_size + 1)
    return max(MIN_ROWS_PER_COLUMN, height // min_safe_spacing)


def validate_rows_per_column(rows_per_column: int, height: int, font_size: int) -> int:
    max_rows = compute_max_rows(height, font_size)
    if rows_per_column < MIN_ROWS_PER_COLUMN:
        raise ValueError(
            f"rows_per_column must be >= {MIN_ROWS_PER_COLUMN}; got {rows_per_column}."
        )
    if rows_per_column > max_rows:
        raise ValueError(
            f"rows_per_column must be <= {max_rows} for canvas height={height} and font size={font_size}; "
            f"got {rows_per_column}."
        )
    return rows_per_column


def derive_grid_dimensions(width: int, height: int, font_size: int, rows_per_column: int) -> GridDimensions:
    """
    Derive grid dimensions from canvas size and row density.

    Row spacing and column width stay coupled so text remains readable.
    """
    validate_rows_per_column(rows_per_column, height, font_size)

    # Primary control: rows_per_column governs vertical density.
    row_spacing = height / rows_per_column

    # Couple horizontal spacing with row spacing to preserve readability.
    column_width = max(font_size * 0.6, row_spacing * 0.55)

    rows = max(1, int(height // row_spacing))
    columns = max(1, int(width // column_width))
    return GridDimensions(
        columns=columns,
        rows=rows,
        column_width=column_width,
        row_spacing=row_spacing,
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Compute wallpaper text grid dimensions.")
    parser.add_argument("--width", type=int, default=1920)
    parser.add_argument("--height", type=int, default=1080)
    parser.add_argument("--font-size", type=int, default=24)
    parser.add_argument("--config", type=str, default=None, help="Optional JSON config file.")
    parser.add_argument(
        "--rows-per-column",
        type=int,
        default=None,
        help=f"Target row count per column (default: {DEFAULT_ROWS_PER_COLUMN}, env: ROWS_PER_COLUMN).",
    )
    return parser.parse_args()


def resolve_rows_per_column(args: argparse.Namespace, config: dict) -> int:
    if args.rows_per_column is not None:
        raw_rows = args.rows_per_column
    elif "rows_per_column" in config:
        raw_rows = int(config["rows_per_column"])
    elif "ROWS_PER_COLUMN" in config:
        raw_rows = int(config["ROWS_PER_COLUMN"])
    else:
        raw_rows = env_int("ROWS_PER_COLUMN", DEFAULT_ROWS_PER_COLUMN)

    return validate_rows_per_column(raw_rows, args.height, args.font_size)


def main() -> None:
    args = parse_args()
    config = load_config(args.config)
    rows_per_column = resolve_rows_per_column(args, config)
    grid = derive_grid_dimensions(args.width, args.height, args.font_size, rows_per_column)

    print(
        json.dumps(
            {
                "width": args.width,
                "height": args.height,
                "font_size": args.font_size,
                "rows_per_column": rows_per_column,
                "columns": grid.columns,
                "rows": grid.rows,
                "column_width": round(grid.column_width, 3),
                "row_spacing": round(grid.row_spacing, 3),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
