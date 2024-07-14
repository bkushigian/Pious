from collections import namedtuple

def color_texture(texture):
    """
    Return a coloration of a texture
    """

    red = "00"
    green = "00"
    blue = "00"

    if "MONOTONE" in texture:
        red = "ff"
    elif "FD" in texture:
        red = "cc"
    elif "RAINBOW" in texture:
        red = "00"
    else:
        print(f"Warning: Unrecognized suitedness {texture}")

    if "STRAIGHT" in texture:
        green = "ff"
    elif "OESD" in texture:
        green = "88"
    elif "GUTSHOT" in texture:
        green = "33"
    elif "DISCONNECTED" in texture:
        green = "00"
    else:
        print(f"Warning: Unrecognized connectedness {texture}")

    if "TOAK" in texture:
        blue = "ff"
    elif "PAIRED" in texture:
        blue = "99"
    elif "UNPAIRED" in texture:
        blue = "00"
    else:
        print(f"Warning: Unrecognized pairedness {texture}")

    return f"#{red}{green}{blue}"


def marker_size_from_high_card(flop, max_size=None, min_size=10):
    if max_size is None:
        max_size = 220
    r, s = card_tuple(flop.split()[0])
    factor = (max_size / min_size) ** (1 / 12)
    size = min_size * factor ** (r - 2)
    return size



Info = namedtuple("Info", ["player", "node_id", "line", "starting_stacks"])


def parse_info(info: str):
    lines = info.splitlines()
    player = lines[0].strip().split()[0]
    node_id = lines[1][9:].strip()
    line = lines[3][6:].strip()
    starting_stacks = int(lines[4].split(":")[1].strip())
    return Info(player, node_id, line, starting_stacks)
