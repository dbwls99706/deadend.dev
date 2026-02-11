"""Bulk generate wave 10: +40 canons.

Usage: python -m generator.bulk_generate_v10
"""

import json
from generator.bulk_generate import (
    canon, de, wa, DATA_DIR,
)


def get_all_canons():
    c = []

    # ── PYTHON ──────────────────────────────────────────

    c.append(canon(
        "python", "eofeerror-unexpected", "py311-linux",
        "EOFError: EOF when reading a line",
        r"EOFError.*EOF when reading",
        "io_error", "python", ">=3.11,<3.13", "linux",
        "true", 0.90, 0.90,
        "input() called but stdin is closed/empty. Common in Docker, piped input, or automated scripts.",
        [de("Add a default value to input()",
            "input() doesn't support defaults — need try/except", 0.75,
            sources=["https://docs.python.org/3/library/functions.html#input"])],
        [wa("Wrap in try/except EOFError for graceful handling", 0.92,
            "try:\n    line = input()\nexcept EOFError:\n    line = ''",
            sources=["https://docs.python.org/3/library/functions.html#input"]),
         wa("Use sys.stdin with check: for line in sys.stdin:", 0.88,
            sources=["https://docs.python.org/3/library/sys.html#sys.stdin"])],
        python=">=3.11,<3.13",
    ))

    c.append(canon(
        "python", "runtimeerror-coroutine-never-awaited", "py311-linux",
        "RuntimeWarning: coroutine 'func' was never awaited",
        r"RuntimeWarning: coroutine .+ was never awaited",
        "async_error", "python", ">=3.11,<3.13", "linux",
        "true", 0.95, 0.95,
        "Called async function without await. Returns a coroutine object, doesn't execute.",
        [de("Wrap in asyncio.ensure_future()",
            "Works but less readable — just use await", 0.55,
            sources=["https://docs.python.org/3/library/asyncio-task.html"])],
        [wa("Add await keyword: result = await async_function()", 0.98,
            sources=["https://docs.python.org/3/library/asyncio-task.html#coroutines"]),
         wa("If calling from sync code, use asyncio.run(async_function())", 0.90,
            sources=["https://docs.python.org/3/library/asyncio-runner.html#asyncio.run"])],
        python=">=3.11,<3.13",
    ))

    c.append(canon(
        "python", "sqlalchemy-detachedinstanceerror", "py311-linux",
        "sqlalchemy.orm.exc.DetachedInstanceError: Instance is not bound to a Session",
        r"DetachedInstanceError|Instance.*not bound.*Session|lazy load.*detached",
        "orm_error", "python", ">=3.11,<3.13", "linux",
        "true", 0.88, 0.90,
        "Accessing a lazy-loaded relationship after the session is closed.",
        [de("Use expire_on_commit=False globally",
            "May serve stale data across requests", 0.60,
            sources=["https://docs.sqlalchemy.org/en/20/orm/session_api.html"])],
        [wa("Eagerly load relationships: joinedload/subqueryload in query", 0.92,
            "from sqlalchemy.orm import joinedload\nquery.options(joinedload(Model.relation))",
            sources=["https://docs.sqlalchemy.org/en/20/orm/queryguide/relationships.html"]),
         wa("Access attributes within the session context (before closing)", 0.88,
            sources=["https://docs.sqlalchemy.org/en/20/orm/session_basics.html"])],
        python=">=3.11,<3.13",
    ))

    c.append(canon(
        "python", "celery-task-not-registered", "py311-linux",
        "celery.exceptions.NotRegistered: 'app.tasks.my_task'",
        r"NotRegistered.*task|Received unregistered task|KeyError.*celery",
        "task_error", "python", ">=3.11,<3.13", "linux",
        "true", 0.88, 0.90,
        "Celery worker doesn't know about the task. Worker code differs from caller code.",
        [de("Use send_task() to bypass registration",
            "send_task skips validation — typos won't be caught", 0.60,
            sources=["https://docs.celeryq.dev/en/stable/userguide/calling.html"])],
        [wa("Restart the Celery worker after code changes — it caches task definitions", 0.95,
            sources=["https://docs.celeryq.dev/en/stable/userguide/workers.html"]),
         wa("Ensure autodiscover_tasks finds the task: check include/imports config", 0.90,
            "app.autodiscover_tasks(['myapp.tasks'])",
            sources=["https://docs.celeryq.dev/en/stable/userguide/tasks.html#automatic-naming-and-relative-imports"]),
         wa("Verify worker and caller import the same task module path", 0.85,
            sources=["https://docs.celeryq.dev/en/stable/userguide/tasks.html"])],
        python=">=3.11,<3.13",
    ))

    # ── NODE ──────────────────────────────────────────

    c.append(canon(
        "node", "err-invalid-url", "node20-linux",
        "TypeError [ERR_INVALID_URL]: Invalid URL",
        r"ERR_INVALID_URL|Invalid URL|Failed to construct.*URL",
        "parse_error", "node", ">=20,<23", "linux",
        "true", 0.95, 0.95,
        "URL constructor received invalid input. Missing protocol, malformed path, or undefined.",
        [de("Wrap every URL in try/catch",
            "Hides the real issue — the URL source is producing bad data", 0.65,
            sources=["https://nodejs.org/api/url.html#new-urlinput-base"])],
        [wa("Validate URL before constructing: check for protocol and format", 0.92,
            "try { new URL(input) } catch { console.error('Invalid:', input) }",
            sources=["https://nodejs.org/api/url.html#new-urlinput-base"]),
         wa("Use the base parameter for relative URLs: new URL(path, 'http://localhost')", 0.88,
            sources=["https://nodejs.org/api/url.html#new-urlinput-base"]),
         wa("Check for undefined/null input before constructing", 0.90,
            sources=["https://nodejs.org/api/url.html"])],
    ))

    c.append(canon(
        "node", "ts-node-syntax-error", "node20-linux",
        "SyntaxError: Cannot use import statement outside a module (ts-node)",
        r"ts-node.*import.*outside|Cannot use import.*ts-node|TSError",
        "config_error", "node", ">=20,<23", "linux",
        "true", 0.90, 0.90,
        "ts-node can't handle ESM syntax. Needs tsconfig configuration for ESM.",
        [de("Convert all imports to require()",
            "Defeats the purpose of TypeScript ES modules", 0.70,
            sources=["https://typestrong.org/ts-node/docs/"])],
        [wa("Use ts-node with --esm flag: ts-node --esm script.ts", 0.92,
            sources=["https://typestrong.org/ts-node/docs/imports#native-ecmascript-modules"]),
         wa("Set 'module': 'nodenext' and 'moduleResolution': 'nodenext' in tsconfig.json", 0.88,
            sources=["https://typestrong.org/ts-node/docs/imports"]),
         wa("Consider tsx as a drop-in replacement: npx tsx script.ts (faster, less config)", 0.90,
            sources=["https://www.npmjs.com/package/tsx"])],
    ))

    c.append(canon(
        "node", "prisma-client-not-generated", "node20-linux",
        "Error: @prisma/client did not initialize yet. Run 'prisma generate'",
        r"prisma.*client.*not.*generat|prisma.*initialize|Run.*prisma generate",
        "orm_error", "node", ">=20,<23", "linux",
        "true", 0.95, 0.95,
        "Prisma client needs generation after schema changes.",
        [de("Import from .prisma/client directly",
            "Internal path that changes between versions", 0.80,
            sources=["https://www.prisma.io/docs/orm/prisma-client/setup-and-configuration/generating-prisma-client"])],
        [wa("Run npx prisma generate after any schema.prisma change", 0.98,
            sources=["https://www.prisma.io/docs/orm/prisma-client/setup-and-configuration/generating-prisma-client"]),
         wa("Add prisma generate to your build/postinstall script", 0.90,
            '{ "scripts": { "postinstall": "prisma generate" } }',
            sources=["https://www.prisma.io/docs/orm/prisma-client/setup-and-configuration/generating-prisma-client"])],
    ))

    c.append(canon(
        "node", "next-dev-port-conflict", "node20-linux",
        "Error: listen EADDRINUSE: address already in use :::3000 (next dev)",
        r"EADDRINUSE.*3000.*next|next.*dev.*port.*in use",
        "server_error", "node", ">=20,<23", "linux",
        "true", 0.95, 0.95,
        "Next.js dev server port already in use. Another instance or process on port 3000.",
        [de("Change to a random port each time",
            "Inconsistent URLs during development", 0.55,
            sources=["https://nextjs.org/docs/api-reference/cli"])],
        [wa("Kill existing process: lsof -i :3000 and kill the PID", 0.95,
            "lsof -ti :3000 | xargs kill -9",
            sources=["https://nextjs.org/docs/api-reference/cli"]),
         wa("Use a different port: next dev -p 3001", 0.90,
            sources=["https://nextjs.org/docs/api-reference/cli#development"])],
    ))

    # ── REACT ──────────────────────────────────────────

    c.append(canon(
        "react", "invalid-dom-property", "react18-linux",
        "Warning: Invalid DOM property 'class'. Did you mean 'className'?",
        r"Invalid DOM property|Did you mean 'className'|did you mean.*class",
        "jsx_error", "react", ">=18,<20", "linux",
        "true", 0.98, 0.95,
        "HTML attributes in JSX use camelCase. class → className, for → htmlFor, etc.",
        [de("Use dangerouslySetInnerHTML to bypass",
            "Overkill and XSS risk for a simple attribute rename", 0.90,
            sources=["https://react.dev/reference/react-dom/components/common#common-props"])],
        [wa("Use React attribute names: className, htmlFor, tabIndex, readOnly, etc.", 0.98,
            sources=["https://react.dev/reference/react-dom/components/common#common-props"]),
         wa("Most HTML attributes are camelCase in JSX except data-* and aria-*", 0.92,
            sources=["https://react.dev/reference/react-dom/components/common"])],
    ))

    c.append(canon(
        "react", "forward-ref-deprecation", "react18-linux",
        "Warning: forwardRef render functions accept exactly two parameters: props and ref",
        r"forwardRef.*two parameters|forwardRef.*props and ref|forwardRef.*deprecated",
        "deprecation_warning", "react", ">=18,<20", "linux",
        "true", 0.90, 0.92,
        "forwardRef component has wrong signature or is being deprecated (React 19+ removes it).",
        [de("Remove forwardRef and pass ref as a regular prop",
            "In React <19, ref is special and won't be forwarded as a prop", 0.60,
            sources=["https://react.dev/reference/react/forwardRef"])],
        [wa("Ensure function takes exactly (props, ref) parameters", 0.92,
            "const Input = forwardRef((props, ref) => <input ref={ref} {...props} />);",
            sources=["https://react.dev/reference/react/forwardRef"]),
         wa("In React 19+, ref is a regular prop — no need for forwardRef", 0.85,
            "function Input({ ref, ...props }) { return <input ref={ref} {...props} />; }",
            sources=["https://react.dev/blog/2024/12/05/react-19"])],
    ))

    # ── DOCKER ──────────────────────────────────────────

    c.append(canon(
        "docker", "npm-install-eacces-docker", "docker27-linux",
        "npm error EACCES: permission denied in Docker container during npm install",
        r"EACCES.*npm.*Docker|npm.*permission denied.*Docker|npm.*EACCES.*container",
        "permission_error", "docker", ">=27,<28", "linux",
        "true", 0.90, 0.90,
        "npm install fails inside Docker due to root user + npm cache permissions.",
        [de("Run npm with --unsafe-perm",
            "Security risk and deprecated flag", 0.70,
            sources=["https://docs.npmjs.com/cli/v10/using-npm/config#unsafe-perm"])],
        [wa("Use a non-root user in Dockerfile: USER node", 0.92,
            "FROM node:20-alpine\nRUN mkdir -p /app && chown node:node /app\nUSER node\nWORKDIR /app",
            sources=["https://docs.docker.com/reference/dockerfile/#user"]),
         wa("Set npm cache directory writable: RUN npm config set cache /tmp/.npm", 0.88,
            sources=["https://docs.npmjs.com/cli/v10/using-npm/config#cache"])],
    ))

    c.append(canon(
        "docker", "pip-install-root-warning", "docker27-linux",
        "WARNING: Running pip as the 'root' user can result in broken permissions",
        r"Running pip as.*root|broken permissions.*pip|WARNING.*pip.*root",
        "permission_warning", "docker", ">=27,<28", "linux",
        "true", 0.90, 0.90,
        "pip warns about installing as root inside Docker. Usually harmless in containers.",
        [de("Create a virtualenv inside Docker",
            "Unnecessary complexity — container IS the isolation", 0.60,
            sources=["https://pip.pypa.io/en/stable/user_guide/"])],
        [wa("Suppress with --root-user-action=ignore (harmless in containers)", 0.95,
            "RUN pip install --root-user-action=ignore -r requirements.txt",
            sources=["https://pip.pypa.io/en/stable/user_guide/"]),
         wa("Or use a non-root user for security best practice", 0.85,
            "RUN useradd -m app\nUSER app",
            sources=["https://docs.docker.com/reference/dockerfile/#user"])],
    ))

    # ── GIT ──────────────────────────────────────────

    c.append(canon(
        "git", "pre-commit-hook-failed", "git2-linux",
        "pre-commit hook failed (add --no-verify to bypass)",
        r"pre-commit.*hook.*failed|hook.*failed.*commit|pre-commit.*exit.*non-zero",
        "hook_error", "git", ">=2.30,<3.0", "linux",
        "true", 0.90, 0.92,
        "Pre-commit hook (linting, formatting, tests) found issues and blocked the commit.",
        [de("Always use --no-verify to bypass",
            "Skips all quality checks — defeats the purpose of hooks", 0.75,
            sources=["https://git-scm.com/docs/git-commit#Documentation/git-commit.txt---no-verify"])],
        [wa("Fix the issues the hook reported — run the linter/formatter manually", 0.95,
            sources=["https://git-scm.com/docs/githooks#_pre_commit"]),
         wa("Run the hook manually to see detailed output: .git/hooks/pre-commit", 0.88,
            sources=["https://git-scm.com/docs/githooks"]),
         wa("If false positive, use --no-verify for this one commit only", 0.80,
            sources=["https://git-scm.com/docs/git-commit#Documentation/git-commit.txt---no-verify"])],
    ))

    c.append(canon(
        "git", "shallow-update-not-allowed", "git2-linux",
        "fatal: refusing to fetch into branch because shallow update is not allowed",
        r"shallow.*update.*not allowed|shallow.*fetch|shallow clone.*error",
        "clone_error", "git", ">=2.30,<3.0", "linux",
        "true", 0.88, 0.90,
        "Git operation on a shallow clone that requires full history.",
        [de("Delete repo and full clone every time",
            "Wastes bandwidth for large repos", 0.55,
            sources=["https://git-scm.com/docs/git-clone#Documentation/git-clone.txt---depthltdepthgt"])],
        [wa("Unshallow the clone: git fetch --unshallow", 0.95,
            sources=["https://git-scm.com/docs/git-fetch#Documentation/git-fetch.txt---unshallow"]),
         wa("Fetch specific depth: git fetch --depth=100 to get more history", 0.85,
            sources=["https://git-scm.com/docs/git-fetch#Documentation/git-fetch.txt---depthltdepthgt"])],
    ))

    # ── KUBERNETES ──────────────────────────────────────────

    c.append(canon(
        "kubernetes", "ingress-502-bad-gateway", "k8s1-linux",
        "502 Bad Gateway (Ingress/Nginx)",
        r"502 Bad Gateway|upstream.*connect.*error|no live upstreams",
        "networking_error", "kubernetes", ">=1.28,<2.0", "linux",
        "partial", 0.80, 0.85,
        "Ingress can't reach backend pods. Service misconfigured, pods not ready, or port mismatch.",
        [de("Increase proxy timeouts to very large values",
            "If pods are down, timeouts don't help", 0.65,
            sources=["https://kubernetes.github.io/ingress-nginx/user-guide/nginx-configuration/annotations/"])],
        [wa("Verify service selector matches pod labels: kubectl get ep <service>", 0.92,
            sources=["https://kubernetes.io/docs/concepts/services-networking/service/#services-without-selectors"]),
         wa("Check pod readiness — unready pods are removed from endpoints", 0.90,
            "kubectl get pods -o wide\nkubectl describe endpoints <service-name>",
            sources=["https://kubernetes.io/docs/concepts/services-networking/service/"]),
         wa("Verify service port matches container port (not just pod port)", 0.88,
            sources=["https://kubernetes.io/docs/concepts/services-networking/service/#defining-a-service"])],
    ))

    c.append(canon(
        "kubernetes", "secret-not-found", "k8s1-linux",
        "Error: secret 'X' not found",
        r"secret.*not found|Secret.*does not exist|MountVolume.*secret.*not found",
        "config_error", "kubernetes", ">=1.28,<2.0", "linux",
        "true", 0.92, 0.92,
        "Pod references a secret that doesn't exist in the namespace.",
        [de("Create an empty secret as placeholder",
            "May cause the app to fail with missing config values", 0.60,
            sources=["https://kubernetes.io/docs/concepts/configuration/secret/"])],
        [wa("Create the secret: kubectl create secret generic <name> --from-literal=key=value", 0.95,
            sources=["https://kubernetes.io/docs/concepts/configuration/secret/#creating-a-secret"]),
         wa("Check namespace — secrets are namespace-scoped", 0.90,
            "kubectl get secrets -n <namespace>",
            sources=["https://kubernetes.io/docs/concepts/configuration/secret/"]),
         wa("Use optional: true in volume mount to allow pod to start without the secret", 0.82,
            sources=["https://kubernetes.io/docs/concepts/configuration/secret/#using-secrets-as-files-from-a-pod"])],
    ))

    # ── RUST ──────────────────────────────────────────

    c.append(canon(
        "rust", "e0308-match-arms-different-types", "rust1-linux",
        "error[E0308]: `match` arms have incompatible types",
        r"E0308.*match.*arms.*incompatible",
        "type_error", "rust", ">=1.70,<2.0", "linux",
        "true", 0.92, 0.92,
        "Match expression arms return different types. All arms must return the same type.",
        [de("Use Box<dyn Any> to erase types",
            "Loses all type safety and requires downcasting", 0.80,
            sources=["https://doc.rust-lang.org/error_codes/E0308.html"])],
        [wa("Return the same type from all arms, or use an enum to unify them", 0.95,
            "enum Shape { Circle(f64), Square(f64) }\nmatch input {\n    \"circle\" => Shape::Circle(r),\n    _ => Shape::Square(s),\n}",
            sources=["https://doc.rust-lang.org/book/ch06-01-defining-an-enum.html"]),
         wa("Use impl Trait or Box<dyn Trait> if arms return different types implementing same trait", 0.85,
            sources=["https://doc.rust-lang.org/book/ch17-02-trait-objects.html"])],
    ))

    c.append(canon(
        "rust", "cargo-feature-not-found", "rust1-linux",
        "error: Package does not have feature 'X'",
        r"does not have.*feature|feature.*not found|unknown feature",
        "build_error", "rust", ">=1.70,<2.0", "linux",
        "true", 0.92, 0.92,
        "Feature flag doesn't exist in the dependency. Typo or version mismatch.",
        [de("Create the feature in your own Cargo.toml",
            "Features must be defined in the dependency's Cargo.toml", 0.85,
            sources=["https://doc.rust-lang.org/cargo/reference/features.html"])],
        [wa("Check the dependency docs for available features: cargo doc --open", 0.92,
            sources=["https://doc.rust-lang.org/cargo/reference/features.html"]),
         wa("Check if the feature was renamed or removed in a version update", 0.88,
            sources=["https://doc.rust-lang.org/cargo/reference/features.html"]),
         wa("Verify the dependency version supports the feature", 0.85,
            sources=["https://doc.rust-lang.org/cargo/reference/specifying-dependencies.html"])],
    ))

    # ── GO ──────────────────────────────────────────

    c.append(canon(
        "go", "method-has-pointer-receiver", "go1-linux",
        "cannot call pointer method on value / cannot take the address of",
        r"cannot call pointer method|cannot take the address of|pointer receiver",
        "type_error", "go", ">=1.21,<2.0", "linux",
        "true", 0.92, 0.92,
        "Calling a pointer receiver method on a non-addressable value (like a map value or function return).",
        [de("Use unsafe.Pointer to get address",
            "Unsafe and undefined behavior for non-addressable values", 0.90,
            sources=["https://go.dev/ref/spec#Method_values"])],
        [wa("Store the value in a variable first to make it addressable", 0.95,
            "val := myMap[key]\nval.PointerMethod()  // val is addressable",
            sources=["https://go.dev/ref/spec#Calls"]),
         wa("Change the method to a value receiver if it doesn't modify the struct", 0.88,
            "func (s MyStruct) Method() { ... }  // value receiver, works on non-addressable",
            sources=["https://go.dev/ref/spec#Method_sets"])],
    ))

    # ── AWS ──────────────────────────────────────────

    c.append(canon(
        "aws", "dynamodb-provisioned-throughput-exceeded", "awscli2-linux",
        "An error occurred (ProvisionedThroughputExceededException)",
        r"ProvisionedThroughputExceededException|throughput.*exceeded",
        "throttling_error", "aws", ">=2.0,<3.0", "linux",
        "partial", 0.82, 0.85,
        "DynamoDB read/write capacity exceeded. Too many requests per second.",
        [de("Increase capacity to maximum immediately",
            "Expensive and doesn't address the access pattern issue", 0.60,
            sources=["https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/ProvisionedThroughput.html"])],
        [wa("Switch to on-demand capacity mode for unpredictable workloads", 0.90,
            sources=["https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/HowItWorks.ReadWriteCapacityMode.html"]),
         wa("Implement exponential backoff for throttled requests", 0.88,
            sources=["https://docs.aws.amazon.com/general/latest/gr/api-retries.html"]),
         wa("Review partition key design — hot partitions cause throttling even with capacity", 0.85,
            sources=["https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/bp-partition-key-design.html"])],
    ))

    # ── TERRAFORM ──────────────────────────────────────────

    c.append(canon(
        "terraform", "output-not-found", "tf1-linux",
        "Error: Output refers to resource that no longer exists",
        r"Output.*no longer exists|output.*resource.*not found|output value.*cannot be determined",
        "config_error", "terraform", ">=1.5,<2.0", "linux",
        "true", 0.92, 0.92,
        "Output block references a resource that was removed from configuration.",
        [de("Comment out the output instead of removing",
            "Commented code is dead code — remove it properly", 0.65,
            sources=["https://developer.hashicorp.com/terraform/language/values/outputs"])],
        [wa("Remove or update the output block to reference existing resources", 0.95,
            sources=["https://developer.hashicorp.com/terraform/language/values/outputs"]),
         wa("If the output is consumed by other modules, coordinate the removal", 0.85,
            sources=["https://developer.hashicorp.com/terraform/language/values/outputs"])],
    ))

    # ── NEXT.JS ──────────────────────────────────────────

    c.append(canon(
        "nextjs", "api-route-body-not-parsed", "nextjs14-linux",
        "API Route body not parsed / req.body is undefined",
        r"body.*undefined|body.*not parsed|req\.body.*undefined",
        "api_error", "nextjs", ">=14,<16", "linux",
        "true", 0.90, 0.90,
        "Request body not parsed in API route. Content-Type header missing or wrong handler setup.",
        [de("Install body-parser middleware",
            "Next.js has built-in body parsing — external middleware is unnecessary", 0.75,
            sources=["https://nextjs.org/docs/app/building-your-application/routing/route-handlers"])],
        [wa("In App Router, use request.json() to parse body: const body = await request.json()", 0.95,
            sources=["https://nextjs.org/docs/app/building-your-application/routing/route-handlers"]),
         wa("Ensure client sends Content-Type: application/json header", 0.88,
            "fetch('/api/route', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(data) })",
            sources=["https://nextjs.org/docs/app/building-your-application/routing/route-handlers"])],
    ))

    # ── CUDA ──────────────────────────────────────────

    c.append(canon(
        "cuda", "cuda-initialization-error", "cuda12-a100",
        "RuntimeError: CUDA error: initialization error",
        r"CUDA error: initialization|CUDA.*initialization error|cudaErrorInitializationError",
        "init_error", "cuda", ">=12.0,<13.0", "linux",
        "partial", 0.78, 0.85,
        "CUDA driver failed to initialize. Driver crash, GPU reset, or process forking issue.",
        [de("Reinstall CUDA toolkit",
            "Usually a driver issue, not toolkit issue", 0.70,
            sources=["https://docs.nvidia.com/cuda/cuda-runtime-api/group__CUDART__ERROR.html"])],
        [wa("Restart the GPU: sudo nvidia-smi --gpu-reset", 0.85,
            sources=["https://docs.nvidia.com/cuda/cuda-runtime-api/group__CUDART__ERROR.html"]),
         wa("If using multiprocessing, set start method to 'spawn' not 'fork'", 0.90,
            "import multiprocessing\nmultiprocessing.set_start_method('spawn')",
            sources=["https://pytorch.org/docs/stable/notes/multiprocessing.html"]),
         wa("Check nvidia-smi for GPU health and driver status", 0.88,
            sources=["https://docs.nvidia.com/cuda/cuda-runtime-api/group__CUDART__ERROR.html"])],
        gpu="A100", vram=40,
    ))

    # ── PIP ──────────────────────────────────────────

    c.append(canon(
        "pip", "backtracking-taking-long", "pip24-linux",
        "INFO: pip is looking at multiple versions of X to determine which version is compatible (backtracking)",
        r"backtracking|pip is looking at multiple versions|Collecting.*very slow",
        "resolution_warning", "pip", ">=24,<25", "linux",
        "partial", 0.75, 0.80,
        "pip dependency resolver backtracking through many versions. Can take minutes to hours.",
        [de("Cancel and use --no-deps",
            "Skips dependency resolution — may install incompatible versions", 0.70,
            sources=["https://pip.pypa.io/en/stable/topics/dependency-resolution/"])],
        [wa("Pin more versions in requirements.txt to reduce the search space", 0.88,
            sources=["https://pip.pypa.io/en/stable/topics/dependency-resolution/"]),
         wa("Use pip-compile (pip-tools) to pre-resolve and lock versions", 0.90,
            "pip-compile requirements.in",
            sources=["https://pip-tools.readthedocs.io/en/stable/"]),
         wa("Upgrade pip — newer versions have faster resolver: pip install --upgrade pip", 0.82,
            sources=["https://pip.pypa.io/en/stable/installation/"])],
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
    print(f"Wave 10: wrote {written} new canons, skipped {skipped} existing")


if __name__ == "__main__":
    main()
