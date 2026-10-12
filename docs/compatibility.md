# HMC compatibility

[Documentation index](index.md)

## What 0.1.0 supports

hmcpctl 0.1.0 claims live verification for exactly the 15 operations below, and for nothing
else in the catalog. Each passed a live run on HMC V10R3 M1060 managing a POWER9 system, and
the code that run exercised is unchanged at the release commit, so the verification ledger
reads `current` for it there. Another HMC level or machine model may answer differently. Together they cover the
[kdive Tier A contract](kdive-tier-a-contract.md)'s power, state and console reads, and the
[bare-CEC LPAR recipe](recipes/bare-cec-lpar.md).

| Operation | MCP tool |
|-----------|----------|
| `system.get` | `hmc_get_system` |
| `lpar.get` | `hmc_get_lpar` |
| `lpar.get_state` | `hmc_get_lpar_state` |
| `lpar.summary` | `hmc_lpar_summary` |
| `lpar.power_on` | `hmc_power_on_lpar` (partial) |
| `lpar.power_off` | `hmc_power_off_lpar` |
| `lpar.capture_console` | `hmc_capture_lpar_console` |
| `lpar.list_refcodes` | `hmc_read_lpar_refcodes` |
| `lpar.create` | `hmc_create_lpar` |
| `lpar.delete` | `hmc_delete_lpar` |
| `job.get` | `hmc_get_job` |
| `job.wait` | `hmc_wait_for_job` |
| `pcie.list_dedicated_slots` | `hmc_list_dedicated_pcie_slots` |
| `pcie.assign_dedicated_slot` | `hmc_assign_dedicated_pcie_slot` (partial) |
| `pcie.unassign_dedicated_slot` | `hmc_unassign_dedicated_pcie_slot` (partial) |

"Partial" is the catalog's implementation state: the operation implements some of the vendor
operation's variants, and the ledger names the ones it does not, such as network boot for
`lpar.power_on`. The claim covers only the implemented variants.

Every other tool in the catalog ships in 0.1.0 without a live-verification claim. Some were
verified at an earlier commit and have since gone stale, and some were never exercised live.
That includes the logical LPAR workflow tools (`hmc_inventory`, `hmc_plan_lpar`,
`hmc_power_lpar`, `hmc_inspect_lpar`, `hmc_operation_status`, `hmc_search_tools` and
`hmc_invoke_tool`), which belong to the work planned for 0.2.0.

The [verification ledger](capabilities/README.md#derived-staleness) is the authority for each
operation's state. On a checkout of the release tag, after `just setup`, run:

```bash
just verification-report
```

It prints one line per operation: its implementation state and its derived verification
state, which is `current`, `stale`, `failed`, `unevidenced` or `unrecorded`. Only `current`
means a passing live observation still applies. The state is derived when the report runs,
and an observation older than 90 days reads `stale`, so the same tag reports fewer `current`
operations as time passes even though its code does not change. The ledger's data is in
[`docs/capabilities/`](capabilities/README.md).

## HMC version compatibility

The checked reference corpus covers retained POWER10 and POWER11 command and REST
documentation snapshots. It is an evidence inventory, not a blanket compatibility
promise for every operation, HMC release, or managed system. Consult the
[HMC reference capability ledger](capabilities/README.md) for the corpus scope and
per-operation evidence, and the [generated tool reference](tools/index.md) for the
maturity currently published by the installed code.

Three VIOS backup catalog tools have a narrower floor:
`hmc_list_vios_backups`, `hmc_backup_vios`, and `hmc_restore_vios` require
**HMC V10 or newer**. Their supported HMC commands do not exist in the V9.1.940
command inventory, so these tools have no runtime version probe or V8/V9
fallback.

**`HMC_SCHEMA_VERSION` — leave this unset for normal operation.** It is opt-in
and unset by default, because HMC V8/V9 targets do not need it and uom
documents already declare `schemaVersion=V1_0`. Set it only to pin schema
negotiation explicitly — for example while debugging a read path.

Where the `X-HMC-Schema-Version` header goes when it *is* set. The rule is per
call site, not per HTTP method — there is no method whose requests all carry it
and none whose requests all omit it:

- **UOM requests carry it unless their own call site opts out.** A call site
  opts out by passing `include_schema_version=False`, so
  `rg -n 'include_schema_version=False' src/hmcpctl/client/` is the current set
  and the only answer that cannot go stale. Opting out was a response to HTTP
  406 on specific endpoints, not a property of any HTTP method or resource
  type: `PUT`/`POST LogicalPartition`, `PUT VirtualNetwork` and child-resource
  adapter `PUT` opt out, and so do many — **not all** — of the VolumeGroup and
  VirtualIOServer storage paths, reads included. Do not read a sibling
  endpoint's omission as covering yours; check the flag at the call site you
  are debugging.
- **Every `/rest/api/web/` request carries it**, reads and writes alike,
  because some HMC releases require it there.
- **Requests that build their own headers never carry it**, whatever this
  variable is set to. That is the `Accept: */*` discovery reads — quick
  properties, and the operation, schema and search-parameter listings, where
  ADR 0139 records the omission deliberately — and every `do/{Operation}`
  job, which is the path LPAR power on/off and activation take.

Unset — or set to the empty string, which disables the header the same way —
is therefore the setting under which no request carries it at all.

A live run prints the resolved value in its run header, on stdout, and records
the same string (`(not set)` when unset) as `run.schema_version` in the
`test-results-*.json` document. Each observation it emits records the same
string as `schema_version`, so an observation cited as evidence says which of
those two request environments produced it; observations stored before maturity
format 4 read `unrecorded` ([ADR 0186](adr/0186-observation-schema-version-stamp.md)).
See [`docs/environment-variables.md`](environment-variables.md) for all
supported variables.

### Firmware write-path compatibility

HMC V10R3 answers a UOM write with HTTP 406 when its `Accept` header names a uom
media type, and with 415 when its `Content-Type` does not name the resource type.
Shared UOM writes therefore send `Accept: */*` with a typed `Content-Type`, and
shared deletes send `Accept: */*` ([ADR 0178](adr/0178-uom-writes-send-untyped-accept.md)).

LPAR creation (`hmc_create_lpar`, `hmc_provision_lpar`) uses the REST create,
which V10R3 accepts for a document that follows its XSD and gives the partition
`default_profile` and a current configuration. It falls back to `mksyscfg` over
SSH when the REST create is refused with a 406 or with a 400 `REST0001` payload
rejection, logging the HMC's message, and always for a create with no memory or
processor values. `HMC_PASSWORD` (or `HMC_SSH_KEY_FILE`) must be set for SSH
auth; the fallback is transparent to the caller.
