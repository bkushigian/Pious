CARDS = tuple(f"{r}{s}" for r in "AKQJT98765432" for s in "shdc")

ranks = {
    "2": 2,
    "3": 3,
    "4": 4,
    "5": 5,
    "6": 6,
    "7": 7,
    "8": 8,
    "9": 9,
    "T": 10,
    "J": 11,
    "Q": 12,
    "K": 13,
    "A": 14,
}


ranks_rev = {
    2: "2",
    3: "3",
    4: "4",
    5: "5",
    6: "6",
    7: "7",
    8: "8",
    9: "9",
    10: "T",
    11: "J",
    12: "Q",
    13: "K",
    14: "A",
}


def ahml(rank):
    if rank == 14:
        return "A"
    if rank > 9:
        return "H"
    if rank > 5:
        return "M"
    else:
        return "L"


def card_tuple(c):
    r, s = c.strip()
    return ranks[r], s
