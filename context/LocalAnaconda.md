# Local Anaconda Guidance

These instructions are for downstream AI agents working in this repo on this William Zipse's work computer.

## What we learned

- Do not assume `python`, `py`, or `conda` are usable from the default shell.
- In this environment, `py` was not available.
- `conda` was not on `PATH`.
- `where.exe python` resolved only to `C:\Users\wzipse\AppData\Local\Microsoft\WindowsApps\python.exe`, which is not a reliable interpreter for project work.
- `C:\Users\wzipse\.anaconda` existed, but it only contained config data and was not the Anaconda install root.
- Jupyter notebook metadata in this repo used the kernel name `python3` with display name `Python 3 (ipykernel)`.
- `PyWaffle` is installed in the user's Anaconda environment on this computer.
- The preferred Anaconda install is the user-scoped install under `C:\Users\wzipse\AppData\Local\anaconda3`, not the ArcGIS-managed Python environment.

## Recommended operating pattern

1. First, assume the Anaconda install is present but not exposed globally.
2. Prefer using the user's Jupyter kernel when the task is notebook-only.
3. If you need to run Python from the terminal, locate the actual interpreter path before proceeding.
4. Use an absolute interpreter path once found. Do not rely on `python`, `py`, or `conda` aliases.

## Discovery steps

Try these in order:

1. Check notebook metadata for the expected kernel:

```powershell
$nb = Get-Content .\SomeNotebook.ipynb -Raw | ConvertFrom-Json
$nb.metadata.kernelspec | Format-List *
```

2. Check for Jupyter kernel specs on disk:

```powershell
Get-ChildItem "$env:APPDATA\\jupyter\\kernels" -Recurse -Filter kernel.json -ErrorAction SilentlyContinue
Get-ChildItem "$env:LOCALAPPDATA\\jupyter\\kernels" -Recurse -Filter kernel.json -ErrorAction SilentlyContinue
```

3. If a `kernel.json` is found, inspect its `argv` entry to get the real Python path.

4. If no kernels are visible, search common install roots explicitly:

```powershell
$paths = @(
  'C:\Users\wzipse\AppData\Local\anaconda3\python.exe',
  'C:\Users\wzipse\Anaconda3\python.exe',
  'C:\Users\wzipse\miniconda3\python.exe',
  'C:\ProgramData\anaconda3\python.exe'
)
foreach ($p in $paths) { if (Test-Path $p) { $p } }
```

## Confirmed preferred Python path (April 2026)

The preferred interpreter for this machine is the user-scoped Anaconda install:

```
C:\Users\wzipse\AppData\Local\anaconda3\python.exe
```

- Python version: 3.13.9
- Includes: pandas, requests, matplotlib, tkinter, PyWaffle
- This is the interpreter to use by default for FIA scripts in this repo.

Run a script directly:

```powershell
& "C:\Users\wzipse\AppData\Local\anaconda3\python.exe" BatchQuery.py
```

The matching conda executable is:

```powershell
C:\Users\wzipse\AppData\Local\anaconda3\Scripts\conda.exe
```

Verification that led here:

- `C:\Users\wzipse\AppData\Local\anaconda3\python.exe --version` returned `Python 3.13.9`
- Import checks confirmed `pandas`, `requests`, `matplotlib`, `tkinter`, and `pywaffle`

## ArcGIS Python fallback

An ArcGIS-managed Python environment may also exist on this machine, but it should be treated as a fallback only. Prefer the user-scoped Anaconda install for general programming work in this repo.

## Related local network notes

If Python can reach the interpreter but HTTPS requests fail because of proxy or certificate behavior on the office network, also read:

- [TrentonNetworkOperating.md](/c:/Users/wzipse/Documents/dev/fiaaitest/TrentonNetworkOperating.md)

That file documents the sandbox proxy issue, local SSL certificate failures, and the safe fallback pattern that worked for FIA API requests on this machine.

5. If that still fails, ask the user for the exact Anaconda interpreter path or the environment name.

## How to run once the path is known

Use the absolute executable directly:

```powershell
& 'C:\full\path\to\python.exe' script.py
```

For inline checks:

```powershell
@'
print("hello")
'@ | & 'C:\full\path\to\python.exe' -
```

If `conda.exe` is found, it is still better to prefer a direct interpreter path for one-off automation because shell activation is often brittle.

## Notebook-specific guidance

- If the user only wants a notebook created or edited, you may not need terminal Python at all.
- It is acceptable to write a valid `.ipynb` file directly and let the user run it inside Jupyter or their IDE.
- If live API validation is needed and Python is not callable, PowerShell web requests can be used as a temporary verification method.
- If a notebook needs waffle charts, prefer using `PyWaffle` rather than recreating a custom waffle chart implementation.

## Practical fallback used successfully here

- The FIA API request was validated with PowerShell `Invoke-RestMethod`.
- The notebook JSON was validated with `ConvertFrom-Json`.
- This allowed progress without needing globally available Python.

## What not to assume

- Do not assume `C:\Users\wzipse\.anaconda` is the install root.
- Do not assume `where python` finds the usable interpreter.
- Do not assume `conda activate` will work in the default shell session.

## When to escalate

- If a live network validation is important and blocked by sandbox/network restrictions, request approval and rerun the command with escalation.
- If locating the interpreter is necessary for the task and local discovery fails, pause and ask the user for the exact Anaconda path rather than guessing.
