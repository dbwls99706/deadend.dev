"""Wave 11: 40 new canons (363 → ~403)."""

import json
from generator.bulk_generate import (
    canon, de, wa, DATA_DIR,
)


def get_all_canons():
    c = []

    # ── Python ──────────────────────────────────────────────────────────
    c.append(canon(
        "python", "unboundlocalerror", "py311-linux",
        "UnboundLocalError: cannot access local variable 'x' referred to before assignment",
        r"UnboundLocalError: cannot access local variable '(\w+)'",
        "scoping", "cpython", ">=3.11", "linux",
        "true", 0.98, 0.97,
        "Variable referenced before assignment in local scope, often caused by reassigning a global/outer variable without nonlocal/global declaration.",
        [de("Adding a try/except around the assignment", "Masks the scoping issue; variable is still unbound on the failing path", 0.85, sources=["https://docs.python.org/3/faq/programming.html#why-am-i-getting-an-unboundlocalerror-when-the-variable-has-a-value"]),
         de("Initializing the variable to None at function top", "Hides the real bug if the None path is never intended", 0.40)],
        [wa("Add 'nonlocal' or 'global' declaration if intending to modify outer scope variable", 0.95, "Use nonlocal x or global x at the top of the inner function", sources=["https://docs.python.org/3/reference/simple_stmts.html#the-nonlocal-statement"]),
         wa("Restructure to avoid shadowing — rename the local variable", 0.92, "Use a different name for the local variable so it doesn't shadow the outer one")],
    ))

    c.append(canon(
        "python", "typeerror-unhashable-list", "py310-linux",
        "TypeError: unhashable type: 'list'",
        r"TypeError: unhashable type: 'list'",
        "typing", "cpython", ">=3.8", "linux",
        "true", 0.97, 0.98,
        "Attempting to use a list as a dict key or set element.",
        [de("Wrapping the list in str() to make it hashable", "Loses structure; str representation can collide for different lists", 0.70),
         de("Using json.dumps() as hash key", "Fragile — key ordering matters, wastes memory", 0.55)],
        [wa("Convert list to tuple before using as dict key or set element", 0.97, "Use tuple(my_list) as the key instead", sources=["https://docs.python.org/3/glossary.html#term-hashable"]),
         wa("Use frozenset() if order doesn't matter", 0.90, "frozenset(my_list) is hashable and order-independent")],
    ))

    c.append(canon(
        "python", "overflowerror-int-too-large", "py311-linux",
        "OverflowError: Python int too large to convert to C long",
        r"OverflowError: (Python )?int too large to convert to C (long|ssize_t)",
        "numeric", "cpython", ">=3.8", "linux",
        "true", 0.93, 0.95,
        "Python arbitrary-precision int exceeds C long range when passed to C extension or numpy.",
        [de("Casting to float first", "Loses precision for very large integers", 0.60),
         de("Upgrading to 64-bit Python", "Does not help — C long is already 64-bit on 64-bit Linux; the int is simply too large", 0.75)],
        [wa("Use numpy int64 or Python's math module for the calculation", 0.88, "np.int64(value) if within 64-bit range, or use pure Python arithmetic"),
         wa("Chunk the large integer operation to stay within C long bounds", 0.85, "Process in batches or use libraries that handle arbitrary precision natively")],
    ))

    c.append(canon(
        "python", "oserror-too-many-open-files", "py311-linux",
        "OSError: [Errno 24] Too many open files",
        r"OSError: \[Errno 24\] Too many open files",
        "os", "cpython", ">=3.8", "linux",
        "true", 0.94, 0.96,
        "Process has exceeded the OS file descriptor limit (ulimit -n).",
        [de("Increasing ulimit to 1000000", "Masks a file descriptor leak; system will eventually hit kernel limits", 0.65),
         de("Restarting the process periodically", "Workaround not a fix; the leak continues", 0.80)],
        [wa("Fix the file descriptor leak — ensure all files/sockets are closed with context managers", 0.95, "Use 'with open(...)' pattern; audit for unclosed connections", sources=["https://docs.python.org/3/library/functions.html#open"]),
         wa("Increase ulimit -n as an interim measure while fixing the leak", 0.85, "ulimit -n 65536 or edit /etc/security/limits.conf")],
    ))

    c.append(canon(
        "python", "importerror-circular", "py311-linux",
        "ImportError: cannot import name 'X' from partially initialized module 'Y' (most likely due to a circular import)",
        r"ImportError: cannot import name '(\w+)' from partially initialized module",
        "import", "cpython", ">=3.10", "linux",
        "true", 0.95, 0.96,
        "Circular import detected — module A imports from B which imports from A before A is fully loaded.",
        [de("Reordering imports alphabetically", "Does not break the cycle; both modules still depend on each other", 0.85),
         de("Using importlib.reload()", "Does not break circular dependency; may cause duplicate state", 0.70)],
        [wa("Move the import inside the function that needs it (lazy import)", 0.93, "def func(): from module_b import X — defers import until runtime", sources=["https://docs.python.org/3/faq/programming.html#what-are-the-best-practices-for-using-import-in-a-package"]),
         wa("Restructure modules to extract shared code into a third module", 0.95, "Create a common.py with shared definitions imported by both A and B")],
    ))

    # ── Node ────────────────────────────────────────────────────────────
    c.append(canon(
        "node", "err-dlopen-failed", "node20-linux",
        "Error: dlopen failed: cannot open shared object file",
        r"(dlopen failed|cannot open shared object file|ELIBBAD)",
        "native-modules", "node", ">=16", "linux",
        "true", 0.88, 0.90,
        "Native Node.js addon cannot load its shared library, typically after a Node version upgrade or OS update.",
        [de("Manually copying .so files into node_modules", "Version mismatch with Node ABI; will segfault or fail at runtime", 0.80),
         de("Setting LD_LIBRARY_PATH globally", "May conflict with system libraries; not portable", 0.55)],
        [wa("Run npm rebuild or npm rebuild <package> to recompile native addons", 0.92, "npm rebuild rebuilds all native modules against current Node version", sources=["https://docs.npmjs.com/cli/v10/commands/npm-rebuild"]),
         wa("Delete node_modules and reinstall: rm -rf node_modules && npm install", 0.90, "Clean reinstall forces fresh native compilation")],
    ))

    c.append(canon(
        "node", "err-worker-out-of-memory", "node20-linux",
        "FATAL ERROR: Reached heap limit Allocation failed - JavaScript heap out of memory",
        r"(FATAL ERROR: Reached heap limit|JavaScript heap out of memory)",
        "memory", "node", ">=14", "linux",
        "true", 0.90, 0.92,
        "Node.js process exceeded V8 heap memory limit.",
        [de("Setting --max-old-space-size=16384 without investigating the leak", "Delays the crash but the leak still grows unbounded", 0.70),
         de("Splitting the process into workers without fixing the memory issue", "Each worker will also eventually OOM", 0.60)],
        [wa("Profile with --inspect and Chrome DevTools to find the memory leak", 0.93, "node --inspect app.js then open chrome://inspect to take heap snapshots", sources=["https://nodejs.org/en/docs/guides/debugging-getting-started"]),
         wa("Increase heap limit as interim: NODE_OPTIONS=--max-old-space-size=8192", 0.85, "export NODE_OPTIONS='--max-old-space-size=8192' before running")],
    ))

    c.append(canon(
        "node", "err-http-headers-sent", "node20-linux",
        "Error [ERR_HTTP_HEADERS_SENT]: Cannot set headers after they are sent to the client",
        r"ERR_HTTP_HEADERS_SENT.*Cannot set headers after they are sent",
        "http", "node", ">=12", "linux",
        "true", 0.97, 0.98,
        "Attempting to send a response after the response has already been sent — usually a missing return after res.send()/res.json().",
        [de("Wrapping in try/catch", "The error is not an exception in the handler; it fires on the second write", 0.80),
         de("Using res.headersSent check everywhere", "Band-aid; masks control flow bugs", 0.60)],
        [wa("Add return after each res.send()/res.json()/res.end() in conditional branches", 0.97, "return res.json({ok: true}) ensures no further response is attempted", sources=["https://expressjs.com/en/api.html#res.json"]),
         wa("Refactor to single response point at the end of the handler", 0.90, "Collect result in a variable and send once at the end")],
    ))

    c.append(canon(
        "node", "err-unhandled-rejection", "node20-linux",
        "UnhandledPromiseRejectionWarning: This error originated either by throwing inside of an async function without a catch block",
        r"(UnhandledPromiseRejection|unhandled promise rejection)",
        "async", "node", ">=14", "linux",
        "true", 0.95, 0.96,
        "A Promise rejected and no .catch() or try/catch in async function was present to handle it.",
        [de("Adding process.on('unhandledRejection', () => {}) to silence it", "Hides bugs; since Node 15 unhandled rejections crash the process by default", 0.85),
         de("Converting all async functions to callbacks", "Massive refactor that introduces callback hell; not a real fix", 0.90)],
        [wa("Add try/catch blocks around await calls in async functions", 0.95, "try { await fn() } catch(e) { handleError(e) }", sources=["https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Statements/try...catch"]),
         wa("Add .catch() to all Promise chains", 0.93, "promise.then(result => ...).catch(err => ...)")],
    ))

    c.append(canon(
        "node", "enospc-system-limit-watchers", "node20-linux",
        "Error: ENOSPC: System limit for number of file watchers reached",
        r"ENOSPC.*file watchers reached",
        "filesystem", "node", ">=14", "linux",
        "true", 0.96, 0.97,
        "Linux inotify watcher limit exhausted, common with large projects using webpack/vite/jest --watch.",
        [de("Disabling file watching entirely", "Breaks hot-reload and watch mode development workflow", 0.75),
         de("Restarting the dev server repeatedly", "Temporary; watchers accumulate again", 0.80)],
        [wa("Increase inotify watcher limit: echo fs.inotify.max_user_watches=524288 | sudo tee -a /etc/sysctl.conf && sudo sysctl -p", 0.97, "Permanently increases the limit to 524288", sources=["https://github.com/guard/listen/wiki/Increasing-the-amount-of-inotify-watchers"]),
         wa("Add large directories to watchOptions.ignored in webpack/vite config", 0.88, "Ignore node_modules and build output directories from file watching")],
    ))

    # ── Docker ──────────────────────────────────────────────────────────
    c.append(canon(
        "docker", "no-space-left-on-device", "docker24-linux",
        "Error: no space left on device",
        r"no space left on device",
        "storage", "docker", ">=20.10", "linux",
        "true", 0.96, 0.97,
        "Docker has consumed all available disk space with images, containers, volumes, and build cache.",
        [de("Deleting /var/lib/docker manually", "Corrupts Docker's internal database; may brick the daemon", 0.90, sources=["https://docs.docker.com/config/pruning/"]),
         de("Increasing disk size without pruning", "Docker will fill the new space too if images are not cleaned up", 0.55)],
        [wa("Run docker system prune -a --volumes to reclaim space", 0.96, "Removes all stopped containers, unused images, networks, and volumes", sources=["https://docs.docker.com/config/pruning/"]),
         wa("Set up regular cleanup with docker system prune in cron", 0.88, "Add 0 2 * * * docker system prune -af to crontab for nightly cleanup")],
    ))

    c.append(canon(
        "docker", "exec-format-error", "docker24-linux",
        "exec /entrypoint.sh: exec format error",
        r"exec format error",
        "architecture", "docker", ">=20.10", "linux",
        "true", 0.93, 0.95,
        "Binary architecture mismatch — running an amd64 image on arm64 or vice versa, or missing shebang in entrypoint script.",
        [de("Re-pulling the same image tag", "Same architecture will be pulled again", 0.85),
         de("Installing qemu-user without registering binfmt", "QEMU alone doesn't help; binfmt_misc must be registered", 0.65)],
        [wa("Build or pull the image for the correct platform: docker pull --platform linux/amd64", 0.93, "Explicitly specify the target platform", sources=["https://docs.docker.com/build/building/multi-platform/"]),
         wa("For script entrypoints, add #!/bin/sh shebang as the first line", 0.90, "Missing shebang causes exec format error on scripts")],
    ))

    c.append(canon(
        "docker", "oci-runtime-create-failed", "docker24-linux",
        "OCI runtime create failed: container_linux.go: starting container process caused: exec: not found",
        r"OCI runtime create failed.*exec.*not found",
        "runtime", "docker", ">=20.10", "linux",
        "true", 0.91, 0.93,
        "The specified CMD or ENTRYPOINT binary does not exist in the container.",
        [de("Reinstalling Docker", "The issue is with the image, not Docker itself", 0.90),
         de("Switching to a different Docker version", "The binary is missing from the image, not a Docker engine issue", 0.85)],
        [wa("Check that CMD/ENTRYPOINT binary exists in the image: docker run --entrypoint sh image -c 'which binary'", 0.93, "Verify the binary is installed and in PATH"),
         wa("Use full path in CMD/ENTRYPOINT or ensure PATH is set correctly in Dockerfile", 0.91, "CMD [\"/usr/local/bin/app\"] instead of CMD [\"app\"]")],
    ))

    # ── Git ──────────────────────────────────────────────────────────────
    c.append(canon(
        "git", "cannot-lock-ref", "git2-linux",
        "error: cannot lock ref 'refs/heads/branch': is at unexpected OID",
        r"cannot lock ref.*unexpected OID",
        "refs", "git", ">=2.30", "linux",
        "true", 0.94, 0.95,
        "Git ref has been updated by another process between fetch and update, or packed-refs is stale.",
        [de("Deleting .git/refs directory", "Destroys all local branch references; potentially unrecoverable", 0.90),
         de("Running git fsck --full", "Diagnoses but doesn't fix the lock issue", 0.50)],
        [wa("Run git remote prune origin to clean up stale references", 0.92, "Removes remote-tracking refs that no longer exist on the remote", sources=["https://git-scm.com/docs/git-remote"]),
         wa("Run git gc to repack references", 0.90, "Repacks loose refs into packed-refs and cleans up stale entries")],
    ))

    c.append(canon(
        "git", "bad-object-head", "git2-linux",
        "fatal: bad object HEAD",
        r"fatal: bad object HEAD",
        "corruption", "git", ">=2.20", "linux",
        "true", 0.82, 0.85,
        "Git HEAD reference points to a non-existent or corrupt object, usually after disk corruption or interrupted operations.",
        [de("Running git checkout main immediately", "HEAD is corrupt, checkout will fail too", 0.85),
         de("Deleting .git/HEAD", "Makes the repository completely unusable", 0.95)],
        [wa("Restore HEAD from reflog: git reflog and then git reset --hard <last_good_commit>", 0.85, "reflog keeps history of HEAD changes even after corruption", sources=["https://git-scm.com/docs/git-reflog"]),
         wa("Re-clone from remote if reflog is also corrupted", 0.95, "git clone <remote-url> fresh-copy — guaranteed clean state")],
    ))

    c.append(canon(
        "git", "refusing-to-merge-unrelated", "git2-linux",
        "fatal: refusing to merge unrelated histories",
        r"refusing to merge unrelated histories",
        "merge", "git", ">=2.9", "linux",
        "true", 0.96, 0.97,
        "Two branches have no common ancestor, typically when merging a repo that was initialized independently.",
        [de("Force-pushing one branch over the other", "Destroys one side's entire history", 0.90),
         de("Creating a new repo and copying files", "Loses all git history from both repos", 0.85)],
        [wa("Use --allow-unrelated-histories flag: git merge main --allow-unrelated-histories", 0.95, "Explicitly allows merging branches with no common ancestor", sources=["https://git-scm.com/docs/git-merge#Documentation/git-merge.txt---allow-unrelated-histories"]),
         wa("Use git rebase --onto to graft one history onto the other", 0.80, "More complex but produces a linear history")],
    ))

    # ── TypeScript ──────────────────────────────────────────────────────
    c.append(canon(
        "typescript", "ts2345-argument-not-assignable", "ts5-linux",
        "error TS2345: Argument of type 'X' is not assignable to parameter of type 'Y'",
        r"TS2345.*Argument of type.*is not assignable to parameter of type",
        "type-checking", "tsc", ">=4.5", "linux",
        "true", 0.97, 0.98,
        "TypeScript strict type checking rejects an argument because the types are incompatible.",
        [de("Using 'as any' to bypass the error", "Disables type safety; bugs will surface at runtime", 0.80, sources=["https://www.typescriptlang.org/docs/handbook/2/everyday-types.html#type-assertions"]),
         de("Disabling strict mode in tsconfig", "Removes type safety project-wide for one error", 0.85)],
        [wa("Fix the type to match — update the argument or widen the parameter type", 0.97, "Align the types properly or use a union type"),
         wa("Use type guard or type narrowing to satisfy the compiler", 0.93, "if (isTypeX(arg)) { fn(arg) } — narrows the type at the call site")],
    ))

    c.append(canon(
        "typescript", "ts2739-missing-properties", "ts5-linux",
        "error TS2739: Type '{}' is missing the following properties from type 'T': x, y, z",
        r"TS2739.*missing the following properties from type",
        "type-checking", "tsc", ">=4.5", "linux",
        "true", 0.97, 0.98,
        "Object literal does not satisfy the required properties of the target type.",
        [de("Making all properties optional with Partial<T>", "Changes the contract; callers may pass incomplete objects", 0.70),
         de("Using type assertion: {} as T", "Compiles but fails at runtime when properties are accessed", 0.85)],
        [wa("Add the missing required properties to the object literal", 0.97, "Provide values for all required fields of the type"),
         wa("Use Partial<T> only if the function truly accepts partial objects, and update consumers accordingly", 0.85, "Partial<T> makes all properties optional — only use when intentional")],
    ))

    c.append(canon(
        "typescript", "ts7053-no-index-signature", "ts5-linux",
        "error TS7053: Element implicitly has an 'any' type because expression of type 'string' can't be used to index type",
        r"TS7053.*Element implicitly has an 'any' type.*can't be used to index",
        "type-checking", "tsc", ">=4.5", "linux",
        "true", 0.96, 0.97,
        "Using a string variable to index an object that doesn't have an index signature.",
        [de("Adding // @ts-ignore above the line", "Hides the type error; any future type issues on this line are also silenced", 0.80),
         de("Setting noImplicitAny to false", "Disables a fundamental strictness check for the entire project", 0.90)],
        [wa("Add an index signature to the type: { [key: string]: ValueType }", 0.93, "Explicitly declares the object accepts string keys"),
         wa("Use a type assertion or keyof typeof to narrow the key type", 0.90, "obj[key as keyof typeof obj] — asserts the key is valid for this specific object")],
    ))

    # ── Rust ────────────────────────────────────────────────────────────
    c.append(canon(
        "rust", "e0502-borrow-conflict", "rust1-linux",
        "error[E0502]: cannot borrow `x` as mutable because it is also borrowed as immutable",
        r"E0502.*cannot borrow.*as mutable because it is also borrowed as immutable",
        "borrow-checker", "rustc", ">=1.60", "linux",
        "true", 0.93, 0.95,
        "Rust borrow checker prevents mutable borrow while an immutable borrow is still active.",
        [de("Using unsafe to bypass the borrow checker", "Introduces undefined behavior; defeats Rust's safety guarantees", 0.90),
         de("Cloning everything to avoid borrows", "Wastes memory and CPU; hides the architectural issue", 0.65)],
        [wa("Restructure code so immutable borrow ends before mutable borrow begins", 0.95, "Use scoping blocks { let r = &x; ... } then let m = &mut x;", sources=["https://doc.rust-lang.org/book/ch04-02-references-and-borrowing.html"]),
         wa("Use RefCell<T> for interior mutability when compile-time borrow checking is too restrictive", 0.85, "RefCell allows runtime-checked mutable borrows")],
    ))

    c.append(canon(
        "rust", "e0382-use-after-move", "rust1-linux",
        "error[E0382]: borrow of moved value: `x`",
        r"E0382.*borrow of moved value",
        "ownership", "rustc", ">=1.60", "linux",
        "true", 0.94, 0.96,
        "Value has been moved to another owner and cannot be used anymore.",
        [de("Using unsafe to read the moved memory", "Undefined behavior; memory may have been freed or reused", 0.95),
         de("Making everything Copy", "Not all types can be Copy (heap-allocated types like String, Vec)", 0.60)],
        [wa("Clone the value before moving if you need to use it again", 0.92, "let y = x.clone(); move_fn(x); use(y);", sources=["https://doc.rust-lang.org/book/ch04-01-what-is-ownership.html"]),
         wa("Use references instead of moves where possible", 0.95, "fn process(x: &MyType) instead of fn process(x: MyType)")],
    ))

    # ── Go ──────────────────────────────────────────────────────────────
    c.append(canon(
        "go", "nil-pointer-dereference", "go121-linux",
        "runtime error: invalid memory address or nil pointer dereference",
        r"(nil pointer dereference|invalid memory address)",
        "runtime", "go", ">=1.18", "linux",
        "true", 0.96, 0.97,
        "Attempting to dereference a nil pointer, often from unchecked error returns.",
        [de("Using recover() to catch all nil pointer panics", "Masks bugs; recover should only be used at API boundaries", 0.75),
         de("Initializing all pointers to empty structs", "Hides nil-state bugs; empty struct may not be a valid state", 0.55)],
        [wa("Add nil checks before dereferencing: if ptr != nil { ... }", 0.96, "Check for nil at every point where a pointer might be nil", sources=["https://go.dev/doc/effective_go#errors"]),
         wa("Always check error returns: val, err := fn(); if err != nil { return }", 0.97, "Most nil pointer issues come from ignoring error returns")],
    ))

    c.append(canon(
        "go", "multiple-value-in-single-context", "go121-linux",
        "multiple-value f() (value of type (T, error)) used in single-value context",
        r"multiple-value.*used in single-value context",
        "syntax", "go", ">=1.18", "linux",
        "true", 0.99, 0.99,
        "Calling a function that returns multiple values (typically value, error) in a context that expects a single value.",
        [de("Wrapping the function to discard the error", "Silently ignores errors, leading to nil pointer panics", 0.85)],
        [wa("Assign both return values: val, err := fn()", 0.99, "Handle the error: val, err := fn(); if err != nil { return err }", sources=["https://go.dev/doc/effective_go#multiple-returns"]),
         wa("Use _ to explicitly discard: val, _ := fn()", 0.85, "Only when you're certain the error cannot occur or is irrelevant")],
    ))

    # ── Kubernetes ──────────────────────────────────────────────────────
    c.append(canon(
        "kubernetes", "crashloopbackoff", "k8s128-linux",
        "CrashLoopBackOff",
        r"CrashLoopBackOff",
        "pod-lifecycle", "kubernetes", ">=1.24", "linux",
        "true", 0.90, 0.92,
        "Container repeatedly crashes and Kubernetes keeps restarting it with exponential backoff.",
        [de("Deleting and recreating the pod", "Kubernetes will restart it with the same config; crash will recur", 0.85),
         de("Increasing restart policy backoff", "Does not fix the underlying crash", 0.90)],
        [wa("Check container logs: kubectl logs <pod> --previous to see crash reason", 0.95, "The --previous flag shows logs from the last crashed instance", sources=["https://kubernetes.io/docs/tasks/debug/debug-application/debug-pods/"]),
         wa("Use kubectl describe pod <pod> to check events, readiness probes, and resource limits", 0.93, "Common causes: OOM kills, failed liveness probes, missing config/secrets")],
    ))

    c.append(canon(
        "kubernetes", "imagepullbackoff", "k8s128-linux",
        "ImagePullBackOff",
        r"(ImagePullBackOff|ErrImagePull)",
        "pod-lifecycle", "kubernetes", ">=1.24", "linux",
        "true", 0.94, 0.95,
        "Kubernetes cannot pull the container image from the registry.",
        [de("Restarting the kubelet", "The issue is authentication or image reference, not the kubelet", 0.80),
         de("Waiting for it to resolve itself", "ImagePullBackOff has exponential backoff but won't fix auth issues", 0.85)],
        [wa("Verify image name and tag exist in the registry: docker pull <image>", 0.93, "Test from a machine with registry access to confirm image exists"),
         wa("Create or update imagePullSecrets for private registries", 0.95, "kubectl create secret docker-registry regcred --docker-server=... --docker-username=... --docker-password=...", sources=["https://kubernetes.io/docs/tasks/configure-pod-container/pull-image-private-registry/"])],
    ))

    c.append(canon(
        "kubernetes", "pod-evicted", "k8s128-linux",
        "The node was low on resource: ephemeral-storage",
        r"(evicted|low on resource: ephemeral-storage|DiskPressure)",
        "resources", "kubernetes", ">=1.24", "linux",
        "true", 0.91, 0.93,
        "Pod evicted due to node running low on disk (ephemeral storage) or memory.",
        [de("Setting very high resource requests to get scheduled on bigger nodes", "Wastes cluster resources; doesn't fix the storage consumption", 0.70),
         de("Disabling eviction thresholds on the kubelet", "Node can run out of disk and become unresponsive", 0.90)],
        [wa("Set ephemeral-storage resource limits on containers to prevent excessive disk use", 0.92, "resources: limits: ephemeral-storage: 2Gi", sources=["https://kubernetes.io/docs/concepts/configuration/manage-resources-containers/"]),
         wa("Clean up container logs and temp files; use emptyDir sizeLimit", 0.88, "emptyDir: sizeLimit: 1Gi prevents unbounded temp file growth")],
    ))

    # ── Terraform ───────────────────────────────────────────────────────
    c.append(canon(
        "terraform", "cycle-detected", "tf115-linux",
        "Error: Cycle detected in resource dependencies",
        r"Cycle.*resource dependencies",
        "graph", "terraform", ">=1.0", "linux",
        "true", 0.91, 0.93,
        "Terraform dependency graph has a circular reference between resources.",
        [de("Adding depends_on to both resources", "Explicitly creates the cycle that Terraform detected", 0.90),
         de("Using terraform taint on one of the resources", "Does not break the cycle; just marks for recreation", 0.80)],
        [wa("Identify the cycle with terraform graph | dot -Tsvg > graph.svg and break it", 0.92, "Visualize dependencies and remove the circular reference", sources=["https://developer.hashicorp.com/terraform/cli/commands/graph"]),
         wa("Use data sources or outputs instead of direct references to break the cycle", 0.88, "Replace direct resource references with data source lookups where possible")],
    ))

    c.append(canon(
        "terraform", "state-lock-error", "tf115-linux",
        "Error: Error acquiring the state lock",
        r"Error acquiring the state lock",
        "state", "terraform", ">=1.0", "linux",
        "true", 0.94, 0.96,
        "Another Terraform process holds the state lock, or a previous run crashed without releasing it.",
        [de("Running terraform force-unlock immediately", "May corrupt state if another process is genuinely running", 0.70),
         de("Deleting the lock file from the backend manually", "Backend-specific and risky; may lose state data", 0.80)],
        [wa("Wait for the other process to finish, then retry", 0.85, "Check who holds the lock — the error message includes the lock ID and creator"),
         wa("Use terraform force-unlock <LOCK_ID> only after confirming no other process is running", 0.93, "Verify no other Terraform processes: ps aux | grep terraform", sources=["https://developer.hashicorp.com/terraform/cli/commands/force-unlock"])],
    ))

    # ── AWS ──────────────────────────────────────────────────────────────
    c.append(canon(
        "aws", "access-denied-s3", "aws-cli2-linux",
        "An error occurred (AccessDenied) when calling the GetObject operation",
        r"AccessDenied.*calling the (GetObject|PutObject|ListBucket)",
        "iam", "aws-cli", ">=2.0", "linux",
        "true", 0.93, 0.95,
        "S3 access denied due to IAM policy, bucket policy, or ACL misconfiguration.",
        [de("Making the bucket public", "Major security risk; exposes all objects to the internet", 0.95, sources=["https://docs.aws.amazon.com/AmazonS3/latest/userguide/access-control-block-public-access.html"]),
         de("Using the root account credentials", "Against AWS security best practices; no audit trail", 0.85)],
        [wa("Check IAM policy, bucket policy, and ACLs with aws iam simulate-principal-policy", 0.92, "Identify which policy is denying access", sources=["https://docs.aws.amazon.com/IAM/latest/UserGuide/access_policies_testing-policies.html"]),
         wa("Add the required S3 permissions to the IAM role/user policy", 0.95, "Add s3:GetObject, s3:PutObject, etc. for the specific bucket ARN")],
    ))

    c.append(canon(
        "aws", "ecs-service-unable-to-place", "aws-cli2-linux",
        "service unable to place tasks: reason: no container instances available",
        r"unable to place tasks.*no container instances",
        "ecs", "aws", ">=2.0", "linux",
        "true", 0.90, 0.92,
        "ECS cannot schedule tasks because there are no EC2 instances with enough resources or the cluster has no instances.",
        [de("Increasing the desired count further", "More tasks compete for the same insufficient resources", 0.80),
         de("Terminating and relaunching the ECS service", "Service recreates but the capacity problem remains", 0.75)],
        [wa("Scale up the Auto Scaling Group or add capacity providers", 0.93, "Increase ASG desired count or use Fargate capacity provider", sources=["https://docs.aws.amazon.com/AmazonECS/latest/developerguide/cluster-capacity-providers.html"]),
         wa("Check task resource requirements (CPU/memory) vs instance capacity", 0.90, "Task definitions may request more resources than instance types provide")],
    ))

    # ── Next.js ──────────────────────────────────────────────────────────
    c.append(canon(
        "nextjs", "dynamic-server-usage", "next14-linux",
        "Error: Dynamic server usage: cookies",
        r"Dynamic server usage: (cookies|headers|searchParams)",
        "app-router", "next.js", ">=13.4", "linux",
        "true", 0.95, 0.96,
        "Using cookies(), headers(), or searchParams in a component that Next.js is trying to statically render.",
        [de("Adding 'use client' to the component", "cookies/headers are server-only APIs; 'use client' will cause import errors", 0.80),
         de("Wrapping in try/catch", "Next.js checks usage at build time; runtime handling doesn't prevent the error", 0.70)],
        [wa("Export const dynamic = 'force-dynamic' to opt out of static rendering", 0.95, "Forces the page to render dynamically on every request", sources=["https://nextjs.org/docs/app/api-reference/file-conventions/route-segment-config"]),
         wa("Move the dynamic API call to a Server Component that is not statically rendered", 0.90, "Keep the static parts static and only make the dynamic part dynamic")],
    ))

    c.append(canon(
        "nextjs", "hydration-text-mismatch", "next14-linux",
        "Error: Text content does not match server-rendered HTML",
        r"(Text content does not match|Hydration failed because)",
        "hydration", "next.js", ">=13", "linux",
        "true", 0.92, 0.94,
        "Server-rendered HTML differs from client-side render, causing a hydration mismatch.",
        [de("Suppressing with suppressHydrationWarning on every element", "Masks real bugs; mismatches can cause UI inconsistencies", 0.75),
         de("Forcing client-side only rendering for the whole page", "Loses SSR benefits (SEO, performance)", 0.70)],
        [wa("Ensure server and client render the same content — avoid Date.now(), Math.random() in render", 0.93, "Move dynamic content to useEffect or use suppressHydrationWarning only on specific elements", sources=["https://nextjs.org/docs/messages/react-hydration-error"]),
         wa("Use dynamic() with { ssr: false } for components that can only render on the client", 0.88, "import dynamic from 'next/dynamic'; const Comp = dynamic(() => import('./Comp'), { ssr: false })")],
    ))

    # ── React ────────────────────────────────────────────────────────────
    c.append(canon(
        "react", "too-many-rerenders", "react18-linux",
        "Error: Too many re-renders. React limits the number of renders to prevent an infinite loop.",
        r"Too many re-renders.*infinite loop",
        "rendering", "react", ">=17", "linux",
        "true", 0.96, 0.97,
        "Component enters an infinite re-render loop, usually caused by setting state directly in the render body.",
        [de("Adding a useRef flag to prevent re-renders", "Hides the root cause; adds fragile workaround logic", 0.65),
         de("Using useMemo around the state-setting code", "useMemo doesn't prevent the state update from triggering re-render", 0.70)],
        [wa("Move state updates into event handlers or useEffect, not the render body", 0.97, "Instead of setState(x) in render, use useEffect(() => setState(x), [deps])", sources=["https://react.dev/reference/react/useState#im-getting-an-error-too-many-re-renders"]),
         wa("Use a callback form for event handlers: onClick={() => setCount(c+1)} not onClick={setCount(c+1)}", 0.95, "The second form calls setCount immediately during render, causing the loop")],
    ))

    c.append(canon(
        "react", "cannot-update-unmounted", "react18-linux",
        "Warning: Can't perform a React state update on an unmounted component",
        r"Can't perform a React state update on an unmounted component",
        "lifecycle", "react", ">=17", "linux",
        "true", 0.94, 0.95,
        "Async operation (fetch, setTimeout) completes after the component has unmounted and tries to setState.",
        [de("Wrapping in try/catch", "setState on unmounted component is not an exception; try/catch won't help", 0.80),
         de("Ignoring the warning since React 18 removed it", "React 18 removed the warning but the memory leak from the async operation still exists", 0.50)],
        [wa("Use an AbortController to cancel async operations on unmount", 0.95, "useEffect cleanup: const ac = new AbortController(); return () => ac.abort();", sources=["https://react.dev/reference/react/useEffect#fetching-data-with-effects"]),
         wa("Track mounted state with useRef and check before setState", 0.85, "const mounted = useRef(true); useEffect(() => () => { mounted.current = false }, []);")],
    ))

    # ── CUDA ─────────────────────────────────────────────────────────────
    c.append(canon(
        "cuda", "device-side-assert", "cuda12-linux",
        "RuntimeError: CUDA error: device-side assert triggered",
        r"CUDA error: device-side assert triggered",
        "runtime", "cuda", ">=11.0", "linux",
        "true", 0.88, 0.90,
        "A CUDA kernel assertion failed on the GPU, typically due to out-of-bounds index or invalid label in loss function.",
        [de("Restarting the Python process to clear the error", "Device-side asserts are sticky; error persists until GPU context is reset", 0.60),
         de("Catching RuntimeError and continuing training", "GPU is in an error state; all subsequent CUDA operations will fail", 0.85)],
        [wa("Set CUDA_LAUNCH_BLOCKING=1 to get the exact line that triggered the assert", 0.93, "Forces synchronous kernel launches so the traceback points to the offending kernel", sources=["https://docs.nvidia.com/cuda/cuda-c-programming-guide/index.html#assertion"]),
         wa("Check loss function inputs: labels must be in [0, num_classes) range", 0.90, "Most common cause is label index >= num_classes in CrossEntropyLoss")],
    ))

    # ── pip ──────────────────────────────────────────────────────────────
    c.append(canon(
        "pip", "externally-managed-environment", "pip23-linux",
        "error: externally-managed-environment",
        r"externally-managed-environment",
        "environment", "pip", ">=23.0", "linux",
        "true", 0.97, 0.98,
        "PEP 668: pip refuses to install into system Python because the OS package manager manages it.",
        [de("Removing the EXTERNALLY-MANAGED file", "Breaks OS package manager integration; system packages may conflict", 0.85, sources=["https://peps.python.org/pep-0668/"]),
         de("Using --break-system-packages flag", "Bypasses the protection; can corrupt system Python", 0.75)],
        [wa("Use a virtual environment: python -m venv .venv && source .venv/bin/activate", 0.98, "Virtual environments are isolated and don't conflict with system Python", sources=["https://docs.python.org/3/library/venv.html"]),
         wa("Use pipx for CLI tools: pipx install <tool>", 0.93, "pipx installs each tool in its own isolated environment")],
    ))

    return c


def main():
    canons = get_all_canons()
    written = skipped = 0
    for c_item in canons:
        domain = c_item["error"]["domain"]
        slug = c_item["id"].split("/")[1]
        env = c_item["id"].split("/")[2]
        out_dir = DATA_DIR / domain
        out_dir.mkdir(parents=True, exist_ok=True)
        out_file = out_dir / f"{slug}_{env}.json"
        if out_file.exists():
            skipped += 1
            continue
        with open(out_file, "w", encoding="utf-8") as f:
            json.dump(c_item, f, indent=2, ensure_ascii=False)
            f.write("\n")
        written += 1
    print(f"Wave 11: wrote {written} new canons, skipped {skipped} existing")


if __name__ == "__main__":
    main()
