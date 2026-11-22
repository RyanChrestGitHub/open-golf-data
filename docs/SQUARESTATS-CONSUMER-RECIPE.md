# Read two metrics from an existing published fixture

This recipe configures the existing local tools for one third-party CSV already
listed in the [public source manifest](../test-fixtures/square-stats/manifest.json).
It adds no adapter or dataset. The source is pinned by SHA-256, not a newly copied
identifying filename. Review the [fixture handling and source notes](../test-fixtures/square-stats/README.md)
before use; publication of the original does not authorize every derived use.

From a fresh checkout containing this recipe, use Python 3.10+ and PowerShell.
Run at the repository root, within your authorized local handling scope. Choose a
new private working directory outside the checkout; the example prompts for it.
These commands read real source rows and create local copies and output. They are
instructions for an authorized consumer, not permission to repeat a prior test.

```powershell
$digest = '3e01416ef5e9409d7f791c1b47c3b6a9b10a00bb58fca9db3e28f115a67c6b35'
$base = Resolve-Path 'test-fixtures/square-stats'
$manifest = Get-Content (Join-Path $base 'manifest.json') -Raw | ConvertFrom-Json
$entries = @($manifest.files | Where-Object sha256 -eq $digest)
if ($entries.Count -ne 1) { throw 'Expected one pinned manifest entry' }
$source = Join-Path $base $entries[0].path
if ((Get-FileHash -LiteralPath $source -Algorithm SHA256).Hash.ToLowerInvariant() -ne $digest) { throw 'Source digest mismatch' }
$work = Read-Host 'New absolute private working directory outside the checkout'
if (-not [IO.Path]::IsPathRooted($work) -or (Test-Path -LiteralPath $work)) { throw 'Use a new absolute directory' }
New-Item -ItemType Directory -Path $work -ErrorAction Stop | Out-Null
$stage = Join-Path $work 'evidence'
python -m open_golf_data evidence "$source" --output "$stage"
if ($LASTEXITCODE -ne 0) { throw 'Staging failed' }
$evidence = Join-Path $stage ('ev-' + $digest.Substring(0,24))
python -m open_golf_data verify-evidence "$evidence"
if ($LASTEXITCODE -ne 0) { throw 'Verification failed' }
$archive = Join-Path $work 'projection.json'
python -m open_golf_data project-csv "$evidence" --config examples/squarestats_projection.json --output "$archive"
if ($LASTEXITCODE -ne 0) { throw 'Projection failed' }
python -m open_golf_data metric-view "$archive" --mappings examples/squarestats_mappings.json --source-sha256 $digest --key ball_speed
if ($LASTEXITCODE -ne 0) { throw 'Metric view failed' }
python -m open_golf_data metric-view "$archive" --mappings examples/squarestats_mappings.json --source-sha256 $digest --key carry_distance
if ($LASTEXITCODE -ne 0) { throw 'Metric view failed' }
```

The [projection config](../examples/squarestats_projection.json) selects header
record 3 and parsed records 4–6, retaining only `Ball Speed(mph)` / `mph` and
`Carry(yd)` / `yd` in the separate archive. Record ordinals are one-based parsed
CSV records, not physical lines. Other fields remain in the unchanged original.
The [two explicit mappings](../examples/squarestats_mappings.json) expose
`ball_speed` and `carry_distance`, both tentative with kind `unknown`. Successful
views retain lexical cells and order, report `declared` unit status, and perform
no conversion, arithmetic, identity inference or event association. Declared unit
agreement does not verify metric meaning. No output values are reproduced here.

The manifest pins upstream revision `11a4d7225cf5a13633a3afa7e8c433eb250c02a6`.
The fixture's native, processed, transcribed or physical origin is unknown.
Square Omni is a maintainer report, not independently established hardware
compatibility. Exact firmware/software versions are unknown; the manifest's
newest-at-source-date assumption is unverified. Upstream licensing was not
identified and no source-author permission response was received; the existing
maintainer-authorized import does not relicense source terms. This is an archival
representation, not a hardware, authenticated golfer, adoption or efficiency claim.

Keep staged bytes, receipts, projections and terminal output within the existing
handling scope; they can contain sensitive data. Apply its retention and cleanup
requirements to new copies without altering the original fixture. Do not upload
outputs or commit the working directory. An ignored path is not a privacy control.

The [current tool contract](../README.md) limits projection to 1 MiB, 20 selected
records, strict UTF-8 comma CSV without BOM/NUL and unambiguous headers. Publication
uses a same-directory temporary file and a non-overwriting hard link. A filesystem
or execution environment that denies hard links fails closed; do not weaken that
behavior or overwrite an existing archive to get past a failure. Receipt integrity
does not authenticate provenance or establish independent parser fidelity.

The recipe regression uses invented rows only. It checks configuration wiring,
lexical preservation and wrong-source rejection; it does not replay this fixture
or independently validate its origin or physical measurements.
