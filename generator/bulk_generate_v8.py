"""Bulk generate wave 8: +50 canons (target: ~340 total).

Usage: python -m generator.bulk_generate_v8
"""

import json
from generator.bulk_generate import (
    canon, de, wa, DATA_DIR,
)


def get_all_canons():
    c = []

    # ── PYTHON ──────────────────────────────────────────

    c.append(canon(
        "python", "attributeerror-module-no-attribute", "py311-linux",
        "AttributeError: module 'X' has no attribute 'Y'",
        r"AttributeError: module '(\w+)' has no attribute '(\w+)'",
        "import_error", "python", ">=3.11,<3.13", "linux",
        "true", 0.92, 0.92,
        "Module imported but attribute doesn't exist. Common: file named same as module (shadowing).",
        [de("Reinstall the package",
            "Usually not a package issue — it's a naming conflict in your project", 0.65,
            sources=["https://docs.python.org/3/reference/import.html"]),
         de("Use importlib to force reimport",
            "Reimporting doesn't fix shadowed module names", 0.70,
            sources=["https://docs.python.org/3/library/importlib.html"])],
        [wa("Check if you have a local file named same as the module: ls *.py | grep <module>", 0.95,
            "# e.g., having 'random.py' shadows stdlib random module",
            sources=["https://docs.python.org/3/reference/import.html#the-module-search-path"]),
         wa("Check the module version — attribute may have been added/removed in an update", 0.88,
            "python -c 'import module; print(module.__version__)'",
            sources=["https://docs.python.org/3/library/importlib.metadata.html"])],
        python=">=3.11,<3.13",
    ))

    c.append(canon(
        "python", "runtimeerror-set-changed-size", "py311-linux",
        "RuntimeError: Set changed size during iteration",
        r"RuntimeError: Set changed size during iteration",
        "runtime_error", "python", ">=3.11,<3.13", "linux",
        "true", 0.95, 0.95,
        "Modifying a set while iterating. Same issue as dict changed size during iteration.",
        [de("Use try/except to catch and retry",
            "Unreliable — iteration results are undefined after modification", 0.80,
            sources=["https://docs.python.org/3/library/stdtypes.html#set"]),
         de("Convert to a thread-safe set",
            "Thread safety doesn't fix single-threaded iteration mutation", 0.75,
            sources=["https://docs.python.org/3/library/stdtypes.html#set"])],
        [wa("Iterate over a copy: for item in set(my_set): my_set.discard(item)", 0.95,
            sources=["https://docs.python.org/3/library/stdtypes.html#frozenset"]),
         wa("Build a new set with set comprehension instead of modifying in place", 0.92,
            "filtered = {x for x in my_set if condition(x)}",
            sources=["https://docs.python.org/3/tutorial/datastructures.html#sets"])],
        python=">=3.11,<3.13",
    ))

    c.append(canon(
        "python", "subprocess-calledprocesserror", "py311-linux",
        "subprocess.CalledProcessError: Command '...' returned non-zero exit status 1",
        r"CalledProcessError.*returned non-zero exit status",
        "subprocess_error", "python", ">=3.11,<3.13", "linux",
        "partial", 0.82, 0.85,
        "Subprocess command failed. The actual error is in the subprocess output, not in Python.",
        [de("Use shell=True to avoid the error",
            "shell=True doesn't fix the command failure and adds security risks", 0.80,
            sources=["https://docs.python.org/3/library/subprocess.html#security-considerations"]),
         de("Remove check=True to ignore errors",
            "Silently ignores failures — downstream code may get wrong results", 0.65,
            sources=["https://docs.python.org/3/library/subprocess.html#subprocess.run"])],
        [wa("Read stderr output to see the actual error: e.stderr.decode()", 0.95,
            "try:\n    subprocess.run(cmd, check=True, capture_output=True)\nexcept subprocess.CalledProcessError as e:\n    print(e.stderr.decode())",
            sources=["https://docs.python.org/3/library/subprocess.html#subprocess.CalledProcessError"]),
         wa("Test the command manually in terminal first to debug", 0.90,
            sources=["https://docs.python.org/3/library/subprocess.html#subprocess.run"])],
        python=">=3.11,<3.13",
    ))

    c.append(canon(
        "python", "pydantic-validation-error", "py311-linux",
        "pydantic.error_wrappers.ValidationError: N validation errors for Model",
        r"ValidationError.*validation error.*for|pydantic.*ValidationError",
        "validation_error", "python", ">=3.11,<3.13", "linux",
        "true", 0.92, 0.92,
        "Pydantic model received data that doesn't match the schema. Type or required field error.",
        [de("Use model_construct() to skip validation",
            "Creates invalid model instances — bugs will surface later", 0.75,
            sources=["https://docs.pydantic.dev/latest/concepts/models/#model-methods-and-properties"]),
         de("Make all fields Optional",
            "Defeats the purpose of validation — model can hold invalid state", 0.70,
            sources=["https://docs.pydantic.dev/latest/concepts/fields/"])],
        [wa("Read the error details — Pydantic tells you exactly which field and what's wrong", 0.95,
            "try:\n    Model(**data)\nexcept ValidationError as e:\n    print(e.errors())  # detailed field-by-field errors",
            sources=["https://docs.pydantic.dev/latest/concepts/models/"]),
         wa("Use model_validate with strict=False for coercion if types are close", 0.85,
            sources=["https://docs.pydantic.dev/latest/concepts/models/#model-methods-and-properties"])],
        python=">=3.11,<3.13",
    ))

    # ── NODE ──────────────────────────────────────────

    c.append(canon(
        "node", "cors-blocked", "node20-linux",
        "Access to fetch has been blocked by CORS policy: No 'Access-Control-Allow-Origin' header",
        r"CORS.*blocked|Access-Control-Allow-Origin|has been blocked by CORS",
        "http_error", "node", ">=20,<23", "linux",
        "true", 0.92, 0.92,
        "Browser blocks cross-origin request. Server must send correct CORS headers.",
        [de("Disable CORS in the browser",
            "Only works for development — can't ask users to disable CORS", 0.80,
            sources=["https://developer.mozilla.org/en-US/docs/Web/HTTP/CORS"]),
         de("Use no-cors mode in fetch",
            "Response becomes opaque — you can't read the data", 0.85,
            sources=["https://developer.mozilla.org/en-US/docs/Web/API/Request/mode"])],
        [wa("Add CORS headers on the server: Access-Control-Allow-Origin", 0.95,
            "// Express: app.use(cors())\n// or: res.setHeader('Access-Control-Allow-Origin', '*')",
            sources=["https://developer.mozilla.org/en-US/docs/Web/HTTP/CORS"]),
         wa("Use a proxy in development: Next.js rewrites, Vite proxy, or CRA proxy", 0.90,
            sources=["https://developer.mozilla.org/en-US/docs/Web/HTTP/CORS"]),
         wa("For APIs you don't control, use a server-side proxy to make the request", 0.85,
            sources=["https://developer.mozilla.org/en-US/docs/Web/HTTP/CORS"])],
    ))

    c.append(canon(
        "node", "cannot-find-module-relative", "node20-linux",
        "Error: Cannot find module './X' (local file import)",
        r"Cannot find module '\.\/.+'|MODULE_NOT_FOUND.*\.\/",
        "module_error", "node", ">=20,<23", "linux",
        "true", 0.95, 0.95,
        "Local file import failed. Wrong path, missing extension, or file doesn't exist.",
        [de("Install it as an npm package",
            "It's a local file (./), not a package — it won't be on npm", 0.90,
            sources=["https://nodejs.org/api/modules.html#file-modules"]),
         de("Add an index.js file",
            "Only works if importing a directory, not a specific file", 0.65,
            sources=["https://nodejs.org/api/modules.html#folders-as-modules"])],
        [wa("Check the file path — case-sensitive on Linux: ./Utils.js != ./utils.js", 0.95,
            sources=["https://nodejs.org/api/modules.html#file-modules"]),
         wa("For TypeScript/ESM, you may need the extension: import './file.js' (not .ts)", 0.90,
            sources=["https://nodejs.org/api/esm.html#mandatory-file-extensions"]),
         wa("Verify the file exists at the path relative to the importing file", 0.88,
            sources=["https://nodejs.org/api/modules.html#file-modules"])],
    ))

    c.append(canon(
        "node", "segfault-native-module", "node20-linux",
        "Segmentation fault (core dumped) in Node.js",
        r"Segmentation fault|SIGSEGV|segfault",
        "crash_error", "node", ">=20,<23", "linux",
        "partial", 0.70, 0.80,
        "Node process crashed with segfault. Usually a native addon bug or memory corruption.",
        [de("Increase memory with --max-old-space-size",
            "Segfaults aren't OOM errors — more memory won't help", 0.80,
            sources=["https://nodejs.org/api/report.html"]),
         de("Use try/catch to handle segfaults",
            "Segfaults can't be caught by JavaScript — they crash the process", 0.95,
            sources=["https://nodejs.org/api/process.html#event-uncaughtexception"])],
        [wa("Rebuild native modules for current Node version: npm rebuild", 0.90,
            sources=["https://nodejs.org/api/addons.html"]),
         wa("Run with --report-on-fatalerror to get diagnostic report", 0.85,
            "node --report-on-fatalerror app.js",
            sources=["https://nodejs.org/api/report.html"]),
         wa("If reproducible, report to the native module's issue tracker with Node version info", 0.78,
            sources=["https://nodejs.org/api/report.html"])],
    ))

    # ── DOCKER ──────────────────────────────────────────

    c.append(canon(
        "docker", "entrypoint-not-found", "docker27-linux",
        "docker: Error response from daemon: OCI runtime create failed: exec: \"entrypoint.sh\": not found",
        r"exec:.*not found|entrypoint.*not found|executable file not found",
        "runtime_error", "docker", ">=27,<28", "linux",
        "true", 0.92, 0.92,
        "Container entrypoint/cmd executable not found. Wrong path, missing file, or line endings.",
        [de("Use shell form CMD instead of exec form",
            "Shell form has overhead and signal handling issues", 0.55,
            sources=["https://docs.docker.com/reference/dockerfile/#cmd"]),
         de("Install bash in the container",
            "If using alpine, shell scripts need #!/bin/sh not #!/bin/bash", 0.60,
            sources=["https://docs.docker.com/reference/dockerfile/#entrypoint"])],
        [wa("Check the path is correct and the file was COPYed into the image", 0.95,
            "docker run --rm <image> ls -la /app/entrypoint.sh",
            sources=["https://docs.docker.com/reference/dockerfile/#entrypoint"]),
         wa("Fix line endings — Windows CRLF breaks Linux scripts: dos2unix entrypoint.sh", 0.90,
            sources=["https://docs.docker.com/reference/dockerfile/#entrypoint"]),
         wa("Make script executable: RUN chmod +x /app/entrypoint.sh in Dockerfile", 0.88,
            sources=["https://docs.docker.com/reference/dockerfile/#run"])],
    ))

    c.append(canon(
        "docker", "layer-cache-miss", "docker27-linux",
        "Docker build not using cache / rebuilding all layers",
        r"(COPY|ADD).*cache miss|layer cache|--no-cache|cache bust",
        "build_error", "docker", ">=27,<28", "linux",
        "true", 0.90, 0.90,
        "Docker layer cache invalidated. A COPY before the layer invalidates all subsequent layers.",
        [de("Use --no-cache to fix cache issues",
            "Rebuilds everything — the opposite of what you want", 0.90,
            sources=["https://docs.docker.com/build/cache/"]),
         de("Put all COPY commands at the beginning",
            "Invalidates all layers on any file change — worst ordering", 0.85,
            sources=["https://docs.docker.com/build/cache/"])],
        [wa("Order Dockerfile: system deps → copy package files → install deps → copy source", 0.95,
            "COPY package.json package-lock.json ./\nRUN npm install\nCOPY . .  # source changes don't bust npm cache",
            sources=["https://docs.docker.com/build/cache/#order-your-layers"]),
         wa("Use .dockerignore to exclude files that change frequently (logs, .git, node_modules)", 0.90,
            sources=["https://docs.docker.com/build/concepts/context/#dockerignore-files"]),
         wa("Use BuildKit cache mounts for package managers: --mount=type=cache,target=/root/.cache/pip", 0.85,
            sources=["https://docs.docker.com/build/cache/#use-cache-mounts"])],
    ))

    # ── GIT ──────────────────────────────────────────

    c.append(canon(
        "git", "cherry-pick-conflict", "git2-linux",
        "error: could not apply <hash>... Commit message (cherry-pick conflict)",
        r"could not apply.*cherry.?pick|CONFLICT.*cherry.?pick|cherry-pick.*failed",
        "cherry_pick_error", "git", ">=2.30,<3.0", "linux",
        "true", 0.88, 0.90,
        "Cherry-pick has conflicts. Target branch diverged from the source branch.",
        [de("Use --skip to skip conflicting commits",
            "Loses the changes from that commit entirely", 0.75,
            sources=["https://git-scm.com/docs/git-cherry-pick"]),
         de("Abort and merge instead",
            "Merge brings all commits — you wanted just specific ones", 0.55,
            sources=["https://git-scm.com/docs/git-cherry-pick"])],
        [wa("Resolve conflicts manually, then: git add <files> && git cherry-pick --continue", 0.95,
            sources=["https://git-scm.com/docs/git-cherry-pick"]),
         wa("Use -x flag to record the source commit hash in the message", 0.82,
            "git cherry-pick -x <hash>",
            sources=["https://git-scm.com/docs/git-cherry-pick#Documentation/git-cherry-pick.txt--x"]),
         wa("Abort and start over if it gets messy: git cherry-pick --abort", 0.88,
            sources=["https://git-scm.com/docs/git-cherry-pick"])],
    ))

    c.append(canon(
        "git", "submodule-not-initialized", "git2-linux",
        "fatal: no submodule mapping found in .gitmodules for path 'X'",
        r"no submodule mapping|submodule.*not initialized|Submodule.*not updated",
        "submodule_error", "git", ">=2.30,<3.0", "linux",
        "true", 0.90, 0.90,
        "Git submodule not initialized. Common after cloning a repo with submodules.",
        [de("Delete the submodule directory and re-clone the whole repo",
            "git submodule init is much simpler", 0.75,
            sources=["https://git-scm.com/docs/git-submodule"]),
         de("Copy the submodule code directly into the repo",
            "Defeats the purpose of submodules — lose upstream updates", 0.70,
            sources=["https://git-scm.com/docs/git-submodule"])],
        [wa("Initialize and update: git submodule init && git submodule update", 0.95,
            sources=["https://git-scm.com/docs/git-submodule"]),
         wa("Or clone with submodules included: git clone --recurse-submodules <url>", 0.92,
            sources=["https://git-scm.com/docs/git-clone#Documentation/git-clone.txt---recurse-submodules"]),
         wa("Update to latest: git submodule update --init --recursive", 0.90,
            sources=["https://git-scm.com/docs/git-submodule"])],
    ))

    # ── KUBERNETES ──────────────────────────────────────────

    c.append(canon(
        "kubernetes", "crd-version-not-served", "k8s1-linux",
        "error: unable to recognize: no matches for kind \"X\" in version \"v1alpha1\"",
        r"no matches for kind.*in version|version.*not served|apiVersion.*not supported",
        "api_version_error", "kubernetes", ">=1.28,<2.0", "linux",
        "true", 0.88, 0.90,
        "CRD API version deprecated or not served. Cluster upgraded and old API version removed.",
        [de("Downgrade the cluster",
            "Dangerous and loses features from newer versions", 0.85,
            sources=["https://kubernetes.io/docs/reference/using-api/deprecation-policy/"]),
         de("Force apply with --validate=false",
            "Bypasses validation but API server still rejects the version", 0.80,
            sources=["https://kubernetes.io/docs/reference/using-api/deprecation-policy/"])],
        [wa("Update the apiVersion in your manifests to the current served version", 0.95,
            "# Old: apiVersion: extensions/v1beta1\n# New: apiVersion: apps/v1",
            sources=["https://kubernetes.io/docs/reference/using-api/deprecation-policy/"]),
         wa("Use kubectl convert to migrate manifests: kubectl convert -f old.yaml --output-version apps/v1", 0.88,
            sources=["https://kubernetes.io/docs/tasks/tools/install-kubectl-linux/"]),
         wa("Check deprecation notices: kubectl api-resources to see current API groups", 0.85,
            sources=["https://kubernetes.io/docs/reference/using-api/deprecation-policy/"])],
    ))

    c.append(canon(
        "kubernetes", "node-not-ready", "k8s1-linux",
        "Node condition: NotReady",
        r"NotReady|node.*not ready|condition.*Ready.*False",
        "node_error", "kubernetes", ">=1.28,<2.0", "linux",
        "partial", 0.78, 0.85,
        "Kubernetes node is not healthy. Kubelet, container runtime, or networking issue.",
        [de("Delete the node and readd it",
            "May lose workloads that aren't replicated", 0.65,
            sources=["https://kubernetes.io/docs/concepts/architecture/nodes/"]),
         de("Cordon and ignore",
            "Doesn't fix the issue — workloads won't be scheduled there", 0.50,
            sources=["https://kubernetes.io/docs/concepts/architecture/nodes/"])],
        [wa("Check kubelet status: systemctl status kubelet on the node", 0.92,
            sources=["https://kubernetes.io/docs/reference/command-line-tools-reference/kubelet/"]),
         wa("Check node conditions: kubectl describe node <name> for detailed status", 0.90,
            sources=["https://kubernetes.io/docs/concepts/architecture/nodes/#condition"]),
         wa("Common causes: disk pressure, memory pressure, PID pressure, or container runtime down", 0.85,
            sources=["https://kubernetes.io/docs/concepts/architecture/nodes/#condition"])],
    ))

    # ── RUST ──────────────────────────────────────────

    c.append(canon(
        "rust", "e0282-type-annotations-needed", "rust1-linux",
        "error[E0282]: type annotations needed",
        r"E0282.*type annotations needed|cannot infer type",
        "type_error", "rust", ">=1.70,<2.0", "linux",
        "true", 0.95, 0.95,
        "Rust can't infer the type. Need explicit annotation or turbofish syntax.",
        [de("Use dyn Any to avoid specifying types",
            "Loses all type safety — defeats the purpose of Rust's type system", 0.85,
            sources=["https://doc.rust-lang.org/error_codes/E0282.html"]),
         de("Use macro magic to auto-infer",
            "Macros can't infer types that the compiler can't", 0.80,
            sources=["https://doc.rust-lang.org/error_codes/E0282.html"])],
        [wa("Add type annotation: let x: Vec<i32> = vec![];", 0.95,
            sources=["https://doc.rust-lang.org/error_codes/E0282.html"]),
         wa("Use turbofish syntax: iter.collect::<Vec<_>>()", 0.92,
            sources=["https://doc.rust-lang.org/reference/expressions/method-call-expr.html"]),
         wa("Provide type through usage context: the compiler can sometimes infer from how the value is used", 0.85,
            sources=["https://doc.rust-lang.org/book/ch03-02-data-types.html"])],
    ))

    # ── GO ──────────────────────────────────────────

    c.append(canon(
        "go", "race-condition-detected", "go1-linux",
        "WARNING: DATA RACE",
        r"DATA RACE|race condition|concurrent map (read and map write|writes)",
        "concurrency_error", "go", ">=1.21,<2.0", "linux",
        "true", 0.88, 0.90,
        "Race detector found concurrent access to shared data without synchronization.",
        [de("Ignore race detector warnings",
            "Race conditions cause data corruption and random crashes", 0.90,
            sources=["https://go.dev/doc/articles/race_detector"]),
         de("Add sleep() to avoid races",
            "Sleep doesn't synchronize — just makes races less frequent", 0.85,
            sources=["https://go.dev/doc/articles/race_detector"])],
        [wa("Use sync.Mutex to protect shared data", 0.92,
            "var mu sync.Mutex\nmu.Lock()\nsharedMap[key] = value\nmu.Unlock()",
            sources=["https://pkg.go.dev/sync#Mutex"]),
         wa("Use channels for goroutine communication instead of shared memory", 0.90,
            "ch := make(chan Result)\ngo func() { ch <- compute() }()",
            sources=["https://go.dev/doc/effective_go#channels"]),
         wa("Use sync.Map for concurrent map access", 0.85,
            sources=["https://pkg.go.dev/sync#Map"])],
    ))

    c.append(canon(
        "go", "connection-refused", "go1-linux",
        "dial tcp [::1]:PORT: connect: connection refused",
        r"dial tcp.*connection refused|connect:.*connection refused",
        "network_error", "go", ">=1.21,<2.0", "linux",
        "partial", 0.82, 0.85,
        "TCP connection refused. Target server not running or wrong host/port.",
        [de("Increase the connection timeout",
            "Connection refused is immediate — timeout doesn't help", 0.80,
            sources=["https://pkg.go.dev/net#Dial"]),
         de("Use net.DialUDP instead",
            "If the server expects TCP, switching to UDP won't work", 0.90,
            sources=["https://pkg.go.dev/net"])],
        [wa("Verify the server is running on the expected host:port", 0.95,
            "curl -v http://localhost:PORT  # or: ss -tlnp | grep PORT",
            sources=["https://pkg.go.dev/net#Dial"]),
         wa("Check if using IPv6 [::1] vs IPv4 127.0.0.1 — server may only listen on one", 0.88,
            sources=["https://pkg.go.dev/net#Dial"]),
         wa("Add retry logic with backoff for services that start slowly", 0.82,
            sources=["https://pkg.go.dev/net#Dial"])],
    ))

    # ── AWS ──────────────────────────────────────────

    c.append(canon(
        "aws", "assume-role-unauthorized", "awscli2-linux",
        "An error occurred (AccessDenied) when calling the AssumeRole operation",
        r"AccessDenied.*AssumeRole|not authorized to perform.*sts:AssumeRole",
        "iam_error", "aws", ">=2.0,<3.0", "linux",
        "true", 0.88, 0.90,
        "Can't assume the IAM role. Trust policy doesn't allow the caller, or caller lacks sts:AssumeRole.",
        [de("Use root credentials instead",
            "Root account should never be used for programmatic access", 0.90,
            sources=["https://docs.aws.amazon.com/IAM/latest/UserGuide/id_roles_use_switch-role-api.html"]),
         de("Disable STS in the account",
            "STS is required for role assumption — can't disable it", 0.95,
            sources=["https://docs.aws.amazon.com/IAM/latest/UserGuide/id_credentials_temp_enable-regions.html"])],
        [wa("Check the role's trust policy allows your principal (user/role ARN)", 0.92,
            "aws iam get-role --role-name <name> --query 'Role.AssumeRolePolicyDocument'",
            sources=["https://docs.aws.amazon.com/IAM/latest/UserGuide/id_roles_use_switch-role-api.html"]),
         wa("Ensure caller has sts:AssumeRole permission for the target role ARN", 0.90,
            sources=["https://docs.aws.amazon.com/STS/latest/APIReference/API_AssumeRole.html"]),
         wa("Check for ExternalId requirement if assuming cross-account role", 0.82,
            sources=["https://docs.aws.amazon.com/IAM/latest/UserGuide/id_roles_create_for-user_externalid.html"])],
    ))

    # ── TERRAFORM ──────────────────────────────────────────

    c.append(canon(
        "terraform", "provider-version-constraint", "tf1-linux",
        "Error: Failed to query available provider packages",
        r"Failed to query available provider|provider.*version constraints|no available releases match",
        "provider_error", "terraform", ">=1.5,<2.0", "linux",
        "true", 0.90, 0.90,
        "No provider version matches the constraint. Version pinned too tightly or doesn't exist.",
        [de("Remove all version constraints",
            "May install incompatible provider versions that break your config", 0.70,
            sources=["https://developer.hashicorp.com/terraform/language/providers/requirements"]),
         de("Use a local provider binary",
            "Hard to maintain and doesn't get security updates", 0.65,
            sources=["https://developer.hashicorp.com/terraform/cli/config/config-file#provider-installation"])],
        [wa("Check available versions: terraform providers --help or browse the registry", 0.92,
            sources=["https://registry.terraform.io/"]),
         wa("Relax version constraint: use ~> for minor version flexibility", 0.90,
            'required_providers {\n  aws = { source = "hashicorp/aws", version = "~> 5.0" }\n}',
            sources=["https://developer.hashicorp.com/terraform/language/providers/requirements#version-constraints"]),
         wa("Run terraform init -upgrade to refresh provider cache", 0.85,
            sources=["https://developer.hashicorp.com/terraform/cli/commands/init"])],
    ))

    c.append(canon(
        "terraform", "depends-on-module", "tf1-linux",
        "Error: Module output depends on resource that no longer exists",
        r"depends on resource.*no longer exists|orphan.*resource|module.*output.*depends",
        "state_error", "terraform", ">=1.5,<2.0", "linux",
        "partial", 0.80, 0.85,
        "Module references a resource that was removed from config but exists in state.",
        [de("Delete the entire module and recreate",
            "Destroys all resources in the module — may cause outage", 0.75,
            sources=["https://developer.hashicorp.com/terraform/language/modules/syntax"]),
         de("Manually edit the state JSON",
            "Error-prone — one mistake can corrupt the entire state", 0.80,
            sources=["https://developer.hashicorp.com/terraform/language/state"])],
        [wa("Use terraform state rm to remove the orphaned resource from state", 0.92,
            "terraform state rm module.name.resource_type.name",
            sources=["https://developer.hashicorp.com/terraform/cli/commands/state/rm"]),
         wa("Run terraform plan to see what will change, then targeted apply if needed", 0.85,
            "terraform plan -target=module.name",
            sources=["https://developer.hashicorp.com/terraform/cli/commands/plan"]),
         wa("Use terraform state list to inventory what's tracked vs what's in config", 0.82,
            sources=["https://developer.hashicorp.com/terraform/cli/commands/state/list"])],
    ))

    # ── NEXT.JS ──────────────────────────────────────────

    c.append(canon(
        "nextjs", "loading-chunk-failed", "nextjs14-linux",
        "ChunkLoadError: Loading chunk X failed",
        r"ChunkLoadError|Loading chunk.*failed|Failed to fetch dynamically imported module",
        "build_error", "nextjs", ">=14,<16", "linux",
        "partial", 0.82, 0.85,
        "Webpack chunk (code split piece) not found. Deploy replaced files while users had old HTML.",
        [de("Disable code splitting",
            "Destroys performance — one huge bundle", 0.80,
            sources=["https://nextjs.org/docs/app/building-your-application/optimizing/lazy-loading"]),
         de("Force reload on every navigation",
            "Terrible UX — kills SPA behavior", 0.75,
            sources=["https://nextjs.org/docs/app/building-your-application/deploying"])],
        [wa("Add error boundary that triggers window.location.reload() on ChunkLoadError", 0.90,
            sources=["https://react.dev/reference/react/Component#catching-rendering-errors-with-an-error-boundary"]),
         wa("Use content-addressed filenames (default in Next.js) so old chunks remain available", 0.85,
            sources=["https://nextjs.org/docs/app/building-your-application/deploying"]),
         wa("Keep old build assets for a grace period during deployments", 0.82,
            sources=["https://nextjs.org/docs/app/building-your-application/deploying"])],
    ))

    # ── REACT ──────────────────────────────────────────

    c.append(canon(
        "react", "context-value-undefined", "react18-linux",
        "Cannot destructure property 'X' of useContext(...) as it is null/undefined",
        r"Cannot destructure.*useContext|useContext.*undefined|context.*null",
        "context_error", "react", ">=18,<20", "linux",
        "true", 0.92, 0.92,
        "useContext returns default (undefined/null) because component isn't wrapped in Provider.",
        [de("Provide a default value in createContext that mimics the real value",
            "Default values mask the missing Provider — bugs appear silently", 0.60,
            sources=["https://react.dev/reference/react/createContext"]),
         de("Use optional chaining on every context property",
            "Verbose and hides the real issue — missing Provider", 0.65,
            sources=["https://react.dev/reference/react/useContext"])],
        [wa("Ensure the component is a child of the Context.Provider in the tree", 0.95,
            "<MyContext.Provider value={value}>\n  <ChildComponent />  {/* can now useContext */}\n</MyContext.Provider>",
            sources=["https://react.dev/reference/react/useContext"]),
         wa("Create a custom hook that throws if used outside Provider", 0.90,
            "function useMyContext() {\n  const ctx = useContext(MyCtx);\n  if (!ctx) throw new Error('Missing Provider');\n  return ctx;\n}",
            sources=["https://react.dev/reference/react/useContext"])],
    ))

    # ── TYPESCRIPT ──────────────────────────────────────────

    c.append(canon(
        "typescript", "ts2742-inferred-type-not-portable", "ts5-linux",
        "error TS2742: The inferred type of 'X' cannot be named without a reference to 'Y'",
        r"TS2742.*inferred type.*cannot be named",
        "type_error", "typescript", ">=5.0,<6.0", "linux",
        "true", 0.85, 0.88,
        "TypeScript can infer the type but can't express it in declaration files. Common with monorepos.",
        [de("Set declaration: false in tsconfig",
            "Breaks libraries that need .d.ts files for consumers", 0.65,
            sources=["https://www.typescriptlang.org/tsconfig/#declaration"]),
         de("Use any as the explicit type",
            "Loses all type information for consumers", 0.75,
            sources=["https://www.typescriptlang.org/docs/handbook/2/everyday-types.html#any"])],
        [wa("Add the dependency that defines the type to your package.json dependencies (not just devDependencies)", 0.92,
            sources=["https://www.typescriptlang.org/docs/handbook/modules/reference.html"]),
         wa("Add an explicit return type annotation to avoid relying on inference", 0.88,
            "export function create(): ExplicitReturnType { ... }",
            sources=["https://www.typescriptlang.org/docs/handbook/2/functions.html#return-type-annotations"]),
         wa("In monorepos, ensure TypeScript project references are set up correctly", 0.82,
            sources=["https://www.typescriptlang.org/docs/handbook/project-references.html"])],
    ))

    # ── CUDA ──────────────────────────────────────────

    c.append(canon(
        "cuda", "cuda-lazy-loading", "cuda12-rtx4090",
        "RuntimeError: CUDA lazy loading is not enabled",
        r"CUDA lazy loading|CUDA_MODULE_LOADING|lazy.*loading.*CUDA",
        "config_error", "cuda", ">=12.0,<13.0", "linux",
        "true", 0.90, 0.90,
        "CUDA lazy loading environment variable not set. Improves startup time and memory usage.",
        [de("Set CUDA_MODULE_LOADING=EAGER",
            "EAGER is the default — you want LAZY for better performance", 0.70,
            sources=["https://docs.nvidia.com/cuda/cuda-c-programming-guide/index.html"]),
         de("Ignore the warning",
            "Missing lazy loading wastes GPU memory at startup", 0.55,
            sources=["https://pytorch.org/docs/stable/notes/cuda.html"])],
        [wa("Set CUDA_MODULE_LOADING=LAZY in your environment", 0.95,
            "export CUDA_MODULE_LOADING=LAZY",
            sources=["https://pytorch.org/docs/stable/notes/cuda.html"]),
         wa("Add to .bashrc or .env file for persistence", 0.90,
            sources=["https://docs.nvidia.com/cuda/cuda-c-programming-guide/index.html"])],
        gpu="RTX 4090", vram=24,
    ))

    # ── PIP ──────────────────────────────────────────

    c.append(canon(
        "pip", "yanked-version-warning", "pip24-linux",
        "WARNING: The candidate selected for download or install is a yanked version",
        r"yanked version|yanked.*release|has been yanked",
        "security_warning", "pip", ">=24,<25", "linux",
        "true", 0.88, 0.88,
        "Package version was yanked (recalled) from PyPI. Usually has a critical bug or security issue.",
        [de("Pin to the yanked version to suppress the warning",
            "The version was yanked for a reason — likely has a serious issue", 0.80,
            sources=["https://pip.pypa.io/en/stable/topics/yanked/"]),
         de("Ignore the warning",
            "You may be installing a broken or vulnerable version", 0.75,
            sources=["https://pip.pypa.io/en/stable/topics/yanked/"])],
        [wa("Install a different version: pip install 'pkg!=yanked_version'", 0.95,
            sources=["https://pip.pypa.io/en/stable/topics/yanked/"]),
         wa("Check PyPI for the reason it was yanked and the recommended replacement version", 0.90,
            sources=["https://pypi.org/"]),
         wa("Update to the latest non-yanked version: pip install --upgrade pkg", 0.88,
            sources=["https://pip.pypa.io/en/stable/cli/pip_install/"])],
    ))

    return c


def main():
    canons = get_all_canons()
    written = 0
    skipped = 0
    for c in canons:
        domain = c["error"]["domain"]
        slug = c["id"].split("/")[1]
        env = c["id"].split("/")[2]
        out_dir = DATA_DIR / domain
        out_dir.mkdir(parents=True, exist_ok=True)
        out_file = out_dir / f"{slug}_{env}.json"
        if out_file.exists():
            skipped += 1
            continue
        with open(out_file, "w", encoding="utf-8") as f:
            json.dump(c, f, indent=2, ensure_ascii=False)
            f.write("\n")
        written += 1
    print(f"Wave 8: wrote {written} new canons, skipped {skipped} existing")


if __name__ == "__main__":
    main()
