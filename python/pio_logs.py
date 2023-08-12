""" 
pio_logs.py: parse output logs of PIO
"""
from math import nan
from argparse import ArgumentParser
import pandas as pd

ranks = "23456789TJQKA"
suits = "shcd"

KEYS = (
    "Board",
    "running time",
    "EV OOP",
    "EV IP",
    "OOP's MES",
    "IP's MES",
    "Exploitable for",
)
DELTABLE_KEYS = ("EV OOP", "EV IP", "OOP's MES", "IP's MES", "Exploitable for")
KEYS_WITH_DELTAS = (
    "Board",
    "Iteration",
    "running time",
    "EV OOP",
    "dEV OOP",
    "EV IP",
    "dEV IP",
    "OOP's MES",
    "dOOP's MES",
    "IP's MES",
    "dIP's MES",
    "Exploitable for",
    "dExploitable for",
    "Stop reason",
)


def card_to_tuple(card):
    return ranks.index(card[0]), suits.index(card[1])


def sort_board(board):
    cards = [board[i : i + 2] for i in range(0, len(board), 2)]
    return "".join(sorted(cards, key=lambda c: card_to_tuple(c), reverse=True))


def add_row_deltas(parsed_data, stop_reasons):
    new_data = {}

    for file in parsed_data:
        stop_reason = stop_reasons.get(file, "unknown")
        new_rows = []
        new_data[file] = new_rows
        last_row = None
        for idx, row in enumerate(parsed_data[file]):
            new_row = row.copy()
            new_rows.append(new_row)
            new_row["Iteration"] = idx + 1
            new_row["Stop reason"] = stop_reason
            for key in KEYS:
                if last_row is None:
                    new_row[make_delta_key(key)] = row[key]
                elif key in DELTABLE_KEYS:
                    new_row[make_delta_key(key)] = row[key] - last_row[key]
            last_row = row
    return new_data


def pio_log_to_df(log_file: str) -> pd.DataFrame:
    with open(log_file) as f:
        log = f.read()
    return parse_log(log)


def parse_log(log: str):
    files = {}
    stop_reasons = {}
    current_file = None
    current_rows = None
    row = None
    board = None
    for line_no, line in enumerate(log.split("\n")):
        line = line.strip()

        if not line:
            continue
        if line.startswith("Solving "):
            current_file, current_rows = line[8:], []
            board = current_file.split("\\")[-1][:-4]
            board = sort_board(board)
            files[current_file] = current_rows
            continue

        elif "SOLVER: started" in line:
            continue

        elif line == "SOLVER:":
            row = {"Board": board}
            current_rows.append(row)
            continue

        elif "SOLVER: stopped" in line:
            stop_reasons[current_file] = line.split(": ")[-1]
            continue

        #  We have a key-value pair
        try:
            key, value = line.split(": ")
        except Exception as e:
            print("Exception:", e)
            print(f"Line {line_no + 1}: `{line}`")
            raise e
        row[key] = float(value)
    with_deltas = add_row_deltas(files, stop_reasons)
    return parsed_data_to_df(with_deltas)


def parsed_data_to_df(parsed_data):
    all_rows = []

    for file in parsed_data:
        rows = parsed_data[file]
        for row in rows:
            all_rows.append(row)

    df = pd.DataFrame(all_rows, columns=KEYS_WITH_DELTAS)
    return df


def fmt(x):
    if isinstance(x, float):
        return f"{x:>12.3f}"
    else:
        return f"{x:>12}"


def make_delta_key(key):
    return "d" + key


def df_to_csv(df, filename="output.csv"):
    df.to_csv(filename, index=False)


def final_iterations_df(df: pd.DataFrame):
    """
    Get a df with only the final iterations for each board
    """
    max_idx = df.groupby("Board")["Iteration"].transform(max) == df["Iteration"]
    return df[max_idx]


def print_final_iterations(df: pd.DataFrame):
    df = final_iterations_df(df)
    # Now, add a final row called 'Average'
    averages = df.iloc[:, 1:-1].mean(axis=0)
    average_row = ["Average"] + averages.tolist() + ["---"]
    df.loc[len(df)] = average_row
    print(df.to_string(index=False))


def print_parsed_data(parsed_data, header_every_file=False, last_line_only=False):
    header = ", ".join([fmt(k) for k in KEYS_WITH_DELTAS])
    if not header_every_file:
        print(header)
    for file in parsed_data:
        if header_every_file:
            print()
            print(header)
        rows = parsed_data[file]
        for row in rows:
            print(", ".join([f"{fmt(row.get(k, ''))}" for k in KEYS_WITH_DELTAS]))


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("piolog", help="Pio log to parse")
    parser.add_argument(
        "--header-per-board", action="store_true", help="print a header for every board"
    )
    parser.add_argument(
        "--last-line-only",
        "-l",
        action="store_true",
        help="Only print the last line for each board",
    )

    args = parser.parse_args()

    with open(args.piolog) as f:
        log = f.read()

    df = parse_log(log)

    if args.last_line_only:
        print_final_iterations(df)
    else:
        print(df.to_string(index=False))
