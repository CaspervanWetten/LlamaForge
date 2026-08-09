---
title: Troubleshooting
section: troubleshooting
order: 1
---

# Troubleshooting

## Inline load-failure diagnosis

When a model fails to load, the Models tab doesn't just show you a blank error — it calls `GET /api/model/diag?model=<id>`, which runs the router's last 120 log lines through `backend/diag.py`'s `diagnose()` function and renders the result inline (`.faildiag` block in `web/js/models.js`) instead of making you scroll the Router Log panel.

While the diagnosis is loading, the row shows *"reading the router log..."*. If the log doesn't match a known failure pattern, it shows *"Load failed, but no specific cause was found in the router log - see the Router Log panel below."*

`diagnose()` checks the log (case-insensitively) against an ordered list of regex rules, most specific first, and returns the first match. Some suggestions insert your model's current `n-gpu-layers` / `ctx-size` value, shown below as `{ngl}` / `{ctx}`:

| Log pattern matched | Diagnosis shown | Suggested fix |
|---|---|---|
| `out of memory`, `failed to allocate`, `cudaMalloc failed`, `oom` | Ran out of memory loading the model. | Lower n-gpu-layers (currently `{ngl}`) to offload fewer layers, or reduce ctx-size (currently `{ctx}`) to shrink the KV cache. |
| `cuda error`, `cudart error`, `cudaMalloc`, `cublas`, `ggml_cuda` | GPU/CUDA error while loading. | The build hit a CUDA error. Confirm the GPU has free VRAM (Models tab) and that this llama.cpp build matches your CUDA driver. |
| `not enough space in the context`, `kv_cache`/`kv cache`, `n_ctx` | The context is too large for available memory. | Reduce ctx-size (currently `{ctx}`) - the KV cache scales with it. |
| `unknown argument`, `invalid argument`, `unrecognized`, `error: unknown` | The router rejected a launch flag. | One of the knobs isn't supported by this llama.cpp build. Clear the most recently changed knob, or rebuild from the Build tab. |
| `no such file`, `does not exist`, `failed to open gguf`, `cannot find the file` | The model file could not be opened. | The GGUF path is missing or moved. Re-scan drives from Setup, or fix the model path. |
| `unsupported`, `unknown model architecture`, `unknown tokenizer`/`unknown pre-tokenizer` | This build can't run this model. | The architecture/quant isn't supported by the current build. Update llama.cpp from the Build tab. |
| `failed to load model`, `error loading model`, `llama_model_load`/`llama_load` | The model failed to load. | Check the Router Log below for the exact llama.cpp line. Common causes: too little VRAM (reduce n-gpu-layers, currently `{ngl}`) or a corrupt download. |

The "Diagnosis shown" text is replaced by the actual last error-ish line from the log when one exists (the log's own wording takes priority over the generic label above it). If no rule matches but the log's last relevant line still looks like an error, LlamaForge shows that line with the fallback fix *"See the Router Log below for full context."*

> [!TIP]
> If none of this is enough, the Router Log panel on the Models tab has the full untruncated output — `diagnose()` only ever looks at the last 120 lines.

## Setup tab: missing prerequisites

The **Setup** tab (`backend/prereqs.py`) checks for `git`, `cmake`, `ninja`, and `python` (via `<tool> --version`), a C++ compiler, and CUDA, and reports whether each can be auto-installed on your platform.

| Issue | Cause | Fix |
|---|---|---|
| A tool shows as missing (git/cmake/ninja/python) | Not found on `PATH` (`shutil.which`) | On Windows/macOS, click install from the Setup tab (winget/choco, or Homebrew). On Linux, the dashboard never runs `sudo` — it shows the exact `apt`/`dnf`/`pacman` command to run yourself. |
| C++ compiler not found | Windows: no MSVC install with the "Desktop development with C++" workload found via `vswhere.exe` (or a `cl.exe` scan under `Program Files`). Linux/macOS: neither `clang++` nor `g++` on `PATH`. | Windows: install Build Tools for Visual Studio with the C++ workload. macOS: `xcode-select --install`. Linux: install `g++` or `clang++` via your package manager. |
| CUDA not found | No `CUDA_PATH` set and `nvcc` not on `PATH`. Not applicable on macOS (Metal is used instead — the row is hidden). | Only needed for NVIDIA GPU builds; install from https://developer.nvidia.com/cuda-downloads, or build CPU-only. |
| Install button does nothing / fails on Windows | Neither `winget` nor `choco` is available, or the install command exited non-zero. | Install the tool manually from the URL shown for that tool in the Setup tab. |
| Install fails on macOS | Homebrew isn't installed. | Install Homebrew (https://brew.sh) first, or install the tool manually. |

## Bootstrap script issues

`bootstrap.ps1` (Windows) and `bootstrap.sh` (Linux/macOS) get a fresh checkout to the point where the dashboard can take over.

- **"Python not found" (Windows) / "python3 not found" (Linux/macOS)** — Python 3.10+ is required to run the backend. `bootstrap.ps1` offers to install Python 3.12 via winget; without winget it points you to https://www.python.org/downloads/windows/. `bootstrap.sh` prints `brew install python@3.12` on macOS or a `sudo apt-get install -y python3`-style hint on Linux, then exits — it does not install Python for you.
- **"Git not found"** — Git is recommended for fetching/updating llama.cpp. `bootstrap.ps1` offers to install it via winget; `bootstrap.sh` prints the platform-appropriate install command. Bootstrap continues either way; you can clone llama.cpp manually later.
- **"llama.cpp source not found at `<path>`"** — `config.json`'s `llama_src` doesn't point at a git checkout. Answer `y` to clone it (needs Git), or point `llama_src` in `config.json` at an existing checkout and re-run.
- **Re-run bootstrap after installing Python** — `bootstrap.ps1` exits after installing Python and asks you to open a new terminal so `PATH` picks it up, then run bootstrap again.

## First run

- **`config.json` / `models.ini` missing** — no longer fatal. The launchers copy `config.example.json` to `config.json` on a fresh checkout, and a `[*]`-only `models.ini` is created if absent (the router won't start without it). Set your real paths in the Setup tab afterward.
- **Router port already in use** — port `8080` collides with XAMPP/Apache and other dev servers. `run.ps1`/`run.sh` now name the process holding `router_port` and skip starting the router instead of leaving every model showing "offline" for no visible reason; free the port or change `router_port` in Setup.
- **All models "offline" / zero models after moving the folder** — a relative `models_ini` (the shipped default `./models.ini`) is now anchored to the repo root, so the router no longer reads an empty registry when launched from another directory. If you still see this, check `models_ini` in `config.json` points at the right file.
- **Build shows "built, with warnings"** — `llama-server` built fine but a non-essential step (usually the npm/`sharp` UI assets on Windows) failed. The binary is usable; the failing step is in the Build Log. This is distinct from a red **BUILD FAILED**, which means no fresh `llama-server` was produced.

## Everything else

- **Dashboard won't open** — `run.ps1`/`run.sh` skip starting the router or dashboard if something is already listening on `router_port` (default `8080`) or `panel_port` (default `8090`); check nothing else on your machine is bound to those ports.
- **Shutting everything down cleanly** — use `stop.ps1` (Windows) or `stop.sh` (Linux/macOS) rather than killing windows manually; they stop the dashboard, the router, and every `llama-server` process the router spawned (and, on Windows, any `vllm serve` process running inside WSL).
- **vLLM startup looks stuck** — vLLM has no hot reload, so saving knobs on a loaded model restarts it; startup can take 1–5 minutes. Watch the vLLM Log panel rather than assuming it hung.
