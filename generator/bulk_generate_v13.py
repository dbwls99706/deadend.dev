"""Wave 13: 40 new canons (429 → ~469)."""

import json
from generator.bulk_generate import (
    canon, de, wa, DATA_DIR,
)


def get_all_canons():
    c = []

    # ── Python ──────────────────────────────────────────────────────────
    c.append(canon(
        "python", "filenotfounderror", "py311-linux",
        "FileNotFoundError: [Errno 2] No such file or directory: 'config.yaml'",
        r"FileNotFoundError: \[Errno 2\] No such file or directory",
        "filesystem", "cpython", ">=3.8", "linux",
        "true", 0.98, 0.99,
        "File path does not exist or the working directory is different from expected.",
        [de("Creating an empty file at the path", "Masks the real issue; empty file may cause downstream errors", 0.60),
         de("Using os.path.exists check with pass in else", "Silently skips the missing file; feature doesn't work", 0.50)],
        [wa("Use pathlib.Path with proper path resolution: Path(__file__).parent / 'config.yaml'", 0.96, "Resolves relative to the script location, not the working directory", sources=["https://docs.python.org/3/library/pathlib.html"]),
         wa("Verify the current working directory: print(os.getcwd()) and adjust path accordingly", 0.92, "The working directory may differ between development and production")],
    ))

    c.append(canon(
        "python", "runtimeerror-event-loop-running", "py311-linux",
        "RuntimeError: This event loop is already running",
        r"RuntimeError: This event loop is already running",
        "asyncio", "cpython", ">=3.8", "linux",
        "true", 0.93, 0.95,
        "Calling asyncio.run() or loop.run_until_complete() when an event loop is already running (common in Jupyter/IPython).",
        [de("Creating a new event loop with asyncio.new_event_loop()", "May cause resource leaks and conflicts with the existing loop", 0.65),
         de("Using threading to run a separate event loop", "Overly complex; creates concurrency issues", 0.70)],
        [wa("In Jupyter, use 'await coroutine()' directly (top-level await) instead of asyncio.run()", 0.95, "Jupyter has its own running event loop; use it directly", sources=["https://ipython.readthedocs.io/en/stable/interactive/autoawait.html"]),
         wa("Use nest_asyncio.apply() to allow nested event loops", 0.88, "import nest_asyncio; nest_asyncio.apply() — enables nested run_until_complete()")],
    ))

    c.append(canon(
        "python", "connectionrefusederror", "py311-linux",
        "ConnectionRefusedError: [Errno 111] Connection refused",
        r"ConnectionRefusedError: \[Errno 111\] Connection refused",
        "network", "cpython", ">=3.8", "linux",
        "true", 0.94, 0.96,
        "TCP connection refused because the target server is not running or not accepting connections on the specified port.",
        [de("Retrying infinitely with no backoff", "Floods the server; wastes resources if service is genuinely down", 0.70),
         de("Disabling the firewall", "Usually not a firewall issue; the service simply isn't running", 0.75)],
        [wa("Verify the target service is running: systemctl status <service> or ss -tlnp | grep <port>", 0.95, "Check the exact host and port the service is listening on"),
         wa("Implement retry with exponential backoff: tenacity.retry(wait=exponential())", 0.88, "Handles transient failures gracefully", sources=["https://tenacity.readthedocs.io/en/latest/"])],
    ))

    c.append(canon(
        "python", "typeerror-missing-required-arg", "py311-linux",
        "TypeError: __init__() missing 1 required positional argument: 'name'",
        r"TypeError: \w+\(\) missing \d+ required positional argument",
        "call-signature", "cpython", ">=3.8", "linux",
        "true", 0.98, 0.99,
        "Function or method called without providing all required arguments.",
        [de("Making all arguments optional with defaults", "Hides API contract; None defaults cause AttributeError later", 0.65),
         de("Using *args to absorb extra/missing arguments", "Breaks function signatures; IDE help becomes useless", 0.80)],
        [wa("Pass all required arguments: MyClass(name='value') or check the function signature", 0.98, "Use help(func) or inspect.signature(func) to see required parameters", sources=["https://docs.python.org/3/library/inspect.html#inspect.signature"]),
         wa("If subclassing, ensure super().__init__() is called with all required args", 0.93, "super().__init__(name=name) — pass through parent's required parameters")],
    ))

    c.append(canon(
        "python", "jsondecodeerror", "py311-linux",
        "json.decoder.JSONDecodeError: Expecting value: line 1 column 1 (char 0)",
        r"JSONDecodeError: Expecting (value|property name|',')",
        "parsing", "cpython", ">=3.8", "linux",
        "true", 0.96, 0.97,
        "Invalid JSON string passed to json.loads() — empty string, HTML response, or malformed JSON.",
        [de("Wrapping in try/except and returning empty dict", "Silently discards parse errors; downstream code gets wrong data", 0.60),
         de("Using eval() instead of json.loads()", "Security vulnerability; arbitrary code execution", 0.95)],
        [wa("Inspect the raw response before parsing: print(repr(text[:200]))", 0.95, "Often the response is HTML error page, not JSON"),
         wa("Check HTTP response status code before parsing the body", 0.93, "if resp.status_code == 200: data = resp.json() else: handle_error()", sources=["https://docs.python.org/3/library/json.html#json.JSONDecodeError"])],
    ))

    # ── Node ────────────────────────────────────────────────────────────
    c.append(canon(
        "node", "err-module-not-found-esm", "node20-linux",
        "Error [ERR_MODULE_NOT_FOUND]: Cannot find module '/app/utils' imported from /app/index.js",
        r"ERR_MODULE_NOT_FOUND.*Cannot find module",
        "esm", "node", ">=16", "linux",
        "true", 0.94, 0.96,
        "ESM import cannot find the module — missing file extension in import path.",
        [de("Adding 'type': 'commonjs' to package.json", "Switches the entire project back to CJS; breaks ES imports", 0.70),
         de("Using require() instead of import", "Mixing module systems causes more problems", 0.65)],
        [wa("Add the .js file extension to imports: import { fn } from './utils.js'", 0.96, "ESM requires explicit file extensions unlike CJS", sources=["https://nodejs.org/api/esm.html#mandatory-file-extensions"]),
         wa("Configure TypeScript or bundler to handle extension rewriting", 0.85, "In tsconfig: moduleResolution: 'nodenext' adds extensions in output")],
    ))

    c.append(canon(
        "node", "syntax-error-unexpected-token-import", "node20-linux",
        "SyntaxError: Cannot use import statement outside a module",
        r"Cannot use import statement outside a module",
        "esm", "node", ">=14", "linux",
        "true", 0.96, 0.97,
        "Using ES module import syntax in a CommonJS context.",
        [de("Transpiling everything to require()", "Loses ESM benefits; extra build step for simple projects", 0.55),
         de("Adding --experimental-modules flag", "Flag was removed in Node 14+; not needed", 0.80)],
        [wa("Add 'type': 'module' in package.json to enable ESM", 0.95, "Makes all .js files treated as ES modules", sources=["https://nodejs.org/api/packages.html#type"]),
         wa("Rename the file to .mjs extension", 0.90, ".mjs files are always treated as ES modules regardless of package.json")],
    ))

    c.append(canon(
        "node", "err-invalid-arg-type", "node20-linux",
        "TypeError [ERR_INVALID_ARG_TYPE]: The 'path' argument must be of type string. Received undefined",
        r"ERR_INVALID_ARG_TYPE.*argument must be of type",
        "validation", "node", ">=14", "linux",
        "true", 0.96, 0.97,
        "Node.js API received an argument of the wrong type, usually undefined or null where a string was expected.",
        [de("Adding type coercion: String(value)", "Converts undefined to 'undefined' string; wrong but doesn't crash", 0.70),
         de("Wrapping in try/catch to silently continue", "Masks the bug; the undefined value needs to be fixed", 0.75)],
        [wa("Trace back where the variable becomes undefined — check environment variables, config files, and function parameters", 0.95, "The root cause is usually a missing env var or config value"),
         wa("Add input validation at the function boundary", 0.88, "if (!path) throw new Error('path is required') — fail fast with a clear message")],
    ))

    # ── Docker ──────────────────────────────────────────────────────────
    c.append(canon(
        "docker", "manifest-unknown", "docker24-linux",
        "Error response from daemon: manifest for image:tag not found: manifest unknown",
        r"manifest (unknown|not found)",
        "registry", "docker", ">=20.10", "linux",
        "true", 0.95, 0.96,
        "The specified image tag does not exist in the registry.",
        [de("Pulling without specifying a tag (defaults to :latest)", "latest tag may not exist; many repos don't publish it", 0.50),
         de("Switching Docker registries", "The image might exist in the specified registry but with a different tag", 0.60)],
        [wa("Check available tags: docker manifest inspect <image> or visit the registry's web UI", 0.93, "Verify the exact tag name — tags are case-sensitive"),
         wa("For multi-arch images, specify the platform: docker pull --platform linux/amd64 <image:tag>", 0.88, "Some tags only exist for specific architectures")],
    ))

    c.append(canon(
        "docker", "build-arg-not-set", "docker24-linux",
        "WARNING: One or more build-args were not consumed",
        r"build-args? (were|was) not consumed",
        "build", "docker", ">=20.10", "linux",
        "true", 0.93, 0.94,
        "Build arguments passed via --build-arg are not declared in the Dockerfile with ARG.",
        [de("Ignoring the warning", "The build arg isn't being used; the feature it should configure isn't applied", 0.50),
         de("Setting build args as ENV instead", "ENV is baked into the image at runtime; different semantics from build-time ARG", 0.60)],
        [wa("Add ARG <name> in the Dockerfile before the RUN command that uses it", 0.96, "ARG must appear before the first usage in the Dockerfile", sources=["https://docs.docker.com/reference/dockerfile/#arg"]),
         wa("For multi-stage builds, add ARG in each stage that needs it", 0.90, "ARG is scoped to the build stage; must be redeclared after each FROM")],
    ))

    # ── Git ──────────────────────────────────────────────────────────────
    c.append(canon(
        "git", "detached-head", "git2-linux",
        "You are in 'detached HEAD' state.",
        r"detached HEAD state",
        "checkout", "git", ">=2.20", "linux",
        "true", 0.96, 0.97,
        "HEAD points to a commit directly instead of a branch — commits will be orphaned when switching branches.",
        [de("Making commits in detached HEAD and switching branches", "Commits become unreachable and will be garbage collected", 0.85),
         de("Using git reset to fix it", "reset in detached HEAD doesn't reattach to a branch", 0.70)],
        [wa("Create a new branch at the current commit: git checkout -b <new-branch>", 0.97, "Reattaches HEAD to a named branch that includes your commits", sources=["https://git-scm.com/docs/git-checkout#_detached_head"]),
         wa("Return to a branch: git checkout <branch-name>", 0.93, "If you haven't made commits, just switch to the desired branch")],
    ))

    c.append(canon(
        "git", "permission-denied-publickey", "git2-linux",
        "Permission denied (publickey). fatal: Could not read from remote repository.",
        r"Permission denied \(publickey\)",
        "auth", "git", ">=2.20", "linux",
        "true", 0.94, 0.96,
        "SSH authentication failed — no matching SSH key for the remote repository.",
        [de("Switching to HTTP URL as a permanent solution", "HTTP auth requires tokens/passwords on every push; less secure long-term", 0.40),
         de("Disabling SSH strict host key checking", "Security risk; doesn't fix the authentication problem", 0.85)],
        [wa("Generate and add SSH key: ssh-keygen -t ed25519 && cat ~/.ssh/id_ed25519.pub → add to GitHub/GitLab", 0.95, "Ed25519 keys are recommended for security and performance", sources=["https://docs.github.com/en/authentication/connecting-to-github-with-ssh"]),
         wa("Test SSH connection: ssh -T git@github.com to verify the key works", 0.90, "Shows which key is being used and whether it's accepted")],
    ))

    # ── TypeScript ──────────────────────────────────────────────────────
    c.append(canon(
        "typescript", "ts2304-cannot-find-name", "ts5-linux",
        "error TS2304: Cannot find name 'document'",
        r"TS2304.*Cannot find name",
        "declarations", "tsc", ">=4.5", "linux",
        "true", 0.96, 0.97,
        "TypeScript doesn't know about a global variable, usually because the correct lib or types are not configured.",
        [de("Declaring it as 'any': declare const document: any", "Loses all type safety for DOM operations", 0.75),
         de("Adding // @ts-nocheck at file top", "Disables all type checking in the file", 0.90)],
        [wa("Add the appropriate lib to tsconfig: lib: ['es2020', 'dom', 'dom.iterable']", 0.96, "dom lib adds all browser globals: document, window, etc.", sources=["https://www.typescriptlang.org/tsconfig#lib"]),
         wa("Install environment-specific types: npm install -D @types/node for Node.js globals", 0.93, "Node globals like process, Buffer need @types/node")],
    ))

    c.append(canon(
        "typescript", "ts1259-can-only-default-import-esinterop", "ts5-linux",
        "error TS1259: Module can only be default-imported using the 'esModuleInterop' flag",
        r"TS1259.*can only be default-imported using.*esModuleInterop",
        "modules", "tsc", ">=4.5", "linux",
        "true", 0.97, 0.98,
        "Trying to default-import a CommonJS module without esModuleInterop enabled.",
        [de("Using require() instead of import", "Bypasses TypeScript module checking; loses type information", 0.70),
         de("Using import * as X from 'module'", "Works but makes all usage look like X.default; awkward API", 0.45)],
        [wa("Enable esModuleInterop in tsconfig.json: 'esModuleInterop': true", 0.97, "Allows default imports from CJS modules; recommended by TypeScript team", sources=["https://www.typescriptlang.org/tsconfig#esModuleInterop"]),
         wa("Also enable allowSyntheticDefaultImports if esModuleInterop is not feasible", 0.85, "Less strict; only changes type checking, not emit behavior")],
    ))

    # ── Rust ────────────────────────────────────────────────────────────
    c.append(canon(
        "rust", "e0433-unresolved-import", "rust1-linux",
        "error[E0433]: failed to resolve: use of undeclared crate or module",
        r"E0433.*failed to resolve.*undeclared (crate|module)",
        "modules", "rustc", ">=1.60", "linux",
        "true", 0.95, 0.96,
        "Import refers to a crate that isn't in Cargo.toml or a module that doesn't exist.",
        [de("Adding the module as a feature flag", "Feature flags don't create new modules; they enable optional code", 0.70),
         de("Creating a dummy module to satisfy the import", "Wrong approach; the real dependency needs to be added", 0.80)],
        [wa("Add the crate to [dependencies] in Cargo.toml: cargo add <crate>", 0.96, "cargo add downloads and adds the dependency automatically", sources=["https://doc.rust-lang.org/cargo/commands/cargo-add.html"]),
         wa("Check module paths: use crate::module_name for internal modules", 0.90, "Modules must be declared with mod module_name; in lib.rs or main.rs")],
    ))

    c.append(canon(
        "rust", "e0308-mismatched-types", "rust1-linux",
        "error[E0308]: mismatched types expected `String`, found `&str`",
        r"E0308.*mismatched types",
        "type-system", "rustc", ">=1.60", "linux",
        "true", 0.97, 0.98,
        "Rust's strict type system rejects assignment because types don't match exactly.",
        [de("Using unsafe transmute to convert between types", "Undefined behavior for non-equivalent types", 0.95),
         de("Changing the function signature to accept any type", "Loses type safety; may break other callers", 0.60)],
        [wa("Convert between String and &str explicitly: .to_string() or .as_str()", 0.97, "String::from(s) or s.to_string() for &str→String; s.as_str() for String→&str", sources=["https://doc.rust-lang.org/book/ch08-02-strings.html"]),
         wa("Use Into<String> or AsRef<str> as parameter types for flexibility", 0.90, "fn process(s: impl Into<String>) accepts both &str and String")],
    ))

    # ── Go ──────────────────────────────────────────────────────────────
    c.append(canon(
        "go", "undefined-reference", "go121-linux",
        "undefined: functionName",
        r"undefined: \w+",
        "compilation", "go", ">=1.18", "linux",
        "true", 0.96, 0.97,
        "Function or variable not defined in the current package or not exported (lowercase first letter).",
        [de("Adding the function to a different package without importing", "Go requires explicit imports between packages", 0.80),
         de("Using go:linkname to access unexported symbols", "Compiler hack; breaks with Go version updates", 0.90)],
        [wa("Ensure the function starts with uppercase to be exported: MyFunc not myFunc", 0.95, "Only uppercase-initial identifiers are exported in Go", sources=["https://go.dev/doc/effective_go#names"]),
         wa("Check build tags and file suffixes (_test.go, _linux.go) that may exclude the file", 0.88, "Files with build constraints may not be compiled in your environment")],
    ))

    c.append(canon(
        "go", "missing-go-sum-entry", "go121-linux",
        "missing go.sum entry for module",
        r"missing go\.sum entry",
        "modules", "go", ">=1.16", "linux",
        "true", 0.97, 0.98,
        "Dependency checksum not recorded in go.sum file.",
        [de("Deleting go.sum and recreating", "Removes all verified checksums; next build verifies from scratch against a potentially compromised source", 0.60),
         de("Setting GONOSUMCHECK to skip verification", "Disables tamper detection for dependencies", 0.85)],
        [wa("Run go mod tidy to update go.sum with correct entries", 0.97, "Adds missing entries and removes unused ones", sources=["https://go.dev/ref/mod#go-mod-tidy"]),
         wa("Run go mod download to download and verify all dependencies", 0.92, "Downloads all modules and updates go.sum")],
    ))

    # ── Kubernetes ──────────────────────────────────────────────────────
    c.append(canon(
        "kubernetes", "pod-unschedulable", "k8s128-linux",
        "0/3 nodes are available: 3 Insufficient cpu",
        r"(\d+/\d+ nodes are available|Insufficient (cpu|memory)|Unschedulable)",
        "scheduling", "kubernetes", ">=1.24", "linux",
        "true", 0.91, 0.93,
        "No node has enough CPU or memory to schedule the pod.",
        [de("Removing resource requests to bypass scheduling", "Pod can be scheduled anywhere but may OOM or starve other pods", 0.75),
         de("Draining a node to free resources", "Moves pods to other nodes; doesn't add capacity", 0.60)],
        [wa("Review and right-size resource requests: kubectl top nodes to see actual usage", 0.93, "Requests may be over-provisioned; reduce to actual needs", sources=["https://kubernetes.io/docs/concepts/configuration/manage-resources-containers/"]),
         wa("Add more nodes or use cluster autoscaler to scale up automatically", 0.90, "autoscaler provisions new nodes when pods can't be scheduled")],
    ))

    c.append(canon(
        "kubernetes", "readiness-probe-failed", "k8s128-linux",
        "Readiness probe failed: HTTP probe failed with statuscode: 503",
        r"Readiness probe failed",
        "probes", "kubernetes", ">=1.24", "linux",
        "true", 0.93, 0.95,
        "Container's readiness probe is failing — Kubernetes won't send traffic to the pod.",
        [de("Removing the readiness probe", "All traffic goes to unready pods; users see 500 errors", 0.85),
         de("Setting the probe to check a path that always returns 200", "Defeats the purpose of readiness checks", 0.80)],
        [wa("Check the health endpoint inside the container: kubectl exec <pod> -- curl localhost:<port>/health", 0.95, "Verify the app is actually responding on the probed path"),
         wa("Adjust probe timing: increase initialDelaySeconds, periodSeconds, failureThreshold", 0.88, "Slow-starting apps need longer initial delay", sources=["https://kubernetes.io/docs/tasks/configure-pod-container/configure-liveness-readiness-startup-probes/"])],
    ))

    # ── Terraform ───────────────────────────────────────────────────────
    c.append(canon(
        "terraform", "invalid-provider-config", "tf115-linux",
        "Error: Invalid provider configuration",
        r"Invalid provider configuration",
        "providers", "terraform", ">=1.0", "linux",
        "true", 0.93, 0.95,
        "Provider configuration has invalid or missing required settings like region, credentials, or project.",
        [de("Hardcoding credentials in the provider block", "Security risk; credentials end up in version control", 0.90),
         de("Using default provider without explicit configuration", "Fails in CI/CD where defaults don't exist", 0.65)],
        [wa("Set credentials via environment variables: AWS_ACCESS_KEY_ID, GOOGLE_CREDENTIALS, etc.", 0.95, "Environment variables are the recommended way for credentials", sources=["https://developer.hashicorp.com/terraform/language/providers/configuration"]),
         wa("Use a backend-specific auth method: AWS IAM roles, GCP service accounts, Azure managed identity", 0.90, "Machine identity is more secure than static credentials")],
    ))

    # ── AWS ──────────────────────────────────────────────────────────────
    c.append(canon(
        "aws", "parameter-store-not-found", "aws-cli2-linux",
        "An error occurred (ParameterNotFound) when calling the GetParameter operation",
        r"ParameterNotFound.*GetParameter",
        "ssm", "aws", ">=2.0", "linux",
        "true", 0.95, 0.96,
        "SSM Parameter Store key does not exist or the name is wrong.",
        [de("Creating the parameter with an empty value", "Empty values cause application errors downstream", 0.60),
         de("Hardcoding the value instead of using Parameter Store", "Loses the benefits of centralized config management", 0.70)],
        [wa("Verify the parameter name and path: aws ssm get-parameter --name '/myapp/config'", 0.95, "Parameter names are case-sensitive and path-based", sources=["https://docs.aws.amazon.com/systems-manager/latest/userguide/systems-manager-parameter-store.html"]),
         wa("Check the region — Parameter Store is regional; the parameter may exist in a different region", 0.90, "Use --region flag or AWS_DEFAULT_REGION env var to specify")],
    ))

    c.append(canon(
        "aws", "sts-access-denied", "aws-cli2-linux",
        "An error occurred (AccessDenied) when calling the AssumeRole operation",
        r"AccessDenied.*calling the AssumeRole",
        "iam", "aws", ">=2.0", "linux",
        "true", 0.92, 0.94,
        "IAM identity cannot assume the target role — trust policy or permissions boundary issue.",
        [de("Attaching AdministratorAccess to the calling identity", "Excessive permissions; violates least privilege", 0.85),
         de("Modifying the role trust policy to allow all principals", "Any AWS account could assume the role", 0.90)],
        [wa("Check the role's trust policy: ensure the calling principal is listed in the trust relationship", 0.95, "aws iam get-role --role-name <role> shows the trust policy", sources=["https://docs.aws.amazon.com/IAM/latest/UserGuide/id_roles_create_for-user.html"]),
         wa("Verify the caller has sts:AssumeRole permission in their IAM policy", 0.90, "The caller needs permission to assume AND the role must trust the caller")],
    ))

    # ── Next.js ──────────────────────────────────────────────────────────
    c.append(canon(
        "nextjs", "metadata-not-supported-client", "next14-linux",
        "Error: You are attempting to export 'metadata' from a component marked with 'use client'",
        r"export.*metadata.*use client",
        "app-router", "next.js", ">=13.4", "linux",
        "true", 0.97, 0.98,
        "Next.js metadata export (for SEO) is only supported in Server Components, not Client Components.",
        [de("Using document.title in useEffect instead", "Loses SEO benefits; meta tags aren't set during SSR", 0.70),
         de("Removing 'use client' from the page", "May break if the component uses hooks or browser APIs", 0.55)],
        [wa("Export metadata from a Server Component (layout.tsx or page.tsx without 'use client')", 0.97, "Keep metadata in the page/layout, keep interactive parts in child Client Components", sources=["https://nextjs.org/docs/app/building-your-application/optimizing/metadata"]),
         wa("Use generateMetadata() function for dynamic metadata based on params", 0.92, "export async function generateMetadata({ params }) { return { title: ... } }")],
    ))

    c.append(canon(
        "nextjs", "server-action-redirect-error", "next14-linux",
        "Error: NEXT_REDIRECT",
        r"NEXT_REDIRECT",
        "server-actions", "next.js", ">=13.4", "linux",
        "true", 0.94, 0.95,
        "redirect() in a try/catch block — Next.js redirect throws a special error that must propagate.",
        [de("Catching and ignoring the error", "The redirect never happens; the action appears to do nothing", 0.80),
         de("Using router.push() in the server action", "router is a client-side API; not available in server actions", 0.85)],
        [wa("Move redirect() outside the try/catch block, or re-throw NEXT_REDIRECT errors", 0.95, "if (error.digest?.includes('NEXT_REDIRECT')) throw error", sources=["https://nextjs.org/docs/app/api-reference/functions/redirect"]),
         wa("Use the redirect after the try/catch: try { ... } catch { ... } redirect('/path')", 0.90, "Place redirect at the end of the function where it can propagate freely")],
    ))

    # ── React ────────────────────────────────────────────────────────────
    c.append(canon(
        "react", "hooks-rules-violation", "react18-linux",
        "Error: Rendered more hooks than during the previous render",
        r"(Rendered (more|fewer) hooks|hooks rules|Rules of Hooks)",
        "hooks", "react", ">=16.8", "linux",
        "true", 0.95, 0.96,
        "Hooks called conditionally or in different order between renders — violates Rules of Hooks.",
        [de("Using useRef to track which hooks to call", "Adds complexity; still violates hook ordering rules", 0.80),
         de("Converting to class components to avoid hooks entirely", "Loses functional component benefits; class components are less ergonomic", 0.65)],
        [wa("Move all hooks to the top level of the component, before any conditionals or returns", 0.97, "Hooks must be called in the same order every render", sources=["https://react.dev/reference/rules/rules-of-hooks"]),
         wa("Use the eslint-plugin-react-hooks to catch violations at lint time", 0.93, "npm install -D eslint-plugin-react-hooks — catches hook order violations automatically")],
    ))

    c.append(canon(
        "react", "invalid-hook-call", "react18-linux",
        "Error: Invalid hook call. Hooks can only be called inside the body of a function component",
        r"Invalid hook call.*Hooks can only be called inside.*function component",
        "hooks", "react", ">=16.8", "linux",
        "true", 0.94, 0.96,
        "Hook called outside a React function component — in a class component, regular function, or event handler.",
        [de("Wrapping the function in React.memo to make it a component", "memo wraps components, not plain functions; hook still can't be called", 0.80),
         de("Using global state instead of hooks", "Loses React's reactivity system; manual re-renders needed", 0.65)],
        [wa("Ensure hooks are called inside function components or custom hooks (functions starting with 'use')", 0.96, "Custom hooks must start with 'use' prefix to be recognized", sources=["https://react.dev/reference/rules/rules-of-hooks"]),
         wa("Check for duplicate React versions: npm ls react — multiple copies cause this error", 0.88, "Two React copies mean hooks registered in one aren't recognized by the other")],
    ))

    # ── CUDA ─────────────────────────────────────────────────────────────
    c.append(canon(
        "cuda", "no-kernel-image-for-device", "cuda12-linux",
        "CUDA error: no kernel image is available for execution on the device",
        r"no kernel image is available for execution on the device",
        "compatibility", "cuda", ">=11.0", "linux",
        "true", 0.90, 0.92,
        "The compiled CUDA binary doesn't include kernels for the GPU architecture (compute capability mismatch).",
        [de("Installing a different CUDA toolkit version", "The toolkit version doesn't determine compiled architectures", 0.70),
         de("Using CUDA_VISIBLE_DEVICES to select a different GPU", "All GPUs on the machine likely have the same architecture", 0.80)],
        [wa("Rebuild with the correct CUDA architecture: set TORCH_CUDA_ARCH_LIST or pass -arch=sm_XX", 0.93, "For RTX 3090 use sm_86, RTX 4090 use sm_89, A100 use sm_80", sources=["https://developer.nvidia.com/cuda-gpus"]),
         wa("Install pre-built binaries that support your GPU: pip install torch --index-url https://download.pytorch.org/whl/cu121", 0.90, "PyTorch wheels include all common architectures")],
    ))

    # ── pip ──────────────────────────────────────────────────────────────
    c.append(canon(
        "pip", "subprocess-error-build-wheel", "pip23-linux",
        "error: subprocess-exited-with-error: pip subprocess to build wheel failed",
        r"subprocess-exited-with-error.*build wheel",
        "build", "pip", ">=22.0", "linux",
        "true", 0.87, 0.89,
        "pip failed to build a wheel for a package with C/C++ extensions — missing compiler or header files.",
        [de("Using --no-binary :all: to force source builds", "Actually makes the problem worse by requiring compilation for all packages", 0.80),
         de("Installing an older version of the package", "Older versions may have the same build requirements", 0.45)],
        [wa("Install system build dependencies: sudo apt install python3-dev build-essential libffi-dev", 0.90, "Most C extensions need gcc and Python headers"),
         wa("Check if a pre-built wheel exists: pip install <package> --only-binary :all:", 0.88, "Avoids compilation entirely by using pre-built wheels", sources=["https://pip.pypa.io/en/stable/cli/pip_install/#cmdoption-only-binary"])],
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
    print(f"Wave 13: wrote {written} new canons, skipped {skipped} existing")


if __name__ == "__main__":
    main()
