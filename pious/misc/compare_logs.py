from pio_logs import pio_log_to_df, final_iterations_df
from argparse import ArgumentParser
from typing import List
import pandas as pd
from os import path as osp


def compare_log_dfs(
    df1: List[pd.DataFrame], df2: List[pd.DataFrame], ip_ev=False, oop_ev=False
) -> pd.DataFrame:
    """
    Compare the given log dataframes
    """
    keys = ["Board"]
    if ip_ev:
        keys.append("EV IP")
    if oop_ev:
        keys.append("EV OOP")

    suffixes = (f"_{df1.iloc[0]['Description']}", f"_{df2.iloc[0]['Description']}")

    df_merged = pd.merge(df1[keys], df2[keys], on="Board", suffixes=suffixes)
    print(df_merged)


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("log1", help="First log")
    parser.add_argument("log2", help="Second log")
    parser.add_argument("--suffix1", help="Description for log1")
    parser.add_argument("--suffix2", help="Description for log2")
    parser.add_argument("--ip-ev", action="store_true", help="Compare IP EV")
    parser.add_argument("--oop-ev", action="store_true", help="Compare OOP EV")

    args = parser.parse_args()

    log1_description = osp.basename(args.log1).split(".")[0]
    log2_description = osp.basename(args.log2).split(".")[0]
    if args.suffix1:
        log1_description = args.suffix1
    if args.suffix2:
        log2_description = args.suffix2

    log1_df = final_iterations_df(pio_log_to_df(args.log1))
    log2_df = final_iterations_df(pio_log_to_df(args.log2))

    log1_df["Description"] = log1_description
    log2_df["Description"] = log2_description

    compare_log_dfs(log1_df, log2_df, args.ip_ev, args.oop_ev)
