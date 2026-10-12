# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/). The six-name
`hmcpctl.api` facade is defined by ADR 0118; record changes to it under ordinary release
categories. Domain-module APIs remain pre-release and are not facade movement.

## [Unreleased]

## [0.1.0] - 2026-10-12

First tagged release. It ships the `hmcpctl` CLI, the MCP server, and the Python library. Its
stable Python API is the six-name `hmcpctl.api` facade (ADR 0118); every other module is a
pre-release domain API. The release claims live verification for 15 operations, listed with
how to check any other operation's state in
[`docs/compatibility.md`](docs/compatibility.md#what-010-supports).

The entries below record the development that preceded the tag. Defect fixes made before the
tag are not itemized, because no earlier release shipped the defects; each is in the commit
history under its issue number, and the behavior it settled is described in the guides and the
generated tool reference. An entry that reports live verification describes a run at an earlier
commit; the verification ledger, not this changelog, says which observations still apply.

### Added

- MCP server and CLI for the IBM HMC REST API, the supported `hmcpctl.api` facade, and the
  ownership-stamp workflow operations.
- Live verification of the PCM preference, metric and partition-template operations (#634).
  Round2's subtask 5 asserts what those reads return, and subtask 12 no longer toggles the
  managed system's long-term monitor flag. A new opt-in `pcm` arm, `scripts/live_pcm.py`
  (subtask 38), toggles each of the five PCM collection flags and restores all five to the
  read it took first; preflight lists it. The nine operations gain maturity records, and
  their reference rows now name only the endpoints each one requests.
- Live verification of the partition-profile, LPAR-property, memory-pool and memory-affinity
  operations (#627). It runs through a new `profiles` arm, `scripts/live_profiles.py`
  (subtasks 0, 4, 10 and 15), the only arm that runs the system-wide profile backup and
  type-3 merge-restore. Each round trip restores the value it read first. The maturity
  catalog records:
  - passed observations for 17 of these operations, on V10R3/POWER9 and, for the
    capability-gated affinity reads, V11R2/POWER11;
  - a failed `lpar.set_msp`: the tool cannot resolve a VIOS (#1318);
  - a failed `lpar_profile.restore`: the merge resets a not-activated partition's
    `resource_config`.

  Their capability-ledger rows now name the commands they issue.

- `hmc_inspect_lpar` (operation `lpar.inspect`, `read`) reports one LPAR's state, RMC,
  resources (memory and processor figures, and the storage mappings its system's VIOSes hold
  for it), up to 20 reference codes and profile drift, with `next_actions` naming tools only.
  It reads as `hmc_get_lpar`, and each section is authorized as the tool it uses and reports
  `ok`, `unavailable` or `denied`. It never opens a console; `profile_drift` is `unavailable`
  until a read-only profile read exists (#1224, ADR 0200).
- `hmc_power_lpar` (operation `lpar.power`, `destructive`) starts, stops or restarts one LPAR as
  a durable logical operation: one journaled HMC job, a bounded wait, and a verified host power
  state, with `already_in_state` when nothing needed doing. `mode=immediate` must be stated;
  graceful is PowerOff `osshutdown`. `start` is authorized as `hmc_power_on_lpar` and
  `stop`/`restart` as `hmc_power_off_lpar`, per partition, on every call. A resumed operation
  never submits a second power job (#1223, ADR 0199).
- `hmc_plan_lpar` (operation `lpar.plan`, `read`) plans provisioning one LPAR without writing
  or reserving anything: the selected system, VIOS and volume group, a `plan_digest`, each
  candidate's blockers, the intended changes and what it could not verify. `placement`
  evaluates at most 16 systems. It needs every tool it reads, and each read is authorized as
  that tool for its system or VIOS; a denied target is a `denied` blocker (#1221, ADR 0198).
- `hmc_inventory` (operation `inventory.logical`, `read`) lists one connection's systems and
  partitions with stable `<connection>/<uuid>` ids, state, capacity and owner, paged by
  `cursor` (at most 16 systems and 200 partitions a page). Each part is authorized as the
  tool it delegates to and reported per system as `ok`, `unavailable` or `denied`; enumerating
  systems needs `hmc_list_systems`, or pass `systems` selectors (#1220, ADR 0196).
- `hmc_search_tools` (operation `tools.search`, `read`) finds the tools this server exposes by
  intent, or returns one tool's input schema by exact name, at most 20 per call.
  `hmc_invoke_tool` (operation `tools.invoke`, `destructive`) calls one of them by name through
  that tool's own validation, authorization and audit, returning `{name, result}`; it refuses
  the gateway tools, `arbitrary-command` tools and arguments over 64 KiB. `tools/list` now
  carries a `catalog-tier` metadata entry, `primary` or `secondary`, without changing what is
  listed (#1219, ADR 0189).
- `hmc_operation_status` (operation `operation.status`) pages through this agent's logical
  operations in a new local SQLite store under `HMCPCTL_STATE_DIR` (ADR 0190), which the
  logical LPAR tools will record their HMC writes in and resume from (#1218, ADR 0195).
- `hmc_dump_restart_lpar` (operation `lpar.dump_restart`) crashes a partition and takes a
  platform dump: the PowerOff job with `operation=dumprestart`. It still refuses unless
  `allow_dump_restart=true`. It is a separate tool so an access policy can grant the ordinary
  stop without the crash (#896, ADR 0188).
- `hmcpctl report utilization --csv PATH` surveys every configured profile read-only and writes
  per-system, per-HMC and fleet CPU and memory allocation, idle reserved capacity, and failed
  profiles (#1252, ADR 0184).
- `hmcpctl report utilization` adds VIOS disk capacity (internal and SAN; assigned and free),
  I/O slot occupancy and SR-IOV logical ports per system and in each roll-up, appended after
  `notes` (#1253, ADR 0185).
- `hmcpctl report utilization --html PATH` writes the same survey as one self-contained,
  printable HTML page: fleet tiles, a per-HMC table, a sortable per-system table and failed
  profiles, with no network references. `--csv` is now optional; give either or both (#1254).
- A tracked read-only capture pipeline and an offline gate over it (#1202).
  `scripts/live_capture_sweep.py` calls every read-only MCP tool and a declared list of
  raw GETs and `ls*` commands against one HMC profile, below a guard that refuses any
  other REST method (logon and logoff excepted) or CLI command before it is sent.
  `scripts/live_capture_export.py` tokenizes the private output, failing closed when a
  name, host, address, serial, location code, session or SSH key survives, and derives the
  committed vocabularies under `tests/fixtures/live/vocabulary/`: one vocabulary and one
  schema enum list per HMC release and system, from the 2026-09-30 sweeps of V10R3 with
  POWER9 and V11R2 with POWER9, POWER10 and two POWER11 systems. `scripts/live_test/capture.py`
  gains a raw mode for the sweep, which keeps secret-bearing answers for the exporter and
  refuses a destination inside any git work tree; the default stays wholesale.
  `just live-vocabulary` (a `static` member with its prek hook) fails when a schema-enum
  element value in `src/` or `tests/` is neither captured nor an enum value, or when a
  REST read or `ls*` command in `src/` has no capture; job `Status` values are checked
  against the documented job statuses. Unfixed cases are listed in `allowlist.json` with
  their reasons, and a deliberately non-HMC test value carries
  `# live-vocabulary: allow <reason>` on its line.
- SR-IOV inventory reads answer on the environments the 2026-09-30 captures admit, per ADR 0183.
  `hmc_list_sriov_adapters`, `hmc_set_sriov_adapter_mode`'s current-mode check and their CLI
  commands answer on HMC V11R2 SP1120 with POWER9 9009-42A, POWER11 9824-42A or 9242-21B, as
  well as V10R3 M1060 with 8375-42A. Physical- and logical-port inventory answer on V11R2 with
  9009-42A as well; on the POWER11 pairs they report `capability-unavailable` because no
  SR-IOV-mode adapter is captured there. SR-IOV and vNIC mutations stay on V10R3 M1060 with 8375-42A, and their
  refusal now says no mutation is captured anywhere else. LPAR
  creation with SR-IOV or vNIC assignments refuses before creating the partition anywhere else.
- `docs/api-patterns.md` records the HMC REST and CLI behaviour verified live on V10R3 with
  POWER9 hardware: the 47 patterns from the #1161 capture windows and four observations from
  the #879 window, grouped by envelope, identifiers, links, media types, jobs, error codes,
  schema and CLI output. Each row names the capture commit and the hmcpctl code that conforms
  or diverges, with the fixing issue or PR (#1161).
- A capture harness for live probes, `scripts/live_test/capture.py`. `capture(path)` records
  every REST request and SSH command hmcpctl makes inside the block as one JSON line, drops
  session headers and redacts logon exchanges and secret-bearing text before writing, and
  refuses a destination git does not ignore; `.gitignore` now ignores `*.capture.jsonl` and
  `hmc-captures/` (#1161).
- `tests/fixtures/live/` holds 15 tokenized captures from the #1161 windows, each citing its
  capture, and these guessed mocks now replay them: the shared job entry is a captured
  `JobResponse` with a numeric JobID that differs from its entry UUID; the guessed
  `COMPLETED` job reads in the template, server-tool, storage, LPM and client tests are the
  captured `COMPLETED_OK` read, and the client's running reads the captured `RUNNING` one;
  quick `PartitionState` answers are JSON-quoted, an unowned slot's owner is `null`, and refcode
  timestamps read `MM/DD/YYYY HH:MM:SS`. New tests feed the captured 404 REST0005,
  400 REST000E and job-feed refusals through the job read paths, and the captured LPAR
  create, read and miss through the client (#1161).
- Live observations for the v0.1.0 bare-CEC path, from the #879 window at `90c97b5f` on HMC
  V10R3 with a POWER9 (8375-42A) system: `lpar.create`, `pcie.list_dedicated_slots`,
  `pcie.assign_dedicated_slot`, `lpar.power_on`, `lpar.get_state`, `job.get`, `job.wait`,
  `lpar.list_refcodes`, `lpar.capture_console`, `lpar.power_off`,
  `pcie.unassign_dedicated_slot` and `lpar.delete`, plus refreshed observations for the eight
  inventory reads. `just verification-report` reports 20 operations `current` and none stale.
  `lpar.power_on` is recorded `partial`: network boot is #868. `docs/recipes/bare-cec-lpar.md`
  now records the outcomes of its verbatim run (#879).
- The power-path `ownership_override` cost is now stated as the source has it: the partition
  resolution plus one partition-name GET, with no SSH command and no managed-system name read.
  Corrected in the `_power_on` docstring and `docs/environment-variables.md`, and ADR 0092 §4
  carries a dated amendment naming `resolve_and_authorize_lpar_mutation` (#1135).
- `hmc_power_off_lpar`, `lpars power-off` and `power_lpar` now write an `lpar-power-off` audit
  record, at `WARNING`, immediately before the PowerOff job is submitted: the resolved
  partition, the HMC host, and the `operation`, `immediate` and `restart` values sent, so a
  `dumprestart` crash is distinguishable from a graceful stop. A call refused by validation or
  the ownership guard writes none (ADR 0180, #895). The decommission workflow's own PowerOff
  (`hmc_decommission_lpar`, `lpars decommission`, `decommission_lpar`) writes one too, with
  `operation` `shutdown`, `restart` false and the `immediate` it sends; an already-off
  partition or a dry run writes none (#1115).
- `hmc_power_on_lpar`, `lpars power-on --keylock` and `power_on_lpar`/`power_lpar` accept an
  optional PowerOn `keylock` of `manual` or `norm` (normal) — the job's own spelling, not the
  creation-time `normal`/`manual`/`auto` — refused before any HMC call, including when the
  partition is already running. Omitted, the PowerOn document is unchanged and the HMC keeps
  choosing the position (#894).
- SR-IOV logical-port assignment refuses a capacity that is not a multiple of the physical
  port's Ethernet capacity granularity (`min_eth_capacity_granularity`) before any HMC change,
  naming both values; a port that reports no granularity is unchanged. SR-IOV physical-port
  inventory now fills `minimum_capacity_granularity_percent` (#1035).
- `lpars provision` and `hmc_provision_lpar` report where the network adapter and storage
  mapping they add now live: a `change_location` result field, read once after
  those steps rather than through the standalone adapter/storage operations, in the same shape
  and CLI rendering as `adapters add-network` (#1056).
- `storage attach-disk` and `hmc_attach_disk_to_lpar` report where the new mapping lives: a
  `change_location` result field, read once before the storage leg, in the same shape and CLI
  rendering as `lpars provision`; null with a warning when the read fails (#1069).
- Adapter and mapping commands say where their change lives. `adapters add-network`,
  `add-vscsi`, `add-vfc` and `delete`, and `storage map`, `mount-optical-media`, `detach-mapping`
  and `unmount-optical-media`, read the partition's `CurrentProfileSync` before the write and
  report it: `On` means the HMC also writes the change to the partition's current profile;
  `Disabled` or `Suspended` means it lives only in the current configuration. The MCP tools
  carry it as a `change_location` object or a closing sentence. `lpars power-on
  --partition-profile` and `hmc_power_on_lpar` now return `warnings` naming each current virtual
  SCSI, Fibre Channel or Ethernet client adapter whose slot that profile lacks, and still
  activate (#981).
- `WritableConsoleSession`, a `ConsoleSession` subclass, writes to a partition console
  (ADR 0176). `write(data)` sends raw bytes while collection keeps running. `send_sysrq(key,
  prefix=...)` sends the prefix plus the key as one write; the prefix defaults to Ctrl-O since
  #1149. `async with session.raw_mode() as channel:` gives a
  preempting holder, such as KGDB, exclusive reads and writes while the vterm stays held, and
  returns the channel to the collector afterwards. Every write first emits a `console-write`
  audit record that carries the length and never the bytes. `ConsoleSession`, the bounded
  capture and `hmc_capture_lpar_console` keep sealed stdin, and no MCP tool or CLI command
  writes (#958).
- Console connections send SSH keepalives, so a dead but idle channel is detected within about
  60 s (ADR 0174). `ConsoleSession(..., reconnect=True)` then acquires the console again and
  yields a `ConsoleGap` marker before the new stream. A console still held after the drop raises
  `ConsoleHeldAfterDropError`, a `ConsoleHeldError`, with no `rmvterm`; with `take_over=True`
  the reconnect reclaims it. The bounded capture never reconnects, but on a dead idle channel it
  now ends with `stop_reason="error"` instead of waiting for its idle or duration bound (#977).
- `hmcpctl lpars capture-console LPAR --system SYSTEM` takes the same bounded, input-free console
  capture as the MCP tool `hmc_capture_lpar_console`, with the same `--duration`, `--max-bytes`
  and `--idle-timeout` defaults and limits. It writes raw bytes to stdout or to a new `--output`
  file, reports the stop reason and `released` on stderr, and exits 0, 1, 2 or 3 as ADR 0175
  states; 3 means the console may still be held. The bare-CEC recipe now captures the console
  with it. The MCP tool and the command share one selector resolver (#959).
- `ConsoleSession` can yield the console to a preempting hold in two named modes (ADR 0173).
  `async with session.hand_over() as handover:` moves the channel to an in-process holder while
  the session keeps the vterm held, with no release gap. `suspend()` releases the vterm with the
  usual `rmvterm` and probe proof for an external holder, and `resume()` acquires it again. It
  raises `ConsoleHeldError`, issuing no `rmvterm`, if the slot was taken. The collector's
  `read()` waits while paused. `close()` of a suspended session issues no `rmvterm`. The bounded
  capture is unchanged (#976).
- `hmcpctl storage mount-optical-media` and `unmount-optical-media` mount and unmount an ISO
  from a VIOS media repository on an LPAR. The LPAR ISO installation recipe,
  `docs/recipes/lpar-iso-install.md`, uses them with `hmcpctl lpars capture-console` to create,
  provision, ISO-boot, observe, and clean up an LPAR. The ISO recipe ran live on 2026-09-23 on
  a patched build; it names the open issues that block it on `main` and the three HMC CLI steps
  it still needs (#776).

- `hmcpctl.ssh.console.ConsoleSession`, a read-only hold on one partition's console with no
  duration or byte cap: `open()`, iterate raw bytes, `close()`. `close()` releases the vterm with
  the same `rmvterm` and independent-probe proof as the bounded capture and reports `released`.
  The session runs the release to completion when cancelled. ADR 0170 states which process
  exits leave the console held. `capture_lpar_console` is now built on the session with the same
  signature and results. One exception: if its task is cancelled during the final release, the
  capture now raises `CancelledError` after the release, as ADR 0072 documents. It is a
  pre-release domain-module API, not a `hmcpctl.api` export (#974).

- A bare-CEC LPAR recipe, `docs/recipes/bare-cec-lpar.md`: create a partition, assign a
  dedicated PCIe slot, activate it to SMS, read its state and reference codes, power it off,
  unassign the slot and delete it, using installed `hmcpctl` commands only. It is unverified until
  the v0.1.0 live window runs it (#877).

- A kdive Tier A contract page, `docs/kdive-tier-a-contract.md`: the pre-release
  `hmcpctl.operations.lpar` imports, kdive's `PowerAction` mapped onto PowerOn and PowerOff job
  parameters, the read-only console capture and its `released` flag, and the ownership and SSH
  host-key settings. A structural test checks every name the page uses (#878).

- A `bare-cec` live-test arm, `scripts/live_bare_cec.py`. It creates a partition with explicit
  processing units, assigns a dedicated slot through `hmc_assign_dedicated_pcie_slot`, records a
  PowerOn that names no profile, and activates the partition to SMS against its own profile. It
  then inspects that job, reads reference codes and captures the console. It runs the PowerOff
  variants, unassigns the slot and deletes the partition. Each of its ten operations is recorded
  as a promotable observation. It reuses the dedicated arm's `LIVE_TEST_DEDICATED_PCIE_*` keys and
  requires `HMC_AUTHORIZE_POWER_OPERATIONS=true`. `LIVE_TEST_ACCEPT_PLATFORM_DUMP=true` opts into
  the `dumprestart` step. A results document written before this key existed no longer restores
  artifacts into a subset run; the runner warns and continues (#876).

- `hmc_power_off_lpar`, `power_lpar` and `hmcpctl lpars power-off` accept the PowerOff job's
  `restart` and `operation` parameters. `operation` is a closed set — `shutdown`, `osshutdown`,
  `dumprestart` — refused before any XML is built; the vendor's fourth value `dumpretry` is
  documented but not accepted. `dumprestart` crashes the partition and takes a platform dump, so
  it is refused unless the caller passes `allow_dump_restart` / `--allow-dump-restart`
  (ADR 0164, #872).

- `hmc_read_lpar_refcodes` and `hmcpctl lpars refcodes` read a partition's most recent reference
  codes over SSH, bounded to 1-100 and projected onto `lpar_name`, `time_stamp` and `refcode`.
  Read-only and needing no virtual terminal, so an activation can be followed by polling alone
  (#874).

- `HMCClient.list_search_parameters(resource_type)` reads the search-parameter names an HMC defines
  for a resource type, at `/rest/api/uom/{R}/search`, returning them with the response's
  `X-HMC-Schema-Version`. The names are the `ParameterName` texts of the `SearchParameterSet` the
  anchor answers with, captured at `V1_17_0` and `V1_20_0` across eleven types. A type that defines
  no search parameters returns an empty list — six of the eleven do; the names are `None` rather
  than a list when the level's answer is not a fact about the type, which is a 204 or a
  `SearchParameterSet` holding parameters this parse cannot name, whether they carry an empty
  `ParameterName` or no `ParameterName` at all (ADR 0144). A 200 carrying no
  `SearchParameterSet` at all raises `HMCError`, as does a level that does not serve the anchor,
  carrying its status. **No captured level serves a child-anchored form:** the reference documents
  `/rest/api/uom/{P}/{UUID}/{C}/search` and the HMC answers it 400 `INVALID_URL` while serving the
  plain child feed and `/quick` on the same parent, so no parent arguments are offered
  (ADR 0142, #789).

- `HMCClient.search_uom` takes a keyword-only `validate=False`. With `validate=True` a property
  name the resource type does not define raises `ValueError` before any request is sent, checked
  against the names `list_search_parameters` reports; those are read once per type and cached for
  the client's lifetime, and a level where the read yields no names validates nothing rather than
  raising. A type that defines none is refused locally instead — every name of it, with a message
  saying so (ADR 0144). Off by default, because the client is constructed per tool call, so the
  cache would rarely be reused. The round trip it saves is a 500, not the 400 the design was
  written against (ADR 0142, #789).

- `HMCClient.get_quick_property` takes a keyword-only `validate=False`. With `validate=True` an
  unknown property name raises `ValueError` before any request is sent, checked against the names
  `list_quick_properties` reports for the resource type; those are read once per type and cached for
  the client's lifetime, and a level where the read yields no names validates nothing rather than
  raising. A type that defines none is refused locally instead — every name of it, with a message
  saying so (ADR 0144). Off by default, because the client is constructed per tool call
  (ADR 0141, #799).

- `HMCClient.list_quick_properties(resource_type, *, parent_type=None, parent_uuid=None)` reads
  the quick-property names an HMC defines for a resource type, at the root anchor
  `/rest/api/uom/{R}/quick` and the child anchor `/rest/api/uom/{P}/{UUID}/{C}/quick`. It returns
  those names paired with the response's `X-HMC-Schema-Version`, that second element being `None`
  when the HMC sends no such header
  (ADR 0139, ADR 0140, #788). The body is an Atom `<entry>` wrapping a `QuickProperty_Collection`,
  and the names are the `Nickname` texts. A type that defines no quick properties returns an empty
  list — a 200 carrying the container with neither a `QuickProperty` nor a `Nickname` element under
  it; the names are `None` rather
  than a list when the level's answer is not a fact about the type, which is a 204 or a
  `QuickProperty_Collection` holding properties this parse cannot name, whether they carry an empty
  `Nickname` or no `Nickname` at all (ADR 0144). A 200 carrying no
  `QuickProperty_Collection` at all raises `HMCError`, because without the container it is
  indistinguishable from the HMC's known `HttpErrorResponse` feed (#811). The returned header value
  is verbatim and is not guaranteed to hold a version. Confirmed against FW950: 39 names for
  `ManagedSystem`, 28 for `LogicalPartition`, and the returned names resolve when fed back to
  `get_quick_property`. Anchor availability is per type — `NetworkBridge` answers 400 at the root
  and 200 as a child.
  **There is no `/quick/all`** — that anchor answers 400, so no `all_properties` argument is
  offered; the differently capitalized `/quick/All` is a separate endpoint returning per-instance
  values, not names.

- `xmlutil.find_all_text(xml_text, *names)`, the all-matches sibling of `find_text`, returning the
  text of every element whose local name matches instead of only the first.

- `HMCClient.list_operations(resource_type, *, parent_type=None, parent_uuid=None)` reads
  the job operations an HMC defines for a resource type, at the root anchor
  `/rest/api/uom/{R}/operations` and the child anchor
  `/rest/api/uom/{P}/{UUID}/{C}/operations`. It returns the parsed feed paired with the
  response's `X-HMC-Schema-Version`, or `None` when the HMC sends none (ADR 0139, #787).
  The feed is one `OperationSet` per anchor holding every operation the type defines, not
  one entry per operation, and repeated elements within it collapse to a bare dict when the
  HMC sends exactly one — see the method's docstring before iterating the result. The
  returned header value is verbatim and is not guaranteed to be a version string. Not
  available on every firmware level: V1_20_0 HMCs answered 500.

- Transport and inventory contract tests bound to the F1 reference corpus
  (`rest:logon-and-logoff`, `rest:job-status`): logon PUT endpoint and method,
  `LogonRequest`/`LogonResponse` media types, X-API-Session token propagation,
  UOM Accept/Content-Type header behaviour, and complete terminal-status vocabulary
  including `EXCEPTION` and `COMPLETED_WITH_ERROR`. Eight inventory operations
  (`system.get`, `lpar.list`, `lpar.get`, `vios.list`, `console.list_resources`,
  `system.summary`, `lpar.summary`, `console.info`) now emit `record_verified`
  observations from the live runner, adding maturity evidence for seven operations
  and recording the firmware-500 gap for `console.info` on this hardware (#625).

- `docs/capabilities/maturity.json` carries its first live observation, from the
  harness shake-down run against V10R3 / POWER10 hardware: `console.info`, result
  `failed`, on an HMC firmware defect serializing a null `Session/SessionId` property.
  The row derives as `stale (closure-changed)` rather than `failed` on current `main`,
  because the operation's import closure moved after the observation was taken — the
  staleness rule working as designed, not a recording error (#708).

- `python -m hmcpctl` now runs the CLI, as an alias for the `hmcpctl` console script wherever
  the `app` extra is installed — like the console script, it needs that extra and fails the
  same way without it. It delegates to the same entry point and takes no arguments of its own,
  so the two remain one program; the program name Typer reports differs. One difference does
  matter operationally: `-m` places the current working directory first on `sys.path`, where
  the console script does not, so prefer `hmcpctl` for a served process and use
  `python -P -m hmcpctl` (or `PYTHONSAFEPATH=1`) when launching from a directory you do not
  control. The live audit proof uses it because the generated console script cannot be relied
  on to exec with stderr closed once the interpreter path is long enough that `uv` emits a
  `/bin/sh` trampoline (#709, ADR 0128).
- A warning-level `install-submitted` audit event now carries the remote PID returned by a
  detached `installios` submission to served operators (#544, ADR 0109).
- Serve startup now submits a warning-level `power-ownership-guard` audit record for every
  policy-reachable connection, preserving the effective guard value when the permissions
  inspection tool is withheld (#533, ADR 0107).
- Seven bounded SSH-backed VIOS label tools list, set, and remove individual FC-port
  labels and list, create, update, and remove individual vFC group labels using the
  POWER10 and POWER11 `lslabelvios`/`labelvios` grammar. They do not expose MSP,
  vNIC, vSCSI, override-default, bulk-removal, or adapter-mutation behavior. Issue
  #559 tracks live-system field and mutation evidence not established by the manuals.
  The matching `hmcpctl vios` commands are `list-fc-port-labels`,
  `set-fc-port-label`, `remove-fc-port-label`, `list-vfc-group-labels`,
  `create-vfc-group-label`, `update-vfc-group-label`, and `remove-vfc-group-label`.
- `ManagedSystemPatch` and `LpmMigrationRequest` provide reusable typed request
  values for managed-system configuration and LPM destination inputs.
- `VirtualNetworkResult` exposes the resolved managed-system UUID beside the
  resource returned by `create_virtual_network`.
- `DecommissionBlastRadius` and `DecommissionAdapterRecord` expose the fixed
  `DecommissionResult.blast_radius` inventory schema to reusable Python callers.
- `StorageMapResult` records the authorized LPAR UUID beside the resource returned by
  `map_storage`, so library and CLI callers no longer resolve the partition independently
  before the guarded storage operation (ADR 0104).
- `VolumeGroup`, `OpticalMedia`, and `StorageMapping` provide stable storage
  inventory values for reusable Python callers (ADR 0117).
- Opt-in ADR 0011 ownership guard on LPAR power operations (#371, ADR 0092 §4): the new
  `authorize_power_operations` setting (`HMC_AUTHORIZE_POWER_OPERATIONS`, TOML profile key
  `authorize_power_operations`) defaults to `false`, leaving the `power_lpar` call path
  unchanged and opening no SSH connection. When `true`, `power_lpar` reads the ownership
  token before submitting the job and refuses a partition another agent owns; it accepts a
  new `ownership_override` parameter with the same audited semantics as its guarded
  siblings. `system_name_or_uuid` stays optional (ADR 0063): the guard routes through
  ADR 0094's shared resolve chain, which derives the owning managed system by bounded
  parent discovery when the caller omits it and confirms the partition lives on the
  named system when they supply it. `hmc_power_on_lpar`, `hmc_power_off_lpar`, and
  `hmcpctl lpars power-on` / `power-off` gained the matching `ownership_override`
  argument, and the two CLI commands gained `--system`, which replaces the fleet walk
  with one read. `provision_lpar` passes the override on its own activation leg, which
  targets the partition that workflow just created and stamped. Both new parameters move
  the frozen public signature digest.
- `HMCConfig.from_mapping(values)`: environment-isolated construction for library
  consumers (#368, ADR 0096). `HMCConfig` is a pydantic-settings model with
  `env_prefix="HMC_"`, so the ordinary constructor resolves every field a caller leaves
  unset from the ambient process environment — right for the CLI and the MCP server,
  wrong for a process building one config per HMC from database rows, where a stray
  `HMC_HOST` silently retargets a backend, a stray `HMC_SSH_KEY_FILE` offers the wrong
  key, and a stray `HMC_AGENT_ID` corrupts ADR 0011 ownership attribution.
  `from_mapping` reads no environment variable and no dotenv file; every field the
  mapping omits takes its declared default. `load_profile` is unchanged —
  environment-over-TOML precedence on the operator path is deliberate. **Note:**
  `_env_file=None` is *not* an isolation mechanism — it suppresses a dotenv source, never
  the environment, and `HMCConfig` configures no dotenv source at all, so it does nothing.
  `docs/environment-variables.md` gains a "Library Consumers" section covering precedence
  and the isolation pattern.
- Cross-process job polling: the `get_job` and `wait_for_job` operations in the new
  `hmcpctl.operations_jobs` module, plus the `JobOutcome` facade export (#364, ADR 0093). The
  supported handle for a job is two persistable strings — `job_id` and an optional `job_href` —
  so a consumer can store them, restart, construct a fresh `HMCClient`, and poll from a different
  process than the one that submitted the work. A job the HMC no longer knows about (reaped,
  deleted, or never present) now returns `found=False` instead of an opaque HTTP 404 `HMCError`,
  which is what lets a restarted worker tell "still running" from "gone". `JobOutcome` gained the
  `found: bool` and `job_href: str | None` fields. Neither has a default — that keeps both in the
  `required` set of the MCP output schema the wait tools share — so any direct construction of
  `JobOutcome` from the previous five fields must now supply them. Its field set is a package-owned
  model contract under ADR 0029, except `job`, which stays an opaque HMC resource mapping. The
  handle and `found` semantics above describe outcomes returned by `get_job` and `wait_for_job`;
  the submitting operations share the type but report a submission, so their `job_id` may be a
  synthetic label and their `found=False` means "this submission returned no job entry"
  (ADR 0093 clause 3).
- `set_lpar_ownership_description` operation and facade export (#376, ADR 0066).
- Strict LPAR ownership stamping (#377, ADR 0067): `provision_lpar` accepts a new
  `stamp_policy` field on `LparCreation` with literal alternatives `"best-effort"` (default) and
  `"required"`.
- Audit sink emits a `tls-verification-disabled` event when TLS verification is off, as
  controlled by `HMC_VERIFY_SSL` (#379).
- `list_lpar_ownership` operation, facade export, and `hmc_list_lpar_ownership` MCP tool
  (#375, ADR 0071): parsed ADR 0011 ownership per LPAR from the REST bulk list feed — one
  call covers every partition on a managed system. Partitions with no description
  (REST `<Description>` element absent), a non-token description (`unparsed`), and a valid
  ownership stamp (`owned`/`owner`) are reported as distinct facts; none are dropped.
- Bounded, non-interactive LPAR console capture: `capture_lpar_console`
  operation, `ConsoleCapture` / `ConsoleHeldError` facade exports, and the
  `hmc_capture_lpar_console` MCP tool (#385, ADR 0072). Runs `mkvterm` over a
  dedicated asyncssh process session with stdin sealed by construction (no
  code path can write to the partition console), enforces client-side
  duration/max-bytes/idle bounds, returns raw bytes (truncation never splits a
  multi-byte UTF-8 or incomplete ANSI escape sequence), detects vterm
  contention by the recorded stdout sentinel (exit code is always 0), and
  runs `rmvterm` on every exit path — with `released` true only after an
  independent-session mkvterm probe proves the slot free. Designed from the
  P1–P8 live-hardware prototype recorded on #385 (HMC V10R3 M1060); only idle
  partition streams were observed live, so the ANSI truncation rule is
  protocol-derived.
- Facade exports for four operations ADR 0029's selection rule already covered but the manifest
  omitted: `list_optical_mappings`, `mount_optical_media`, `unmount_optical_media` (shipped
  unexported by #205) and `assess_post_activation_affinity` (shipped unexported by #318) (#363).
  A contract test now applies the selection rule to every `operations_*` module by introspection
  and replaces the hand-written module-to-names map that could not detect the omission, since the
  same edit maintained both the map and `__all__`. **Consumer note:** ADR 0092 §3.2 records
  `mount_optical_media` and `unmount_optical_media` as ownership-unguarded — they mutate a named
  client partition without an ADR 0011 ownership check. Exporting them does not change that; #440
  adds the guard, and doing so will add an `ownership_override` keyword to both signatures.
- `set_lpar_processors` and `set_lpar_memory` operations and facade exports (#365, ADR
  0013/0029/0092/0094): the DLPAR processor and memory workflows move out of the
  `hmc_dlpar_proc` / `hmc_dlpar_mem` tool bodies into `operations_lpar`, so a consumer already
  running an event loop can call them — the tool path reached them only through `asyncio.run`,
  which raises inside a running loop. Tool names and existing parameters are unchanged.
  **Both are now guarded.** ADR 0092 §3.2 classifies DLPAR resource changes as Reconfiguring,
  which must be guarded unconditionally, so each calls `authorize_lpar_mutation` before the write
  and each tool gains an appended `ownership_override: bool = False`. Two consumer-visible
  consequences: a guarded call now needs SSH reachability to the HMC as well as REST, because the
  ADR 0011 token is read over SSH (#459 makes that failure actionable); and a call that omits
  `system_name_or_uuid` now discovers the owning managed system by a bounded fleet walk, because
  the guard is keyed by CLI system name — supply the selector to skip it. ADR 0094 records the
  derivation and its alternatives.
- `install_vios_by_lpar_selector` and `install_vios` operations and facade exports (#366, ADR 0013/0029/0070):
  the `installios` orchestration moves out of the `hmc_install_vios_by_lpar_selector` / `hmc_install_vios` tool
  bodies into a new `operations_install` module, so a consumer already running an event loop can
  call it — the tool path reached it only through `asyncio.run`. Both return the CLI bridge's
  detach handle (resolved system and partition names, the remote PID, the install log path, and a
  message restating them), not an HMC job identifier: there is no HMC job on this path (ADR 0069)
  and nothing to poll. Tool names, parameter lists, and returned payloads are unchanged. Both are
  classified in ADR 0092 §3.4a — outside §1's ownership rule by resource type, since `installios`
  requires a Virtual I/O Server partition and ADR 0011 stamps no token on one.
  **Consumer note:** both operations now preflight the resolved target and reject a non-Virtual
  I/O Server or any state other than `not activated` before SSH submission. Submission is not
  idempotent: a second concurrent call submits a second detached `installios` against the same
  partition, and the install log path is keyed on the partition *name* alone — the managed system
  is not part of it, and the redirect truncates — so two same-named partitions on different
  managed systems behind one HMC share one log and destroy each other's only diagnostic record.
  The returned `log_path` is not unique per system; serializing per partition name across every
  managed system on the HMC is the caller's responsibility. A returned handle means the process
  was backgrounded, not that the detached install later completed successfully. The preflight
  raises `HMCError` for an unsafe type or state, adds no parameter, and therefore does not move
  the frozen signature digest (#460).
- `ownership-denied` audit record for a refused ADR 0011 ownership check (#467, ADR 0100).
  The guard recorded approved overrides and nothing else, so an operator reading the stream
  could not tell "nobody tried to mutate a partition they do not own" from "many attempts were
  refused" — and on the CLI and Python API paths, which no access policy reaches, a refusal
  left no trace at all. Both denial branches now emit one `WARNING` record naming the guard
  entry point (`operation`: `lpar-mutation` or `lpar-decommission-snapshot`), the rule that
  refused (`denial`: `foreign-owner` or `malformed-token`), the system, the partition, the
  owner the LPAR's token claims (`null` on `malformed-token`), the HMC, and the acting agent.
  `ownership-override` is untouched — same name, same fields, same level — so an
  `event == "ownership-override"` filter keeps counting approved bypasses and nothing else.
  `docs/authorization-audit.md` documents the record and the caveats on alerting from it.
  No exported signature changes.
- `hmc_effective_permissions` reports `power_ownership_guards` (#470): the effective,
  post-precedence `authorize_power_operations` (ADR 0092 §4) for every connection the access
  policy's grants name, resolved inside the running server rather than in the shell that
  asks. The guard fails **open** and `HMCConfig` sets `extra="ignore"`, so a mistyped profile
  key or environment variable is dropped silently and is otherwise indistinguishable from a
  correct `false`; each entry carries the `source` that supplied the value — `environment`,
  `profile`, or `default`, where `default` is the answer that means nothing the operator
  wrote arrived. Environment names are matched case-insensitively, so exact and variant
  spellings both report `environment` and override the profile consistently (#547, ADR 0110).
  `hmcpctl config show` could not answer
  either deployment the documentation
  recommends: it exits 1 with no `config.toml`, and it reads the invoking shell's environment
  rather than the served process's. The entry keeps the setting's own name and polarity —
  `authorize_power_operations: true` means the ownership guard is enforced — because
  `authorized: false` would read as "not authorized" for the permissive state, which is the
  misreading this change exists to end. With `HMC_HOST` set the report carries at most the
  `<default>` row, because every connection token collapses there at dispatch. A connection
  whose config cannot be built reports
  `authorize_power_operations: null` with `source: unresolved` and a closed `detail` — the
  exception class,
  plus the rejected field names for a `ValidationError`. The underlying message is withheld
  from the caller and logged instead: `ConfigError` names every `profiles` and `nicknames`
  key in `config.toml`, which is the connection inventory ADR 0038 refuses to disclose, and
  a `ValidationError` quotes the value it rejected. Beyond the connection names the policy
  already declares, the entries carry no host, user, or credential; ADR 0037's disclosure
  bullet is amended to record the narrowed claim. `describe()` takes the resolved guards as
  a fourth argument and stays a pure function of its arguments; `EffectivePermissions` is not
  a `hmcpctl.api` export, so the facade manifest is unaffected.
- `install-attempted` audit record for a detached `installios` submission (#469, ADR 0102).
  `install_vios_by_lpar_selector` and `install_vios` submit an irreversible install against a partition's
  disks and detach; the path has no HMC job, no ADR 0011 ownership guard, and — for an
  `hmcpctl.api` consumer — no dispatch-boundary `authorization` record. The two `INFO` lines
  it left instead went to the unconfigured `hmcpctl.operations_install` logger, whose
  effective level is the root's `WARNING`, so they were dropped before formatting. That left a
  bare `hmcpctl.api` consumer with no local trace at all, and a served deployment with only
  the `authorization` permit for the tool call — which names the tool but never the resolved
  system, partition, or log path, and which `--audit-level WARNING` drops. One `WARNING`
  record now goes to the
  reserved `hmcpctl.audit` logger immediately **before** the submit — the ambiguous case,
  since the raised exception cannot say whether anything was submitted — carrying the resolved
  system and partition, the HMC-side `log_path`, the HMC, and the acting agent. The
  post-submit "Detached" line stays on the module logger; the PID it adds is already in the
  returned `InstallHandle`. No exported signature changes.

### Changed

- `hmc_modify_user` without a replacement password sends the empty `UserProfilePassword`
  element as GET serves it. V10R3 accepted the writes in the #1409 probe. Its users-arm
  observation remains failed: an empty description resets to `HMC User`, which the arm
  had expected to read as empty. The arm now checks that exact observed default;
  consolidated live verification of the corrected harness remains pending (ADR 0202).
- Bind `lpar.modify` delegated assignment rows and extend ST39 with an optional
  scratch-only dedicated-slot proof, guarded restoration and explicit read failures.
- The live harness gained an opt-in `lpar-power` arm (`scripts/live_lpar_power.py`, subtask
  41). It creates `hmcpctl-live-pwr-<8 hex>` partitions and verifies `hmc_create_lpar`'s
  refusals, `hmc_power_on_lpar` (profile and current-configuration activation, and a
  running partition reported without a job), `hmc_power_off_lpar` (delayed and immediate),
  `hmc_power_lpar`, `hmc_capture_lpar_console` and `hmc_delete_lpar` (refused while
  activated), then `hmc_provision_lpar` on a run-owned 1 GiB VIOS volume and
  `hmc_decommission_lpar`; preflight names it and `scripts/live_test_recovery.py` reports any
  `hmcpctl-live-pwr-` partition, `lppwr` volume mapping or adapter serving one (#1346). The
  bare-cec arm now records its create, PowerOn, console, PowerOff and delete steps as rows,
  so each of those operations has one observing arm. The power and lifecycle operations'
  capability rows now name the requests the code issues, and `lpar.power`,
  `lpar.decommission`, `provision.lpar`, `system.power_on` and `system.power_off` carry
  maturity records. `lpar.dump_restart`, provision's SR-IOV and vNIC arguments, a graceful
  `hmc_power_lpar` stop and whole-system power stay unverified, each recorded with what it
  needs. Live on V10R3 six of the arm's eight observations passed. `lpar.power_on`
  failed because the HMC refuses the `OperationType` PowerOn parameter
  (`INVALID_PARAMETER`; the request without it activates), and `provision.lpar` failed
  because a dedicated slot it assigns lands in the profile while its PowerOn activates the
  current configuration, so the running partition lacks the slot.
- The live harness gained an opt-in `lpar-config` arm (`scripts/live_lpar_config.py`, subtask
  39). It creates one `hmcpctl-live-lpar-<8 hex>` partition, verifies `hmc_modify_lpar`,
  `hmc_rename_lpar`, `hmc_dlpar_mem`, `hmc_dlpar_proc`, `hmc_set_lpar_boot_order` and the
  `hmc_clear_lpar_boot_order` refusal against it, activates it to SMS for the activated DLPAR
  case, and deletes it; preflight names it and `scripts/live_test_recovery.py` reports any
  `hmcpctl-live-lpar-` partition left behind (#1345). Live on V10R3 all six observations
  passed. ST8 no longer declares an expected HTTP 406 for `hmc_modify_lpar`: the
  read-modify-write path is accepted, so a 406 there is now a failure, not a gap. DLPAR on a
  partition activated to SMS was refused (`HSCL7016`, the partition must be running), so DLPAR
  on a running operating system stays unverified; the `hmc_modify_lpar` observation covers its
  resource path, not its PCIe assignments. Memory above the maximum is refused with
  `REST0264`.
- `hmc_create_user` and `hmc_modify_user` take `associated_task_role` as a task-role name
  (`TaskRoleName` from `hmc_list_task_roles`) and `associated_resource_roles` as resource-role
  names, not hrefs. The `UserProfile` document now writes them as the documented
  `AssociatedTaskRole` and `AssociatedResourceRole` text elements, in the documented element
  order, with `AuthenticationType` in the lower case the HMC lists (a V10R3 create carrying
  `Local` was refused with `REST0001`); an href passed as before is sent as a name (ADR 0202,
  #632). The builder is in every
  handler's import closure, so every previously current live observation now reads `stale`
  (`closure-changed`, ADR 0127) until its arm re-runs.
- The live harness's user lifecycle moved from round2 to its own opt-in `users` arm
  (`scripts/live_users.py`, subtask 11). It creates one `hmcpctl-live-<8 hex>` viewer user with
  remote access disabled and deletes it by UUID in the same run; preflight names it, and
  `scripts/live_test_recovery.py` reports any `hmcpctl-live-` user left behind.
  `LIVE_TEST_TEST_USER_NAME` is retired: a `.env` that still sets it loads with a notice, and the
  line can be deleted (#632). Live on V10R3 the HMC refused `hmc_create_user` (REST0001: a `kb`
  marking must be `COR`), so creation, and the get, modify and delete that follow it, remain
  unverified; the user, role and remote-access reads are verified.
- `HMCClient` no longer raises a logoff transport failure (`HMCTransportError`) when its
  `async with` body completed: it logs a warning naming the HMC host and noting that the HMC
  session may persist until the HMC times it out, so a completed tool call is no longer reported
  as failed. An HMC rejection of the logoff (`HMCError`) still raises, and a body that raised
  still carries every cleanup failure as a note (ADR 0028 amendment, #1325).
- `hmc_power_off_lpar`, `hmcpctl lpars power-off`, `power_lpar`, `submit_power_off` and
  `jobs.power_off_lpar_job` refuse `operation=shutdown` with `restart=true` and
  `immediate=false` before any job is built. On the HMC that combination is a dump restart,
  which crashes the partition, and it previously needed no `allow_dump_restart` grant. Pass
  `immediate=true` (CLI: `--immediate`) for an immediate restart, use `operation=osshutdown`
  for an operating-system restart, or use `hmc_dump_restart_lpar` for the dump. The tool's
  docstring no longer calls `immediate=false` graceful: it is a delayed shutdown
  (ADR 0164 amendment, #1314).
- `hmc_upload_iso` and `hmcpctl storage upload-iso` return the download digest as
  `source_sha256` instead of `sha256`, with no alias. It is computed from the bytes fetched from
  the source URL, not read back from the VIOS; `media` is documented as the HMC repository entry,
  whose `MountType` can differ from VIOS `lsrep` (#1281).
- `hmc_list_lpars`, `hmc_list_vios` and `hmc_list_lpar_ownership` return `entries` and
  `unreadable_systems` instead of a bare list, as do `hmcpctl lpars list --json` and
  `hmcpctl vios list --json` and the `list_lpars`, `list_vios` and `list_lpar_ownership`
  operations. Without a system they no longer read the HMC-wide partition or VIOS feeds,
  which timed out on an HMC with one system in `No Connection`. They read each operating
  managed system's own feed and name every other system in `unreadable_systems`; the CLI also
  prints one `Skipped managed system` line per skipped system on stderr. A VIOS state filter is
  now always applied locally (ADR 0197, #1293).

- **Access-policy contract:** a grant naming `hmc_power_off_lpar` no longer reaches the
  `dumprestart` crash; add `hmc_dump_restart_lpar` to the grant to keep it. An
  `effects = ["destructive"]` grant admits both. `hmc_power_off_lpar` now admits `operation`
  `shutdown` or `osshutdown` only and no longer accepts `allow_dump_restart`; an MCP call that
  still passes it, even as `false`, is refused, so drop the argument. The CLI and `power_lpar`
  are unchanged (#896, ADR 0188).
- `hmcpctl lpars set-boot-order` prints the boot string it set and the pending boot string
  read back from the HMC, not the whole updated LPAR document; `--json` prints the document
  as before. The operation and the `hmc_set_lpar_boot_order` tool return value are unchanged
  (#1248).
- `docs/capabilities/maturity.json` moves to format 4: every live observation carries a
  required `schema_version` — the run's `HMC_SCHEMA_VERSION` as a `V<n>_<n>[_<n>...]` token
  or `(not set)`, the string its header prints — and the 20 observations stored before it
  read `unrecorded`. A run whose variable fits neither form writes no observations; the
  runner warns at startup when an observation environment is configured (#1090, ADR 0186).
- `WritableConsoleSession.send_sysrq` defaults its keyword-only `prefix` to `b"\x0f"`
  (Ctrl-O); a caller can still pass another prefix. A live run on HMC V10R3 M1060 with
  partition firmware FW950 showed the vterm passing Ctrl-O plus `h` to a Linux guest's hvc
  console, which printed its SysRq help within about a second. The same run found that written
  `~.` does not end the vterm (mid-line or after a CR, at SMS, GRUB and a Linux installer), that
  a writable session stays held with no stdin EOF, and that written keystrokes reach the
  partition firmware too; the docstrings and ADR 0176 record these outcomes (#1149).
- `docs/recipes/lpar-iso-install.md` now records the #1085 boot-order retest (V10R3 M1060,
  FW950.00). Firmware names a virtual optical device `disk@<LUN>`, not `cdrom@`, and boots the
  ISO from `/vdevice/v-scsi@<0x30000000 + client slot>/disk@<LogicalUnitAddress>`. It does not
  honour `cd/dvd-all`, and it does not fall back to the CD when the boot list names only a blank
  disk. Step 5 now sets that path with `set-boot-order` before the power-on. Step 4 notes the
  `REST0269` refusal of `mount-optical-media` on a partition never activated with its profile,
  and step 5 notes the second Enter that Debian's GRUB needs after its client-architecture-support
  reboot. `lpars set-boot-order` help and the `hmc_set_lpar_boot_order` docstring say how to
  build the optical path.
- **Breaking (pre-release):** `hmc_create_lpar`, `create_and_stamp_lpar` (`LparCreation`) and
  `build_lpar_document` no longer take `os_type`, and `OsType` / `OS_TYPES` are removed from
  `hmcpctl.documents`. V10R3 treats `OperatingSystemType` as read-only, refuses a create that
  sends it, and sets `AIX/Linux` itself; `partition_type` (`AIX/Linux` or `OS400`) is the
  distinction a create can make (#1179).
- **Breaking (pre-release):** `hmc_create_lpar`, `hmc_provision_lpar`, `lpars create`,
  `lpars provision`, `create_and_stamp_lpar` and `provision_lpar` no longer offer
  `partition_type="Virtual IO Server"`. V10R3 answers a LogicalPartition create typed Virtual IO
  Server with HTTP 500 `REST0140 Invalid Partition Type associated with LogicalPartition`. The
  MCP schemas list only `AIX/Linux` and `OS400` and point to `hmc_create_vios`; every other
  caller is refused before any HMC request with a message naming the VIOS create path.
  `PARTITION_TYPES` and `PartitionType` are now `AIX/Linux` and `OS400`, and the CLI `--type`
  error reads `--type: partition_type must be one of …` (#1179).
- SR-IOV physical-port inventory reads the `roce`, `ethc` and `eth` levels and merges the
  rows, refusing a port listed at two levels. It read `roce` and `ethc` and accepted only one
  non-empty level, so an adapter with ports at both `ethc` and `eth` (captured on V11R2 with a
  POWER9 9009-42A) could not be listed (ADR 0183).
- **Interface change:** `hmc_restore_lpar_profiles` takes a required keyword `restore_type`
  with no default, and `rstprofdata` now carries it as `-l`, which the HMC requires
  (`rstprofdata -m S -l type -f F`). `1` restores the backup in full, `2` merges with the
  backup winning conflicts, and `3` merges with the current data winning. Any other value,
  including `4` (initialize, which deletes every partition), is refused before the command
  runs. The tool used to send `rstprofdata` without `-l`, which the HMC's synopsis does not
  allow (#1202).
- `hmc_list_optical_media`, `storage list-optical-media` and `list_optical_media` no longer
  return `media_type`, and the CLI table drops its Type column. No captured V10R3 or V11R2
  medium and no IBM reference page carries a `MediaType` element, so the field was always
  null. Each medium is now `name` and `size_mib` (#1202).
- **Output-schema change:** `hmc_fleet_health`, `fetch_fleet_health` and `hmcpctl systems
  health` no longer return `failed_jobs`, and no longer read `GET /rest/api/uom/Job`. That
  feed is not in the HMC REST reference, and every captured HMC (V10R3 and V11R2) refused it
  with `400 REST000E`, so the field was always empty alongside an "unavailable" warning. The
  envelope is now `systems`, `vios`, `lpars` and `warnings`; ADR 0019 carries the amendment
  (#1202).
- **Interface change:** the `state` values `hmc_list_lpars`, `hmc_list_vios`,
  `hmcpctl lpars list --state` and `hmcpctl vios list --state` accept are now the HMC
  schema's `LogicalPartitionState.Enum` (identical on V10R3 and V11R2). `stopping`,
  `migrating` and lower-case `unknown`, which no HMC reports, are rejected; `not available`,
  `migrating not active`, `migrating running`, `hardware discovery`, `suspending` and
  `Unknown` are accepted (#1202).
- **Interface change:** `job_href` on `hmc_get_job`, `hmc_wait_for_job`, `get_job`,
  `wait_for_job` and `hmcpctl jobs show|wait --job-href` must be a
  `/rest/api/uom/jobs/{JobID}` link (a read-side `jobs/{JobID}/{uuid}` link is still reduced
  to it). The per-operation `.../do/{Operation}/Job/{id}` form accepted for #95, the
  `/rest/api/uom/Job/{id}` form and relative `jobs/{id}` paths are refused: no HMC capture or
  reference shows them, and the reference documents only `rest/api/uom/jobs/{job_id}` (#1202).
- The `HMC_TIMEOUT` default (TOML `timeout`) is now 180 seconds, raised from 60. A read-only
  sweep found that a `GET /rest/api/uom/ManagedSystem` feed read on a large V11R2 HMC took longer
  than 60 seconds, and neither IBM's documentation nor hmcpctl sets an upper bound on how long
  such a read may take. `HMC_UPLOAD_TIMEOUT` (600 seconds) still exceeds it (#1202).
- A `targets` table can now grant `hmc_attach_disk_to_lpar`: its LPAR, managed-system and
  `vios_uuid` selectors bound everything it touches, so a grant naming all three reaches it and
  one that omits any of them, or a call that omits `system_name_or_uuid`, is denied.
  `hmc_provision_lpar` still requires `targets = "all-targets"`, because its `assignments` name
  vNIC backing VIOSes, DRC indexes and SR-IOV ports no selector declares (#1086).

- `hmc_detach_storage_mapping` returns `{"mapping_id", "change_location"}` instead of the bare
  mapping ID. `hmc_add_network_adapter`, `hmc_add_vscsi_adapter`, `hmc_add_vfc_adapter` and
  `hmc_mount_optical_media` add a `change_location` key beside the resource's own keys (#981).
- Console contention now quotes what the HMC printed in `ConsoleHeldError`, with the same error
  type. `ConsoleSession(..., take_over=True)` is a new, explicit option: it issues `rmvterm`
  and then acquires with proven acquisition. The default is `False`, and neither the capture nor
  the MCP tool sets it. `capture_lpar_console` no longer leaks its own proven hold when console
  output quotes the contention sentence: it releases the hold, then raises `ConsoleHeldError`
  as before. A contention sentence that follows the acquisition banner in the same read now
  counts as console content, both at open and in the release probe (#975, ADR 0172).

- `hmcpctl lpars create` and `hmc_create_lpar` apply the new partition profile, `default_profile`,
  when the HMC creates the partition through `mksyscfg` (its REST create returned HTTP 406). The
  apply is `chsyscfg -r lpar -o apply` and leaves the partition not activated. Before this, such a
  partition had no current configuration: REST adapter writes failed with `REST0269` and the
  create result showed zero memory and processors. The result reports an `apply_profile` step; a
  failed apply stops the remaining steps and leaves the partition in place. `--no-apply` /
  `apply_partition_profile=false` skips it and returns a warning instead (#939).

- The distribution, console script, Python package and configuration directory are renamed
  from `hmc-mcp` / `hmc_mcp` to `hmcpctl`, with no compatibility alias: the facade is now
  `hmcpctl.api`, `import hmc_mcp` fails, and the former configuration directory is not read.
  Data the former tool wrote keeps its old name and is no longer recognised: a
  `[hmc-mcp owner:…]` stamp reads as unowned, an `hmc-mcp.lpar-snapshot` is refused, and
  `X-Audit-Memento` is now `hmcpctl:<agent_id>`. The
  [cutover guide](docs/configuration.md#clean-cutover-from-the-former-name) moves the
  configuration and lists what to do about each (ADR 0167, #898).

- `assign_dedicated_pcie_slot`, `unassign_dedicated_pcie_slot` (`hmc_assign_dedicated_pcie_slot`,
  `hmc_unassign_dedicated_pcie_slot`) and create-time or modify-time `assignments.dedicated` now
  change the profile on HMC V10R3 M1060 with managed-system model 8375-42A. They write the
  documented `io_slots+=<drc>//0` / `io_slots-=<drc>//0` grammar without `--force`, then verify
  the result with the ADR 0165 readback. They never write back a value they read, and they refuse
  a slot the profile lists in any other form. The LPAR must be `Not Activated`, and assign
  refuses a slot another LPAR's profile already lists. `drc_index` must be eight uppercase
  hexadecimal digits. Outside that envelope they still raise `PcieAssignmentUnavailableError`, whose reason
  now names the envelope. A dispatched change that the readback does not confirm raises the new
  `PcieAssignmentPartialError`. The admitted read and its parser are
  `ssh.profiles.read_profile_io_slot_rows` and `parse_profile_io_slots` (ADR 0166, #882).

- Exact `lssyscfg -r prof -m SYSTEM -F lpar_name,name,io_slots --header` profile readback is
  admitted, on a redacted live
  capture rather than on documentation — `io_slots` is documented input-side only, so a
  `documented`-support record would have carried a fabricated locator. The admission is
  confined to HMC V10R3 M1060 on managed-system model 8375-42A, the pair the capture covers
  and the pair `require_admitted_environment` already enforces for SR-IOV. **No runtime
  behaviour changes**: dedicated PCIe assign and unassign still fail closed, now because no
  code path selects the readback rather than because none is admitted (ADR 0165, #881).

- Installed CLI, MCP discovery, and generated tool references now publish the same
  operation-keyed implementation, verification, and runtime-eligibility evidence.
  Compatibility guidance now describes the POWER10/POWER11 reference corpus and
  per-operation evidence instead of claiming blanket HMC V8–V11 and POWER support
  (#624, ADR 0131).

- `scripts/run_tests.py` now preserves an interrupted pytest's `KeyboardInterrupt`
  diagnostic under the host load ADR 0130 measured, where a fixed 3-second grace
  truncated it. The window before `SIGTERM` and the reap before `SIGKILL` are separate
  bounds sized to the quantities they guard, and a second `Ctrl-C` escalates at once
  instead of escaping with the captured output unreplayed, the status misreported and
  the pytest child orphaned (#728, ADR 0130).

- Live-verification evidence is now trustworthy promotion evidence. `maturity.json`
  moves to format 2: one closed observation shape, no stored currency, and no free
  text beyond two grammar-bound environment strings. Staleness is derived when the
  catalog is read — from the operation's own import closure, or a 90-day ceiling —
  and is never a validation error, so recording evidence cannot turn the build red.
  `just verification-report` prints each operation's state; it warns on pull requests
  and fails only on the weekly scheduled run. The live runner asserts named
  postconditions instead of treating "the call returned" as a pass, checks every
  dispatch against the served tool schema, and emits observations only from a clean
  tree to a path Git ignores (#623, ADR 0127, superseding ADR 0126).

- Streamlined the README around installation, CLI, and MCP quick starts; moved
  configuration, API contracts, operation details, and development reference into
  topic guides under `docs/`.

- SSH commands and consoles now verify host keys against the process user's
  `~/.ssh/known_hosts`; provision independently verified keys before upgrading.
  `ssh_verify_host_key=false` (or `HMC_SSH_VERIFY_HOST_KEY=false`) explicitly
  bypasses verification with a warning. The operator probe requires `--insecure`
  for its own per-run bypass (#605, ADR 0116).
- The HMC PTF query operation and MCP tool now use submission-oriented names:
  `submit_available_hmc_ptfs_query` and `hmc_submit_available_hmc_ptfs_query`.
- SR-IOV physical-port inventory now queries both evidenced `roce` and `ethc`
  levels, accepts exactly one non-empty result, and maps HMC states `1` and `0`
  to `up` and `down` respectively (#557, ADR 0113).
- `hmc_get_job` and `hmc_wait_for_job` now reject `job_href` values containing
  TAB, CR, or LF before any HMC read, so validated and echoed links have the
  same spelling (#537, ADR 0093).
- `hmc_set_lpar_description` now accepts HMC-resolved partition names containing spaces or
  semicolons, matching live HMC behavior while retaining attribute-record delimiter checks (#288).
- Optical unmount now resolves an exact LPAR-scoped `MediaName` to one mapping UUID and
  removes it through the shared ADR-0079 parent-VIOS remover. Empty, absent, ambiguous,
  or malformed identities fail without a POST; prefixes and incidental mapping text no
  longer select another device (#439).
- Route Python warnings in served deployments through the bounded, producer-prefixed stderr
  logging sink while leaving non-served library warning behavior unchanged (#550).
- `modify_system` now accepts a cohesive `ManagedSystemPatch`, and the LPM
  validation and migration operations accept `LpmMigrationRequest` for their
  destination-specific inputs. Shared wait and authorization controls remain
  explicit keyword-only arguments.
- Mutation results now identify the affected resource consistently: `delete_adapter`
  returns the deleted adapter UUID, and `create_virtual_network` returns a
  `VirtualNetworkResult` containing the resolved system UUID and HMC resource.
- `hmc_create_volume_group` now declares its actual HMC resource payload return
  (`dict | None`) instead of the unrelated storage-mapping workflow result.
- Capacity and summary contracts now name mebibyte values explicitly:
  `desired_memory_mib`, `current_memory_mib`, `total_memory_mib`,
  `assigned_memory_mib`, and `free_memory_mib` replace their misleading
  `*_mb` names across the facade, MCP tools, CLI adapters, and live-test state.
- `ConsoleCapture` now preserves a bounded, single-line transport diagnostic in
  `error` when `stop_reason` is `"error"`. Partial console bytes and mandatory
  vterm release behavior are unchanged; non-error captures report `error=None`.
- Exported vSCSI and vFC adapter creation operations now match network adapter
  creation by accepting the optional client slot as keyword-only
  `slot_number=None`.
- Provisioning workflow results now report virtual-disk capacity as
  `capacity_mib`, matching the value's mebibyte unit.
- Exported LPAR operations now place `system_name_or_uuid` before
  `lpar_name_or_uuid`, including LPM, disk attachment, summaries, ownership
  authorization, and PCIe assignment workflows. Presentation adapters pass
  `None` when they intentionally request fleet-wide LPAR-name resolution.
- Exported VIOS storage operations now require `vios_name_or_uuid` first and
  accept the optional `system_name_or_uuid` selector as a keyword-only argument.
- The supported VIOS storage-detail operation and MCP tool are now
  `get_vios_storage_detail` and `hmc_get_vios_storage_detail`; the ambiguous
  `get_vios` and `hmc_get_vios` names were removed.
- Storage inventory operations now return bounded `VolumeGroup`, `OpticalMedia`,
  and `StorageMapping` values instead of raw HMC response mappings (ADR 0117).

- `create_user` and `modify_user` now expose the documented user-profile fields as
  explicit typed keyword parameters instead of accepting an untyped `**fields` bag.
- User deletion and remote-access MCP tools now call the client boundary directly;
  remote-access validation and document merging have one owner in the client layer.
- `fetch_metric_links` and `fetch_metric_data` require metric kind, time range, sample count, and
  managed-system scope as named arguments after the resource selector.
- Affinity assessment models, pure evaluation, and live orchestration now live together
  in `operations.affinity`; snapshot modules consume that boundary without a reverse
  dependency from operations into the snapshot package.

- `provision_lpar` now requires `partition_type` and all subsequent workflow
  controls as keyword arguments. The HMC client, system/name selectors, network,
  storage, and resource payload remain positional; boolean and policy controls can
  no longer be silently misbound by position.

- `update_console_software` and `hmc_update_console_software` no longer expose a
  `kind` selector whose `"upgrade"` branch always failed. The operation now models
  only the supported `UpdateManagementConsole` job; any future multi-job console
  upgrade will require a separately named workflow.

- `upload_iso` now documents and returns its sole successful status, `"uploaded"`;
  removed the always-`None` `existing_name` result field and the CLI's unreachable
  duplicate-content output branch. Name collisions continue to raise
  `FileExistsError` before transfer.

- Public VIOS and storage operations now use `*_name_or_uuid` selector names, place
  `system_name_or_uuid` before the resource selector, and require non-selector controls by
  keyword.
- LPAR ownership operations now live with the ownership policy in `lpar_ownership`, and
  post-activation affinity orchestration now lives with the shared affinity assessment models.
  The facade names and signatures are unchanged.
- `create_media_repository` no longer removes and recreates an existing virtual media
  repository. A repeated request for the same size returns the existing repository without a
  write; a different requested size raises an actionable conflict and leaves the repository
  untouched. Resizing or replacement requires a separately explicit destructive operation.
- `hmc_wait_for_job` and `hmc_get_job` now read through `operations_jobs` instead of calling
  `HMCClient` directly, so an MCP caller can tell a reaped job from a running one (#474, ADR 0093
  amendment). **Tool behaviour changes:** a job the HMC no longer has returns `found: false`
  (`hmc_wait_for_job`) or null (`hmc_get_job`) instead of raising `HMCError`, and polling stops on
  it rather than running to the deadline — read `found` first, and note that a caller which only
  caught `HMCError` for a vanished job now gets a successful result. `found: false` still carries
  `timed_out: true`, now returned immediately rather than after the deadline, so `timed_out` must
  not be read as "still running" without checking `found`. `hmc_wait_for_job`'s `job_href` also
  changes: a `job_href` you passed that resolved is echoed back verbatim, where the value
  previously came from the HMC's own SELF link. A 404 on the *first* read is
  reported straight through, so a momentary one now reads as `found: false` where it previously
  raised; only a disappearance after the job has been seen alive gets the confirming re-read. The
  output schema is
  unchanged: `found` was already a required property of the shared wait shape. Two smaller
  changes come with the shared operation. `timeout_seconds` is now a soft bound: a job that
  disappears after being seen alive is re-read once before being reported gone, and that read is
  owed past the deadline, so `hmc_wait_for_job` can return a whole `poll_interval` late —
  more than the deadline itself if `poll_interval` exceeds `timeout_seconds`. And a `job_uuid`
  that is empty, is a bare dot, or carries a path, query, fragment, percent, or interior
  whitespace character now raises `ValueError` before any request for the job is made — though
  after the session is opened, so a malformed handle still costs a logon and logoff;
  surrounding whitespace is still trimmed. That check applies **even when `job_href` is
  supplied**, where the client previously ignored `job_uuid` altogether — so an issue #95 caller
  that persisted only the submission link must now pass the identifier too. Every non-404 HMC
  failure still raises. Two consequences specific to `hmc_get_job`: null no longer separates a
  reaped job from an HMC that produced no entry, where the `HMCError` used to, and because that
  tool returns the HMC entry rather than the outcome, the `link` it carries can be one a read just
  proved dead — ADR 0093 clause 2's never-store-a-dead-link guarantee does not reach it. The
  `hmc jobs` CLI commands keep the previous behaviour; #526 owns that pass.
- `HMC_AGENT_ID` values containing double quotes or backslashes are rejected at config load
  instead of being passed through into SSH command construction (#386).
- `hmc_install_vios_by_lpar_selector` and `hmc_install_vios` now drive the HMC CLI
  `installios` command over SSH (submit-and-detach: they return the remote PID
  and log path instead of a job, and `hmc_get_job`/`hmc_wait_for_job` do not
  apply). The targeted `InstallLPAR`/`InstallVIOS` REST jobs do not exist on
  any surveyed HMC (ADR 0069). Parameter changes: `nim_ip` is removed (under
  CLI semantics the HMC itself serves the install image); a required
  `install_source` (`-d`) and `system_name_or_uuid` (`-s`) replace it, and a
  required `profile_name` (`-r`, default `"default"`) plus optional
  `mac_address` (`-m`) join; `wait`/`wait_timeout_seconds`/`poll_interval`/
  `hmc_timeout_minutes` are removed because there is no job to poll (#410,
  ADR 0070).
- A lower- or mixed-case `HMC_*` export now overrides a TOML profile's matching key, for
  every `HMCConfig` field (#531). `HMCConfig` leaves pydantic-settings' `case_sensitive`
  at its `False` default, so `hmc_host=…` always reached the `host` field; the profile
  loader's exact-case membership test did not agree, and handed the profile's value to the
  constructor as an init kwarg, which outranks every environment source. Three further
  hand-rolled `HMC_*` reads that mirror or report on that resolution move to the same
  case-insensitive rule: `build_config`'s `HMC_HOST` branch gate, the ADR 0038
  `connection_scope` mirror of that gate, and the #379 TLS audit record's `source` field,
  which named `explicit-argument` for a value only the environment had supplied. The
  `connection_scope` mirror is what makes leaving it exact-case a fail-open — the token
  would resolve to a profile key while the call reached the exported host — and pre-fix
  that divergence was already reachable, though only for a profile that omits `host`,
  since a profile carrying one handed it over as an init kwarg that outranked the variant.
  One reader inside `src/hmcpctl` was left behind by that change — `audit.py` imports
  nothing from the package by design, so its `HMC_AGENT_ID` attribution read needed a
  case-fold of its own — and #543 below carries it, along with the `scripts/live_test_runner.py`
  sweep. Several casings of one
  variable fold to a single field, and the last one in the process environment wins —
  `env_var_value` resolves the tie the way pydantic-settings does, pinned by a test
  against `HMCConfig` rather than against a reading of the library. `HMC_PROFILE` is
  unchanged and still matched exactly on POSIX; it names no `HMCConfig` field and no
  settings loader reads it. **Upgrade note:** a deployment whose environment already
  carries a case-variant `HMC_*` name gets a different resolution after this change —
  the export now beats the profile's TOML key where it previously lost. Audit for them
  before upgrading (`env | grep -iE '^hmc_'`). Four things flip in the fail-open
  direction. A stale `hmc_verify_ssl=false` over a profile's `verify_ssl = true` is at
  least visible, as `client.py` emits `tls-verification-disabled` naming the environment.
  A stale `hmc_authorize_power_operations=false` over a profile's `true` leaves no runtime
  record at all — a guard that is off simply does not run — so `hmcpctl config show` is
  the check for that one. The largest is on the access-policy surface: a stale
  `hmc_host` now collapses every connection token to `<default>`, so an ADR 0038 grant of
  `connections = ["<default>"]` permits calls it previously denied, issued against the
  exported host, while a grant naming a profile key now denies calls it previously
  allowed. The authorization records show it — `connection.resolved` reads `<default>`
  for a call that named a profile. Finally, a stale `hmc_agent_id` now beats a profile's
  `agent_id`, and that is the identity the ADR 0011 ownership guard compares against, so
  it changes which LPARs this process may mutate — `hmc_agent_id=team-b` over a profile's
  `agent_id = "team-a"` turns every denial of a `team-b`-stamped partition into a
  permit. The authorization records show this one as well: `audit.py` folds the casings the
  loader folds (#543), so a record's `attribution` names the identity the guard compared —
  the same one the LPAR ownership stamps and the `X-Audit-Memento` header carry.
- The authorization audit record's `attribution` reads `HMC_AGENT_ID` without regard to
  case (#543, ADR 0040). `HMC_AGENT_ID` is an `HMCConfig` field and `HMCConfig` matches its
  variables case-blind, so a `hmc_agent_id=alice` export stamped every LPAR the process
  created with the ADR 0011 ownership token for `alice` and sent `X-Audit-Memento:
  hmcpctl:alice`, while every authorization record from that same process carried no
  claimant at all — the audit stream said nobody acted while the partitions said `alice`
  did. Several casings at once resolve to the last in the process environment's order, as
  they do for every other `HMC_*` variable. `audit.py` imports nothing from the package, so
  it carries its own copy of the fold rather than calling `config.env_var_value`; a test
  pins the two against each other.
- The live integration runner (`scripts/live_test_runner.py`) reads each `HMC_*` variable
  the way that variable's own reader reads it (#543). Five places predicted or overrode a
  config resolution exact-case. The credential and `HMC_SCHEMA_VERSION` pre-checks each refused to
  start on a case variant that would have connected, telling the operator to set a variable
  that was already set. The ISO allowlist merge dropped a case variant's entries, and it
  now also removes every other casing before writing the canonical name — assigning to an
  existing key updates it in place rather than moving it, so a variant would otherwise stay
  last in `os.environ` order and stay the one that reaches the field, leaving ADR 0050 to
  refuse every upload in the run while the printed banner said the host was permitted. The
  worst was the `.env` loader: `_bootstrap_config` documents an already-set `HMC_*` variable
  as priority 1 and `.env` as priority 3, but the exact-case membership test did not
  recognise an exported `hmc_host` as an already-set `HMC_HOST`, injected the canonical
  spelling, and — a newly created key landing last in `os.environ` order — let the
  committed `.env` outrank the export, so an operator who exported a lab host ran the
  destructive suite against the HMC `.env` named. The `config.toml` injection beside it
  took the same guard. Only a name `HMCConfig` resolves as one of its own fields is folded:
  `HMC_PROFILE` and a profile's `password_env` target carry the prefix but are read
  exact-case, and folding them would let a variant nothing reads suppress the `.env` line
  spelling them canonically.
- The diagnostic that `HMC_AGENT_ID` is discarding a custom `HMC_AUDIT_MEMENTO` now logs once
  per process instead of once per `HMCConfig` construction (#546). Repeats are available at
  `DEBUG`, and concurrent construction cannot duplicate the warning-level record. The redundant
  `warnings.warn` emission was removed: after #534 the package log record reaches ADR 0043's
  bounded served sink, while Python warnings still write synchronously to fd 2 outside it.
  **Operator-visible change:** a long-lived server emits one bounded diagnostic rather than one
  log line per tool call plus a separate Python warning.

### Removed

- `hmc_install_vios_by_lpar_selector` (operation `lpar.install_os`) and the
  `install_vios_by_lpar_selector` operation are retired (#1371, ADR 0203). The selector
  resolved its target only through the `LogicalPartition` feed and then required a Virtual I/O
  Server, which is listed only in the `VirtualIOServer` feed, so it could never submit an
  install. Install a VIOS with `hmc_install_vios` (`install_vios`): it takes the same arguments,
  with `vios_name_or_uuid` and `vios_ip` in place of `lpar_name_or_uuid` and `lpar_ip`. The
  `lpar.install_os` capability and maturity rows are gone; `cli:commands/installios` stays bound
  by `vios.install`. The server exposes 162 tools by default.
- `hmcpctl.documents.build_media_repository_delete_document` and
  `build_virtual_optical_media_delete_document` are removed. No request path called them:
  `hmc_delete_media_repository` and `hmc_delete_optical_media` remove the node by VolumeGroup
  read-modify-write (#1415).

- `hmc_list_recent_jobs` and `hmcpctl jobs list`. Both read `GET /rest/api/uom/Job`, which
  the HMC REST reference does not document (it documents only `GET`/`DELETE
  /rest/api/uom/jobs/{job_id}`), and which every captured HMC refused with
  `400 REST000B/REST000E "Unrecognized root REST type of Job"` (one V10R3 and three V11R2
  HMCs). Poll a submitted job with `hmc_get_job` or `hmc_wait_for_job` and the JobID the
  submitting tool returned (#1202).
- The inputs that only fed the removed `vscsi` step (#1030): `vios_partition_id` and
  `vios_slot` on `hmc_attach_disk_to_lpar` and `attach_disk_to_lpar`, `--vios-id` and
  `--vios-slot` on `storage attach-disk`, `ProvisionAdapters.vios_partition_id` and
  `.vios_slot` (the `adapters.vios_partition_id` and `adapters.vios_slot` keys of
  `hmc_provision_lpar`, which MCP now ignores rather than rejects), `--vios-partition-id` and
  `--vios-slot` on `lpars provision`, and the live-test settings
  `LIVE_TEST_DRY_RUN_VIOS_SLOT` and `LIVE_TEST_DRY_RUN_VIOS_PARTITION_ID`.
- `hmc_detach_optical_mapping` MCP tool and its `media.detach_mapping` operation name, plus the
  `detach_optical_mapping` operation behind them (#362). Both duplicated
  `hmc_unmount_optical_media` / `media.unmount` byte for byte. As this client implements optical
  mount, the media is referenced from inside the `VirtualSCSIMapping` and no unload-without-detach
  path has been identified on the surveyed firmware, so detaching the mapping and unmounting the
  image are one operation; #200 requirement 6 was amended to describe the one behavior that is
  currently buildable. **Upgrade note:** the server is
  fail-closed on unknown tool grants (ADR 0041), so an `access-policy.toml` that grants
  `hmc_detach_optical_mapping` now refuses to start — drop that entry or rename it to
  `hmc_unmount_optical_media`. The exposed tool count drops from 148 to 147.

### Documentation

- Every generated `docs/tools/` page now states that its Summary column is the first line of
  each tool's MCP description, and that the complete text — including the conditions under which
  a tool refuses — is the handler's docstring under `src/hmcpctl/server_tools/`. `tools/list`
  carries that docstring's prose and, in the input schema, its argument detail, but not its
  `Returns:` or `Raises:` sections (ADR 0097, #929).

- ADR 0096 records the decision behind `HMCConfig.from_mapping` and why documentation alone was
  not enough (#368). `AGENTS.md` no longer teaches `HMCConfig(_env_file=None)` as the
  credential-free idiom: that private pydantic-settings parameter suppresses a dotenv source
  rather than the environment, `HMCConfig` configures no dotenv source at all so it is entirely
  inert, and the guidance additionally told maintainers to delete the `monkeypatch.delenv` calls
  that were the only thing isolating those tests.
- ADR 0069 records the live-HMC survey finding that the HMC REST API does not advertise the
  `InstallLPAR`/`InstallVIOS` jobs at any surveyed firmware level (#381); the disposition of the
  affected tools is tracked in #410. No code change.
- ADR 0070 records the operator decision to bridge the install tools to the
  HMC CLI `installios` command, the grammar mapping with sources, the
  submit-and-detach semantics, and the injection-validation approach (#410).
- ADR 0071 records the decision to feed the bulk LPAR ownership read from the REST list
  endpoint per the #374 live-REST survey (descriptions inlined since schema V1_2_0,
  absent-element empty semantics), superseding the issue's N×SSH sketch, and the
  parse-failure honesty policy (#375). Also corrects the disproven "not exposed via REST"
  claim in `get_lpar_description`'s docstring.
- A served process now routes its own `hmcpctl.*` log records through ADR 0043's bounded stderr
  sink (#534, ADR 0043 amendment). Only the reserved `hmcpctl.audit` logger and the third-party
  set were on it, so a warning from any other module — `hmcpctl.config`'s audit-memento override,
  `hmcpctl.server_permissions`' unresolved-profile line — reached fd 2 through
  `logging.lastResort`: synchronous, unbounded, and unescaped. Those *log records* now carry
  the `hmcpctl:` producer prefix and are drop-counted like every other line on the queue.
  `warnings.warn` is a separate mechanism and is not covered; #546 removes the redundant
  audit-memento warning while throttling that site's bounded log record.
  **What an operator sees change:** the prefix, and — if you route `hmcpctl.*` into your own
  logging — a second rendering, because `propagate` is deliberately left alone here, unlike on
  `hmcpctl.audit`. Your handlers keep receiving these records exactly as before; the sink is an
  added destination, not a replacement. A handler you attach to `hmcpctl` itself is left in
  place and takes the records instead of the sink, with the two constraints
  `docs/authorization-audit.md` states for a handler on `hmcpctl.audit`: it must not write to
  `sys.stdout` under stdio, and it is called on the dispatch path, so one that blocks there
  blocks the call. Nothing changes for a library or CLI process, which installs no sink. The
  `WARNING` floor is unchanged at the shipped default; what grows is the sink's share of the
  1024-slot queue it shares with the audit trail, since these records did not enter it at all
  before.

### Facade manifest

`hmcpctl.api.__all__` is exactly six names: `ConfigError`, `HMCClient`, `HMCConfig`,
`HMCError`, `HMCTransportError`, and `TLSVerificationDisabledWarning`
(`tests/unit/test_public_api.py`). This is the first manifest a release ships. Earlier drafts
of this changelog recorded a 127-name `hmc_mcp.api` manifest and its deltas; no release shipped
them, and the operations they named are now pre-release domain-module APIs
([Python library](docs/python-api.md)).

[unreleased]: https://github.com/randomparity/hmc-mcp/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/randomparity/hmc-mcp/releases/tag/v0.1.0
