# Manual pbi-tools extract – debug missing Report folder

Run these in PowerShell from the **repo root** to verify extract and debug why some reports get no `Report/sections/` (e.g. Global Marketing, Spotify).

**Important:** You must use the call operator `&` before the exe path (e.g. `& $PbiToolsExe ...`). Without `&`, PowerShell treats `extract` as a separate token and errors.

## 1. Set paths (edit to your .pbix and exe)

```powershell
$RepoRoot = "C:\squareshift\powerbi\powerbi_to_looker_parser"
$PbiToolsExe = "$RepoRoot\pbi-tools\pbi-tools.1.2.0\pbi-tools.exe"
$PbixPath   = "$RepoRoot\collector_output\Global Marketing & Customer Insights Dashboard_ad094011.pbix"
$OutLong    = "$RepoRoot\parsed_output\Global Marketing & Customer Insights Dashboard_ad094011"
$OutShort   = "C:\p\test_global_marketing"
```

## 2. Extract to long path (same as script – may fail for Report)

Use `&` before the exe:

```powershell
& $PbiToolsExe extract $PbixPath -extractFolder $OutLong -modelSerialization Raw
```

Check exit code and stdout. If you see `DirectoryNotFoundException` or non-zero exit, note the path in the error.

## 3. Extract to short path (test path-length / long-path)

```powershell
New-Item -ItemType Directory -Force -Path "C:\p" | Out-Null
& $PbiToolsExe extract $PbixPath -extractFolder $OutShort -modelSerialization Raw
```

Then check whether `Report` exists:

```powershell
Get-ChildItem -Path $OutShort -Recurse -Directory | Where-Object { $_.Name -eq "Report" }
Get-ChildItem -Path "$OutShort\Report\sections" -ErrorAction SilentlyContinue
```

If `Report/sections` appears with the short path but not with the long path, the issue is path length or long-path support.

## 4. One-liner (copy-paste, run from repo root; no variables)

**Long path (repo):** Use `&` to run the .exe.

```powershell
cd C:\squareshift\powerbi\powerbi_to_looker_parser
& ".\pbi-tools\pbi-tools.1.2.0\pbi-tools.exe" extract ".\collector_output\Global Marketing & Customer Insights Dashboard_ad094011.pbix" -extractFolder ".\parsed_output\Global_Marketing_test" -modelSerialization Raw
```

**Short path:**

```powershell
cd C:\squareshift\powerbi\powerbi_to_looker_parser
& ".\pbi-tools\pbi-tools.1.2.0\pbi-tools.exe" extract ".\collector_output\Global Marketing & Customer Insights Dashboard_ad094011.pbix" -extractFolder "C:\p\test_global_marketing" -modelSerialization Raw
```

## 5. Validate long paths (Windows)

```powershell
powershell -ExecutionPolicy Bypass -File scripts/validate_long_paths.ps1
```

Expect: `OK: Long paths are ENABLED (LongPathsEnabled = 1)`.

---

## 6. If extract "succeeds" but there is no Report folder

If the log shows "Completed" but only lists Version, Connections, ReportMetadata, ReportSettings, DiagramLayout, LinguisticSchema, Model, StaticResources (and no "Report" or "sections"), then pbi-tools did not write the Report tree for that .pbix. This is not a path-length issue.

Possible causes:
- **pbi-tools version or mode:** Some versions or serialization modes may not extract Report/sections for all reports (e.g. report format 1.32 or certain layouts).
- **Report content:** The way this report’s pages/sections are stored might not be serialized to disk by this build.

Next steps:
1. Check whether `C:\p\test_global_marketing\Report` exists; if not, the tool simply didn’t write it.
2. Check pbi-tools release notes / GitHub for "Report" extraction or known limitations.
3. Try a different report that you know produces Report/sections (e.g. University Analytics) with the same exe to confirm the exe can write Report when it’s supported.
4. For reports where Report is never written, dashboard/viz details would need another source (e.g. Power BI API, or a different tool).
