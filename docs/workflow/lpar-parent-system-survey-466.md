# LogicalPartition parent-system link survey — issue #466

**Finding: positive.** Every `LogicalPartition` the survey sampled — in the
single-entry read, the per-system feed and the fleet-wide feed — carries an
`AssociatedManagedSystem` element whose `href` is the bare
`.../rest/api/uom/ManagedSystem/<uuid>` of the partition's parent system. No
sampled partition omitted it, whatever its state (the sampled states are below).

## What was read

All requests were `GET`s through the read-only capture harness
(`scripts/live_test/capture.py` in raw mode behind `read_only_guard` from
`scripts/live_capture_sweep.py`). Raw answers stay private to the operator; the
fixture named below is tokenized with `scripts/live_capture_export.py`.

| Read, on one V10R3 HMC (M1060) managing 16 systems, 2026-10-12 | Result |
|---|---|
| `GET /rest/api/uom/ManagedSystem/<uuid>/LogicalPartition`, one per system | 77 entries, 77 with the element; every `href` is the queried system |
| `GET /rest/api/uom/LogicalPartition` (fleet-wide) | 77 entries, 77 with the element, 16 distinct parents; the 77 `href`s equal the per-system ones |
| `GET /rest/api/uom/LogicalPartition/<uuid>`, 40 partitions sampled | 40 of 40 with the element; each `href` equals the feed's |

The 77 partitions were 61 `running`, 13 `not activated` and 3 `open firmware`, so
the inactive case is covered on every path. Every `href` matched
`^https://<host>[:port]/rest/api/uom/ManagedSystem/<36-char uuid>$` with no
trailing path. The system UUID is lower case where the partition's own
`PartitionUUID` is upper case, so a comparison has to fold case.

The element is `<AssociatedManagedSystem kb="CUD" kxe="false" href="..." rel="related"/>`;
it has no text, and `href` is its only payload. `xmlutil.parse_feed` keeps it as
`{"href": ..., "rel": "related"}` under `Resource`.

## Earlier captures: V11R2 gives the same answer

The 2026-09-30 read-only sweep (#1202) of HMCs at V11R2 SP1120 holds the same three
reads. Four of its fleet-wide feeds carry 52, 90, 133 and 93 entries (368 in all)
and every entry has the element with an exact `ManagedSystem/<uuid>` `href`. Their
states include `running`, `not activated`, `open firmware` and `not available`.
Every per-system feed entry and every single-entry read in those captures has the
element too. Those raw files are private; the figures are counts of entries with
the element against entries in the feed.

## Schema version

All three representations print `schemaVersion="V1_0"` on the `LogicalPartition`
element, and `AssociatedManagedSystem` carries no `ksv` attribute. Elements added
after the base schema carry one (`V1_2_0` and later appear in the same bodies), so
the link belongs to the base `V1_0` schema, not to a later addition. The vendor
reference lists it for the partition on both generations
(`docs/refs/hmc-rest-api-p10/managed-system/145-logical-partition.md:97`,
`docs/refs/hmc-rest-api-p11/managed-system/165-logical-partition.md:97`).

## Not covered

A migrating partition was not sampled (the capture was read-only, so none was
induced, and none happened to be in flight), so whether the element survives a
migration is unobserved. Every sampled
partition reported `MigrationState` `Not_Migrating`.

## Evidence in the repository

- `tests/fixtures/live/rest-lpar-feed-per-system.json` — a tokenized per-system
  feed of one `running` and one `not activated` partition (capture
  `2026-10-12-q466`). Its partitions are renamed `sys-R13-lp1` and `sys-R13-lp2`:
  the exporter keeps a name's suffix, and these suffixes were not synthetic. The
  adapters' `MACAddressPrefix` values and the running partition's `Uptime` are
  zeroed for the same reason.
- `tests/fixtures/live/rest-lpar-entry.json` and `rest-lpar-entry-lp3.json` — the
  single-entry reads of `not activated` partitions (2026-09-29, 2026-09-30), which
  already carried the element.
- `tests/lpar/test_lpar_parent_system_link.py` pins all three.

The fleet-wide feed is not committed: it is 1.2 MB for 77 partitions, and its
entries carry the same links as the per-system feeds.

## What this does not change

No code reads the link. ADR 0094's bounded parent discovery stands; replacing it
with a read of this link is a separate decision (ADR 0092 §4).
