"""Half-open interval arithmetic on aware datetimes (FR-05, FR-14, FR-16)."""

from datetime import datetime

Interval = tuple[datetime, datetime]


def merge(intervals: list[Interval]) -> list[Interval]:
    """Sort and fuse overlapping or touching intervals; drop empty ones."""
    result: list[Interval] = []
    for start, end in sorted(i for i in intervals if i[0] < i[1]):
        if result and start <= result[-1][1]:
            if end > result[-1][1]:
                result[-1] = (result[-1][0], end)
        else:
            result.append((start, end))
    return result


def clip(intervals: list[Interval], lo: datetime, hi: datetime) -> list[Interval]:
    """Restrict intervals to ''[lo, hi)'', dropping those that become empty."""
    clipped = [(max(start, lo), min(end, hi)) for start, end in intervals]
    return [i for i in clipped if i[0] < i[1]]


def subtract(base: list[Interval], cuts: list[Interval]) -> list[Interval]:
    """Return ''base'' minus ''cuts''; both inputs must be merged."""
    result: list[Interval] = []
    for start, end in base:
        cursor = start
        for cut_start, cut_end in cuts:
            if cut_end <= cursor:
                continue
            if cut_start >= end:
                break
            if cut_start > cursor:
                result.append((cursor, cut_start))
            cursor = max(cursor, cut_end)
            if cursor >= end:
                break
        if cursor < end:
            result.append((cursor, end))
    return result


def intersect(left: list[Interval], right: list[Interval]) -> list[Interval]:
    """Return the intersection of two merged interval lists."""
    result: list[Interval] = []
    i = j = 0
    while i < len(left) and j < len(right):
        start = max(left[i][0], right[j][0])
        end = min(left[i][1], right[j][1])
        if start < end:
            result.append((start, end))
        if left[i][1] < right[j][1]:
            i += 1
        else:
            j += 1
    return result
