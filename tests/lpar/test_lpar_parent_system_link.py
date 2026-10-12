"""A LogicalPartition names its parent managed system (#466).

Captured V10R3 answers: the single-entry read and the per-system feed carry an
``AssociatedManagedSystem`` link whose ``href`` ends at the ``ManagedSystem`` UUID.
The survey that backs these captures is ``docs/workflow/lpar-parent-system-survey-466.md``.
"""

from __future__ import annotations

import re

import pytest
from conftest import live_fixture

from hmcpctl.xmlutil import parse_feed

_PARENT_HREF = re.compile(r"^https://[^/]+/rest/api/uom/ManagedSystem/([0-9a-f-]{36})$")
_FEED = live_fixture("rest-lpar-feed-per-system")
_FEED_SYSTEM_UUID = _FEED["path"].split("/")[-2]


def _parent_uuid(entry: dict) -> str:
    link = entry["Resource"]["AssociatedManagedSystem"]
    match = _PARENT_HREF.fullmatch(link["href"])
    assert match, (
        f"AssociatedManagedSystem href is not a bare ManagedSystem URL: {link}"
    )
    return match.group(1)


def test_per_system_feed_entries_name_the_queried_system() -> None:
    entries = parse_feed(_FEED["body"])

    states = {entry["Resource"]["PartitionState"] for entry in entries}
    assert states == {"running", "not activated"}
    assert {_parent_uuid(entry) for entry in entries} == {_FEED_SYSTEM_UUID}


@pytest.mark.parametrize("name", ["rest-lpar-entry", "rest-lpar-entry-lp3"])
def test_single_entry_of_an_inactive_partition_names_its_system(name: str) -> None:
    (entry,) = parse_feed(live_fixture(name)["body"])

    assert entry["Resource"]["PartitionState"] == "not activated"
    assert _parent_uuid(entry)
