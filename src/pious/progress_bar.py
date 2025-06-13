import sys
from typing import Callable, Optional
import time

_PROGRESS_BAR_NESTING = 0


def progress_bar(
    it,
    prefix: str | Callable = "",
    size: int = 60,
    inc: Optional[int] = None,
    out=sys.stdout,
    track_time: bool = True,
):
    """
    Print a progress bar

    Taken from https://stackoverflow.com/a/34482761
    """
    global _PROGRESS_BAR_NESTING
    if _PROGRESS_BAR_NESTING > 0:
        print(file=out, flush=True)
    _PROGRESS_BAR_NESTING += 1
    count = len(it)
    if track_time:
        start_time = time.time()
    if inc is None:
        inc = 1
        if count > 1000:
            inc = count // 100

    def eta(j):
        if track_time:
            elapsed = time.time() - start_time
            if j > 0:
                return f" {elapsed:.1f}/{elapsed * (count / j):.1f}s"
            return ""
        return ""

    if count == 0:
        print(
            f"{prefix}[{u'█'*size}] {0}/{0} ({100.0:3.2f}%){eta(0)}",
            file=out,
            flush=True,
        )
        return

    def show(j):
        x = int(size * j / count)
        print(
            f"{prefix}[{u'█'*x}{('.'*(size-x))}] {j}/{count} ({100*j/count:3.2f}%){eta(j)}     ",
            end="\r",
            file=out,
            flush=True,
        )

    show(0)
    for i, item in enumerate(it):
        yield item
        if (i + 1) % inc == 0:
            show(i + 1)
    _PROGRESS_BAR_NESTING -= 1
    if _PROGRESS_BAR_NESTING > 0:
        print("\033[4A")
    print("\n", flush=True, file=out)
