"""Unit tests for interval arithmetic (FR-05, FR-14, FR-16, AC-03, AC-04, AC-05)."""

from datetime import UTC, datetime

from slotfinder.intervals import clip, intersect, merge, subtract


def t(hour: int) -> datetime:
    return datetime(2025, 1, 6, hour, tzinfo=UTC)


def test_merge_fuses_overlapping_intervals_ac04():
    """AC-04 / FR-14: overlapping intervals become their union."""
    assert merge([(t(11), t(13)), (t(10), t(12))]) == [(t(10), t(13))]


def test_merge_fuses_touching_intervals_ac03():
    """AC-03 / FR-05: half-open touching intervals leave no gap and fuse."""
    assert merge([(t(10), t(11)), (t(11), t(12))]) == [(t(10), t(12))]


def test_merge_removes_duplicates_ac05():
    """AC-05 / FR-14: duplicates collapse to one interval."""
    assert merge([(t(10), t(11)), (t(10), t(11))]) == [(t(10), t(11))]


def test_merge_keeps_separate_intervals_sorted_fr16():
    """FR-16: disjoint intervals are returned sorted and unfused."""
    assert merge([(t(14), t(15)), (t(10), t(11))]) == [(t(10), t(11)), (t(14), t(15))]


def test_merge_contained_interval_does_not_shrink_outer_fr14():
    """FR-14: an interval contained in another does not shorten the union."""
    assert merge([(t(10), t(15)), (t(11), t(12))]) == [(t(10), t(15))]


def test_merge_drops_empty_intervals_fr14():
    """FR-14: empty intervals carry no time and are dropped."""
    assert merge([(t(10), t(10))]) == []


def test_clip_restricts_to_window_fr15():
    """FR-15: clipping keeps only the part inside the window."""
    assert clip([(t(8), t(12)), (t(13), t(14)), (t(20), t(22))], t(10), t(13)) == [(t(10), t(12))]


def test_clip_drops_intervals_outside_ac08():
    """AC-08: intervals entirely outside the window vanish."""
    assert clip([(t(1), t(2)), (t(20), t(21))], t(10), t(13)) == []


def test_subtract_splits_base_around_cut_fr15():
    """FR-15: a cut inside the base splits it in two."""
    assert subtract([(t(9), t(17))], [(t(12), t(13))]) == [(t(9), t(12)), (t(13), t(17))]


def test_subtract_cut_touching_edges_keeps_boundaries_ac03():
    """AC-03: cutting [10,12) from [9,17) leaves slots touching the cut at 10 and 12."""
    assert subtract([(t(9), t(17))], [(t(10), t(12))]) == [(t(9), t(10)), (t(12), t(17))]


def test_subtract_cut_covering_base_leaves_nothing_fr15():
    """FR-15: a cut covering the base removes it."""
    assert subtract([(t(9), t(17))], [(t(8), t(18))]) == []


def test_subtract_cut_before_and_after_base_changes_nothing_fr15():
    """FR-15: cuts outside the base have no effect."""
    assert subtract([(t(9), t(17))], [(t(1), t(2)), (t(20), t(22))]) == [(t(9), t(17))]


def test_subtract_cut_overlapping_start_and_end_fr15():
    """FR-15: cuts overlapping each edge trim the base."""
    assert subtract([(t(9), t(17))], [(t(8), t(10)), (t(16), t(18))]) == [(t(10), t(16))]


def test_subtract_with_multiple_bases_fr15():
    """FR-15: each base interval is cut independently."""
    assert subtract([(t(1), t(5)), (t(8), t(12))], [(t(3), t(9))]) == [(t(1), t(3)), (t(9), t(12))]


def test_intersect_overlap_fr15():
    """FR-15: the intersection of overlapping ranges is their overlap."""
    assert intersect([(t(9), t(12))], [(t(10), t(17))]) == [(t(10), t(12))]


def test_intersect_touching_is_empty_fr05():
    """FR-05: ranges that only touch share no instant."""
    assert intersect([(t(9), t(10))], [(t(10), t(11))]) == []


def test_intersect_multiple_intervals_fr15():
    """FR-15: two lists with several ranges intersect pairwise."""
    left = [(t(1), t(4)), (t(6), t(10))]
    right = [(t(2), t(7)), (t(9), t(12))]
    assert intersect(left, right) == [(t(2), t(4)), (t(6), t(7)), (t(9), t(10))]


def test_intersect_with_empty_list_is_empty_fr15():
    """FR-15: intersecting with no time yields no time."""
    assert intersect([(t(1), t(4))], []) == []
