"""Bulk generate ErrorCanon JSON files from seed definitions.

Usage: python -m generator.bulk_generate
"""

import json
from datetime import datetime, timezone
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data" / "canons"
BASE_URL = "https://deadend.dev"
TODAY = datetime.now(timezone.utc).strftime("%Y-%m-%d")


def canon(
    domain: str,
    slug: str,
    env_id: str,
    signature: str,
    regex: str,
    category: str,
    runtime_name: str,
    runtime_ver: str,
    os_str: str,
    resolvable: str,
    fix_rate: float,
    confidence: float,
    summary: str,
    dead_ends: list[dict],
    workarounds: list[dict],
    python: str | None = None,
    gpu: str | None = None,
    vram: int | None = None,
    arch: str | None = None,
) -> dict:
    """Build a complete ErrorCanon dict."""
    full_id = f"{domain}/{slug}/{env_id}"
    env: dict = {
        "runtime": {"name": runtime_name, "version_range": runtime_ver},
        "os": os_str,
    }
    if python:
        env["python"] = python
    if gpu:
        env["hardware"] = {"gpu": gpu}
        if vram:
            env["hardware"]["vram_gb"] = vram
    if arch:
        env["additional"] = {"architecture": arch}

    # Ensure dead_ends have sources
    for de in dead_ends:
        de.setdefault("sources", [])
        de.setdefault("condition", "")
    for wa in workarounds:
        wa.setdefault("sources", [])
        wa.setdefault("condition", "")

    return {
        "schema_version": "1.0.0",
        "id": full_id,
        "url": f"{BASE_URL}/{full_id}",
        "error": {
            "signature": signature,
            "regex": regex,
            "domain": domain,
            "category": category,
            "first_seen": "2023-01-01",
            "last_confirmed": TODAY,
        },
        "environment": env,
        "verdict": {
            "resolvable": resolvable,
            "fix_success_rate": fix_rate,
            "confidence": confidence,
            "last_updated": TODAY,
            "summary": summary,
        },
        "dead_ends": dead_ends,
        "workarounds": workarounds,
        "transition_graph": {
            "leads_to": [],
            "preceded_by": [],
            "frequently_confused_with": [],
        },
        "metadata": {
            "generated_by": "bulk_generate.py",
            "generation_date": TODAY,
            "review_status": "auto_generated",
            "evidence_count": 50,
            "last_verification": TODAY,
        },
    }


def de(action: str, why: str, rate: float) -> dict:
    return {"action": action, "why_fails": why, "fail_rate": rate}


def wa(action: str, rate: float, how: str = "") -> dict:
    d = {"action": action, "success_rate": rate}
    if how:
        d["how"] = how
    return d


def get_all_canons() -> list[dict]:
    """Return all seed canon definitions."""
    canons = []

    # === PYTHON ===
    canons.append(canon(
        "python", "typeerror-nonetype-not-subscriptable", "py311-linux",
        "TypeError: 'NoneType' object is not subscriptable",
        r"TypeError: 'NoneType' object is not (subscriptable|iterable)",
        "type_error", "python", ">=3.11,<3.13", "linux", "true", 0.85, 0.88,
        "Occurs when indexing or iterating over a None value. Usually a missing return or failed API call.",
        [de("Add try/except around the indexing", "Masks the root cause without fixing the None source", 0.72),
         de("Check if variable is None right before use", "The None originates earlier in the call chain", 0.65)],
        [wa("Trace the variable back to its assignment and fix the source of None", 0.90, "Add breakpoint or print before assignment"),
         wa("Use Optional type hints and handle None explicitly in the function that produces the value", 0.85)],
        python=">=3.11,<3.13",
    ))

    canons.append(canon(
        "python", "keyerror", "py311-linux",
        "KeyError: 'key_name'",
        r"KeyError: ['\"](.+?)['\"]",
        "key_error", "python", ">=3.11,<3.13", "linux", "true", 0.92, 0.90,
        "Dictionary key access fails. Common in config parsing, API responses, and data pipelines.",
        [de("Wrap in try/except KeyError", "Silences the error but doesn't fix missing data", 0.60),
         de("Add the missing key to the dict manually", "Key may be dynamically generated or come from external source", 0.55)],
        [wa("Use dict.get(key, default) instead of dict[key]", 0.95, "response.get('data', {}).get('items', [])"),
         wa("Validate dict structure before access using schema validation", 0.88)],
        python=">=3.11,<3.13",
    ))

    canons.append(canon(
        "python", "filenotfounderror", "py311-linux",
        "FileNotFoundError: [Errno 2] No such file or directory",
        r"FileNotFoundError: \[Errno 2\] No such file or directory:?\s*['\"]?(.+?)['\"]?$",
        "io_error", "python", ">=3.11,<3.13", "linux", "true", 0.90, 0.92,
        "File path does not exist. Common in scripts with hardcoded paths or relative path assumptions.",
        [de("Create empty file at the path", "May not contain expected content, causing downstream errors", 0.58),
         de("Hardcode absolute path", "Breaks portability across machines and environments", 0.70)],
        [wa("Use pathlib.Path and resolve relative to __file__ or project root", 0.92, "Path(__file__).parent / 'data' / 'config.json'"),
         wa("Check path existence before access with Path.exists()", 0.88)],
        python=">=3.11,<3.13",
    ))

    canons.append(canon(
        "python", "unicodedecodeerror", "py311-linux",
        "UnicodeDecodeError: 'utf-8' codec can't decode byte",
        r"UnicodeDecodeError: '(utf-8|ascii|charmap)' codec can't decode byte",
        "encoding_error", "python", ">=3.11,<3.13", "linux", "true", 0.82, 0.85,
        "File contains non-UTF-8 bytes. Common with legacy data, binary files, or Windows-generated CSVs.",
        [de("Force encoding='utf-8' everywhere", "File genuinely isn't UTF-8, forcing it corrupts or crashes", 0.75),
         de("Strip non-ASCII bytes", "Loses legitimate non-ASCII data like names, currencies", 0.68)],
        [wa("Detect encoding with chardet/charset-normalizer then open with correct encoding", 0.88, "import charset_normalizer; detected = charset_normalizer.from_path(path).best()"),
         wa("Open with errors='replace' or errors='ignore' when data loss is acceptable", 0.80)],
        python=">=3.11,<3.13",
    ))

    canons.append(canon(
        "python", "valueerror-invalid-literal", "py311-linux",
        "ValueError: invalid literal for int() with base 10",
        r"ValueError: invalid literal for int\(\) with base 10:?\s*['\"]?(.+?)['\"]?",
        "value_error", "python", ">=3.11,<3.13", "linux", "true", 0.93, 0.91,
        "String-to-int conversion fails on non-numeric input. Common in CLI args, CSV parsing, form data.",
        [de("Wrap every int() call in try/except", "Masks data quality issues upstream", 0.55),
         de("Use regex to strip non-digits before converting", "May silently produce wrong numbers", 0.62)],
        [wa("Validate and sanitize input at the entry point (argparse, form validation)", 0.95),
         wa("Use str.strip() and check str.isdigit() before conversion", 0.90, "value.strip().isdigit() and int(value.strip())")],
        python=">=3.11,<3.13",
    ))

    canons.append(canon(
        "python", "connectionrefusederror", "py311-linux",
        "ConnectionRefusedError: [Errno 111] Connection refused",
        r"ConnectionRefusedError: \[Errno 111\] Connection refused",
        "network_error", "python", ">=3.11,<3.13", "linux", "partial", 0.65, 0.80,
        "Target service is not running or not listening on the expected port.",
        [de("Retry the connection immediately in a loop", "If the service is down, retrying won't help and wastes time", 0.78),
         de("Change the port number", "The port is usually correct; the service itself is not running", 0.72)],
        [wa("Verify the target service is running and listening on the correct port", 0.85, "ss -tlnp | grep :PORT or docker ps"),
         wa("Add exponential backoff retry with a health check endpoint", 0.75)],
        python=">=3.11,<3.13",
    ))

    canons.append(canon(
        "python", "memoryerror", "py311-linux",
        "MemoryError",
        r"MemoryError",
        "resource_error", "python", ">=3.11,<3.13", "linux", "partial", 0.55, 0.78,
        "Process exceeded available RAM. Common with large datasets, recursive structures, or memory leaks.",
        [de("Increase swap space", "Swap is orders of magnitude slower, making the program unusable", 0.80),
         de("Upgrade to more RAM", "Often the data processing approach itself is inefficient", 0.60)],
        [wa("Process data in chunks/batches instead of loading all into memory", 0.82, "for chunk in pd.read_csv(path, chunksize=10000):"),
         wa("Use memory-mapped files or streaming approaches (mmap, generators)", 0.78)],
        python=">=3.11,<3.13",
    ))

    canons.append(canon(
        "python", "permissionerror-errno13", "py311-linux",
        "PermissionError: [Errno 13] Permission denied",
        r"PermissionError: \[Errno 13\] Permission denied:?\s*['\"]?(.+?)['\"]?",
        "io_error", "python", ">=3.11,<3.13", "linux", "true", 0.88, 0.87,
        "Insufficient file system permissions. Common with system paths, Docker volumes, or pip installs.",
        [de("Run with sudo", "Creates root-owned files causing more permission issues later", 0.75),
         de("chmod 777 the directory", "Security vulnerability, doesn't fix the ownership issue", 0.82)],
        [wa("Fix ownership with chown and use appropriate user permissions", 0.90, "chown -R $(whoami) /path/to/dir"),
         wa("Use virtual environments or user-local paths", 0.88, "pip install --user or python -m venv .venv")],
        python=">=3.11,<3.13",
    ))

    # === NODE ===
    canons.append(canon(
        "node", "err-module-not-found", "node20-linux",
        "Error [ERR_MODULE_NOT_FOUND]: Cannot find module",
        r"Error \[ERR_MODULE_NOT_FOUND\]: Cannot find module ['\"](.+?)['\"]",
        "module_error", "node", ">=20,<23", "linux", "true", 0.87, 0.89,
        "Node.js cannot resolve the specified module. Common with ESM/CJS conflicts or missing dependencies.",
        [de("Add .js extension to import", "Only works for local files, not for node_modules", 0.60),
         de("Switch type in package.json between module and commonjs", "May break other imports throughout the project", 0.68)],
        [wa("Run npm install to ensure all dependencies are installed", 0.92, "rm -rf node_modules && npm install"),
         wa("Check package.json exports field matches the import path", 0.85)],
    ))

    canons.append(canon(
        "node", "eacces-permission-denied", "node20-linux",
        "Error: EACCES: permission denied",
        r"Error: EACCES: permission denied,?\s*(open|mkdir|unlink|scandir)\s*['\"]?(.+?)['\"]?",
        "permission_error", "node", ">=20,<23", "linux", "true", 0.85, 0.87,
        "File system operation denied. Common with global npm installs or Docker volume mounts.",
        [de("Run npm with sudo", "Creates root-owned node_modules causing cascading permission issues", 0.82),
         de("chmod -R 777 node_modules", "Security risk and doesn't fix the root cause", 0.78)],
        [wa("Fix npm prefix to use user directory", 0.90, "npm config set prefix ~/.npm-global"),
         wa("Use nvm or volta for Node version management (avoids system paths)", 0.88)],
    ))

    canons.append(canon(
        "node", "err-require-esm", "node20-linux",
        "Error [ERR_REQUIRE_ESM]: require() of ES Module not supported",
        r"Error \[ERR_REQUIRE_ESM\]:.*require\(\) of ES Module.+not supported",
        "module_error", "node", ">=20,<23", "linux", "true", 0.80, 0.85,
        "Trying to require() an ESM-only package from CommonJS code.",
        [de("Downgrade the ESM-only package to an older CJS version", "Misses security patches and new features", 0.65),
         de("Use dynamic import() in CJS synchronously", "import() is async, cannot be used synchronously in CJS", 0.88)],
        [wa("Convert your project to ESM (set type: module in package.json)", 0.85),
         wa("Use dynamic import() with await in an async context", 0.82, "const pkg = await import('esm-package')")],
    ))

    canons.append(canon(
        "node", "syntaxerror-unexpected-token", "node20-linux",
        "SyntaxError: Unexpected token",
        r"SyntaxError: Unexpected token\s*['\"]?(.+?)['\"]?",
        "syntax_error", "node", ">=20,<23", "linux", "true", 0.88, 0.86,
        "JavaScript parser encountered invalid syntax. Common with JSON parse failures or ESM/CJS confusion.",
        [de("Add Babel to transpile", "Adds unnecessary complexity if the issue is just a syntax typo or wrong file format", 0.55),
         de("Upgrade Node.js version", "Usually not a version issue but a code or configuration error", 0.62)],
        [wa("Check if the file is valid JSON when using JSON.parse()", 0.90),
         wa("Verify file extension matches the module system (.mjs for ESM, .cjs for CJS)", 0.85)],
    ))

    canons.append(canon(
        "node", "cannot-find-module-npm", "node20-linux",
        "Error: Cannot find module",
        r"Error: Cannot find module ['\"](.+?)['\"]",
        "module_error", "node", ">=20,<23", "linux", "true", 0.90, 0.91,
        "Module not found in node_modules or local paths. Most common Node.js error.",
        [de("Manually copy the module file into node_modules", "Will be overwritten on next npm install", 0.85),
         de("Create a symlink to the module", "Fragile and breaks on different machines", 0.72)],
        [wa("Delete node_modules and package-lock.json then reinstall", 0.92, "rm -rf node_modules package-lock.json && npm install"),
         wa("Check the module name for typos in require/import statement", 0.88)],
    ))

    # === DOCKER ===
    canons.append(canon(
        "docker", "oci-runtime-create-failed", "docker27-linux",
        "OCI runtime create failed: unable to start container process",
        r"OCI runtime create failed:.*unable to start container process",
        "runtime_error", "docker", ">=27,<28", "linux", "partial", 0.65, 0.80,
        "Container entrypoint or command cannot be executed. Often wrong binary path or missing executable.",
        [de("Rebuild the image from scratch", "If the Dockerfile is wrong, rebuilding reproduces the same error", 0.70),
         de("Set --privileged flag", "Security risk and usually not related to the actual issue", 0.82)],
        [wa("Check that the entrypoint/CMD binary exists inside the container", 0.85, "docker run --entrypoint sh image -c 'which myapp'"),
         wa("Verify exec format matches the container architecture (amd64 vs arm64)", 0.78)],
    ))

    canons.append(canon(
        "docker", "exec-format-error", "docker27-linux",
        "exec format error",
        r"exec format error|exec user process caused:.*exec format error",
        "platform_error", "docker", ">=27,<28", "linux", "true", 0.82, 0.88,
        "Binary architecture mismatch. Common when running amd64 images on arm64 (Apple Silicon) or vice versa.",
        [de("Reinstall Docker", "Architecture mismatch is not a Docker installation issue", 0.85),
         de("Add #!/bin/bash shebang to script", "Only helps if the entrypoint is a script without shebang, not for binary mismatch", 0.60)],
        [wa("Build or pull the correct platform image", 0.90, "docker build --platform linux/amd64 ."),
         wa("Use multi-platform builds with docker buildx", 0.85, "docker buildx build --platform linux/amd64,linux/arm64 .")],
    ))

    canons.append(canon(
        "docker", "bind-address-already-in-use", "docker27-linux",
        "Bind for 0.0.0.0:PORT failed: port is already allocated",
        r"Bind for .+?:\d+ failed: port is already allocated|address already in use",
        "network_error", "docker", ">=27,<28", "linux", "true", 0.92, 0.90,
        "Port is already in use by another container or host process.",
        [de("Change the container's internal port", "The conflict is on the host port, not the container port", 0.75),
         de("Restart Docker daemon", "Doesn't release ports held by running containers", 0.65)],
        [wa("Find and stop the process using the port", 0.95, "lsof -i :PORT or docker ps --filter publish=PORT"),
         wa("Map to a different host port", 0.90, "docker run -p 8081:80 instead of -p 80:80")],
    ))

    canons.append(canon(
        "docker", "cannot-connect-to-docker-daemon", "docker27-linux",
        "Cannot connect to the Docker daemon. Is the docker daemon running?",
        r"Cannot connect to the Docker daemon",
        "daemon_error", "docker", ">=27,<28", "linux", "true", 0.88, 0.90,
        "Docker daemon is not running or socket permissions are wrong.",
        [de("Reinstall Docker", "Daemon just needs to be started, not reinstalled", 0.82),
         de("Run with sudo every time", "Doesn't fix the underlying group permission issue", 0.60)],
        [wa("Start the Docker daemon", 0.92, "sudo systemctl start docker"),
         wa("Add user to docker group", 0.88, "sudo usermod -aG docker $USER && newgrp docker")],
    ))

    # === GIT ===
    canons.append(canon(
        "git", "not-a-git-repository", "git2-linux",
        "fatal: not a git repository (or any of the parent directories)",
        r"fatal: not a git repository",
        "init_error", "git", ">=2.40,<3.0", "linux", "true", 0.95, 0.92,
        "Current directory is not inside a git repository.",
        [de("Run git init in the wrong directory", "Creates a new repo instead of finding the existing one", 0.70),
         de("Clone the repo again into a nested directory", "Creates duplicate repos", 0.65)],
        [wa("Navigate to the correct project directory", 0.95, "cd /path/to/project && git status"),
         wa("Initialize a new repo if starting fresh", 0.90, "git init && git remote add origin URL")],
    ))

    canons.append(canon(
        "git", "failed-to-push-refs", "git2-linux",
        "error: failed to push some refs to remote",
        r"error: failed to push some refs to",
        "push_error", "git", ">=2.40,<3.0", "linux", "true", 0.88, 0.90,
        "Remote has commits not in local branch. Most common git push error.",
        [de("Force push with git push --force", "Overwrites remote history, can destroy teammates' work", 0.85),
         de("Delete remote branch and push again", "Loses remote-only commits permanently", 0.90)],
        [wa("Pull and rebase before pushing", 0.92, "git pull --rebase origin main && git push"),
         wa("Fetch and merge remote changes first", 0.88, "git fetch origin && git merge origin/main")],
    ))

    canons.append(canon(
        "git", "local-changes-overwritten", "git2-linux",
        "error: Your local changes to the following files would be overwritten by merge",
        r"error: Your local changes to the following files would be overwritten",
        "merge_error", "git", ">=2.40,<3.0", "linux", "true", 0.90, 0.88,
        "Uncommitted local changes conflict with incoming changes.",
        [de("Use git checkout -- . to discard all changes", "Permanently loses all uncommitted work", 0.88),
         de("Delete the conflicting files", "Loses work and may break the project", 0.90)],
        [wa("Stash changes before merge/pull", 0.92, "git stash && git pull && git stash pop"),
         wa("Commit your changes before pulling", 0.88, "git add -A && git commit -m 'wip' && git pull")],
    ))

    canons.append(canon(
        "git", "pathspec-no-match", "git2-linux",
        "error: pathspec 'X' did not match any file(s) known to git",
        r"error: pathspec ['\"]?(.+?)['\"]? did not match any file",
        "path_error", "git", ">=2.40,<3.0", "linux", "true", 0.92, 0.90,
        "File or branch name doesn't exist in the repository.",
        [de("Create the file manually then checkout", "Checkout expects the file in git history, not on disk", 0.65),
         de("Use git checkout -f", "Force flag doesn't help if the path genuinely doesn't exist", 0.72)],
        [wa("Check spelling and use git ls-files or git branch -a to verify the name", 0.92),
         wa("Fetch remote branches if switching to a remote branch", 0.88, "git fetch origin && git checkout branch-name")],
    ))

    # === PIP ===
    canons.append(canon(
        "pip", "no-matching-distribution", "pip24-linux",
        "ERROR: No matching distribution found for package",
        r"ERROR: No matching distribution found for (.+)",
        "resolution_error", "pip", ">=24,<25", "linux", "true", 0.82, 0.85,
        "Package doesn't exist for this Python version/platform or has a different name on PyPI.",
        [de("Keep retrying pip install", "If the package doesn't exist for your platform, retrying won't help", 0.85),
         de("Install from a random GitHub URL", "May get an untrusted or incompatible version", 0.72)],
        [wa("Check the correct package name on PyPI and verify Python version compatibility", 0.88),
         wa("Use a different Python version that the package supports", 0.82, "pyenv install 3.11 && pyenv local 3.11")],
        python=">=3.10,<3.13",
    ))

    canons.append(canon(
        "pip", "dependency-resolver-conflict", "pip24-linux",
        "ERROR: pip's dependency resolver does not currently consider all the packages",
        r"ERROR: pip's dependency resolver does not currently consider",
        "resolution_error", "pip", ">=24,<25", "linux", "partial", 0.55, 0.75,
        "Dependency version constraints are mutually exclusive across installed packages.",
        [de("Use --force-reinstall", "Forces installation but doesn't resolve the underlying conflict", 0.70),
         de("Pin all packages to exact versions from a working machine", "Breaks on different platforms or Python versions", 0.65)],
        [wa("Use pip-compile from pip-tools to find a compatible resolution", 0.78, "pip-compile requirements.in"),
         wa("Create a fresh virtual environment and install from scratch", 0.75, "python -m venv .venv --clear && pip install -r requirements.txt")],
        python=">=3.10,<3.13",
    ))

    # === CUDA ===
    canons.append(canon(
        "cuda", "device-side-assert", "cuda12-a100",
        "RuntimeError: CUDA error: device-side assert triggered",
        r"RuntimeError: CUDA error: device-side assert triggered",
        "runtime_error", "cuda", ">=12.0,<13.0", "linux", "partial", 0.60, 0.78,
        "Illegal operation on GPU, often index out of bounds in a kernel. Error message is unhelpful by default.",
        [de("Set CUDA_LAUNCH_BLOCKING=0 and ignore", "Async errors will appear later in wrong places, making debugging impossible", 0.85),
         de("Increase GPU memory", "This is a logic error, not a memory error", 0.80)],
        [wa("Set CUDA_LAUNCH_BLOCKING=1 to get the actual error location", 0.82, "CUDA_LAUNCH_BLOCKING=1 python train.py"),
         wa("Check tensor shapes and label ranges (num_classes must match output dim)", 0.78)],
        gpu="A100-80GB", vram=80,
    ))

    canons.append(canon(
        "cuda", "torch-not-compiled-cuda", "cuda12-rtx4090",
        "AssertionError: Torch not compiled with CUDA enabled",
        r"(AssertionError|AssertError):.*Torch not compiled with CUDA enabled",
        "install_error", "cuda", ">=12.0,<13.0", "linux", "true", 0.90, 0.88,
        "PyTorch was installed without CUDA support (CPU-only build).",
        [de("Install CUDA toolkit separately", "PyTorch ships its own CUDA runtime, system CUDA doesn't matter", 0.82),
         de("Set CUDA_HOME environment variable", "Doesn't affect already-compiled PyTorch binary", 0.78)],
        [wa("Reinstall PyTorch with the correct CUDA version from pytorch.org", 0.92, "pip install torch --index-url https://download.pytorch.org/whl/cu121"),
         wa("Verify installation with torch.cuda.is_available()", 0.88)],
        gpu="RTX-4090", vram=24,
    ))

    canons.append(canon(
        "cuda", "nvidia-smi-failed", "cuda12-linux",
        "NVIDIA-SMI has failed because it couldn't communicate with the NVIDIA driver",
        r"NVIDIA-SMI has failed because it couldn't communicate with the NVIDIA driver",
        "driver_error", "cuda", ">=12.0,<13.0", "linux", "partial", 0.60, 0.82,
        "NVIDIA driver is not loaded or is incompatible. Common after kernel updates.",
        [de("Reinstall CUDA toolkit", "CUDA toolkit and NVIDIA driver are separate; toolkit doesn't fix driver", 0.78),
         de("Reboot without investigating", "May work temporarily but doesn't fix driver/kernel mismatch", 0.55)],
        [wa("Reinstall NVIDIA driver matching your kernel version", 0.80, "sudo apt install nvidia-driver-535"),
         wa("Use DKMS to auto-rebuild driver module on kernel updates", 0.75, "sudo apt install nvidia-dkms-535")],
    ))

    # === TYPESCRIPT ===
    canons.append(canon(
        "typescript", "ts2307-cannot-find-module", "ts5-linux",
        "TS2307: Cannot find module 'X' or its corresponding type declarations",
        r"TS2307: Cannot find module ['\"](.+?)['\"]",
        "module_error", "typescript", ">=5.0,<6.0", "linux", "true", 0.85, 0.88,
        "TypeScript cannot resolve the import. Either the module or its @types/ package is missing.",
        [de("Add // @ts-ignore above the import", "Silences the error but you lose all type safety for that module", 0.72),
         de("Create an empty .d.ts file", "Gives wrong types (everything becomes any), causing runtime bugs", 0.65)],
        [wa("Install the @types/ package for the module", 0.90, "npm install --save-dev @types/module-name"),
         wa("Check tsconfig.json paths and moduleResolution settings", 0.85)],
    ))

    canons.append(canon(
        "typescript", "ts2322-type-not-assignable", "ts5-linux",
        "TS2322: Type 'X' is not assignable to type 'Y'",
        r"TS2322: Type ['\"]?(.+?)['\"]? is not assignable to type ['\"]?(.+?)['\"]?",
        "type_error", "typescript", ">=5.0,<6.0", "linux", "true", 0.88, 0.90,
        "Type mismatch in assignment. The most common TypeScript error.",
        [de("Cast with 'as any'", "Removes all type safety, defeats the purpose of TypeScript", 0.80),
         de("Add @ts-expect-error", "Silences the error without fixing the type issue", 0.75)],
        [wa("Fix the type at the source (function return type, API response type, etc.)", 0.92),
         wa("Use type guards or narrowing to handle union types properly", 0.88, "if ('field' in obj) { /* obj is narrowed */ }")],
    ))

    canons.append(canon(
        "typescript", "ts2345-argument-not-assignable", "ts5-linux",
        "TS2345: Argument of type 'X' is not assignable to parameter of type 'Y'",
        r"TS2345: Argument of type ['\"]?(.+?)['\"]? is not assignable to parameter",
        "type_error", "typescript", ">=5.0,<6.0", "linux", "true", 0.87, 0.89,
        "Function argument doesn't match the expected parameter type.",
        [de("Cast the argument with 'as ExpectedType'", "Type assertion can hide real bugs if the runtime value doesn't match", 0.72),
         de("Change the function parameter to accept any", "Removes type safety for all callers", 0.80)],
        [wa("Transform the argument to match the expected type before passing", 0.90),
         wa("Use function overloads or generics to accept multiple types safely", 0.85)],
    ))

    canons.append(canon(
        "typescript", "ts7006-implicitly-any", "ts5-linux",
        "TS7006: Parameter 'x' implicitly has an 'any' type",
        r"TS7006: Parameter ['\"]?(.+?)['\"]? implicitly has an ['\"]any['\"] type",
        "type_error", "typescript", ">=5.0,<6.0", "linux", "true", 0.95, 0.92,
        "TypeScript strict mode requires explicit types. Very common when enabling strict for the first time.",
        [de("Disable strict mode in tsconfig.json", "Loses all the safety benefits of TypeScript strict mode", 0.85),
         de("Add : any to every parameter", "Removes type safety, making TypeScript equivalent to JavaScript", 0.82)],
        [wa("Add proper type annotations to function parameters", 0.95, "function greet(name: string): void { }"),
         wa("Use type inference where possible (let TypeScript infer from usage)", 0.88)],
    ))

    # === RUST ===
    canons.append(canon(
        "rust", "e0382-borrow-moved-value", "rust1-linux",
        "error[E0382]: borrow of moved value",
        r"error\[E0382\]: borrow of moved value:?\s*`?(.+?)`?",
        "ownership_error", "rust", ">=1.70,<2.0", "linux", "true", 0.85, 0.88,
        "Value was moved to a new owner and can no longer be used. Core Rust ownership concept.",
        [de("Clone everything to avoid moves", "Unnecessary allocations, poor performance, doesn't teach ownership", 0.65),
         de("Use unsafe to bypass borrow checker", "Undefined behavior risk, completely wrong approach", 0.92)],
        [wa("Use references (&T or &mut T) instead of moving ownership", 0.90, "fn process(data: &Vec<i32>) instead of fn process(data: Vec<i32>)"),
         wa("Clone only when genuinely needed and restructure to minimize moves", 0.85)],
    ))

    canons.append(canon(
        "rust", "e0308-mismatched-types", "rust1-linux",
        "error[E0308]: mismatched types",
        r"error\[E0308\]: mismatched types",
        "type_error", "rust", ">=1.70,<2.0", "linux", "true", 0.90, 0.90,
        "Expected one type but got another. Very common with String vs &str, Option<T> vs T, etc.",
        [de("Use as to cast between incompatible types", "as is for numeric casts, not type conversions", 0.72),
         de("Use unsafe transmute", "Undefined behavior, never correct for type mismatches", 0.95)],
        [wa("Use .into(), .as_ref(), .to_string(), or .as_str() for standard conversions", 0.92, "let s: String = my_str.into();"),
         wa("Handle Option/Result with unwrap_or, map, or pattern matching", 0.88)],
    ))

    canons.append(canon(
        "rust", "e0277-trait-bound", "rust1-linux",
        "error[E0277]: the trait bound 'T: Trait' is not satisfied",
        r"error\[E0277\]: the trait bound .+ is not satisfied",
        "trait_error", "rust", ">=1.70,<2.0", "linux", "true", 0.82, 0.85,
        "Type doesn't implement a required trait. Common with Display, Debug, Clone, Serialize.",
        [de("Implement the trait manually when derive would work", "Unnecessary boilerplate for standard traits", 0.55),
         de("Remove the trait bound from the function", "Breaks the function's ability to use trait methods", 0.70)],
        [wa("Add #[derive(Trait)] to your struct/enum", 0.92, "#[derive(Debug, Clone, Serialize)]"),
         wa("Add the trait bound to your generic function signature", 0.85, "fn process<T: Display + Clone>(item: T)")],
    ))

    # === GO ===
    canons.append(canon(
        "go", "undefined-reference", "go1-linux",
        "undefined: X",
        r"undefined:\s+(\w+)",
        "compile_error", "go", ">=1.21,<2.0", "linux", "true", 0.90, 0.88,
        "Symbol not found. Usually an unexported name, missing import, or file not in the same package.",
        [de("Add the missing function to a different package", "Go packages must be imported explicitly, adding to wrong package won't help", 0.65),
         de("Use //go:linkname to access unexported symbols", "Fragile hack that breaks on version updates", 0.88)],
        [wa("Check capitalization (exported names start with uppercase in Go)", 0.92),
         wa("Ensure the file is in the correct package and directory", 0.88, "go vet ./...")],
    ))

    canons.append(canon(
        "go", "imported-not-used", "go1-linux",
        "imported and not used",
        r"imported and not used:?\s*['\"]?(.+?)['\"]?",
        "compile_error", "go", ">=1.21,<2.0", "linux", "true", 0.98, 0.95,
        "Go requires all imports to be used. This is a compile error, not a warning.",
        [de("Comment out the import", "Messy, easy to forget, and goimports will re-add it", 0.60),
         de("Use blank identifier _ for every unused import", "Only correct for side-effect imports, not for temporarily unused ones", 0.55)],
        [wa("Use goimports or gopls to auto-manage imports", 0.98, "goimports -w ."),
         wa("Remove the unused import line", 0.95)],
    ))

    canons.append(canon(
        "go", "cannot-use-as-type", "go1-linux",
        "cannot use X (variable of type T1) as type T2 in argument",
        r"cannot use .+ \(.*type .+\) as .*type .+ in",
        "type_error", "go", ">=1.21,<2.0", "linux", "true", 0.88, 0.87,
        "Type mismatch in function argument or assignment. Go has no implicit conversions.",
        [de("Use unsafe.Pointer to cast between types", "Extremely dangerous, undefined behavior for non-pointer types", 0.92),
         de("Create a type alias", "Aliases don't help with interface satisfaction or conversion", 0.65)],
        [wa("Explicitly convert between compatible types", 0.90, "int64(myInt32) or string(myBytes)"),
         wa("Implement the required interface on your type", 0.85)],
    ))

    # === KUBERNETES ===
    canons.append(canon(
        "kubernetes", "crashloopbackoff", "k8s1-linux",
        "CrashLoopBackOff",
        r"CrashLoopBackOff",
        "pod_error", "kubernetes", ">=1.28,<2.0", "linux", "partial", 0.60, 0.82,
        "Container starts and crashes repeatedly. K8s backs off restart attempts exponentially.",
        [de("Delete and recreate the pod", "Pod will crash again with the same config", 0.82),
         de("Increase restart limit", "There is no restart limit in K8s; the issue is in the container itself", 0.88)],
        [wa("Check container logs for the crash reason", 0.85, "kubectl logs pod-name --previous"),
         wa("Check if the container needs environment variables, secrets, or config maps", 0.80, "kubectl describe pod pod-name")],
    ))

    canons.append(canon(
        "kubernetes", "imagepullbackoff", "k8s1-linux",
        "ImagePullBackOff",
        r"ImagePullBackOff|ErrImagePull",
        "image_error", "kubernetes", ">=1.28,<2.0", "linux", "true", 0.85, 0.88,
        "Cannot pull container image. Wrong image name, tag, or missing registry credentials.",
        [de("Keep waiting for the pull to succeed", "If credentials or image name are wrong, it will never succeed", 0.80),
         de("Pull the image manually on the node", "Not scalable and doesn't fix the underlying auth/name issue", 0.72)],
        [wa("Verify image name and tag exist in the registry", 0.90, "docker pull image:tag"),
         wa("Create or fix imagePullSecrets for private registries", 0.85, "kubectl create secret docker-registry regcred --docker-server=... --docker-username=... --docker-password=...")],
    ))

    canons.append(canon(
        "kubernetes", "oomkilled", "k8s1-linux",
        "OOMKilled",
        r"OOMKilled|Out of memory|OOM",
        "resource_error", "kubernetes", ">=1.28,<2.0", "linux", "partial", 0.55, 0.80,
        "Container exceeded its memory limit and was killed by the kernel OOM killer.",
        [de("Remove memory limits entirely", "Pod can consume all node memory and affect other pods", 0.78),
         de("Set memory limit to maximum node capacity", "Still kills if it exceeds, and starves other pods", 0.72)],
        [wa("Profile actual memory usage and set limits 20-30% above normal usage", 0.80, "kubectl top pod pod-name"),
         wa("Fix memory leaks in the application or reduce batch sizes", 0.75)],
    ))

    # === TERRAFORM ===
    canons.append(canon(
        "terraform", "state-lock-error", "tf1-linux",
        "Error acquiring the state lock",
        r"Error (acquiring|locking) the state lock",
        "state_error", "terraform", ">=1.5,<2.0", "linux", "true", 0.85, 0.88,
        "Another Terraform process holds the state lock or a previous run crashed without releasing it.",
        [de("Delete the state file", "Permanently loses all resource tracking, causing orphaned infrastructure", 0.95),
         de("Use -no-lock flag", "Creates race conditions when multiple users apply simultaneously", 0.78)],
        [wa("Force unlock the state with the lock ID", 0.88, "terraform force-unlock LOCK_ID"),
         wa("Check if another terraform apply is running and wait for it to finish", 0.85)],
    ))

    canons.append(canon(
        "terraform", "provider-not-present", "tf1-linux",
        "Provider configuration not present",
        r"Provider configuration not present|provider .+ not available",
        "config_error", "terraform", ">=1.5,<2.0", "linux", "true", 0.90, 0.88,
        "Required provider is not configured in the Terraform configuration.",
        [de("Manually download the provider binary", "Terraform manages provider binaries; manual placement is fragile", 0.72),
         de("Copy .terraform from another project", "Provider versions and configs may not match", 0.78)],
        [wa("Run terraform init to download and configure providers", 0.92, "terraform init"),
         wa("Add the required_providers block to your terraform configuration", 0.88)],
    ))

    canons.append(canon(
        "terraform", "cycle-in-module", "tf1-linux",
        "Error: Cycle",
        r"Error: Cycle:?\s*(.+)",
        "dependency_error", "terraform", ">=1.5,<2.0", "linux", "partial", 0.55, 0.78,
        "Circular dependency between resources. Terraform cannot determine apply order.",
        [de("Add depends_on to break the cycle", "depends_on can make cycles worse by adding more edges to the dependency graph", 0.65),
         de("Move resources to separate modules", "Cycles across modules are even harder to debug", 0.60)],
        [wa("Use terraform graph to visualize the cycle and refactor", 0.78, "terraform graph | dot -Tpng > graph.png"),
         wa("Break the cycle by using data sources instead of direct references for one direction", 0.72)],
    ))

    # === AWS ===
    canons.append(canon(
        "aws", "access-denied-exception", "awscli2-linux",
        "An error occurred (AccessDeniedException) when calling the X operation",
        r"(AccessDeniedException|AccessDenied|403 Forbidden).*when calling",
        "auth_error", "aws", ">=2.0,<3.0", "linux", "true", 0.82, 0.85,
        "IAM permissions insufficient for the requested operation.",
        [de("Add AdministratorAccess policy", "Severe security risk, violates least-privilege principle", 0.85),
         de("Use root account credentials", "Root should never be used for API calls, critical security issue", 0.95)],
        [wa("Check which specific permission is needed using CloudTrail or IAM Access Analyzer", 0.85, "aws cloudtrail lookup-events --lookup-attributes AttributeKey=EventName,AttributeValue=OperationName"),
         wa("Add the minimum required IAM policy for the specific action and resource", 0.82)],
    ))

    canons.append(canon(
        "aws", "expired-token-exception", "awscli2-linux",
        "An error occurred (ExpiredTokenException): The security token included in the request is expired",
        r"ExpiredTokenException|security token.+is expired|token.+has expired",
        "auth_error", "aws", ">=2.0,<3.0", "linux", "true", 0.90, 0.90,
        "AWS session token has expired. Common with STS temporary credentials and SSO sessions.",
        [de("Hardcode long-lived access keys", "Security anti-pattern, keys can leak and don't rotate", 0.88),
         de("Extend token lifetime to maximum", "Only delays the problem, tokens still expire", 0.55)],
        [wa("Refresh credentials with aws sso login or aws sts assume-role", 0.92, "aws sso login --profile my-profile"),
         wa("Use credential_process or credential helpers for automatic refresh", 0.85)],
    ))

    canons.append(canon(
        "aws", "resource-not-found", "awscli2-linux",
        "An error occurred (ResourceNotFoundException): The specified resource does not exist",
        r"ResourceNotFoundException|NoSuchBucket|NoSuchKey|404.*Not Found",
        "resource_error", "aws", ">=2.0,<3.0", "linux", "true", 0.88, 0.87,
        "AWS resource doesn't exist or is in a different region.",
        [de("Create the resource with the same name", "May not have the same configuration, causing downstream issues", 0.55),
         de("Switch to us-east-1 (default region)", "Resource may be in a completely different region", 0.62)],
        [wa("Check the resource exists in the correct region", 0.90, "aws s3 ls s3://bucket-name --region us-west-2"),
         wa("Verify the ARN or resource identifier for typos", 0.85)],
    ))

    # === NEXTJS ===
    canons.append(canon(
        "nextjs", "hydration-failed", "nextjs14-linux",
        "Error: Hydration failed because the initial UI does not match what was rendered on the server",
        r"Hydration failed because the initial UI does not match",
        "render_error", "nextjs", ">=14,<16", "linux", "partial", 0.60, 0.82,
        "Server-rendered HTML doesn't match client-side render. Common with dynamic content, dates, or browser APIs.",
        [de("Suppress hydration warnings with suppressHydrationWarning", "Masks real bugs, content will flash/shift for users", 0.65),
         de("Make everything client-side with 'use client'", "Loses all SSR/SSG benefits, defeats the purpose of Next.js", 0.78)],
        [wa("Move browser-only code into useEffect", 0.82, "const [mounted, setMounted] = useState(false); useEffect(() => setMounted(true), []);"),
         wa("Use dynamic import with ssr: false for client-only components", 0.78, "const Comp = dynamic(() => import('./Comp'), { ssr: false })")],
    ))

    canons.append(canon(
        "nextjs", "module-not-found-resolve", "nextjs14-linux",
        "Module not found: Can't resolve 'X'",
        r"Module not found: Can't resolve ['\"](.+?)['\"]",
        "build_error", "nextjs", ">=14,<16", "linux", "true", 0.88, 0.90,
        "Webpack/Turbopack cannot find the module. Usually a missing dependency or wrong import path.",
        [de("Add the module to webpack externals", "Makes the module unavailable at runtime", 0.72),
         de("Use require() instead of import", "Doesn't fix the missing module, just changes the error format", 0.65)],
        [wa("Install the missing dependency", 0.92, "npm install missing-package"),
         wa("Check for typos in the import path and use correct relative/absolute paths", 0.88)],
    ))

    canons.append(canon(
        "nextjs", "server-component-client-hook", "nextjs14-linux",
        "Error: useState/useEffect can only be used in Client Components",
        r"(useState|useEffect|useContext).+can only be used in Client Components",
        "component_error", "nextjs", ">=14,<16", "linux", "true", 0.92, 0.90,
        "React hooks used in a Server Component. Next.js App Router defaults to Server Components.",
        [de("Make the entire page a Client Component", "Loses server-side rendering benefits for the whole page", 0.72),
         de("Pass hooks through props from a parent Client Component", "Hooks cannot be passed as props, they must be called in the component", 0.85)],
        [wa("Add 'use client' directive at the top of the file that uses hooks", 0.95, "// Add as first line:\n'use client';"),
         wa("Extract the interactive part into a separate Client Component", 0.90)],
    ))

    # === REACT ===
    canons.append(canon(
        "react", "invalid-hook-call", "react18-linux",
        "Invalid hook call. Hooks can only be called inside the body of a function component",
        r"Invalid hook call.*Hooks can only be called inside",
        "hook_error", "react", ">=18,<20", "linux", "true", 0.85, 0.88,
        "Hook called outside a component, in a class component, or with multiple React copies.",
        [de("Convert class component to function component just for hooks", "If the class has complex lifecycle, conversion may introduce bugs", 0.55),
         de("Call hooks inside event handlers or callbacks", "Hooks must be at the top level, not inside conditions or callbacks", 0.82)],
        [wa("Ensure hooks are called at the top level of a function component", 0.92),
         wa("Check for duplicate React versions in node_modules", 0.85, "npm ls react")],
    ))

    canons.append(canon(
        "react", "cannot-update-while-rendering", "react18-linux",
        "Cannot update a component while rendering a different component",
        r"Cannot update a component .+ while rendering a different component",
        "render_error", "react", ">=18,<20", "linux", "true", 0.82, 0.85,
        "State update triggered during render phase of another component. Usually setState in render body.",
        [de("Wrap the update in setTimeout", "Hacky fix that can cause flickering and race conditions", 0.65),
         de("Use useLayoutEffect for the update", "May cause the same issue if the update triggers a re-render", 0.60)],
        [wa("Move the state update into useEffect", 0.90, "useEffect(() => { setState(value); }, [dependency]);"),
         wa("Restructure to lift state up or use a shared context", 0.82)],
    ))

    canons.append(canon(
        "react", "too-many-rerenders", "react18-linux",
        "Error: Too many re-renders. React limits the number of renders to prevent an infinite loop",
        r"Too many re-renders.*React limits the number of renders",
        "render_error", "react", ">=18,<20", "linux", "true", 0.88, 0.90,
        "Infinite render loop caused by setState during render or wrong useEffect dependencies.",
        [de("Increase React's render limit", "There is no configurable render limit; the issue is an infinite loop", 0.90),
         de("Remove all useEffect dependencies", "Makes useEffect run on every render, potentially worsening the loop", 0.78)],
        [wa("Check for setState calls during render (not inside useEffect or event handlers)", 0.92),
         wa("Fix useEffect dependency arrays to prevent retriggering", 0.88, "useEffect(() => { ... }, [specificDep]); // not [object] or []")],
    ))

    return canons


def main():
    generated = 0
    skipped = 0
    for c in get_all_canons():
        parts = c["id"].split("/")
        out_dir = DATA_DIR / parts[0] / parts[1]
        out_file = out_dir / f"{parts[2]}.json"

        if out_file.exists():
            skipped += 1
            continue

        out_dir.mkdir(parents=True, exist_ok=True)
        out_file.write_text(
            json.dumps(c, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        generated += 1
        print(f"  Created: {c['id']}")

    print(f"\nDone: {generated} created, {skipped} skipped (already exist)")


if __name__ == "__main__":
    main()
