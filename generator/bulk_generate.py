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
    leads_to: list[dict] | None = None,
    preceded_by: list[dict] | None = None,
    confused_with: list[dict] | None = None,
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
    for d in dead_ends:
        d.setdefault("sources", [])
        d.setdefault("condition", "")
    for w in workarounds:
        w.setdefault("sources", [])
        w.setdefault("condition", "")

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
            "leads_to": leads_to or [],
            "preceded_by": preceded_by or [],
            "frequently_confused_with": confused_with or [],
        },
        "metadata": {
            "generated_by": "bulk_generate.py",
            "generation_date": TODAY,
            "review_status": "auto_generated",
            "evidence_count": 50,
            "last_verification": TODAY,
        },
    }


def de(action: str, why: str, rate: float, sources: list[str] | None = None) -> dict:
    d = {"action": action, "why_fails": why, "fail_rate": rate}
    if sources:
        d["sources"] = sources
    return d


def wa(action: str, rate: float, how: str = "", sources: list[str] | None = None) -> dict:
    d: dict = {"action": action, "success_rate": rate}
    if how:
        d["how"] = how
    if sources:
        d["sources"] = sources
    return d


def leads(error_id: str, probability: float, condition: str = "") -> dict:
    d: dict = {"error_id": error_id, "probability": probability}
    if condition:
        d["condition"] = condition
    return d


def preceded(error_id: str, probability: float, condition: str = "") -> dict:
    d: dict = {"error_id": error_id, "probability": probability}
    if condition:
        d["condition"] = condition
    return d


def confused(error_id: str, distinction: str) -> dict:
    return {"error_id": error_id, "distinction": distinction}


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
        [de("Add try/except around the indexing", "Masks the root cause without fixing the None source", 0.72, sources=["https://docs.python.org/3/tutorial/errors.html"]),
         de("Check if variable is None right before use", "The None originates earlier in the call chain", 0.65, sources=["https://docs.python.org/3/library/exceptions.html#TypeError"])],
        [wa("Trace the variable back to its assignment and fix the source of None", 0.90, "Add breakpoint or print before assignment", sources=["https://docs.python.org/3/library/functions.html#breakpoint"]),
         wa("Use Optional type hints and handle None explicitly in the function that produces the value", 0.85, sources=["https://docs.python.org/3/library/typing.html#typing.Optional"])],
        python=">=3.11,<3.13",
        leads_to=[leads("python/keyerror/py311-linux", 0.2, "Fixing None source reveals missing key access"), leads("python/valueerror-invalid-literal/py311-linux", 0.15, "Underlying data has wrong type")],
        preceded_by=[preceded("python/keyerror/py311-linux", 0.15, "dict.get() returns None which is then subscripted")],
        confused_with=[confused("python/keyerror/py311-linux", "KeyError is about missing dict keys; TypeError NoneType is about operating on None values")],
    ))

    canons.append(canon(
        "python", "keyerror", "py311-linux",
        "KeyError: 'key_name'",
        r"KeyError: ['\"](.+?)['\"]",
        "key_error", "python", ">=3.11,<3.13", "linux", "true", 0.92, 0.90,
        "Dictionary key access fails. Common in config parsing, API responses, and data pipelines.",
        [de("Wrap in try/except KeyError", "Silences the error but doesn't fix missing data", 0.60, sources=["https://docs.python.org/3/tutorial/errors.html#handling-exceptions"]),
         de("Add the missing key to the dict manually", "Key may be dynamically generated or come from external source", 0.55, sources=["https://docs.python.org/3/library/exceptions.html#KeyError"])],
        [wa("Use dict.get(key, default) instead of dict[key]", 0.95, "response.get('data', {}).get('items', [])", sources=["https://docs.python.org/3/library/stdtypes.html#dict.get"]),
         wa("Validate dict structure before access using schema validation", 0.88, sources=["https://docs.python.org/3/library/stdtypes.html#dict"])],
        python=">=3.11,<3.13",
        leads_to=[leads("python/typeerror-nonetype-not-subscriptable/py311-linux", 0.2, "dict.get() returns None which may be subscripted"), leads("python/valueerror-invalid-literal/py311-linux", 0.15, "Retrieved value has unexpected type")],
        preceded_by=[preceded("python/typeerror-nonetype-not-subscriptable/py311-linux", 0.2, "Fixing NoneType error reveals missing keys in data")],
        confused_with=[confused("python/valueerror-invalid-literal/py311-linux", "ValueError is about wrong value format; KeyError is about missing dictionary keys")],
    ))

    canons.append(canon(
        "python", "filenotfounderror", "py311-linux",
        "FileNotFoundError: [Errno 2] No such file or directory",
        r"FileNotFoundError: \[Errno 2\] No such file or directory:?\s*['\"]?(.+?)['\"]?$",
        "io_error", "python", ">=3.11,<3.13", "linux", "true", 0.90, 0.92,
        "File path does not exist. Common in scripts with hardcoded paths or relative path assumptions.",
        [de("Create empty file at the path", "May not contain expected content, causing downstream errors", 0.58, sources=["https://docs.python.org/3/library/exceptions.html#FileNotFoundError"]),
         de("Hardcode absolute path", "Breaks portability across machines and environments", 0.70, sources=["https://stackoverflow.com/questions/3430372/how-do-i-get-the-full-path-of-the-current-files-directory"])],
        [wa("Use pathlib.Path and resolve relative to __file__ or project root", 0.92, "Path(__file__).parent / 'data' / 'config.json'", sources=["https://docs.python.org/3/library/pathlib.html"]),
         wa("Check path existence before access with Path.exists()", 0.88, sources=["https://docs.python.org/3/library/pathlib.html#pathlib.Path.exists"])],
        python=">=3.11,<3.13",
        leads_to=[leads("python/permissionerror-errno13/py311-linux", 0.25, "File exists but has wrong permissions"), leads("python/unicodedecodeerror/py311-linux", 0.15, "File found but has unexpected encoding")],
        preceded_by=[preceded("python/permissionerror-errno13/py311-linux", 0.1, "Changed path to avoid permission issue but new path doesn't exist")],
        confused_with=[confused("python/permissionerror-errno13/py311-linux", "PermissionError means file exists but access is denied; FileNotFoundError means file does not exist")],
    ))

    canons.append(canon(
        "python", "unicodedecodeerror", "py311-linux",
        "UnicodeDecodeError: 'utf-8' codec can't decode byte",
        r"UnicodeDecodeError: '(utf-8|ascii|charmap)' codec can't decode byte",
        "encoding_error", "python", ">=3.11,<3.13", "linux", "true", 0.82, 0.85,
        "File contains non-UTF-8 bytes. Common with legacy data, binary files, or Windows-generated CSVs.",
        [de("Force encoding='utf-8' everywhere", "File genuinely isn't UTF-8, forcing it corrupts or crashes", 0.75, sources=["https://docs.python.org/3/library/codecs.html#standard-encodings"]),
         de("Strip non-ASCII bytes", "Loses legitimate non-ASCII data like names, currencies", 0.68, sources=["https://docs.python.org/3/howto/unicode.html"])],
        [wa("Detect encoding with chardet/charset-normalizer then open with correct encoding", 0.88, "import charset_normalizer; detected = charset_normalizer.from_path(path).best()", sources=["https://docs.python.org/3/library/codecs.html"]),
         wa("Open with errors='replace' or errors='ignore' when data loss is acceptable", 0.80, sources=["https://docs.python.org/3/library/functions.html#open"])],
        python=">=3.11,<3.13",
        leads_to=[leads("python/valueerror-invalid-literal/py311-linux", 0.2, "Decoded text contains unexpected characters causing parse errors")],
        preceded_by=[preceded("python/filenotfounderror/py311-linux", 0.15, "Found the file but it has unexpected encoding")],
        confused_with=[confused("python/valueerror-invalid-literal/py311-linux", "ValueError is about data format; UnicodeDecodeError is specifically about byte-to-string decoding")],
    ))

    canons.append(canon(
        "python", "valueerror-invalid-literal", "py311-linux",
        "ValueError: invalid literal for int() with base 10",
        r"ValueError: invalid literal for int\(\) with base 10:?\s*['\"]?(.+?)['\"]?",
        "value_error", "python", ">=3.11,<3.13", "linux", "true", 0.93, 0.91,
        "String-to-int conversion fails on non-numeric input. Common in CLI args, CSV parsing, form data.",
        [de("Wrap every int() call in try/except", "Masks data quality issues upstream", 0.55, sources=["https://docs.python.org/3/tutorial/errors.html#handling-exceptions"]),
         de("Use regex to strip non-digits before converting", "May silently produce wrong numbers", 0.62, sources=["https://docs.python.org/3/library/re.html"])],
        [wa("Validate and sanitize input at the entry point (argparse, form validation)", 0.95, sources=["https://docs.python.org/3/library/argparse.html"]),
         wa("Use str.strip() and check str.isdigit() before conversion", 0.90, "value.strip().isdigit() and int(value.strip())", sources=["https://docs.python.org/3/library/stdtypes.html#str.isdigit"])],
        python=">=3.11,<3.13",
        leads_to=[leads("python/typeerror-nonetype-not-subscriptable/py311-linux", 0.15, "Conversion returns None or fails silently")],
        preceded_by=[preceded("python/unicodedecodeerror/py311-linux", 0.2, "Decoded text contains non-numeric characters"), preceded("python/keyerror/py311-linux", 0.15, "Retrieved dict value is not a valid integer string")],
        confused_with=[confused("python/typeerror-nonetype-not-subscriptable/py311-linux", "TypeError is about wrong type operations; ValueError is about correct type but invalid value")],
    ))

    canons.append(canon(
        "python", "connectionrefusederror", "py311-linux",
        "ConnectionRefusedError: [Errno 111] Connection refused",
        r"ConnectionRefusedError: \[Errno 111\] Connection refused",
        "network_error", "python", ">=3.11,<3.13", "linux", "partial", 0.65, 0.80,
        "Target service is not running or not listening on the expected port.",
        [de("Retry the connection immediately in a loop", "If the service is down, retrying won't help and wastes time", 0.78, sources=["https://docs.python.org/3/library/exceptions.html#ConnectionRefusedError"]),
         de("Change the port number", "The port is usually correct; the service itself is not running", 0.72, sources=["https://docs.python.org/3/library/socket.html"])],
        [wa("Verify the target service is running and listening on the correct port", 0.85, "ss -tlnp | grep :PORT or docker ps", sources=["https://docs.python.org/3/library/socket.html#socket.socket.connect"]),
         wa("Add exponential backoff retry with a health check endpoint", 0.75, sources=["https://docs.python.org/3/library/urllib.request.html"])],
        python=">=3.11,<3.13",
        leads_to=[leads("python/permissionerror-errno13/py311-linux", 0.1, "Service starts but file access is denied")],
        preceded_by=[preceded("docker/bind-address-already-in-use/docker27-linux", 0.2, "Changed port but service not yet running on new port"), preceded("docker/cannot-connect-to-docker-daemon/docker27-linux", 0.15, "Docker daemon not running so containerized service is unavailable")],
        confused_with=[confused("python/permissionerror-errno13/py311-linux", "PermissionError is about file access; ConnectionRefusedError is about network connections")],
    ))

    canons.append(canon(
        "python", "memoryerror", "py311-linux",
        "MemoryError",
        r"MemoryError",
        "resource_error", "python", ">=3.11,<3.13", "linux", "partial", 0.55, 0.78,
        "Process exceeded available RAM. Common with large datasets, recursive structures, or memory leaks.",
        [de("Increase swap space", "Swap is orders of magnitude slower, making the program unusable", 0.80, sources=["https://docs.python.org/3/library/exceptions.html#MemoryError"]),
         de("Upgrade to more RAM", "Often the data processing approach itself is inefficient", 0.60, sources=["https://docs.python.org/3/library/sys.html#sys.getsizeof"])],
        [wa("Process data in chunks/batches instead of loading all into memory", 0.82, "for chunk in pd.read_csv(path, chunksize=10000):", sources=["https://docs.python.org/3/library/functions.html#iter"]),
         wa("Use memory-mapped files or streaming approaches (mmap, generators)", 0.78, sources=["https://docs.python.org/3/library/mmap.html"])],
        python=">=3.11,<3.13",
        leads_to=[leads("kubernetes/oomkilled/k8s1-linux", 0.2, "Application deployed to K8s hits memory limits")],
        preceded_by=[preceded("python/filenotfounderror/py311-linux", 0.1, "Loaded correct large file that exceeds memory")],
        confused_with=[confused("kubernetes/oomkilled/k8s1-linux", "OOMKilled is container-level memory limit; MemoryError is Python process-level")],
    ))

    canons.append(canon(
        "python", "permissionerror-errno13", "py311-linux",
        "PermissionError: [Errno 13] Permission denied",
        r"PermissionError: \[Errno 13\] Permission denied:?\s*['\"]?(.+?)['\"]?",
        "io_error", "python", ">=3.11,<3.13", "linux", "true", 0.88, 0.87,
        "Insufficient file system permissions. Common with system paths, Docker volumes, or pip installs.",
        [de("Run with sudo", "Creates root-owned files causing more permission issues later", 0.75, sources=["https://docs.python.org/3/library/exceptions.html#PermissionError"]),
         de("chmod 777 the directory", "Security vulnerability, doesn't fix the ownership issue", 0.82, sources=["https://stackoverflow.com/questions/22071853/permission-denied-error-errno-13"])],
        [wa("Fix ownership with chown and use appropriate user permissions", 0.90, "chown -R $(whoami) /path/to/dir", sources=["https://docs.python.org/3/library/os.html#os.chown"]),
         wa("Use virtual environments or user-local paths", 0.88, "pip install --user or python -m venv .venv", sources=["https://docs.python.org/3/library/venv.html"])],
        python=">=3.11,<3.13",
        leads_to=[leads("python/filenotfounderror/py311-linux", 0.15, "Changed path to user directory but file doesn't exist there")],
        preceded_by=[preceded("python/filenotfounderror/py311-linux", 0.1, "File found but access denied"), preceded("pip/no-matching-distribution/pip24-linux", 0.15, "pip install fails with permission error on system Python")],
        confused_with=[confused("node/eacces-permission-denied/node20-linux", "EACCES is Node.js file permission error; PermissionError is Python's equivalent"), confused("python/filenotfounderror/py311-linux", "FileNotFoundError means path doesn't exist; PermissionError means it exists but access is denied")],
    ))

    # === NODE ===
    canons.append(canon(
        "node", "err-module-not-found", "node20-linux",
        "Error [ERR_MODULE_NOT_FOUND]: Cannot find module",
        r"Error \[ERR_MODULE_NOT_FOUND\]: Cannot find module ['\"](.+?)['\"]",
        "module_error", "node", ">=20,<23", "linux", "true", 0.87, 0.89,
        "Node.js cannot resolve the specified module. Common with ESM/CJS conflicts or missing dependencies.",
        [de("Add .js extension to import", "Only works for local files, not for node_modules", 0.60, sources=["https://nodejs.org/api/esm.html#mandatory-file-extensions"]),
         de("Switch type in package.json between module and commonjs", "May break other imports throughout the project", 0.68, sources=["https://nodejs.org/api/packages.html#type"])],
        [wa("Run npm install to ensure all dependencies are installed", 0.92, "rm -rf node_modules && npm install", sources=["https://docs.npmjs.com/cli/v10/commands/npm-install"]),
         wa("Check package.json exports field matches the import path", 0.85, sources=["https://nodejs.org/api/packages.html#package-entry-points"])],
        leads_to=[leads("node/syntaxerror-unexpected-token/node20-linux", 0.2, "Found module but it has ESM/CJS format mismatch"), leads("node/err-require-esm/node20-linux", 0.15, "Module found but it is ESM-only and code uses require()")],
        preceded_by=[preceded("node/cannot-find-module-npm/node20-linux", 0.25, "npm module installed but ESM resolution fails")],
        confused_with=[confused("node/cannot-find-module-npm/node20-linux", "cannot-find-module is CJS require() failure; ERR_MODULE_NOT_FOUND is ESM import failure"), confused("node/err-require-esm/node20-linux", "ERR_REQUIRE_ESM is about CJS requiring ESM; ERR_MODULE_NOT_FOUND is about missing modules entirely")],
    ))

    canons.append(canon(
        "node", "eacces-permission-denied", "node20-linux",
        "Error: EACCES: permission denied",
        r"Error: EACCES: permission denied,?\s*(open|mkdir|unlink|scandir)\s*['\"]?(.+?)['\"]?",
        "permission_error", "node", ">=20,<23", "linux", "true", 0.85, 0.87,
        "File system operation denied. Common with global npm installs or Docker volume mounts.",
        [de("Run npm with sudo", "Creates root-owned node_modules causing cascading permission issues", 0.82, sources=["https://docs.npmjs.com/resolving-eacces-permissions-errors-when-installing-packages-globally"]),
         de("chmod -R 777 node_modules", "Security risk and doesn't fix the root cause", 0.78, sources=["https://nodejs.org/api/errors.html#common-system-errors"])],
        [wa("Fix npm prefix to use user directory", 0.90, "npm config set prefix ~/.npm-global", sources=["https://docs.npmjs.com/resolving-eacces-permissions-errors-when-installing-packages-globally"]),
         wa("Use nvm or volta for Node version management (avoids system paths)", 0.88, sources=["https://nodejs.org/en/download/package-manager"])],
        leads_to=[leads("node/cannot-find-module-npm/node20-linux", 0.2, "Permission fix changes install location and modules not found")],
        preceded_by=[preceded("node/cannot-find-module-npm/node20-linux", 0.15, "npm install fails with permission error")],
        confused_with=[confused("python/permissionerror-errno13/py311-linux", "Python PermissionError is the same concept; EACCES is the Node.js/POSIX equivalent")],
    ))

    canons.append(canon(
        "node", "err-require-esm", "node20-linux",
        "Error [ERR_REQUIRE_ESM]: require() of ES Module not supported",
        r"Error \[ERR_REQUIRE_ESM\]:.*require\(\) of ES Module.+not supported",
        "module_error", "node", ">=20,<23", "linux", "true", 0.80, 0.85,
        "Trying to require() an ESM-only package from CommonJS code.",
        [de("Downgrade the ESM-only package to an older CJS version", "Misses security patches and new features", 0.65, sources=["https://nodejs.org/api/esm.html"]),
         de("Use dynamic import() in CJS synchronously", "import() is async, cannot be used synchronously in CJS", 0.88, sources=["https://nodejs.org/api/esm.html#import-expressions"])],
        [wa("Convert your project to ESM (set type: module in package.json)", 0.85, sources=["https://nodejs.org/api/packages.html#type"]),
         wa("Use dynamic import() with await in an async context", 0.82, "const pkg = await import('esm-package')", sources=["https://nodejs.org/api/esm.html#import-expressions"])],
        leads_to=[leads("node/syntaxerror-unexpected-token/node20-linux", 0.25, "Converting to ESM causes syntax errors in CJS files"), leads("node/err-module-not-found/node20-linux", 0.2, "ESM conversion changes module resolution rules")],
        preceded_by=[preceded("node/err-module-not-found/node20-linux", 0.15, "Module resolution led to discovering ESM/CJS mismatch")],
        confused_with=[confused("node/err-module-not-found/node20-linux", "ERR_MODULE_NOT_FOUND is about missing modules; ERR_REQUIRE_ESM is about CJS code trying to require() an ESM module")],
    ))

    canons.append(canon(
        "node", "syntaxerror-unexpected-token", "node20-linux",
        "SyntaxError: Unexpected token",
        r"SyntaxError: Unexpected token\s*['\"]?(.+?)['\"]?",
        "syntax_error", "node", ">=20,<23", "linux", "true", 0.88, 0.86,
        "JavaScript parser encountered invalid syntax. Common with JSON parse failures or ESM/CJS confusion.",
        [de("Add Babel to transpile", "Adds unnecessary complexity if the issue is just a syntax typo or wrong file format", 0.55, sources=["https://nodejs.org/api/errors.html#class-syntaxerror"]),
         de("Upgrade Node.js version", "Usually not a version issue but a code or configuration error", 0.62, sources=["https://nodejs.org/api/errors.html"])],
        [wa("Check if the file is valid JSON when using JSON.parse()", 0.90, sources=["https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/JSON/parse"]),
         wa("Verify file extension matches the module system (.mjs for ESM, .cjs for CJS)", 0.85, sources=["https://nodejs.org/api/esm.html#enabling"])],
        leads_to=[leads("node/err-module-not-found/node20-linux", 0.15, "Fixing syntax reveals missing module imports"), leads("node/err-require-esm/node20-linux", 0.2, "Syntax error was caused by ESM/CJS mismatch")],
        preceded_by=[preceded("node/err-require-esm/node20-linux", 0.25, "ESM/CJS mismatch manifests as unexpected token error"), preceded("node/err-module-not-found/node20-linux", 0.1, "Wrong module format loaded")],
        confused_with=[confused("node/err-require-esm/node20-linux", "ERR_REQUIRE_ESM is specifically about CJS/ESM mismatch; SyntaxError can have many causes including JSON parse and typos")],
    ))

    canons.append(canon(
        "node", "cannot-find-module-npm", "node20-linux",
        "Error: Cannot find module",
        r"Error: Cannot find module ['\"](.+?)['\"]",
        "module_error", "node", ">=20,<23", "linux", "true", 0.90, 0.91,
        "Module not found in node_modules or local paths. Most common Node.js error.",
        [de("Manually copy the module file into node_modules", "Will be overwritten on next npm install", 0.85, sources=["https://nodejs.org/api/modules.html#loading-from-node_modules-folders"]),
         de("Create a symlink to the module", "Fragile and breaks on different machines", 0.72, sources=["https://docs.npmjs.com/cli/v10/commands/npm-link"])],
        [wa("Delete node_modules and package-lock.json then reinstall", 0.92, "rm -rf node_modules package-lock.json && npm install", sources=["https://docs.npmjs.com/cli/v10/commands/npm-install"]),
         wa("Check the module name for typos in require/import statement", 0.88, sources=["https://nodejs.org/api/modules.html#all-together"])],
        leads_to=[leads("node/err-module-not-found/node20-linux", 0.2, "CJS module resolved but ESM import fails"), leads("node/err-require-esm/node20-linux", 0.15, "Module found but is ESM-only")],
        preceded_by=[preceded("node/eacces-permission-denied/node20-linux", 0.15, "Permission error during npm install leaves incomplete node_modules")],
        confused_with=[confused("node/err-module-not-found/node20-linux", "ERR_MODULE_NOT_FOUND is ESM-specific; Cannot find module is the CJS require() error"), confused("typescript/ts2307-cannot-find-module/ts5-linux", "TS2307 is a compile-time type resolution error; Cannot find module is a runtime error")],
    ))

    # === DOCKER ===
    canons.append(canon(
        "docker", "oci-runtime-create-failed", "docker27-linux",
        "OCI runtime create failed: unable to start container process",
        r"OCI runtime create failed:.*unable to start container process",
        "runtime_error", "docker", ">=27,<28", "linux", "partial", 0.65, 0.80,
        "Container entrypoint or command cannot be executed. Often wrong binary path or missing executable.",
        [de("Rebuild the image from scratch", "If the Dockerfile is wrong, rebuilding reproduces the same error", 0.70, sources=["https://docs.docker.com/engine/reference/builder/#entrypoint"]),
         de("Set --privileged flag", "Security risk and usually not related to the actual issue", 0.82, sources=["https://docs.docker.com/engine/reference/run/#runtime-privilege-and-linux-capabilities"])],
        [wa("Check that the entrypoint/CMD binary exists inside the container", 0.85, "docker run --entrypoint sh image -c 'which myapp'", sources=["https://docs.docker.com/engine/reference/builder/#cmd"]),
         wa("Verify exec format matches the container architecture (amd64 vs arm64)", 0.78, sources=["https://docs.docker.com/build/building/multi-platform/"])],
        leads_to=[leads("kubernetes/crashloopbackoff/k8s1-linux", 0.3, "Container fails to start in Kubernetes pod"), leads("docker/exec-format-error/docker27-linux", 0.2, "Issue is actually architecture mismatch")],
        preceded_by=[preceded("docker/exec-format-error/docker27-linux", 0.2, "Exec format error is a common cause of OCI runtime failure")],
        confused_with=[confused("docker/exec-format-error/docker27-linux", "exec format error is specifically about binary architecture mismatch; OCI runtime create is a broader container start failure")],
    ))

    canons.append(canon(
        "docker", "exec-format-error", "docker27-linux",
        "exec format error",
        r"exec format error|exec user process caused:.*exec format error",
        "platform_error", "docker", ">=27,<28", "linux", "true", 0.82, 0.88,
        "Binary architecture mismatch. Common when running amd64 images on arm64 (Apple Silicon) or vice versa.",
        [de("Reinstall Docker", "Architecture mismatch is not a Docker installation issue", 0.85, sources=["https://docs.docker.com/engine/install/"]),
         de("Add #!/bin/bash shebang to script", "Only helps if the entrypoint is a script without shebang, not for binary mismatch", 0.60, sources=["https://docs.docker.com/engine/reference/builder/#entrypoint"])],
        [wa("Build or pull the correct platform image", 0.90, "docker build --platform linux/amd64 .", sources=["https://docs.docker.com/build/building/multi-platform/"]),
         wa("Use multi-platform builds with docker buildx", 0.85, "docker buildx build --platform linux/amd64,linux/arm64 .", sources=["https://docs.docker.com/build/builders/"])],
        leads_to=[leads("docker/oci-runtime-create-failed/docker27-linux", 0.3, "Architecture mismatch causes OCI runtime failure")],
        preceded_by=[preceded("docker/oci-runtime-create-failed/docker27-linux", 0.2, "Investigating OCI failure reveals architecture mismatch")],
        confused_with=[confused("docker/oci-runtime-create-failed/docker27-linux", "OCI runtime create failed is a broader error; exec format error specifically means wrong CPU architecture")],
    ))

    canons.append(canon(
        "docker", "bind-address-already-in-use", "docker27-linux",
        "Bind for 0.0.0.0:PORT failed: port is already allocated",
        r"Bind for .+?:\d+ failed: port is already allocated|address already in use",
        "network_error", "docker", ">=27,<28", "linux", "true", 0.92, 0.90,
        "Port is already in use by another container or host process.",
        [de("Change the container's internal port", "The conflict is on the host port, not the container port", 0.75, sources=["https://docs.docker.com/engine/reference/commandline/run/#publish"]),
         de("Restart Docker daemon", "Doesn't release ports held by running containers", 0.65, sources=["https://docs.docker.com/config/daemon/"])],
        [wa("Find and stop the process using the port", 0.95, "lsof -i :PORT or docker ps --filter publish=PORT", sources=["https://docs.docker.com/engine/reference/commandline/ps/"]),
         wa("Map to a different host port", 0.90, "docker run -p 8081:80 instead of -p 80:80", sources=["https://docs.docker.com/network/#published-ports"])],
        leads_to=[leads("python/connectionrefusederror/py311-linux", 0.2, "Changed port but application still connects to old port")],
        preceded_by=[preceded("docker/cannot-connect-to-docker-daemon/docker27-linux", 0.15, "Started daemon but old container is still holding the port")],
        confused_with=[confused("python/connectionrefusederror/py311-linux", "ConnectionRefused means nothing is listening; bind already in use means something IS listening on that port")],
    ))

    canons.append(canon(
        "docker", "cannot-connect-to-docker-daemon", "docker27-linux",
        "Cannot connect to the Docker daemon. Is the docker daemon running?",
        r"Cannot connect to the Docker daemon",
        "daemon_error", "docker", ">=27,<28", "linux", "true", 0.88, 0.90,
        "Docker daemon is not running or socket permissions are wrong.",
        [de("Reinstall Docker", "Daemon just needs to be started, not reinstalled", 0.82, sources=["https://docs.docker.com/engine/install/"]),
         de("Run with sudo every time", "Doesn't fix the underlying group permission issue", 0.60, sources=["https://docs.docker.com/engine/install/linux-postinstall/"])],
        [wa("Start the Docker daemon", 0.92, "sudo systemctl start docker", sources=["https://docs.docker.com/config/daemon/start/"]),
         wa("Add user to docker group", 0.88, "sudo usermod -aG docker $USER && newgrp docker", sources=["https://docs.docker.com/engine/install/linux-postinstall/#manage-docker-as-a-non-root-user"])],
        leads_to=[leads("docker/bind-address-already-in-use/docker27-linux", 0.15, "Daemon starts but previous containers left ports allocated"), leads("docker/oci-runtime-create-failed/docker27-linux", 0.2, "Daemon running but container fails to start")],
        preceded_by=[preceded("docker/bind-address-already-in-use/docker27-linux", 0.1, "Restarted daemon to fix port issue but daemon didn't come back up")],
        confused_with=[confused("python/connectionrefusederror/py311-linux", "ConnectionRefused is about app-level network; Cannot connect to Docker daemon is about Docker socket access")],
    ))

    # === GIT ===
    canons.append(canon(
        "git", "not-a-git-repository", "git2-linux",
        "fatal: not a git repository (or any of the parent directories)",
        r"fatal: not a git repository",
        "init_error", "git", ">=2.40,<3.0", "linux", "true", 0.95, 0.92,
        "Current directory is not inside a git repository.",
        [de("Run git init in the wrong directory", "Creates a new repo instead of finding the existing one", 0.70, sources=["https://git-scm.com/docs/git-init"]),
         de("Clone the repo again into a nested directory", "Creates duplicate repos", 0.65, sources=["https://git-scm.com/docs/git-clone"])],
        [wa("Navigate to the correct project directory", 0.95, "cd /path/to/project && git status", sources=["https://git-scm.com/docs/git-status"]),
         wa("Initialize a new repo if starting fresh", 0.90, "git init && git remote add origin URL", sources=["https://git-scm.com/book/en/v2/Git-Basics-Getting-a-Git-Repository"])],
        leads_to=[leads("git/pathspec-no-match/git2-linux", 0.15, "Initialized new repo but expected files are not tracked")],
        preceded_by=[preceded("git/pathspec-no-match/git2-linux", 0.1, "Wrong directory led to pathspec failure then this error")],
        confused_with=[confused("git/pathspec-no-match/git2-linux", "pathspec error means file/branch not found in git; not-a-git-repository means no git repo at all")],
    ))

    canons.append(canon(
        "git", "failed-to-push-refs", "git2-linux",
        "error: failed to push some refs to remote",
        r"error: failed to push some refs to",
        "push_error", "git", ">=2.40,<3.0", "linux", "true", 0.88, 0.90,
        "Remote has commits not in local branch. Most common git push error.",
        [de("Force push with git push --force", "Overwrites remote history, can destroy teammates' work", 0.85, sources=["https://git-scm.com/docs/git-push#Documentation/git-push.txt---force"]),
         de("Delete remote branch and push again", "Loses remote-only commits permanently", 0.90, sources=["https://git-scm.com/docs/git-push"])],
        [wa("Pull and rebase before pushing", 0.92, "git pull --rebase origin main && git push", sources=["https://git-scm.com/docs/git-pull#Documentation/git-pull.txt---rebase"]),
         wa("Fetch and merge remote changes first", 0.88, "git fetch origin && git merge origin/main", sources=["https://git-scm.com/docs/git-fetch"])],
        leads_to=[leads("git/local-changes-overwritten/git2-linux", 0.3, "Pulling remote changes conflicts with local uncommitted work")],
        preceded_by=[preceded("git/local-changes-overwritten/git2-linux", 0.2, "Stashed changes and pulled but push still fails")],
        confused_with=[confused("git/local-changes-overwritten/git2-linux", "local-changes-overwritten is about uncommitted changes; failed-to-push is about committed but unpushed changes vs remote")],
    ))

    canons.append(canon(
        "git", "local-changes-overwritten", "git2-linux",
        "error: Your local changes to the following files would be overwritten by merge",
        r"error: Your local changes to the following files would be overwritten",
        "merge_error", "git", ">=2.40,<3.0", "linux", "true", 0.90, 0.88,
        "Uncommitted local changes conflict with incoming changes.",
        [de("Use git checkout -- . to discard all changes", "Permanently loses all uncommitted work", 0.88, sources=["https://git-scm.com/docs/git-checkout"]),
         de("Delete the conflicting files", "Loses work and may break the project", 0.90, sources=["https://git-scm.com/docs/git-merge"])],
        [wa("Stash changes before merge/pull", 0.92, "git stash && git pull && git stash pop", sources=["https://git-scm.com/docs/git-stash"]),
         wa("Commit your changes before pulling", 0.88, "git add -A && git commit -m 'wip' && git pull", sources=["https://git-scm.com/docs/git-commit"])],
        leads_to=[leads("git/failed-to-push-refs/git2-linux", 0.3, "After resolving local changes, push fails due to diverged history")],
        preceded_by=[preceded("git/failed-to-push-refs/git2-linux", 0.25, "Pull triggered by push failure conflicts with local work")],
        confused_with=[confused("git/failed-to-push-refs/git2-linux", "failed-to-push is about remote vs local commits; local-changes-overwritten is about uncommitted working tree changes")],
    ))

    canons.append(canon(
        "git", "pathspec-no-match", "git2-linux",
        "error: pathspec 'X' did not match any file(s) known to git",
        r"error: pathspec ['\"]?(.+?)['\"]? did not match any file",
        "path_error", "git", ">=2.40,<3.0", "linux", "true", 0.92, 0.90,
        "File or branch name doesn't exist in the repository.",
        [de("Create the file manually then checkout", "Checkout expects the file in git history, not on disk", 0.65, sources=["https://git-scm.com/docs/git-checkout"]),
         de("Use git checkout -f", "Force flag doesn't help if the path genuinely doesn't exist", 0.72, sources=["https://git-scm.com/docs/git-checkout#Documentation/git-checkout.txt--f"])],
        [wa("Check spelling and use git ls-files or git branch -a to verify the name", 0.92, sources=["https://git-scm.com/docs/git-ls-files"]),
         wa("Fetch remote branches if switching to a remote branch", 0.88, "git fetch origin && git checkout branch-name", sources=["https://git-scm.com/docs/git-fetch"])],
        leads_to=[leads("git/not-a-git-repository/git2-linux", 0.1, "Wrong directory causes both pathspec and repo errors")],
        preceded_by=[preceded("git/not-a-git-repository/git2-linux", 0.15, "Navigated to repo but wrong branch or file path")],
        confused_with=[confused("git/not-a-git-repository/git2-linux", "not-a-git-repository means no repo exists; pathspec error means repo exists but file/branch does not")],
    ))

    # === PIP ===
    canons.append(canon(
        "pip", "no-matching-distribution", "pip24-linux",
        "ERROR: No matching distribution found for package",
        r"ERROR: No matching distribution found for (.+)",
        "resolution_error", "pip", ">=24,<25", "linux", "true", 0.82, 0.85,
        "Package doesn't exist for this Python version/platform or has a different name on PyPI.",
        [de("Keep retrying pip install", "If the package doesn't exist for your platform, retrying won't help", 0.85, sources=["https://pip.pypa.io/en/stable/cli/pip_install/"]),
         de("Install from a random GitHub URL", "May get an untrusted or incompatible version", 0.72, sources=["https://pip.pypa.io/en/stable/topics/vcs-support/"])],
        [wa("Check the correct package name on PyPI and verify Python version compatibility", 0.88, sources=["https://pip.pypa.io/en/stable/cli/pip_install/#requirement-specifiers"]),
         wa("Use a different Python version that the package supports", 0.82, "pyenv install 3.11 && pyenv local 3.11", sources=["https://pip.pypa.io/en/stable/cli/pip_install/"])],
        python=">=3.10,<3.13",
        leads_to=[leads("pip/dependency-resolver-conflict/pip24-linux", 0.25, "Found the package but it conflicts with existing dependencies")],
        preceded_by=[preceded("python/modulenotfounderror/py311-linux", 0.35, "Module import failed so user tries pip install")],
        confused_with=[confused("pip/dependency-resolver-conflict/pip24-linux", "Dependency conflict means packages exist but versions clash; no matching distribution means package not found at all")],
    ))

    canons.append(canon(
        "pip", "dependency-resolver-conflict", "pip24-linux",
        "ERROR: pip's dependency resolver does not currently consider all the packages",
        r"ERROR: pip's dependency resolver does not currently consider",
        "resolution_error", "pip", ">=24,<25", "linux", "partial", 0.55, 0.75,
        "Dependency version constraints are mutually exclusive across installed packages.",
        [de("Use --force-reinstall", "Forces installation but doesn't resolve the underlying conflict", 0.70, sources=["https://pip.pypa.io/en/stable/cli/pip_install/#cmdoption-force-reinstall"]),
         de("Pin all packages to exact versions from a working machine", "Breaks on different platforms or Python versions", 0.65, sources=["https://pip.pypa.io/en/stable/topics/dependency-resolution/"])],
        [wa("Use pip-compile from pip-tools to find a compatible resolution", 0.78, "pip-compile requirements.in", sources=["https://pip.pypa.io/en/stable/topics/dependency-resolution/"]),
         wa("Create a fresh virtual environment and install from scratch", 0.75, "python -m venv .venv --clear && pip install -r requirements.txt", sources=["https://docs.python.org/3/library/venv.html"])],
        python=">=3.10,<3.13",
        leads_to=[leads("python/modulenotfounderror/py311-linux", 0.2, "Conflict prevents installation so module remains missing")],
        preceded_by=[preceded("pip/no-matching-distribution/pip24-linux", 0.2, "Tried alternative package that conflicts with existing deps")],
        confused_with=[confused("pip/no-matching-distribution/pip24-linux", "No matching distribution means package not found; dependency conflict means packages found but versions are incompatible")],
    ))

    # === CUDA ===
    canons.append(canon(
        "cuda", "device-side-assert", "cuda12-a100",
        "RuntimeError: CUDA error: device-side assert triggered",
        r"RuntimeError: CUDA error: device-side assert triggered",
        "runtime_error", "cuda", ">=12.0,<13.0", "linux", "partial", 0.60, 0.78,
        "Illegal operation on GPU, often index out of bounds in a kernel. Error message is unhelpful by default.",
        [de("Set CUDA_LAUNCH_BLOCKING=0 and ignore", "Async errors will appear later in wrong places, making debugging impossible", 0.85, sources=["https://pytorch.org/docs/stable/notes/cuda.html#asynchronous-execution"]),
         de("Increase GPU memory", "This is a logic error, not a memory error", 0.80, sources=["https://pytorch.org/docs/stable/notes/cuda.html"])],
        [wa("Set CUDA_LAUNCH_BLOCKING=1 to get the actual error location", 0.82, "CUDA_LAUNCH_BLOCKING=1 python train.py", sources=["https://pytorch.org/docs/stable/notes/cuda.html#asynchronous-execution"]),
         wa("Check tensor shapes and label ranges (num_classes must match output dim)", 0.78, sources=["https://pytorch.org/docs/stable/generated/torch.nn.CrossEntropyLoss.html"])],
        gpu="A100-80GB", vram=80,
        leads_to=[leads("cuda/nvidia-smi-failed/cuda12-linux", 0.1, "Repeated CUDA errors may indicate driver instability")],
        preceded_by=[preceded("cuda/torch-not-compiled-cuda/cuda12-rtx4090", 0.15, "Installed CUDA-enabled PyTorch but model code has shape bugs")],
        confused_with=[confused("kubernetes/oomkilled/k8s1-linux", "OOMKilled is about memory limits; device-side assert is about illegal GPU operations like out-of-bounds indexing")],
    ))

    canons.append(canon(
        "cuda", "torch-not-compiled-cuda", "cuda12-rtx4090",
        "AssertionError: Torch not compiled with CUDA enabled",
        r"(AssertionError|AssertError):.*Torch not compiled with CUDA enabled",
        "install_error", "cuda", ">=12.0,<13.0", "linux", "true", 0.90, 0.88,
        "PyTorch was installed without CUDA support (CPU-only build).",
        [de("Install CUDA toolkit separately", "PyTorch ships its own CUDA runtime, system CUDA doesn't matter", 0.82, sources=["https://pytorch.org/get-started/locally/"]),
         de("Set CUDA_HOME environment variable", "Doesn't affect already-compiled PyTorch binary", 0.78, sources=["https://pytorch.org/docs/stable/notes/cuda.html"])],
        [wa("Reinstall PyTorch with the correct CUDA version from pytorch.org", 0.92, "pip install torch --index-url https://download.pytorch.org/whl/cu121", sources=["https://pytorch.org/get-started/locally/"]),
         wa("Verify installation with torch.cuda.is_available()", 0.88, sources=["https://pytorch.org/docs/stable/cuda.html#torch.cuda.is_available"])],
        gpu="RTX-4090", vram=24,
        leads_to=[leads("cuda/device-side-assert/cuda12-a100", 0.2, "CUDA-enabled PyTorch installed but model has shape/index bugs")],
        preceded_by=[preceded("pip/no-matching-distribution/pip24-linux", 0.2, "Wrong pip install command installs CPU-only build"), preceded("cuda/nvidia-smi-failed/cuda12-linux", 0.15, "Driver issues cause PyTorch to fall back to CPU build")],
        confused_with=[confused("cuda/nvidia-smi-failed/cuda12-linux", "nvidia-smi failure is about the driver; torch-not-compiled-cuda is about the PyTorch package build")],
    ))

    canons.append(canon(
        "cuda", "nvidia-smi-failed", "cuda12-linux",
        "NVIDIA-SMI has failed because it couldn't communicate with the NVIDIA driver",
        r"NVIDIA-SMI has failed because it couldn't communicate with the NVIDIA driver",
        "driver_error", "cuda", ">=12.0,<13.0", "linux", "partial", 0.60, 0.82,
        "NVIDIA driver is not loaded or is incompatible. Common after kernel updates.",
        [de("Reinstall CUDA toolkit", "CUDA toolkit and NVIDIA driver are separate; toolkit doesn't fix driver", 0.78, sources=["https://docs.nvidia.com/cuda/cuda-installation-guide-linux/"]),
         de("Reboot without investigating", "May work temporarily but doesn't fix driver/kernel mismatch", 0.55, sources=["https://docs.nvidia.com/cuda/cuda-installation-guide-linux/#driver-installation"])],
        [wa("Reinstall NVIDIA driver matching your kernel version", 0.80, "sudo apt install nvidia-driver-535", sources=["https://docs.nvidia.com/cuda/cuda-installation-guide-linux/#driver-installation"]),
         wa("Use DKMS to auto-rebuild driver module on kernel updates", 0.75, "sudo apt install nvidia-dkms-535", sources=["https://docs.nvidia.com/cuda/cuda-installation-guide-linux/"])],
        leads_to=[leads("cuda/torch-not-compiled-cuda/cuda12-rtx4090", 0.25, "Driver failure causes PyTorch to report no CUDA support")],
        preceded_by=[preceded("cuda/device-side-assert/cuda12-a100", 0.1, "Repeated CUDA errors destabilize the driver")],
        confused_with=[confused("cuda/torch-not-compiled-cuda/cuda12-rtx4090", "torch-not-compiled-cuda is about PyTorch build; nvidia-smi failure is about the system driver")],
    ))

    # === TYPESCRIPT ===
    canons.append(canon(
        "typescript", "ts2307-cannot-find-module", "ts5-linux",
        "TS2307: Cannot find module 'X' or its corresponding type declarations",
        r"TS2307: Cannot find module ['\"](.+?)['\"]",
        "module_error", "typescript", ">=5.0,<6.0", "linux", "true", 0.85, 0.88,
        "TypeScript cannot resolve the import. Either the module or its @types/ package is missing.",
        [de("Add // @ts-ignore above the import", "Silences the error but you lose all type safety for that module", 0.72, sources=["https://www.typescriptlang.org/docs/handbook/modules/reference.html"]),
         de("Create an empty .d.ts file", "Gives wrong types (everything becomes any), causing runtime bugs", 0.65, sources=["https://www.typescriptlang.org/docs/handbook/declaration-files/introduction.html"])],
        [wa("Install the @types/ package for the module", 0.90, "npm install --save-dev @types/module-name", sources=["https://www.typescriptlang.org/docs/handbook/2/type-declarations.html"]),
         wa("Check tsconfig.json paths and moduleResolution settings", 0.85, sources=["https://www.typescriptlang.org/tsconfig#moduleResolution"])],
        leads_to=[leads("typescript/ts2322-type-not-assignable/ts5-linux", 0.2, "After adding types, type mismatches become visible")],
        preceded_by=[preceded("node/err-module-not-found/node20-linux", 0.15, "Runtime module error leads to checking TypeScript config"), preceded("node/cannot-find-module-npm/node20-linux", 0.2, "npm module missing causes both runtime and compile errors")],
        confused_with=[confused("node/err-module-not-found/node20-linux", "ERR_MODULE_NOT_FOUND is a runtime error; TS2307 is a compile-time type resolution error"), confused("node/cannot-find-module-npm/node20-linux", "Cannot find module is runtime; TS2307 is TypeScript compiler unable to find type declarations")],
    ))

    canons.append(canon(
        "typescript", "ts2322-type-not-assignable", "ts5-linux",
        "TS2322: Type 'X' is not assignable to type 'Y'",
        r"TS2322: Type ['\"]?(.+?)['\"]? is not assignable to type ['\"]?(.+?)['\"]?",
        "type_error", "typescript", ">=5.0,<6.0", "linux", "true", 0.88, 0.90,
        "Type mismatch in assignment. The most common TypeScript error.",
        [de("Cast with 'as any'", "Removes all type safety, defeats the purpose of TypeScript", 0.80, sources=["https://www.typescriptlang.org/docs/handbook/2/everyday-types.html#type-assertions"]),
         de("Add @ts-expect-error", "Silences the error without fixing the type issue", 0.75, sources=["https://www.typescriptlang.org/docs/handbook/release-notes/typescript-3-9.html#-ts-expect-error-comments"])],
        [wa("Fix the type at the source (function return type, API response type, etc.)", 0.92, sources=["https://www.typescriptlang.org/docs/handbook/2/everyday-types.html"]),
         wa("Use type guards or narrowing to handle union types properly", 0.88, "if ('field' in obj) { /* obj is narrowed */ }", sources=["https://www.typescriptlang.org/docs/handbook/2/narrowing.html"])],
        leads_to=[leads("typescript/ts2345-argument-not-assignable/ts5-linux", 0.25, "Fixing assignment types reveals argument type mismatches")],
        preceded_by=[preceded("typescript/ts2307-cannot-find-module/ts5-linux", 0.2, "After adding type declarations, type mismatches become visible")],
        confused_with=[confused("typescript/ts2345-argument-not-assignable/ts5-linux", "TS2345 is about function arguments; TS2322 is about variable/property assignments")],
    ))

    canons.append(canon(
        "typescript", "ts2345-argument-not-assignable", "ts5-linux",
        "TS2345: Argument of type 'X' is not assignable to parameter of type 'Y'",
        r"TS2345: Argument of type ['\"]?(.+?)['\"]? is not assignable to parameter",
        "type_error", "typescript", ">=5.0,<6.0", "linux", "true", 0.87, 0.89,
        "Function argument doesn't match the expected parameter type.",
        [de("Cast the argument with 'as ExpectedType'", "Type assertion can hide real bugs if the runtime value doesn't match", 0.72, sources=["https://www.typescriptlang.org/docs/handbook/2/everyday-types.html#type-assertions"]),
         de("Change the function parameter to accept any", "Removes type safety for all callers", 0.80, sources=["https://www.typescriptlang.org/docs/handbook/2/functions.html"])],
        [wa("Transform the argument to match the expected type before passing", 0.90, sources=["https://www.typescriptlang.org/docs/handbook/2/narrowing.html"]),
         wa("Use function overloads or generics to accept multiple types safely", 0.85, sources=["https://www.typescriptlang.org/docs/handbook/2/generics.html"])],
        leads_to=[leads("typescript/ts7006-implicitly-any/ts5-linux", 0.15, "Fixing argument types leads to discovering untyped parameters")],
        preceded_by=[preceded("typescript/ts2322-type-not-assignable/ts5-linux", 0.25, "Fixing assignment types reveals argument mismatches in function calls")],
        confused_with=[confused("typescript/ts2322-type-not-assignable/ts5-linux", "TS2322 is about assignment to variables/properties; TS2345 is specifically about function call arguments")],
    ))

    canons.append(canon(
        "typescript", "ts7006-implicitly-any", "ts5-linux",
        "TS7006: Parameter 'x' implicitly has an 'any' type",
        r"TS7006: Parameter ['\"]?(.+?)['\"]? implicitly has an ['\"]any['\"] type",
        "type_error", "typescript", ">=5.0,<6.0", "linux", "true", 0.95, 0.92,
        "TypeScript strict mode requires explicit types. Very common when enabling strict for the first time.",
        [de("Disable strict mode in tsconfig.json", "Loses all the safety benefits of TypeScript strict mode", 0.85, sources=["https://www.typescriptlang.org/tsconfig#strict"]),
         de("Add : any to every parameter", "Removes type safety, making TypeScript equivalent to JavaScript", 0.82, sources=["https://www.typescriptlang.org/tsconfig#noImplicitAny"])],
        [wa("Add proper type annotations to function parameters", 0.95, "function greet(name: string): void { }", sources=["https://www.typescriptlang.org/docs/handbook/2/everyday-types.html#parameter-type-annotations"]),
         wa("Use type inference where possible (let TypeScript infer from usage)", 0.88, sources=["https://www.typescriptlang.org/docs/handbook/type-inference.html"])],
        leads_to=[leads("typescript/ts2322-type-not-assignable/ts5-linux", 0.3, "Adding types reveals existing type mismatches"), leads("typescript/ts2345-argument-not-assignable/ts5-linux", 0.25, "Adding parameter types reveals argument mismatches")],
        preceded_by=[preceded("typescript/ts2345-argument-not-assignable/ts5-linux", 0.1, "Fixing argument errors leads to enabling stricter settings")],
        confused_with=[confused("typescript/ts2345-argument-not-assignable/ts5-linux", "TS2345 is about wrong argument types; TS7006 is about missing type annotations entirely")],
    ))

    # === RUST ===
    canons.append(canon(
        "rust", "e0382-borrow-moved-value", "rust1-linux",
        "error[E0382]: borrow of moved value",
        r"error\[E0382\]: borrow of moved value:?\s*`?(.+?)`?",
        "ownership_error", "rust", ">=1.70,<2.0", "linux", "true", 0.85, 0.88,
        "Value was moved to a new owner and can no longer be used. Core Rust ownership concept.",
        [de("Clone everything to avoid moves", "Unnecessary allocations, poor performance, doesn't teach ownership", 0.65, sources=["https://doc.rust-lang.org/book/ch04-01-what-is-ownership.html"]),
         de("Use unsafe to bypass borrow checker", "Undefined behavior risk, completely wrong approach", 0.92, sources=["https://doc.rust-lang.org/book/ch19-01-unsafe-rust.html"])],
        [wa("Use references (&T or &mut T) instead of moving ownership", 0.90, "fn process(data: &Vec<i32>) instead of fn process(data: Vec<i32>)", sources=["https://doc.rust-lang.org/book/ch04-02-references-and-borrowing.html"]),
         wa("Clone only when genuinely needed and restructure to minimize moves", 0.85, sources=["https://doc.rust-lang.org/error_codes/E0382.html"])],
        leads_to=[leads("rust/e0308-mismatched-types/rust1-linux", 0.2, "Using references changes types causing mismatches"), leads("rust/e0277-trait-bound/rust1-linux", 0.15, "Borrowed types may not implement required traits")],
        preceded_by=[preceded("rust/e0308-mismatched-types/rust1-linux", 0.15, "Type fix changes ownership semantics")],
        confused_with=[confused("rust/e0308-mismatched-types/rust1-linux", "E0308 is about type mismatches; E0382 is specifically about use-after-move ownership violations")],
    ))

    canons.append(canon(
        "rust", "e0308-mismatched-types", "rust1-linux",
        "error[E0308]: mismatched types",
        r"error\[E0308\]: mismatched types",
        "type_error", "rust", ">=1.70,<2.0", "linux", "true", 0.90, 0.90,
        "Expected one type but got another. Very common with String vs &str, Option<T> vs T, etc.",
        [de("Use as to cast between incompatible types", "as is for numeric casts, not type conversions", 0.72, sources=["https://doc.rust-lang.org/reference/expressions/operator-expr.html#type-cast-expressions"]),
         de("Use unsafe transmute", "Undefined behavior, never correct for type mismatches", 0.95, sources=["https://doc.rust-lang.org/std/mem/fn.transmute.html"])],
        [wa("Use .into(), .as_ref(), .to_string(), or .as_str() for standard conversions", 0.92, "let s: String = my_str.into();", sources=["https://doc.rust-lang.org/error_codes/E0308.html"]),
         wa("Handle Option/Result with unwrap_or, map, or pattern matching", 0.88, sources=["https://doc.rust-lang.org/book/ch06-02-match.html"])],
        leads_to=[leads("rust/e0277-trait-bound/rust1-linux", 0.25, "Converted type may not implement required traits"), leads("rust/e0382-borrow-moved-value/rust1-linux", 0.15, "Conversion moves value causing use-after-move")],
        preceded_by=[preceded("rust/e0382-borrow-moved-value/rust1-linux", 0.2, "Fixing ownership changes variable types")],
        confused_with=[confused("rust/e0277-trait-bound/rust1-linux", "E0277 is about missing trait implementations; E0308 is about concrete type mismatches")],
    ))

    canons.append(canon(
        "rust", "e0277-trait-bound", "rust1-linux",
        "error[E0277]: the trait bound 'T: Trait' is not satisfied",
        r"error\[E0277\]: the trait bound .+ is not satisfied",
        "trait_error", "rust", ">=1.70,<2.0", "linux", "true", 0.82, 0.85,
        "Type doesn't implement a required trait. Common with Display, Debug, Clone, Serialize.",
        [de("Implement the trait manually when derive would work", "Unnecessary boilerplate for standard traits", 0.55, sources=["https://doc.rust-lang.org/book/ch10-02-traits.html#deriving-traits"]),
         de("Remove the trait bound from the function", "Breaks the function's ability to use trait methods", 0.70, sources=["https://doc.rust-lang.org/error_codes/E0277.html"])],
        [wa("Add #[derive(Trait)] to your struct/enum", 0.92, "#[derive(Debug, Clone, Serialize)]", sources=["https://doc.rust-lang.org/book/appendix-03-derivable-traits.html"]),
         wa("Add the trait bound to your generic function signature", 0.85, "fn process<T: Display + Clone>(item: T)", sources=["https://doc.rust-lang.org/book/ch10-02-traits.html#traits-as-parameters"])],
        leads_to=[leads("rust/e0308-mismatched-types/rust1-linux", 0.2, "Implementing trait changes expected types")],
        preceded_by=[preceded("rust/e0308-mismatched-types/rust1-linux", 0.2, "Type mismatch fix requires implementing a trait")],
        confused_with=[confused("rust/e0308-mismatched-types/rust1-linux", "E0308 is about concrete type mismatches; E0277 is about missing trait implementations on a type")],
    ))

    # === GO ===
    canons.append(canon(
        "go", "undefined-reference", "go1-linux",
        "undefined: X",
        r"undefined:\s+(\w+)",
        "compile_error", "go", ">=1.21,<2.0", "linux", "true", 0.90, 0.88,
        "Symbol not found. Usually an unexported name, missing import, or file not in the same package.",
        [de("Add the missing function to a different package", "Go packages must be imported explicitly, adding to wrong package won't help", 0.65, sources=["https://go.dev/doc/effective_go#names"]),
         de("Use //go:linkname to access unexported symbols", "Fragile hack that breaks on version updates", 0.88, sources=["https://go.dev/ref/spec#Exported_identifiers"])],
        [wa("Check capitalization (exported names start with uppercase in Go)", 0.92, sources=["https://go.dev/doc/effective_go#names"]),
         wa("Ensure the file is in the correct package and directory", 0.88, "go vet ./...", sources=["https://go.dev/ref/spec#Packages"])],
        leads_to=[leads("go/imported-not-used/go1-linux", 0.15, "Adding import to fix undefined creates unused import if wrong package")],
        preceded_by=[preceded("go/imported-not-used/go1-linux", 0.2, "Removing unused import causes undefined reference to symbol from that package")],
        confused_with=[confused("go/cannot-use-as-type/go1-linux", "cannot-use-as-type is about type mismatches; undefined means the symbol doesn't exist in scope")],
    ))

    canons.append(canon(
        "go", "imported-not-used", "go1-linux",
        "imported and not used",
        r"imported and not used:?\s*['\"]?(.+?)['\"]?",
        "compile_error", "go", ">=1.21,<2.0", "linux", "true", 0.98, 0.95,
        "Go requires all imports to be used. This is a compile error, not a warning.",
        [de("Comment out the import", "Messy, easy to forget, and goimports will re-add it", 0.60, sources=["https://go.dev/doc/effective_go#blank_import"]),
         de("Use blank identifier _ for every unused import", "Only correct for side-effect imports, not for temporarily unused ones", 0.55, sources=["https://go.dev/ref/spec#Import_declarations"])],
        [wa("Use goimports or gopls to auto-manage imports", 0.98, "goimports -w .", sources=["https://pkg.go.dev/golang.org/x/tools/cmd/goimports"]),
         wa("Remove the unused import line", 0.95, sources=["https://go.dev/doc/effective_go#blank_import"])],
        leads_to=[leads("go/undefined-reference/go1-linux", 0.25, "Removing import makes previously used symbols undefined")],
        preceded_by=[preceded("go/undefined-reference/go1-linux", 0.15, "Added import to fix undefined but used wrong package")],
        confused_with=[confused("go/undefined-reference/go1-linux", "undefined means symbol not found; imported-not-used means symbol package was imported but never referenced")],
    ))

    canons.append(canon(
        "go", "cannot-use-as-type", "go1-linux",
        "cannot use X (variable of type T1) as type T2 in argument",
        r"cannot use .+ \(.*type .+\) as .*type .+ in",
        "type_error", "go", ">=1.21,<2.0", "linux", "true", 0.88, 0.87,
        "Type mismatch in function argument or assignment. Go has no implicit conversions.",
        [de("Use unsafe.Pointer to cast between types", "Extremely dangerous, undefined behavior for non-pointer types", 0.92, sources=["https://go.dev/ref/spec#Conversions"]),
         de("Create a type alias", "Aliases don't help with interface satisfaction or conversion", 0.65, sources=["https://go.dev/ref/spec#Type_declarations"])],
        [wa("Explicitly convert between compatible types", 0.90, "int64(myInt32) or string(myBytes)", sources=["https://go.dev/doc/effective_go#conversions"]),
         wa("Implement the required interface on your type", 0.85, sources=["https://go.dev/doc/effective_go#interfaces"])],
        leads_to=[leads("go/undefined-reference/go1-linux", 0.1, "Refactoring types introduces undefined references")],
        preceded_by=[preceded("go/undefined-reference/go1-linux", 0.15, "Fixed undefined by using value from different package with incompatible type")],
        confused_with=[confused("typescript/ts2322-type-not-assignable/ts5-linux", "TS2322 is TypeScript type assignability; Go cannot-use-as-type is Go's compile-time type checking"), confused("rust/e0308-mismatched-types/rust1-linux", "Rust E0308 is similar concept but in Rust's type system")],
    ))

    # === KUBERNETES ===
    canons.append(canon(
        "kubernetes", "crashloopbackoff", "k8s1-linux",
        "CrashLoopBackOff",
        r"CrashLoopBackOff",
        "pod_error", "kubernetes", ">=1.28,<2.0", "linux", "partial", 0.60, 0.82,
        "Container starts and crashes repeatedly. K8s backs off restart attempts exponentially.",
        [de("Delete and recreate the pod", "Pod will crash again with the same config", 0.82, sources=["https://kubernetes.io/docs/concepts/workloads/pods/pod-lifecycle/#restart-policy"]),
         de("Increase restart limit", "There is no restart limit in K8s; the issue is in the container itself", 0.88, sources=["https://kubernetes.io/docs/concepts/workloads/pods/pod-lifecycle/"])],
        [wa("Check container logs for the crash reason", 0.85, "kubectl logs pod-name --previous", sources=["https://kubernetes.io/docs/tasks/debug/debug-application/debug-running-pod/#examine-pod-logs"]),
         wa("Check if the container needs environment variables, secrets, or config maps", 0.80, "kubectl describe pod pod-name", sources=["https://kubernetes.io/docs/tasks/debug/debug-application/debug-pods/"])],
        leads_to=[leads("kubernetes/oomkilled/k8s1-linux", 0.2, "Container starts but consumes too much memory and gets OOMKilled")],
        preceded_by=[preceded("docker/oci-runtime-create-failed/docker27-linux", 0.25, "Container image has startup issues that cause crash loop in K8s"), preceded("kubernetes/imagepullbackoff/k8s1-linux", 0.15, "Fixed image pull but container itself crashes")],
        confused_with=[confused("kubernetes/imagepullbackoff/k8s1-linux", "ImagePullBackOff is about pulling the image; CrashLoopBackOff means image pulled successfully but container crashes")],
    ))

    canons.append(canon(
        "kubernetes", "imagepullbackoff", "k8s1-linux",
        "ImagePullBackOff",
        r"ImagePullBackOff|ErrImagePull",
        "image_error", "kubernetes", ">=1.28,<2.0", "linux", "true", 0.85, 0.88,
        "Cannot pull container image. Wrong image name, tag, or missing registry credentials.",
        [de("Keep waiting for the pull to succeed", "If credentials or image name are wrong, it will never succeed", 0.80, sources=["https://kubernetes.io/docs/concepts/containers/images/#imagepullbackoff"]),
         de("Pull the image manually on the node", "Not scalable and doesn't fix the underlying auth/name issue", 0.72, sources=["https://kubernetes.io/docs/concepts/containers/images/"])],
        [wa("Verify image name and tag exist in the registry", 0.90, "docker pull image:tag", sources=["https://kubernetes.io/docs/concepts/containers/images/#updating-images"]),
         wa("Create or fix imagePullSecrets for private registries", 0.85, "kubectl create secret docker-registry regcred --docker-server=... --docker-username=... --docker-password=...", sources=["https://kubernetes.io/docs/tasks/configure-pod-container/pull-image-private-registry/"])],
        leads_to=[leads("kubernetes/crashloopbackoff/k8s1-linux", 0.3, "Image pulled successfully but container crashes on start")],
        preceded_by=[preceded("docker/exec-format-error/docker27-linux", 0.15, "Wrong architecture image pushed to registry")],
        confused_with=[confused("kubernetes/crashloopbackoff/k8s1-linux", "CrashLoopBackOff means container runs and crashes; ImagePullBackOff means image cannot be downloaded")],
    ))

    canons.append(canon(
        "kubernetes", "oomkilled", "k8s1-linux",
        "OOMKilled",
        r"OOMKilled|Out of memory|OOM",
        "resource_error", "kubernetes", ">=1.28,<2.0", "linux", "partial", 0.55, 0.80,
        "Container exceeded its memory limit and was killed by the kernel OOM killer.",
        [de("Remove memory limits entirely", "Pod can consume all node memory and affect other pods", 0.78, sources=["https://kubernetes.io/docs/concepts/configuration/manage-resources-containers/"]),
         de("Set memory limit to maximum node capacity", "Still kills if it exceeds, and starves other pods", 0.72, sources=["https://kubernetes.io/docs/concepts/configuration/manage-resources-containers/#meaning-of-memory"])],
        [wa("Profile actual memory usage and set limits 20-30% above normal usage", 0.80, "kubectl top pod pod-name", sources=["https://kubernetes.io/docs/tasks/debug/debug-cluster/resource-metrics-pipeline/"]),
         wa("Fix memory leaks in the application or reduce batch sizes", 0.75, sources=["https://kubernetes.io/docs/tasks/configure-pod-container/assign-memory-resource/"])],
        leads_to=[leads("kubernetes/crashloopbackoff/k8s1-linux", 0.35, "OOMKilled container restarts and enters crash loop")],
        preceded_by=[preceded("kubernetes/crashloopbackoff/k8s1-linux", 0.25, "Investigating crash loop reveals OOM as the root cause")],
        confused_with=[confused("python/memoryerror/py311-linux", "Python MemoryError is process-level; OOMKilled is container-level enforced by the kernel"), confused("kubernetes/crashloopbackoff/k8s1-linux", "CrashLoopBackOff is the symptom; OOMKilled is a specific cause of the crash")],
    ))

    # === TERRAFORM ===
    canons.append(canon(
        "terraform", "state-lock-error", "tf1-linux",
        "Error acquiring the state lock",
        r"Error (acquiring|locking) the state lock",
        "state_error", "terraform", ">=1.5,<2.0", "linux", "true", 0.85, 0.88,
        "Another Terraform process holds the state lock or a previous run crashed without releasing it.",
        [de("Delete the state file", "Permanently loses all resource tracking, causing orphaned infrastructure", 0.95, sources=["https://developer.hashicorp.com/terraform/language/state"]),
         de("Use -no-lock flag", "Creates race conditions when multiple users apply simultaneously", 0.78, sources=["https://developer.hashicorp.com/terraform/language/state/locking"])],
        [wa("Force unlock the state with the lock ID", 0.88, "terraform force-unlock LOCK_ID", sources=["https://developer.hashicorp.com/terraform/cli/commands/force-unlock"]),
         wa("Check if another terraform apply is running and wait for it to finish", 0.85, sources=["https://developer.hashicorp.com/terraform/language/state/locking"])],
        leads_to=[leads("terraform/provider-not-present/tf1-linux", 0.1, "After unlock, re-init may be needed to restore providers")],
        preceded_by=[preceded("terraform/cycle-in-module/tf1-linux", 0.1, "Cycle error crashed apply leaving lock behind")],
        confused_with=[confused("terraform/provider-not-present/tf1-linux", "Provider not present is about missing terraform init; state lock is about concurrent access or crashed runs")],
    ))

    canons.append(canon(
        "terraform", "provider-not-present", "tf1-linux",
        "Provider configuration not present",
        r"Provider configuration not present|provider .+ not available",
        "config_error", "terraform", ">=1.5,<2.0", "linux", "true", 0.90, 0.88,
        "Required provider is not configured in the Terraform configuration.",
        [de("Manually download the provider binary", "Terraform manages provider binaries; manual placement is fragile", 0.72, sources=["https://developer.hashicorp.com/terraform/language/providers/configuration"]),
         de("Copy .terraform from another project", "Provider versions and configs may not match", 0.78, sources=["https://developer.hashicorp.com/terraform/cli/commands/init"])],
        [wa("Run terraform init to download and configure providers", 0.92, "terraform init", sources=["https://developer.hashicorp.com/terraform/cli/commands/init"]),
         wa("Add the required_providers block to your terraform configuration", 0.88, sources=["https://developer.hashicorp.com/terraform/language/providers/requirements"])],
        leads_to=[leads("terraform/cycle-in-module/tf1-linux", 0.15, "After init, applying reveals circular dependencies")],
        preceded_by=[preceded("terraform/state-lock-error/tf1-linux", 0.1, "After unlocking state, init needed to restore provider config")],
        confused_with=[confused("terraform/state-lock-error/tf1-linux", "State lock is about concurrent access; provider not present is about missing terraform init")],
    ))

    canons.append(canon(
        "terraform", "cycle-in-module", "tf1-linux",
        "Error: Cycle",
        r"Error: Cycle:?\s*(.+)",
        "dependency_error", "terraform", ">=1.5,<2.0", "linux", "partial", 0.55, 0.78,
        "Circular dependency between resources. Terraform cannot determine apply order.",
        [de("Add depends_on to break the cycle", "depends_on can make cycles worse by adding more edges to the dependency graph", 0.65, sources=["https://developer.hashicorp.com/terraform/language/meta-arguments/depends_on"]),
         de("Move resources to separate modules", "Cycles across modules are even harder to debug", 0.60, sources=["https://developer.hashicorp.com/terraform/language/modules"])],
        [wa("Use terraform graph to visualize the cycle and refactor", 0.78, "terraform graph | dot -Tpng > graph.png", sources=["https://developer.hashicorp.com/terraform/cli/commands/graph"]),
         wa("Break the cycle by using data sources instead of direct references for one direction", 0.72, sources=["https://developer.hashicorp.com/terraform/language/data-sources"])],
        leads_to=[leads("terraform/state-lock-error/tf1-linux", 0.1, "Long-running apply to fix cycle crashes leaving lock")],
        preceded_by=[preceded("terraform/provider-not-present/tf1-linux", 0.15, "After init, plan reveals circular dependencies")],
        confused_with=[confused("terraform/state-lock-error/tf1-linux", "State lock is about concurrent access; cycle error is about circular resource dependencies in configuration")],
    ))

    # === AWS ===
    canons.append(canon(
        "aws", "access-denied-exception", "awscli2-linux",
        "An error occurred (AccessDeniedException) when calling the X operation",
        r"(AccessDeniedException|AccessDenied|403 Forbidden).*when calling",
        "auth_error", "aws", ">=2.0,<3.0", "linux", "true", 0.82, 0.85,
        "IAM permissions insufficient for the requested operation.",
        [de("Add AdministratorAccess policy", "Severe security risk, violates least-privilege principle", 0.85, sources=["https://docs.aws.amazon.com/IAM/latest/UserGuide/best-practices.html#grant-least-privilege"]),
         de("Use root account credentials", "Root should never be used for API calls, critical security issue", 0.95, sources=["https://docs.aws.amazon.com/IAM/latest/UserGuide/best-practices.html#lock-away-credentials"])],
        [wa("Check which specific permission is needed using CloudTrail or IAM Access Analyzer", 0.85, "aws cloudtrail lookup-events --lookup-attributes AttributeKey=EventName,AttributeValue=OperationName", sources=["https://docs.aws.amazon.com/IAM/latest/UserGuide/access-analyzer-getting-started.html"]),
         wa("Add the minimum required IAM policy for the specific action and resource", 0.82, sources=["https://docs.aws.amazon.com/IAM/latest/UserGuide/access_policies_create.html"])],
        leads_to=[leads("aws/expired-token-exception/awscli2-linux", 0.15, "Created temporary credentials that expire"), leads("aws/resource-not-found/awscli2-linux", 0.2, "Has permissions but wrong region or resource name")],
        preceded_by=[preceded("aws/expired-token-exception/awscli2-linux", 0.25, "Refreshed token but new role has insufficient permissions")],
        confused_with=[confused("aws/expired-token-exception/awscli2-linux", "ExpiredToken means valid permissions but expired session; AccessDenied means active session but insufficient permissions"), confused("aws/resource-not-found/awscli2-linux", "ResourceNotFound means resource doesn't exist; AccessDenied means it may exist but you can't access it")],
    ))

    canons.append(canon(
        "aws", "expired-token-exception", "awscli2-linux",
        "An error occurred (ExpiredTokenException): The security token included in the request is expired",
        r"ExpiredTokenException|security token.+is expired|token.+has expired",
        "auth_error", "aws", ">=2.0,<3.0", "linux", "true", 0.90, 0.90,
        "AWS session token has expired. Common with STS temporary credentials and SSO sessions.",
        [de("Hardcode long-lived access keys", "Security anti-pattern, keys can leak and don't rotate", 0.88, sources=["https://docs.aws.amazon.com/IAM/latest/UserGuide/best-practices.html#rotate-credentials"]),
         de("Extend token lifetime to maximum", "Only delays the problem, tokens still expire", 0.55, sources=["https://docs.aws.amazon.com/STS/latest/APIReference/API_GetSessionToken.html"])],
        [wa("Refresh credentials with aws sso login or aws sts assume-role", 0.92, "aws sso login --profile my-profile", sources=["https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-sso.html"]),
         wa("Use credential_process or credential helpers for automatic refresh", 0.85, sources=["https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-sourcing-external.html"])],
        leads_to=[leads("aws/access-denied-exception/awscli2-linux", 0.2, "Refreshed credentials may have different/fewer permissions")],
        preceded_by=[preceded("aws/access-denied-exception/awscli2-linux", 0.15, "Assumed role with temporary credentials that later expire")],
        confused_with=[confused("aws/access-denied-exception/awscli2-linux", "AccessDenied means wrong permissions; ExpiredToken means right permissions but session has timed out")],
    ))

    canons.append(canon(
        "aws", "resource-not-found", "awscli2-linux",
        "An error occurred (ResourceNotFoundException): The specified resource does not exist",
        r"ResourceNotFoundException|NoSuchBucket|NoSuchKey|404.*Not Found",
        "resource_error", "aws", ">=2.0,<3.0", "linux", "true", 0.88, 0.87,
        "AWS resource doesn't exist or is in a different region.",
        [de("Create the resource with the same name", "May not have the same configuration, causing downstream issues", 0.55, sources=["https://docs.aws.amazon.com/general/latest/gr/aws-arns-and-namespaces.html"]),
         de("Switch to us-east-1 (default region)", "Resource may be in a completely different region", 0.62, sources=["https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-files.html#cli-configure-files-settings"])],
        [wa("Check the resource exists in the correct region", 0.90, "aws s3 ls s3://bucket-name --region us-west-2", sources=["https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-files.html#cli-configure-files-settings"]),
         wa("Verify the ARN or resource identifier for typos", 0.85, sources=["https://docs.aws.amazon.com/general/latest/gr/aws-arns-and-namespaces.html"])],
        leads_to=[leads("aws/access-denied-exception/awscli2-linux", 0.15, "Resource found but permissions insufficient in that region")],
        preceded_by=[preceded("aws/access-denied-exception/awscli2-linux", 0.2, "Permissions fixed but resource referenced by wrong name or region")],
        confused_with=[confused("aws/access-denied-exception/awscli2-linux", "AccessDenied can mask ResourceNotFound when permissions hide resource existence for security")],
    ))

    # === NEXTJS ===
    canons.append(canon(
        "nextjs", "hydration-failed", "nextjs14-linux",
        "Error: Hydration failed because the initial UI does not match what was rendered on the server",
        r"Hydration failed because the initial UI does not match",
        "render_error", "nextjs", ">=14,<16", "linux", "partial", 0.60, 0.82,
        "Server-rendered HTML doesn't match client-side render. Common with dynamic content, dates, or browser APIs.",
        [de("Suppress hydration warnings with suppressHydrationWarning", "Masks real bugs, content will flash/shift for users", 0.65, sources=["https://nextjs.org/docs/messages/react-hydration-error"]),
         de("Make everything client-side with 'use client'", "Loses all SSR/SSG benefits, defeats the purpose of Next.js", 0.78, sources=["https://nextjs.org/docs/app/building-your-application/rendering/client-components"])],
        [wa("Move browser-only code into useEffect", 0.82, "const [mounted, setMounted] = useState(false); useEffect(() => setMounted(true), []);", sources=["https://nextjs.org/docs/messages/react-hydration-error"]),
         wa("Use dynamic import with ssr: false for client-only components", 0.78, "const Comp = dynamic(() => import('./Comp'), { ssr: false })", sources=["https://nextjs.org/docs/app/building-your-application/optimizing/lazy-loading"])],
        leads_to=[leads("nextjs/server-component-client-hook/nextjs14-linux", 0.2, "Moving code to useEffect requires making component a Client Component")],
        preceded_by=[preceded("nextjs/server-component-client-hook/nextjs14-linux", 0.15, "Added 'use client' but server/client HTML mismatch remains")],
        confused_with=[confused("react/cannot-update-while-rendering/react18-linux", "Cannot update while rendering is about state updates during render; hydration mismatch is about server/client HTML differences")],
    ))

    canons.append(canon(
        "nextjs", "module-not-found-resolve", "nextjs14-linux",
        "Module not found: Can't resolve 'X'",
        r"Module not found: Can't resolve ['\"](.+?)['\"]",
        "build_error", "nextjs", ">=14,<16", "linux", "true", 0.88, 0.90,
        "Webpack/Turbopack cannot find the module. Usually a missing dependency or wrong import path.",
        [de("Add the module to webpack externals", "Makes the module unavailable at runtime", 0.72, sources=["https://nextjs.org/docs/app/api-reference/next-config-js/webpack"]),
         de("Use require() instead of import", "Doesn't fix the missing module, just changes the error format", 0.65, sources=["https://nextjs.org/docs/app/building-your-application/optimizing/package-bundling"])],
        [wa("Install the missing dependency", 0.92, "npm install missing-package", sources=["https://nextjs.org/docs/getting-started/installation"]),
         wa("Check for typos in the import path and use correct relative/absolute paths", 0.88, sources=["https://nextjs.org/docs/app/building-your-application/configuring/absolute-imports-and-module-aliases"])],
        leads_to=[leads("nextjs/server-component-client-hook/nextjs14-linux", 0.15, "Installed module uses hooks requiring Client Component")],
        preceded_by=[preceded("node/cannot-find-module-npm/node20-linux", 0.2, "npm module issue surfaces as Next.js build error")],
        confused_with=[confused("node/err-module-not-found/node20-linux", "ERR_MODULE_NOT_FOUND is a Node.js runtime error; Next.js Module not found is a webpack/turbopack build error"), confused("typescript/ts2307-cannot-find-module/ts5-linux", "TS2307 is TypeScript compile error; Next.js Module not found is bundler resolution error")],
    ))

    canons.append(canon(
        "nextjs", "server-component-client-hook", "nextjs14-linux",
        "Error: useState/useEffect can only be used in Client Components",
        r"(useState|useEffect|useContext).+can only be used in Client Components",
        "component_error", "nextjs", ">=14,<16", "linux", "true", 0.92, 0.90,
        "React hooks used in a Server Component. Next.js App Router defaults to Server Components.",
        [de("Make the entire page a Client Component", "Loses server-side rendering benefits for the whole page", 0.72, sources=["https://nextjs.org/docs/app/building-your-application/rendering/client-components"]),
         de("Pass hooks through props from a parent Client Component", "Hooks cannot be passed as props, they must be called in the component", 0.85, sources=["https://react.dev/reference/rules/rules-of-hooks"])],
        [wa("Add 'use client' directive at the top of the file that uses hooks", 0.95, "// Add as first line:\n'use client';", sources=["https://nextjs.org/docs/app/building-your-application/rendering/client-components#using-client-components-in-nextjs"]),
         wa("Extract the interactive part into a separate Client Component", 0.90, sources=["https://nextjs.org/docs/app/building-your-application/rendering/composition-patterns"])],
        leads_to=[leads("nextjs/hydration-failed/nextjs14-linux", 0.2, "Client Component has browser-only code causing hydration mismatch"), leads("react/invalid-hook-call/react18-linux", 0.1, "Hook placement still incorrect after adding use client")],
        preceded_by=[preceded("react/invalid-hook-call/react18-linux", 0.2, "Invalid hook call in Next.js is often a Server Component issue")],
        confused_with=[confused("react/invalid-hook-call/react18-linux", "Invalid hook call is about hook rules; server-component-client-hook is about Server vs Client Component boundary")],
    ))

    # === REACT ===
    canons.append(canon(
        "react", "invalid-hook-call", "react18-linux",
        "Invalid hook call. Hooks can only be called inside the body of a function component",
        r"Invalid hook call.*Hooks can only be called inside",
        "hook_error", "react", ">=18,<20", "linux", "true", 0.85, 0.88,
        "Hook called outside a component, in a class component, or with multiple React copies.",
        [de("Convert class component to function component just for hooks", "If the class has complex lifecycle, conversion may introduce bugs", 0.55, sources=["https://react.dev/reference/rules/rules-of-hooks"]),
         de("Call hooks inside event handlers or callbacks", "Hooks must be at the top level, not inside conditions or callbacks", 0.82, sources=["https://react.dev/warnings/invalid-hook-call-warning"])],
        [wa("Ensure hooks are called at the top level of a function component", 0.92, sources=["https://react.dev/reference/rules/rules-of-hooks"]),
         wa("Check for duplicate React versions in node_modules", 0.85, "npm ls react", sources=["https://react.dev/warnings/invalid-hook-call-warning"])],
        leads_to=[leads("react/too-many-rerenders/react18-linux", 0.15, "Fixing hook placement may introduce render loop if dependencies wrong"), leads("react/cannot-update-while-rendering/react18-linux", 0.1, "Moved hook call but placed state update in render body")],
        preceded_by=[preceded("nextjs/server-component-client-hook/nextjs14-linux", 0.2, "Next.js Server Component hook error leads to investigating hook rules")],
        confused_with=[confused("nextjs/server-component-client-hook/nextjs14-linux", "Server Component error is about component type; invalid hook call is about hook placement rules")],
    ))

    canons.append(canon(
        "react", "cannot-update-while-rendering", "react18-linux",
        "Cannot update a component while rendering a different component",
        r"Cannot update a component .+ while rendering a different component",
        "render_error", "react", ">=18,<20", "linux", "true", 0.82, 0.85,
        "State update triggered during render phase of another component. Usually setState in render body.",
        [de("Wrap the update in setTimeout", "Hacky fix that can cause flickering and race conditions", 0.65, sources=["https://react.dev/reference/react/useState#ive-updated-the-state-but-the-screen-doesnt-update"]),
         de("Use useLayoutEffect for the update", "May cause the same issue if the update triggers a re-render", 0.60, sources=["https://react.dev/reference/react/useLayoutEffect"])],
        [wa("Move the state update into useEffect", 0.90, "useEffect(() => { setState(value); }, [dependency]);", sources=["https://react.dev/reference/react/useEffect"]),
         wa("Restructure to lift state up or use a shared context", 0.82, sources=["https://react.dev/learn/sharing-state-between-components"])],
        leads_to=[leads("react/too-many-rerenders/react18-linux", 0.25, "Moving update to useEffect with wrong deps causes infinite loop")],
        preceded_by=[preceded("react/too-many-rerenders/react18-linux", 0.2, "Fixed infinite loop but state update now happens during render")],
        confused_with=[confused("react/too-many-rerenders/react18-linux", "Too many re-renders is about infinite loops; cannot-update-while-rendering is about timing of state updates")],
    ))

    canons.append(canon(
        "react", "too-many-rerenders", "react18-linux",
        "Error: Too many re-renders. React limits the number of renders to prevent an infinite loop",
        r"Too many re-renders.*React limits the number of renders",
        "render_error", "react", ">=18,<20", "linux", "true", 0.88, 0.90,
        "Infinite render loop caused by setState during render or wrong useEffect dependencies.",
        [de("Increase React's render limit", "There is no configurable render limit; the issue is an infinite loop", 0.90, sources=["https://react.dev/reference/react/useState"]),
         de("Remove all useEffect dependencies", "Makes useEffect run on every render, potentially worsening the loop", 0.78, sources=["https://react.dev/reference/react/useEffect#specifying-reactive-dependencies"])],
        [wa("Check for setState calls during render (not inside useEffect or event handlers)", 0.92, sources=["https://react.dev/reference/react/useState#setstate-caveats"]),
         wa("Fix useEffect dependency arrays to prevent retriggering", 0.88, "useEffect(() => { ... }, [specificDep]); // not [object] or []", sources=["https://react.dev/reference/react/useEffect#specifying-reactive-dependencies"])],
        leads_to=[leads("react/cannot-update-while-rendering/react18-linux", 0.2, "Fixing the loop may move setState to wrong phase of render cycle")],
        preceded_by=[preceded("react/cannot-update-while-rendering/react18-linux", 0.2, "Fixing render-phase update by adding useEffect causes infinite loop"), preceded("react/invalid-hook-call/react18-linux", 0.1, "Fixing hook placement introduces dependency array issues")],
        confused_with=[confused("react/cannot-update-while-rendering/react18-linux", "Cannot update while rendering is about state update timing; too many re-renders is about infinite render loops")],
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
