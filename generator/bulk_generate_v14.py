"""Wave 14: 35 new canons (436 → ~471)."""

import json
from generator.bulk_generate import (
    canon, de, wa, DATA_DIR,
)


def get_all_canons():
    c = []

    # ── Python ──────────────────────────────────────────────────────────
    c.append(canon(
        "python", "assertionerror", "py311-linux",
        "AssertionError",
        r"AssertionError",
        "assertions", "cpython", ">=3.8", "linux",
        "true", 0.97, 0.98,
        "An assert statement failed — the condition evaluated to False.",
        [de("Removing all assert statements", "Removes valuable runtime checks; bugs surface later and are harder to debug", 0.75),
         de("Running Python with -O flag to skip asserts", "Asserts are disabled globally; used in production this masks bugs", 0.70)],
        [wa("Fix the failing condition — understand why the assertion is False", 0.97, "Add print/logging before the assert to inspect the values"),
         wa("Replace assert with proper validation and error handling for production code", 0.90, "assert is for development-time checks; use if/raise for production validation", sources=["https://docs.python.org/3/reference/simple_stmts.html#the-assert-statement"])],
    ))

    c.append(canon(
        "python", "unicodeencodeerror", "py311-linux",
        "UnicodeEncodeError: 'ascii' codec can't encode characters in position 0-2: ordinal not in range(128)",
        r"UnicodeEncodeError: '(ascii|latin-1|charmap)' codec can't encode",
        "encoding", "cpython", ">=3.8", "linux",
        "true", 0.95, 0.96,
        "Attempting to encode Unicode text with a codec that cannot represent certain characters.",
        [de("Using .encode('ascii', errors='ignore')", "Silently drops characters; corrupts the data", 0.75),
         de("Replacing with .encode('latin-1')", "Only supports 0-255 codepoints; still fails for CJK, emoji, etc.", 0.65)],
        [wa("Use UTF-8 encoding explicitly: text.encode('utf-8')", 0.96, "UTF-8 can represent all Unicode characters", sources=["https://docs.python.org/3/howto/unicode.html"]),
         wa("Set PYTHONIOENCODING=utf-8 for stdout encoding issues", 0.88, "export PYTHONIOENCODING=utf-8 — fixes encoding errors when piping output")],
    ))

    c.append(canon(
        "python", "recursionerror", "py311-linux",
        "RecursionError: maximum recursion depth exceeded",
        r"RecursionError: maximum recursion depth exceeded",
        "runtime", "cpython", ">=3.8", "linux",
        "true", 0.94, 0.95,
        "Function calls itself (or mutually recursive functions) too deeply, exceeding Python's recursion limit.",
        [de("Setting sys.setrecursionlimit(100000)", "Stack overflow will crash Python with a segfault instead of a clean RecursionError", 0.80),
         de("Using @functools.lru_cache to memoize the recursive function", "Only helps if there are overlapping subproblems; doesn't fix infinite recursion", 0.45)],
        [wa("Convert to an iterative approach with an explicit stack", 0.93, "Replace recursion with a while loop and a list used as a stack", sources=["https://docs.python.org/3/library/sys.html#sys.setrecursionlimit"]),
         wa("Fix the base case — infinite recursion usually means the termination condition is wrong", 0.95, "Add logging to see if the recursive calls are converging toward the base case")],
    ))

    c.append(canon(
        "python", "notimplementederror", "py311-linux",
        "NotImplementedError",
        r"NotImplementedError",
        "abstract", "cpython", ">=3.8", "linux",
        "true", 0.97, 0.98,
        "Abstract method called without being overridden in a subclass.",
        [de("Catching NotImplementedError and returning None", "Silently hides unimplemented functionality; consumers get wrong results", 0.80),
         de("Adding pass instead of raise NotImplementedError", "Method appears implemented but does nothing; subtle bugs", 0.70)],
        [wa("Implement the method in the subclass", 0.97, "Override the abstract method with the actual implementation"),
         wa("Use abc.ABC and @abstractmethod to enforce implementation at class creation time", 0.92, "Abstract methods on ABC subclasses raise TypeError on instantiation, not at call time", sources=["https://docs.python.org/3/library/abc.html"])],
    ))

    # ── Node ────────────────────────────────────────────────────────────
    c.append(canon(
        "node", "err-invalid-package-config", "node20-linux",
        "Error [ERR_INVALID_PACKAGE_CONFIG]: Invalid package config",
        r"ERR_INVALID_PACKAGE_CONFIG",
        "packages", "node", ">=16", "linux",
        "true", 0.93, 0.95,
        "package.json is malformed — JSON syntax error or invalid field values.",
        [de("Deleting package.json and running npm init", "Loses all dependency declarations and scripts", 0.85),
         de("Ignoring the error with --force flag", "Dependency resolution will be broken", 0.75)],
        [wa("Validate package.json: npx package-json-validator or use a JSON linter", 0.93, "Check for trailing commas, missing quotes, or duplicate keys"),
         wa("Check the 'exports' field syntax — most common cause of invalid config in modern packages", 0.88, "Exports map must use proper path patterns: './': './index.js'", sources=["https://nodejs.org/api/packages.html#package-entry-points"])],
    ))

    c.append(canon(
        "node", "err-use-after-close", "node20-linux",
        "Error [ERR_USE_AFTER_CLOSE]: This socket has been ended by the other party",
        r"ERR_USE_AFTER_CLOSE|This socket has been ended",
        "streams", "node", ">=14", "linux",
        "true", 0.91, 0.93,
        "Attempting to write to a socket or stream that has already been closed.",
        [de("Wrapping every write in try/catch", "Masks the lifecycle management bug", 0.65),
         de("Keeping a global reference to prevent garbage collection", "Socket is closed by the remote; keeping a reference doesn't reopen it", 0.80)],
        [wa("Check socket.destroyed before writing", 0.90, "if (!socket.destroyed) socket.write(data)"),
         wa("Handle the 'close' and 'end' events to stop writing", 0.93, "socket.on('close', () => { /* stop sending */ })", sources=["https://nodejs.org/api/net.html#class-netsocket"])],
    ))

    c.append(canon(
        "node", "err-fs-eisdir", "node20-linux",
        "Error: EISDIR: illegal operation on a directory, read",
        r"EISDIR: illegal operation on a directory",
        "filesystem", "node", ">=14", "linux",
        "true", 0.97, 0.98,
        "Attempting to read/write a directory as if it were a file.",
        [de("Adding recursive option to the read call", "fs.readFile doesn't support reading directories; recursive is for mkdir/rmdir", 0.80),
         de("Catching the error and skipping", "The file you need isn't being read; the feature is broken", 0.70)],
        [wa("Check if the path is a file: fs.statSync(path).isFile() before reading", 0.95, "Use lstatSync to not follow symlinks"),
         wa("Fix the path to point to the actual file, not its parent directory", 0.97, "Common when path.join or path.resolve produces a directory path instead of file path")],
    ))

    # ── Docker ──────────────────────────────────────────────────────────
    c.append(canon(
        "docker", "copy-failed-stat", "docker24-linux",
        "COPY failed: file not found in build context",
        r"COPY failed.*not found in build context",
        "build", "docker", ">=20.10", "linux",
        "true", 0.96, 0.97,
        "COPY instruction references a file that doesn't exist in the Docker build context.",
        [de("Using absolute host paths in COPY", "Docker COPY only works within the build context; absolute paths are forbidden", 0.90),
         de("Using volume mounts during build", "docker build doesn't support volumes; only RUN, COPY, ADD work", 0.85)],
        [wa("Check .dockerignore — the file may exist but be ignored during context transfer", 0.93, "Remove the file pattern from .dockerignore", sources=["https://docs.docker.com/build/building/context/#dockerignore-files"]),
         wa("Verify the file path is relative to the build context (the directory passed to docker build)", 0.95, "docker build -f Dockerfile . — the '.' is the build context root")],
    ))

    c.append(canon(
        "docker", "cannot-stop-container", "docker24-linux",
        "Error response from daemon: cannot stop container: permission denied",
        r"cannot stop container",
        "runtime", "docker", ">=20.10", "linux",
        "true", 0.90, 0.92,
        "Docker cannot stop a container, often due to a zombie process or AppArmor/SELinux restriction.",
        [de("Using kill -9 on the container PID from the host", "May leave Docker's state inconsistent; container appears running", 0.60),
         de("Rebooting the host", "Disruptive to all running containers and services", 0.85)],
        [wa("Try docker kill <container> for a SIGKILL instead of SIGTERM", 0.90, "docker stop sends SIGTERM; docker kill sends SIGKILL"),
         wa("Check AppArmor/SELinux: dmesg | grep -i deny for policy blocks", 0.85, "SELinux or AppArmor may prevent container signal delivery", sources=["https://docs.docker.com/engine/security/apparmor/"])],
    ))

    # ── Git ──────────────────────────────────────────────────────────────
    c.append(canon(
        "git", "would-clobber-existing-tag", "git2-linux",
        "fatal: tag 'v1.0.0' already exists",
        r"tag '.*' already exists",
        "tags", "git", ">=2.20", "linux",
        "true", 0.97, 0.98,
        "Attempting to create a tag that already exists.",
        [de("Deleting the tag and recreating", "If already pushed, other clones still have the old tag pointing to the old commit", 0.55),
         de("Using git tag -f to force-update", "Changes tag for you locally but remote and others still have the old one", 0.50)],
        [wa("Use a different tag name: v1.0.1 or v1.0.0-rc2", 0.93, "Semantic versioning should increment, not reuse tags"),
         wa("If you need to move the tag: git tag -d <tag> && git push origin :refs/tags/<tag> && git tag <tag> && git push origin <tag>", 0.88, "Deletes locally and remotely, then recreates — communicate to team", sources=["https://git-scm.com/docs/git-tag"])],
    ))

    c.append(canon(
        "git", "cannot-fast-forward", "git2-linux",
        "fatal: Not possible to fast-forward, aborting.",
        r"Not possible to fast-forward",
        "merge", "git", ">=2.20", "linux",
        "true", 0.96, 0.97,
        "git pull with --ff-only fails because the remote branch has diverged.",
        [de("Using git push -f to overwrite remote", "Destroys remote history; other collaborators lose work", 0.90),
         de("Deleting the local branch and re-checking out", "Loses local unpushed commits", 0.80)],
        [wa("Use git pull --rebase to replay local commits on top of remote", 0.95, "git pull --rebase origin main — creates linear history", sources=["https://git-scm.com/docs/git-pull#_rebase"]),
         wa("Use git pull (merge) if you want a merge commit", 0.90, "git pull origin main — creates a merge commit preserving both histories")],
    ))

    # ── TypeScript ──────────────────────────────────────────────────────
    c.append(canon(
        "typescript", "ts2532-object-possibly-undefined", "ts5-linux",
        "error TS2532: Object is possibly 'undefined'",
        r"TS2532.*Object is possibly 'undefined'",
        "strictness", "tsc", ">=4.5", "linux",
        "true", 0.97, 0.98,
        "Strict null checks detect that a value could be undefined at the point of use.",
        [de("Using the non-null assertion operator (!) everywhere", "Tells TypeScript 'trust me' — runtime errors when wrong", 0.75),
         de("Disabling strictNullChecks", "Disables a critical safety feature; null/undefined bugs become runtime crashes", 0.85)],
        [wa("Add a null/undefined check: if (obj !== undefined) { obj.method() }", 0.97, "Narrows the type and satisfies the compiler", sources=["https://www.typescriptlang.org/docs/handbook/2/narrowing.html"]),
         wa("Use optional chaining: obj?.method() ?? defaultValue", 0.93, "Safely accesses properties and provides a fallback")],
    ))

    c.append(canon(
        "typescript", "ts2769-no-overload-matches", "ts5-linux",
        "error TS2769: No overload matches this call",
        r"TS2769.*No overload matches this call",
        "type-checking", "tsc", ">=4.5", "linux",
        "true", 0.94, 0.95,
        "Arguments don't match any of the function's overload signatures.",
        [de("Adding 'as any' to all arguments", "Bypasses type checking completely; defeats the purpose of overloads", 0.80),
         de("Removing the overload signatures", "Changes the function's type contract; may break other callers", 0.70)],
        [wa("Check each overload signature and match your arguments to the correct one", 0.93, "Hover over the function in your IDE to see all overloads"),
         wa("If passing an object literal, ensure all properties match exactly — no extra properties", 0.88, "TypeScript's excess property checking is strict on object literals")],
    ))

    # ── Rust ────────────────────────────────────────────────────────────
    c.append(canon(
        "rust", "e0106-missing-lifetime", "rust1-linux",
        "error[E0106]: missing lifetime specifier",
        r"E0106.*missing lifetime specifier",
        "lifetimes", "rustc", ">=1.60", "linux",
        "true", 0.92, 0.94,
        "Function returns a reference but Rust cannot determine which input lifetime to use.",
        [de("Using 'static lifetime for everything", "'static means the reference lives forever; rarely correct for function returns", 0.75),
         de("Using Box<dyn Trait> to avoid lifetime annotations", "Allocates on heap; unnecessary overhead for simple references", 0.55)],
        [wa("Add explicit lifetime annotations: fn foo<'a>(x: &'a str) -> &'a str", 0.95, "Tells Rust the output reference lives as long as the input", sources=["https://doc.rust-lang.org/book/ch10-03-lifetime-syntax.html"]),
         wa("If returning owned data, return String instead of &str", 0.90, "Owned types don't need lifetime annotations; consider if ownership transfer makes sense")],
    ))

    c.append(canon(
        "rust", "e0507-cannot-move-out-of-borrowed", "rust1-linux",
        "error[E0507]: cannot move out of borrowed content",
        r"E0507.*cannot move out of.*borrow",
        "ownership", "rustc", ">=1.60", "linux",
        "true", 0.93, 0.95,
        "Attempting to move a value out of a borrowed reference, which would leave the reference dangling.",
        [de("Using unsafe to force the move", "Creates a dangling reference; undefined behavior", 0.95),
         de("Using mem::replace with Default to swap out", "Only works if the type implements Default; may leave invalid state", 0.50)],
        [wa("Clone the value: let owned = borrowed_ref.field.clone()", 0.92, "Creates an independent copy that can be moved freely", sources=["https://doc.rust-lang.org/book/ch04-02-references-and-borrowing.html"]),
         wa("Take ownership by consuming the struct: fn consume(self) -> Field", 0.88, "Change from &self to self to take ownership and decompose")],
    ))

    # ── Go ──────────────────────────────────────────────────────────────
    c.append(canon(
        "go", "slice-bounds-out-of-range", "go121-linux",
        "runtime error: index out of range [5] with length 3",
        r"(index out of range|slice bounds out of range)",
        "runtime", "go", ">=1.18", "linux",
        "true", 0.97, 0.98,
        "Array/slice index exceeds its length.",
        [de("Using recover() to catch the panic", "Masks the bug; the slice access logic is wrong", 0.70),
         de("Pre-allocating a very large slice", "Wastes memory; doesn't fix the indexing logic", 0.80)],
        [wa("Add bounds checking: if i < len(slice) { ... }", 0.97, "Check index before accessing"),
         wa("Use range-based for loop to avoid manual indexing", 0.93, "for i, v := range slice { ... } — cannot go out of bounds", sources=["https://go.dev/tour/moretypes/16"])],
    ))

    c.append(canon(
        "go", "declared-not-used", "go121-linux",
        "declared and not used",
        r"declared (and|but) not used",
        "compilation", "go", ">=1.18", "linux",
        "true", 0.99, 0.99,
        "Go does not allow unused variables — a variable was declared but never read.",
        [de("Assigning to a throwaway: _ = unused", "Suppresses the error but why declare it?", 0.40),
         de("Moving the declaration to a different scope", "Doesn't fix it; still unused in the new scope", 0.80)],
        [wa("Remove the unused variable declaration", 0.97, "If you don't need it, delete it"),
         wa("Use _ for intentionally discarded values: _, err := fn()", 0.95, "The blank identifier _ explicitly discards a value", sources=["https://go.dev/doc/effective_go#blank"])],
    ))

    # ── Kubernetes ──────────────────────────────────────────────────────
    c.append(canon(
        "kubernetes", "service-has-no-endpoints", "k8s128-linux",
        "endpoints for service not found",
        r"(endpoints.*not found|service has no endpoints)",
        "networking", "kubernetes", ">=1.24", "linux",
        "true", 0.93, 0.95,
        "Service has no matching pods — selector doesn't match any pod labels, or pods aren't ready.",
        [de("Removing the selector from the Service", "Creates a Service with no backends; all requests fail", 0.85),
         de("Adding a manual Endpoints resource", "Fragile; must be manually updated when pods change", 0.60)],
        [wa("Verify selectors match: kubectl get pods --selector=app=myapp", 0.95, "Service selector must match pod labels exactly", sources=["https://kubernetes.io/docs/concepts/services-networking/service/"]),
         wa("Check if pods are Ready: kubectl get pods -o wide — unready pods aren't added to endpoints", 0.90, "Pods must pass readiness probes to receive traffic")],
    ))

    c.append(canon(
        "kubernetes", "configmap-not-found", "k8s128-linux",
        "Error: configmaps 'my-config' not found",
        r"configmaps?.*not found",
        "config", "kubernetes", ">=1.24", "linux",
        "true", 0.96, 0.97,
        "Pod references a ConfigMap that doesn't exist in the same namespace.",
        [de("Creating an empty ConfigMap to satisfy the reference", "Pod starts but gets empty config; may crash on missing keys", 0.55),
         de("Making the ConfigMap reference optional without checking implications", "optional: true means the pod starts without the config — may misbehave silently", 0.50)],
        [wa("Create the ConfigMap: kubectl create configmap my-config --from-file=config.yaml", 0.96, "Create before deploying the pod that references it", sources=["https://kubernetes.io/docs/concepts/configuration/configmap/"]),
         wa("Check the namespace: ConfigMaps are namespace-scoped — kubectl get configmap -n <namespace>", 0.92, "The ConfigMap and Pod must be in the same namespace")],
    ))

    # ── Terraform ───────────────────────────────────────────────────────
    c.append(canon(
        "terraform", "unsupported-attribute", "tf115-linux",
        "Error: Unsupported attribute",
        r"Unsupported attribute",
        "config", "terraform", ">=1.0", "linux",
        "true", 0.94, 0.96,
        "Referencing an attribute that doesn't exist on the resource or data source.",
        [de("Using try() function to suppress the error", "Silently returns null; downstream resources get wrong values", 0.65),
         de("Adding a variable with the same name", "Variables and resource attributes are different namespaces", 0.80)],
        [wa("Check the provider documentation for available attributes", 0.95, "Use terraform providers schema to list all attributes", sources=["https://developer.hashicorp.com/terraform/cli/commands/providers/schema"]),
         wa("For nested attributes, check the correct nesting syntax: resource.name.block[0].attr", 0.88, "Terraform 0.12+ changed nested block access syntax")],
    ))

    c.append(canon(
        "terraform", "invalid-count-argument", "tf115-linux",
        "Error: Invalid count argument: count.index is not valid in this context",
        r"Invalid count argument|count\.index.*not valid",
        "meta-arguments", "terraform", ">=1.0", "linux",
        "true", 0.95, 0.96,
        "Using count.index outside of a resource that has count, or mixing count with for_each.",
        [de("Using both count and for_each on the same resource", "Terraform doesn't allow both; pick one", 0.90),
         de("Setting count = 0 to skip the resource", "Works but prevents use of count.index in any expressions", 0.40)],
        [wa("Use for_each with a map/set instead of count for complex scenarios", 0.93, "for_each provides each.key and each.value for more control", sources=["https://developer.hashicorp.com/terraform/language/meta-arguments/for_each"]),
         wa("Ensure count is set on the resource block before using count.index", 0.95, "count.index is only valid inside resources/modules with count defined")],
    ))

    # ── AWS ──────────────────────────────────────────────────────────────
    c.append(canon(
        "aws", "s3-nosuchbucket", "aws-cli2-linux",
        "An error occurred (NoSuchBucket) when calling the ListObjects operation: The specified bucket does not exist",
        r"NoSuchBucket",
        "s3", "aws", ">=2.0", "linux",
        "true", 0.97, 0.98,
        "The S3 bucket doesn't exist or the name is wrong.",
        [de("Creating a new bucket with the same name", "S3 bucket names are globally unique; may be taken", 0.50),
         de("Changing the bucket policy", "Bucket doesn't exist; no policy to change", 0.90)],
        [wa("Verify the bucket name: aws s3 ls — check for typos (names are case-sensitive, lowercase only)", 0.96, "S3 bucket names must be globally unique and DNS-compliant", sources=["https://docs.aws.amazon.com/AmazonS3/latest/userguide/bucketnamingrules.html"]),
         wa("Check the region — S3 bucket names are global but access may require the correct region endpoint", 0.90, "Use --region flag: aws s3 ls s3://bucket --region us-west-2")],
    ))

    c.append(canon(
        "aws", "cognito-user-not-confirmed", "aws-cli2-linux",
        "An error occurred (UserNotConfirmedException) when calling the InitiateAuth operation",
        r"UserNotConfirmedException",
        "cognito", "aws", ">=2.0", "linux",
        "true", 0.95, 0.96,
        "Cognito user exists but hasn't confirmed their email/phone.",
        [de("Deleting and recreating the user", "Loses any associated data; user must re-register", 0.70),
         de("Disabling email verification on the user pool", "Removes a security measure; can't retroactively confirm existing users", 0.75)],
        [wa("Resend confirmation code: aws cognito-idp resend-confirmation-code --client-id <id> --username <user>", 0.93, "User receives a new code to confirm their account", sources=["https://docs.aws.amazon.com/cognito/latest/developerguide/signing-up-users-in-your-app.html"]),
         wa("Admin-confirm the user: aws cognito-idp admin-confirm-sign-up --user-pool-id <id> --username <user>", 0.90, "Bypasses the confirmation flow — useful for testing or support")],
    ))

    # ── Next.js ──────────────────────────────────────────────────────────
    c.append(canon(
        "nextjs", "next-image-unconfigured-host", "next14-linux",
        "Error: Invalid src prop on `next/image`, hostname is not configured",
        r"Invalid src prop.*next/image.*hostname.*not configured",
        "images", "next.js", ">=13", "linux",
        "true", 0.97, 0.98,
        "next/image requires explicit allowlist of external image hostnames.",
        [de("Using a regular <img> tag instead", "Loses Next.js image optimization (lazy loading, resizing, WebP)", 0.55),
         de("Setting unoptimized={true} on the Image component", "Disables all optimization; images are served as-is", 0.50)],
        [wa("Add the hostname to next.config.js images.remotePatterns", 0.97, "images: { remotePatterns: [{ hostname: 'example.com' }] }", sources=["https://nextjs.org/docs/app/api-reference/components/image#remotepatterns"]),
         wa("For all subdomains, use a wildcard: { hostname: '**.example.com' }", 0.88, "Wildcard patterns match any subdomain")],
    ))

    c.append(canon(
        "nextjs", "streaming-not-supported", "next14-linux",
        "Error: Invariant: headers() expects to have requestAsyncStorage",
        r"(requestAsyncStorage|headers\(\) expects|cookies\(\) expects)",
        "server-components", "next.js", ">=13.4", "linux",
        "true", 0.90, 0.92,
        "Calling headers()/cookies() outside of a request context — usually in a cached or generated page.",
        [de("Wrapping in try/catch and returning empty headers", "Silently returns wrong data; features depending on headers break", 0.70),
         de("Moving to middleware", "Middleware is for request routing, not data fetching", 0.60)],
        [wa("Ensure the function is called within a request context — mark the page as dynamic", 0.93, "export const dynamic = 'force-dynamic'", sources=["https://nextjs.org/docs/app/api-reference/file-conventions/route-segment-config"]),
         wa("Pass headers as props from a parent Server Component that has request context", 0.85, "const h = headers(); return <Child headerValue={h.get('x-custom')} />")],
    ))

    # ── React ────────────────────────────────────────────────────────────
    c.append(canon(
        "react", "each-child-unique-key", "react18-linux",
        "Warning: Each child in a list should have a unique 'key' prop",
        r"Each child in a list should have a unique.*key.*prop",
        "rendering", "react", ">=17", "linux",
        "true", 0.98, 0.99,
        "React needs unique keys on list elements for efficient reconciliation.",
        [de("Using Math.random() as key", "Different key every render; React recreates all DOM nodes every time", 0.85),
         de("Using array index as key with reorderable lists", "Index keys cause bugs when items are reordered, deleted, or inserted", 0.65)],
        [wa("Use a stable unique identifier from the data: key={item.id}", 0.97, "Database IDs, UUIDs, or other stable identifiers are ideal", sources=["https://react.dev/learn/rendering-lists#keeping-list-items-in-order-with-key"]),
         wa("Index keys are OK if the list is static (never reordered/filtered): key={index}", 0.80, "Only use index when the list is display-only and items never change order")],
    ))

    # ── CUDA ─────────────────────────────────────────────────────────────
    c.append(canon(
        "cuda", "all-cuda-capable-devices-busy", "cuda12-linux",
        "RuntimeError: CUDA error: all CUDA-capable devices are busy or unavailable",
        r"all CUDA-capable devices are busy or unavailable",
        "device", "cuda", ">=11.0", "linux",
        "true", 0.88, 0.90,
        "All GPUs are in use by other processes or the CUDA driver failed to initialize.",
        [de("Killing all GPU processes with nvidia-smi --gpu-reset", "May corrupt running training jobs; data loss", 0.75),
         de("Restarting the CUDA driver", "Requires root; kills all GPU processes", 0.70)],
        [wa("Check GPU usage: nvidia-smi — identify which processes are using the GPUs", 0.93, "Look for processes with high memory usage that can be stopped safely"),
         wa("Set CUDA_VISIBLE_DEVICES to use a specific free GPU", 0.90, "export CUDA_VISIBLE_DEVICES=1 — restricts to GPU 1 only", sources=["https://docs.nvidia.com/cuda/cuda-c-programming-guide/index.html#env-vars"])],
    ))

    # ── pip ──────────────────────────────────────────────────────────────
    c.append(canon(
        "pip", "hash-mismatch", "pip23-linux",
        "ERROR: THESE PACKAGES DO NOT MATCH THE HASHES FROM THE REQUIREMENTS FILE",
        r"(PACKAGES DO NOT MATCH THE HASHES|hash mismatch)",
        "security", "pip", ">=22.0", "linux",
        "true", 0.93, 0.95,
        "Package hash doesn't match what's recorded in requirements file — corrupted download or changed package.",
        [de("Using --no-cache-dir and retrying", "If the hash in requirements is wrong, cache doesn't matter", 0.50),
         de("Removing the hash from requirements.txt", "Disables hash verification for that package; supply chain risk", 0.70)],
        [wa("Regenerate hashes: pip-compile --generate-hashes to update hash values", 0.93, "pip-compile creates a fresh requirements.txt with correct hashes", sources=["https://github.com/jazzband/pip-tools"]),
         wa("Clear the pip cache and retry: pip cache purge && pip install -r requirements.txt", 0.88, "A corrupted cached download may cause the mismatch")],
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
    print(f"Wave 14: wrote {written} new canons, skipped {skipped} existing")


if __name__ == "__main__":
    main()
