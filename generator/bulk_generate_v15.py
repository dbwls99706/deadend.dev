"""Wave 15: 40 new canons (460 → 500)."""

import json
from generator.bulk_generate import (
    canon, de, wa, DATA_DIR,
)


def get_all_canons():
    c = []

    # ── Python ──────────────────────────────────────────────────────────
    c.append(canon(
        "python", "indexerror-list-out-of-range", "py311-linux",
        "IndexError: list index out of range",
        r"IndexError: list index out of range",
        "collections", "cpython", ">=3.8", "linux",
        "true", 0.98, 0.99,
        "Accessing a list element at an index that doesn't exist.",
        [de("Catching IndexError and returning None", "Silently hides off-by-one or empty list bugs", 0.60),
         de("Pre-filling the list with None values to ensure indices exist", "Wastes memory; hides the logic error", 0.70)],
        [wa("Check length before access: if i < len(lst): value = lst[i]", 0.97, "Guard against empty lists and out-of-range indices"),
         wa("Use negative indexing safely: lst[-1] for last element, but only if list is non-empty", 0.90, "if lst: last = lst[-1]", sources=["https://docs.python.org/3/tutorial/introduction.html#lists"])],
    ))

    c.append(canon(
        "python", "attributeerror-nonetype", "py311-linux",
        "AttributeError: 'NoneType' object has no attribute 'split'",
        r"AttributeError: 'NoneType' object has no attribute",
        "typing", "cpython", ">=3.8", "linux",
        "true", 0.97, 0.98,
        "Calling a method on None — usually from an unhandled function return value or missing dictionary key.",
        [de("Adding a global try/except AttributeError", "Masks the None source; bug surfaces elsewhere", 0.75),
         de("Setting a default attribute on NoneType", "Cannot modify built-in types; SyntaxError in strict mode", 0.90)],
        [wa("Trace where the None comes from — add assertions or type hints", 0.95, "assert value is not None, 'Expected non-None from function X'"),
         wa("Use Optional type hints and None checks: if result is not None: result.split()", 0.93, "Type checkers like mypy will flag unsafe None access", sources=["https://docs.python.org/3/library/typing.html#typing.Optional"])],
    ))

    c.append(canon(
        "python", "syntaxerror-invalid-syntax", "py311-linux",
        "SyntaxError: invalid syntax",
        r"SyntaxError: invalid syntax",
        "parsing", "cpython", ">=3.8", "linux",
        "true", 0.99, 0.99,
        "Python parser cannot understand the code — missing colon, unmatched parenthesis, or Python 2 syntax in Python 3.",
        [de("Downgrading Python version", "Rarely helps; most syntax errors are typos not version issues", 0.85),
         de("Using exec() to run the code string", "Hides syntax errors in strings; harder to debug", 0.90)],
        [wa("Check the line indicated AND the line above it — Python often reports the error one line late", 0.96, "Missing closing parenthesis on line N causes SyntaxError on line N+1"),
         wa("Look for common Python 2→3 issues: print statement, except Exception, e:", 0.85, "print('hello') not print 'hello'; except Exception as e: not except Exception, e:", sources=["https://docs.python.org/3/whatsnew/3.0.html"])],
    ))

    c.append(canon(
        "python", "nameerror-not-defined", "py311-linux",
        "NameError: name 'variable' is not defined",
        r"NameError: name '(\w+)' is not defined",
        "scoping", "cpython", ">=3.8", "linux",
        "true", 0.98, 0.99,
        "Variable or function name doesn't exist in the current scope — typo, missing import, or scope issue.",
        [de("Using globals() to inject the variable", "Fragile; breaks encapsulation", 0.80),
         de("Wrapping in try/except NameError", "Hides the real bug — the name truly doesn't exist", 0.75)],
        [wa("Check for typos in the variable/function name", 0.97, "Use IDE autocomplete to avoid typos; Python is case-sensitive"),
         wa("Ensure the import or definition is at the top of the file or before first use", 0.95, "Variables must be defined before they are referenced", sources=["https://docs.python.org/3/reference/executionmodel.html#naming-and-binding"])],
    ))

    c.append(canon(
        "python", "keyerror-dict", "py311-linux",
        "KeyError: 'missing_key'",
        r"KeyError:",
        "collections", "cpython", ">=3.8", "linux",
        "true", 0.98, 0.99,
        "Dictionary key doesn't exist.",
        [de("Using defaultdict everywhere", "Changes the dict behavior globally; may mask missing data issues", 0.50),
         de("Adding all possible keys with None defaults upfront", "Hides missing data; downstream code gets None instead of useful errors", 0.55)],
        [wa("Use dict.get(key, default) for optional keys", 0.97, "data.get('key', 'fallback') returns fallback if key is missing", sources=["https://docs.python.org/3/library/stdtypes.html#dict.get"]),
         wa("Use 'key in dict' check for required keys", 0.93, "if 'key' in data: value = data['key'] else: raise ValueError('missing key')")],
    ))

    # ── Node ────────────────────────────────────────────────────────────
    c.append(canon(
        "node", "typeerror-not-a-function", "node20-linux",
        "TypeError: x is not a function",
        r"TypeError: .* is not a function",
        "runtime", "node", ">=14", "linux",
        "true", 0.96, 0.97,
        "Attempting to call something that isn't a function — usually a wrong import or undefined variable.",
        [de("Wrapping in try/catch and calling a fallback", "Masks the import/API issue; fallback may not be equivalent", 0.65),
         de("Adding typeof checks before every function call", "Boilerplate; hides the root cause", 0.70)],
        [wa("Check the import: the function may be a named export, not default", 0.95, "import { fn } from 'mod' vs import mod from 'mod'; mod.fn()"),
         wa("Verify the API — the method may have been renamed or removed in a newer version", 0.88, "Check the package changelog and documentation", sources=["https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Errors/Not_a_function"])],
    ))

    c.append(canon(
        "node", "err-crypto-invalid-iv-length", "node20-linux",
        "Error: Invalid IV length",
        r"Invalid IV length",
        "crypto", "node", ">=14", "linux",
        "true", 0.95, 0.96,
        "Initialization vector (IV) length doesn't match what the cipher expects (usually 16 bytes for AES).",
        [de("Padding the IV with zeros", "Weakens cryptographic security; predictable IV bytes", 0.80),
         de("Using a fixed/hardcoded IV", "Completely defeats the purpose of an IV; same plaintext → same ciphertext", 0.90)],
        [wa("Generate a random IV of the correct length: crypto.randomBytes(16) for AES-128/256", 0.96, "Store the IV alongside the ciphertext for decryption", sources=["https://nodejs.org/api/crypto.html#cryptorandombytessize-callback"]),
         wa("Check the cipher algorithm — different ciphers require different IV lengths", 0.88, "AES-CBC/CTR needs 16 bytes; ChaCha20 needs 12 bytes")],
    ))

    c.append(canon(
        "node", "err-require-esm", "node20-linux",
        "Error [ERR_REQUIRE_ESM]: require() of ES Module not supported",
        r"ERR_REQUIRE_ESM.*require\(\) of ES Module",
        "modules", "node", ">=14", "linux",
        "true", 0.93, 0.95,
        "Trying to require() an ES module from CommonJS code — the imported package has switched to ESM-only.",
        [de("Pinning to the last CJS version of the package", "Misses security patches and features in newer versions", 0.50),
         de("Patching the package to add CJS exports", "Will be overwritten on npm install; maintenance burden", 0.80)],
        [wa("Use dynamic import(): const pkg = await import('package')", 0.93, "Dynamic import() works in both CJS and ESM contexts", sources=["https://nodejs.org/api/esm.html#interoperability-with-commonjs"]),
         wa("Convert your project to ESM: add 'type': 'module' to package.json", 0.90, "Use import/export syntax throughout your project")],
    ))

    # ── Docker ──────────────────────────────────────────────────────────
    c.append(canon(
        "docker", "healthcheck-failing", "docker24-linux",
        "health: starting (unhealthy)",
        r"(health: starting|unhealthy)",
        "healthcheck", "docker", ">=20.10", "linux",
        "true", 0.92, 0.94,
        "Container's HEALTHCHECK command is failing — the application isn't ready or the check is misconfigured.",
        [de("Removing HEALTHCHECK from Dockerfile", "Container appears healthy but may not actually be serving traffic", 0.70),
         de("Setting the health check to always return 0", "Defeats the purpose; orchestrators think the container is always healthy", 0.90)],
        [wa("Debug the health check: docker inspect --format='{{.State.Health}}' <container>", 0.93, "Shows the last N health check results and exit codes", sources=["https://docs.docker.com/reference/dockerfile/#healthcheck"]),
         wa("Test the health command inside the container: docker exec <container> curl -f http://localhost:8080/health", 0.90, "Run the same command the HEALTHCHECK uses to see what fails")],
    ))

    c.append(canon(
        "docker", "layer-already-being-pulled", "docker24-linux",
        "layer already being pulled by another client. Waiting...",
        r"layer already being pulled|already being pulled by another",
        "registry", "docker", ">=20.10", "linux",
        "true", 0.92, 0.93,
        "Another Docker pull is downloading the same layer concurrently.",
        [de("Canceling and restarting the pull", "Will hit the same issue if another pull is still running", 0.60),
         de("Deleting all local images to force a fresh pull", "Wastes bandwidth; all images need to be re-downloaded", 0.75)],
        [wa("Wait for the other pull to complete — this is expected behavior during parallel pulls", 0.90, "Docker daemon serializes layer downloads; the second pull reuses the first's result"),
         wa("If stuck, restart Docker daemon: sudo systemctl restart docker", 0.85, "Clears stuck layer downloads; running containers will stop")],
    ))

    # ── Git ──────────────────────────────────────────────────────────────
    c.append(canon(
        "git", "stash-apply-conflict", "git2-linux",
        "error: Your local changes to the following files would be overwritten by merge",
        r"local changes.*would be overwritten",
        "merge", "git", ">=2.20", "linux",
        "true", 0.96, 0.97,
        "Local uncommitted changes conflict with the incoming changes (pull, checkout, stash apply).",
        [de("Using git checkout -- . to discard all changes", "Destroys all uncommitted work", 0.90),
         de("Using git clean -fd", "Deletes untracked files permanently", 0.85)],
        [wa("Stash your changes first: git stash && git pull && git stash pop", 0.95, "Safely saves and restores your changes around the operation", sources=["https://git-scm.com/docs/git-stash"]),
         wa("Commit your changes first, then pull/merge", 0.93, "git add . && git commit -m 'wip' && git pull — can revert if needed")],
    ))

    c.append(canon(
        "git", "merge-conflict-markers", "git2-linux",
        "CONFLICT (content): Merge conflict in file.txt",
        r"CONFLICT \(content\): Merge conflict in",
        "merge", "git", ">=2.0", "linux",
        "true", 0.95, 0.96,
        "Git cannot automatically merge changes — both branches modified the same lines.",
        [de("Accepting 'ours' or 'theirs' blindly for all files", "Discards one side's changes entirely without reviewing", 0.75),
         de("Deleting the conflicting files and recreating them", "Loses git history; may miss important changes from either side", 0.85)],
        [wa("Resolve manually: open conflicting files, choose correct code between <<<<<<< and >>>>>>>", 0.95, "Use git diff to see both sides; remove conflict markers after resolving"),
         wa("Use a merge tool: git mergetool — opens a visual diff/merge editor", 0.90, "Configure with: git config merge.tool vimdiff", sources=["https://git-scm.com/docs/git-mergetool"])],
    ))

    # ── TypeScript ──────────────────────────────────────────────────────
    c.append(canon(
        "typescript", "ts18048-possibly-undefined", "ts5-linux",
        "error TS18048: 'x' is possibly 'undefined'",
        r"TS18048.*is possibly 'undefined'",
        "strictness", "tsc", ">=4.5", "linux",
        "true", 0.97, 0.98,
        "Variable might be undefined based on type analysis; strict null checks require a guard.",
        [de("Adding ! assertion to every occurrence", "Ignores the type system's warning; runtime errors when truly undefined", 0.75),
         de("Initializing everything to empty string/zero", "Wrong defaults cause subtle bugs worse than crashes", 0.60)],
        [wa("Add a runtime check: if (x !== undefined) { use(x) }", 0.97, "Type narrowing satisfies the compiler and catches real issues"),
         wa("Use nullish coalescing: const value = x ?? defaultValue", 0.93, "Provides a safe default when the value is null/undefined", sources=["https://www.typescriptlang.org/docs/handbook/2/narrowing.html"])],
    ))

    # ── Rust ────────────────────────────────────────────────────────────
    c.append(canon(
        "rust", "e0282-type-annotations-needed", "rust1-linux",
        "error[E0282]: type annotations needed",
        r"E0282.*type annotations needed",
        "type-inference", "rustc", ">=1.60", "linux",
        "true", 0.96, 0.97,
        "Rust's type inference cannot determine the type; explicit annotation is required.",
        [de("Adding turbofish everywhere: ::<Type>", "Over-annotating makes code less readable", 0.30),
         de("Using unsafe to bypass type checking", "unsafe doesn't help with type inference; it's for memory operations", 0.90)],
        [wa("Add type annotation on the variable: let x: Vec<i32> = ...", 0.96, "Annotate the binding to help inference", sources=["https://doc.rust-lang.org/book/ch03-02-data-types.html"]),
         wa("Use turbofish syntax on the method: .collect::<Vec<_>>()", 0.93, "Common with iterator methods like collect, parse, etc.")],
    ))

    c.append(canon(
        "rust", "e0015-cannot-call-non-const-fn", "rust1-linux",
        "error[E0015]: cannot call non-const fn in constants",
        r"E0015.*cannot call non-const fn",
        "const-eval", "rustc", ">=1.60", "linux",
        "true", 0.91, 0.93,
        "Trying to call a runtime function in a const context (const, static, or const fn).",
        [de("Using unsafe to bypass the const restriction", "unsafe doesn't make non-const functions callable in const context", 0.90),
         de("Using a different type that has const constructors", "May not be functionally equivalent", 0.45)],
        [wa("Use lazy_static! or std::sync::LazyLock for runtime-initialized static values", 0.93, "lazy_static! { static ref DATA: Vec<i32> = compute(); }", sources=["https://doc.rust-lang.org/std/sync/struct.LazyLock.html"]),
         wa("Move the initialization to a const fn if possible", 0.85, "Mark the function as const fn if all its operations are const-evaluable")],
    ))

    # ── Go ──────────────────────────────────────────────────────────────
    c.append(canon(
        "go", "interface-conversion-panic", "go121-linux",
        "interface conversion: interface is nil, not T",
        r"interface conversion.*interface is nil",
        "runtime", "go", ">=1.18", "linux",
        "true", 0.95, 0.96,
        "Type assertion on a nil interface value.",
        [de("Using recover() globally to catch the panic", "Masks the nil interface bug; inconsistent state continues", 0.75),
         de("Checking for nil after the assertion", "Panic already happened; nil check is too late", 0.85)],
        [wa("Use the two-value type assertion: val, ok := iface.(T); if !ok { handle }", 0.96, "Safe form doesn't panic; ok is false if assertion fails", sources=["https://go.dev/tour/methods/15"]),
         wa("Check for nil before type-asserting: if iface != nil { val := iface.(T) }", 0.90, "Nil interfaces always fail type assertions")],
    ))

    c.append(canon(
        "go", "cannot-assign-to-struct-field-in-map", "go121-linux",
        "cannot assign to struct field in map",
        r"cannot assign to struct field in map",
        "language", "go", ">=1.18", "linux",
        "true", 0.96, 0.97,
        "Go doesn't allow modifying a struct field directly through a map access because map values are not addressable.",
        [de("Using reflect to modify the field", "Overly complex; bypasses type safety", 0.85),
         de("Using unsafe.Pointer to get the address", "Map values may move during rehashing; undefined behavior", 0.95)],
        [wa("Copy the struct, modify it, and assign back: v := m[key]; v.Field = x; m[key] = v", 0.96, "The idiomatic Go pattern for map-of-structs modification"),
         wa("Use a map of pointers instead: map[Key]*Struct", 0.93, "Pointer values are addressable; fields can be modified directly: m[key].Field = x", sources=["https://go.dev/doc/effective_go#maps"])],
    ))

    # ── Kubernetes ──────────────────────────────────────────────────────
    c.append(canon(
        "kubernetes", "namespace-terminating", "k8s128-linux",
        "namespace is being terminated",
        r"namespace.*terminating",
        "namespace", "kubernetes", ">=1.24", "linux",
        "true", 0.90, 0.92,
        "Namespace stuck in Terminating state — usually due to a finalizer that can't complete.",
        [de("Force-deleting the namespace with kubectl delete ns --force --grace-period=0", "Does not work for stuck Terminating namespaces; finalizers still block", 0.80),
         de("Waiting indefinitely for it to resolve", "May never resolve if the finalizer controller is gone", 0.70)],
        [wa("Remove the finalizer: kubectl get ns <ns> -o json | jq '.spec.finalizers = []' | kubectl replace --raw /api/v1/namespaces/<ns>/finalize -f -", 0.92, "Clears the stuck finalizer allowing deletion to proceed", sources=["https://kubernetes.io/docs/concepts/overview/working-with-objects/finalizers/"]),
         wa("Check what's preventing deletion: kubectl api-resources --verbs=list --namespaced -o name | xargs -n1 kubectl get -n <ns>", 0.85, "Lists all remaining resources in the namespace that may block deletion")],
    ))

    c.append(canon(
        "kubernetes", "invalid-value-metadata-name", "k8s128-linux",
        "Invalid value: must be no more than 63 characters",
        r"Invalid value.*must be no more than 63 characters",
        "validation", "kubernetes", ">=1.24", "linux",
        "true", 0.96, 0.97,
        "Kubernetes resource names must follow DNS label rules — max 63 characters, lowercase, alphanumeric and hyphens.",
        [de("Truncating the name arbitrarily", "May cause duplicate names or lose identifying information", 0.50),
         de("Using underscores instead of hyphens", "Underscores are not valid in Kubernetes resource names", 0.85)],
        [wa("Shorten the name to 63 characters or fewer while keeping it identifiable", 0.95, "Use abbreviations: 'prod' not 'production', 'svc' not 'service'"),
         wa("Use generateName for automatic suffix: metadata.generateName: 'my-prefix-'", 0.88, "Kubernetes adds a random suffix; ensures uniqueness within 63 chars", sources=["https://kubernetes.io/docs/reference/using-api/api-concepts/#generated-values"])],
    ))

    # ── Terraform ───────────────────────────────────────────────────────
    c.append(canon(
        "terraform", "error-loading-state", "tf115-linux",
        "Error loading state: state snapshot was created by Terraform v1.6, which is newer than current v1.5",
        r"Error loading state.*newer than current",
        "state", "terraform", ">=1.0", "linux",
        "true", 0.94, 0.95,
        "Terraform state was written by a newer version than the one you're running.",
        [de("Editing the state file to change the version number", "Corrupts the state file; Terraform may not understand newer format", 0.90),
         de("Creating a new state with terraform init", "Loses track of all existing infrastructure; resources become unmanaged", 0.95)],
        [wa("Upgrade Terraform to at least the version that created the state", 0.96, "tfenv install 1.6 && tfenv use 1.6 — or download from hashicorp.com", sources=["https://developer.hashicorp.com/terraform/downloads"]),
         wa("Ensure all team members use the same Terraform version via .terraform-version or required_version", 0.90, "terraform { required_version = '>= 1.6' }")],
    ))

    c.append(canon(
        "terraform", "moved-block-error", "tf115-linux",
        "Error: Moved object still exists",
        r"Moved object still exists",
        "refactoring", "terraform", ">=1.1", "linux",
        "true", 0.92, 0.94,
        "A moved block references a resource that still exists in the configuration.",
        [de("Removing the moved block and running apply", "Terraform will try to destroy the old resource and create a new one", 0.80),
         de("Using terraform state rm to remove the old address", "May lose track of the resource; potential orphaned infrastructure", 0.65)],
        [wa("Remove the old resource block after adding the moved block", 0.94, "moved { from = old_address; to = new_address } — then delete the old resource block", sources=["https://developer.hashicorp.com/terraform/language/modules/develop/refactoring"]),
         wa("Run terraform plan to verify the move before applying", 0.90, "Plan should show 'moved' not 'destroy/create'")],
    ))

    # ── AWS ──────────────────────────────────────────────────────────────
    c.append(canon(
        "aws", "secrets-manager-not-found", "aws-cli2-linux",
        "An error occurred (ResourceNotFoundException) when calling the GetSecretValue operation",
        r"ResourceNotFoundException.*GetSecretValue",
        "secrets", "aws", ">=2.0", "linux",
        "true", 0.95, 0.96,
        "Secrets Manager secret doesn't exist or has been deleted.",
        [de("Creating a new secret with the same name immediately after deletion", "Deleted secrets have a recovery window (7-30 days) during which the name is reserved", 0.70),
         de("Hardcoding the secret value in code", "Security violation; secrets in code get committed to version control", 0.90)],
        [wa("Verify the secret name and region: aws secretsmanager list-secrets --region <region>", 0.95, "Secret names are case-sensitive and region-specific", sources=["https://docs.aws.amazon.com/secretsmanager/latest/userguide/manage_search-secret.html"]),
         wa("If recently deleted, restore it: aws secretsmanager restore-secret --secret-id <name>", 0.88, "Secrets in the recovery window can be restored")],
    ))

    c.append(canon(
        "aws", "rds-connection-timeout", "aws-cli2-linux",
        "OperationalError: (2003, 'Can't connect to MySQL server on rds-host (timed out)')",
        r"(Can't connect to.*server on.*timed out|Connection timed out.*rds)",
        "rds", "aws", ">=2.0", "linux",
        "true", 0.91, 0.93,
        "Cannot connect to RDS instance — usually a security group or network configuration issue.",
        [de("Making the RDS instance publicly accessible", "Security risk; database exposed to the internet", 0.85),
         de("Opening all ports in the security group (0.0.0.0/0)", "Exposes all services; major security vulnerability", 0.95)],
        [wa("Check security group inbound rules: allow port 3306 (MySQL) or 5432 (PostgreSQL) from your IP/VPC", 0.95, "Security group must allow the database port from the client's IP or security group", sources=["https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/CHAP_Troubleshooting.html#CHAP_Troubleshooting.Connecting"]),
         wa("Verify the instance is in a reachable subnet — check VPC routing tables and NAT gateway", 0.88, "Private subnets need NAT gateway for outbound; clients need a route to the RDS subnet")],
    ))

    # ── Next.js ──────────────────────────────────────────────────────────
    c.append(canon(
        "nextjs", "err-next-api-write-after-end", "next14-linux",
        "Error: write after end in API route",
        r"(write after end|Cannot set headers after they are sent)",
        "api-routes", "next.js", ">=13", "linux",
        "true", 0.95, 0.96,
        "API route sends response twice — usually a missing return after res.json().",
        [de("Adding res.headersSent check before every response", "Band-aid; masks the control flow bug", 0.60),
         de("Wrapping everything in try/catch", "The second write is intentional code, not an exception", 0.75)],
        [wa("Add return after res.json()/res.send(): return res.json({ ok: true })", 0.96, "return prevents execution of code below that would send another response"),
         wa("Refactor to single response point at the end of the handler", 0.88, "Collect the response data in a variable and send once at the end")],
    ))

    c.append(canon(
        "nextjs", "missing-suspense-boundary", "next14-linux",
        "Error: Missing Suspense boundary with useSearchParams",
        r"Missing Suspense boundary.*useSearchParams",
        "app-router", "next.js", ">=13.4", "linux",
        "true", 0.96, 0.97,
        "useSearchParams() must be wrapped in a Suspense boundary for static rendering.",
        [de("Adding 'use client' to the page", "Page is already a client component; the issue is the missing Suspense", 0.80),
         de("Using router.query instead", "router.query doesn't exist in App Router; it's a Pages Router API", 0.85)],
        [wa("Wrap the component using useSearchParams in <Suspense>: <Suspense fallback={<Loading/>}><SearchComponent/></Suspense>", 0.96, "Suspense boundary enables static rendering with dynamic client-side params", sources=["https://nextjs.org/docs/app/api-reference/functions/use-search-params"]),
         wa("Use searchParams page prop for server-side access", 0.88, "export default function Page({ searchParams }) — available in Server Components")],
    ))

    # ── React ────────────────────────────────────────────────────────────
    c.append(canon(
        "react", "useeffect-missing-dependency", "react18-linux",
        "React Hook useEffect has a missing dependency: 'value'. Either include it or remove the dependency array.",
        r"React Hook useEffect has a missing dependency",
        "hooks", "react", ">=16.8", "linux",
        "true", 0.96, 0.97,
        "ESLint exhaustive-deps rule warns about a variable used in useEffect but not in its dependency array.",
        [de("Adding // eslint-disable-next-line react-hooks/exhaustive-deps", "Suppresses a real bug warning; effect may use stale values", 0.70),
         de("Passing an empty dependency array to only run once", "Effect will use stale closure values if it reads state or props", 0.65)],
        [wa("Add the missing dependency to the array: useEffect(() => { ... }, [value])", 0.95, "Ensures the effect re-runs when its dependencies change", sources=["https://react.dev/reference/react/useEffect#specifying-reactive-dependencies"]),
         wa("If you intentionally want to exclude it, use useRef to hold the value", 0.85, "const valueRef = useRef(value); valueRef.current = value; — ref doesn't trigger re-runs")],
    ))

    c.append(canon(
        "react", "context-undefined", "react18-linux",
        "TypeError: Cannot read properties of undefined (reading 'dispatch'). useContext must be used within a Provider",
        r"(Cannot read properties of undefined.*useContext|useContext.*must be used within)",
        "context", "react", ">=16.8", "linux",
        "true", 0.96, 0.97,
        "useContext returns undefined because the component is not wrapped in the corresponding Provider.",
        [de("Providing a default value in createContext to avoid the error", "Default value masks missing Provider; component uses stale/wrong data", 0.55),
         de("Making the context value optional and checking everywhere", "Adds null checks throughout the codebase; verbose and error-prone", 0.60)],
        [wa("Wrap the component tree with the Provider: <MyContext.Provider value={...}>", 0.96, "Ensure the Provider is above the component that calls useContext in the tree", sources=["https://react.dev/reference/react/useContext"]),
         wa("Create a custom hook that throws if context is missing: useMyContext() with runtime check", 0.90, "const ctx = useContext(MyCtx); if (!ctx) throw new Error('Missing Provider'); return ctx;")],
    ))

    # ── CUDA ─────────────────────────────────────────────────────────────
    c.append(canon(
        "cuda", "cudnn-not-compiled-with-support", "cuda12-linux",
        "RuntimeError: cuDNN error: CUDNN_STATUS_NOT_SUPPORTED",
        r"cuDNN error: CUDNN_STATUS_NOT_SUPPORTED",
        "compatibility", "cuda", ">=11.0", "linux",
        "true", 0.88, 0.90,
        "cuDNN operation not supported for the given tensor configuration, often due to tensor format or data type.",
        [de("Downgrading cuDNN to an older version", "Older versions have fewer supported configurations, not more", 0.70),
         de("Disabling cuDNN entirely with torch.backends.cudnn.enabled = False", "Huge performance degradation; cuDNN is critical for conv ops", 0.65)],
        [wa("Set torch.backends.cudnn.benchmark = True to let cuDNN auto-select the best algorithm", 0.88, "benchmark mode tries all algorithms and caches the fastest one", sources=["https://pytorch.org/docs/stable/backends.html#torch.backends.cudnn.benchmark"]),
         wa("Check if the tensor needs to be contiguous: x = x.contiguous() before the op", 0.85, "Non-contiguous tensors may not be supported by certain cuDNN kernels")],
    ))

    # ── pip ──────────────────────────────────────────────────────────────
    c.append(canon(
        "pip", "could-not-find-version", "pip23-linux",
        "ERROR: Could not find a version that satisfies the requirement package>=2.0",
        r"Could not find a version that satisfies the requirement",
        "resolution", "pip", ">=22.0", "linux",
        "true", 0.93, 0.95,
        "No version of the package matches the version constraint, or the package doesn't exist on PyPI.",
        [de("Installing from a random third-party URL", "Supply chain risk; may install a malicious package", 0.90),
         de("Removing the version constraint entirely", "May install an incompatible old version", 0.55)],
        [wa("Check PyPI for available versions: pip index versions <package>", 0.93, "Lists all available versions; find one matching your constraint", sources=["https://pypi.org"]),
         wa("Verify the package name is correct — pip install is case-insensitive but some packages have unexpected names", 0.88, "Example: Pillow not PIL, opencv-python not opencv")],
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
    print(f"Wave 15: wrote {written} new canons, skipped {skipped} existing")


if __name__ == "__main__":
    main()
