"""Wave 12: 40 new canons (397 → ~437)."""

import json
from generator.bulk_generate import (
    canon, de, wa, DATA_DIR,
)


def get_all_canons():
    c = []

    # ── Python ──────────────────────────────────────────────────────────
    c.append(canon(
        "python", "valueerror-too-many-values-unpack", "py311-linux",
        "ValueError: too many values to unpack (expected 2)",
        r"ValueError: too many values to unpack \(expected \d+\)",
        "unpacking", "cpython", ">=3.8", "linux",
        "true", 0.98, 0.98,
        "Iterable yields more values than the target variables in an unpacking assignment.",
        [de("Adding more variables blindly to match", "May mismatch data structure if it varies in length", 0.50),
         de("Wrapping in try/except ValueError", "Hides data format bugs", 0.70)],
        [wa("Use starred assignment to capture extras: a, b, *rest = iterable", 0.95, "Captures remaining elements in a list", sources=["https://docs.python.org/3/tutorial/datastructures.html#tuples-and-sequences"]),
         wa("Inspect the data to understand its actual shape before unpacking", 0.90, "print(len(data), data[:5]) to see what you're unpacking")],
    ))

    c.append(canon(
        "python", "zerodivisionerror", "py311-linux",
        "ZeroDivisionError: division by zero",
        r"ZeroDivisionError: (division|integer division or modulo) by zero",
        "arithmetic", "cpython", ">=3.8", "linux",
        "true", 0.99, 0.99,
        "Division operation where the denominator is zero.",
        [de("Setting denominator to 1 as default", "Silently produces wrong results when denominator is legitimately zero", 0.65),
         de("Using try/except to return 0 on division error", "Zero may not be the correct result; masks data issues", 0.55)],
        [wa("Guard with an explicit check: if denominator != 0: ... else: handle", 0.98, "Choose the appropriate fallback for your domain"),
         wa("Use math.inf or float('inf') when division by zero means infinity in your domain", 0.80, "import math; result = math.inf if denom == 0 else num / denom")],
    ))

    c.append(canon(
        "python", "stopiteration", "py311-linux",
        "StopIteration",
        r"StopIteration",
        "iterator", "cpython", ">=3.8", "linux",
        "true", 0.96, 0.97,
        "next() called on an exhausted iterator without a default value.",
        [de("Catching StopIteration inside a generator (pre PEP 479)", "Since Python 3.7 StopIteration inside generators becomes RuntimeError", 0.80, sources=["https://peps.python.org/pep-0479/"]),
         de("Resetting the iterator by reassigning", "Creates a new iterator, doesn't rewind the original", 0.45)],
        [wa("Use next(iterator, default) to provide a fallback value", 0.96, "next(iter([]), None) returns None instead of raising StopIteration"),
         wa("Use a for loop instead of manual next() calls", 0.93, "for item in iterator: ... handles StopIteration automatically")],
    ))

    c.append(canon(
        "python", "lookuperror-unknown-encoding", "py311-linux",
        "LookupError: unknown encoding: utf8mb4",
        r"LookupError: unknown encoding:",
        "encoding", "cpython", ">=3.8", "linux",
        "true", 0.95, 0.96,
        "Python codec registry does not recognize the encoding name, often a MySQL-specific encoding passed to Python.",
        [de("Installing a third-party codec package", "utf8mb4 is MySQL-only; Python's utf-8 handles the same bytes", 0.70),
         de("Monkey-patching codecs module", "Fragile and breaks other encoding operations", 0.85)],
        [wa("Map MySQL encodings to Python equivalents: utf8mb4 → utf-8", 0.95, "encoding = 'utf-8' if encoding == 'utf8mb4' else encoding"),
         wa("Set charset='utf8' in MySQL connection params instead of utf8mb4", 0.88, "Python MySQL drivers handle the conversion automatically")],
    ))

    c.append(canon(
        "python", "permissionerror-errno13", "py311-linux",
        "PermissionError: [Errno 13] Permission denied",
        r"PermissionError: \[Errno 13\] Permission denied",
        "filesystem", "cpython", ">=3.8", "linux",
        "true", 0.94, 0.96,
        "Process lacks permissions to read, write, or execute the target file/directory.",
        [de("Running everything as root/sudo", "Security risk; masks permission design issues", 0.85),
         de("Setting chmod 777 on the file", "World-writable files are a security vulnerability", 0.90)],
        [wa("Fix ownership: chown user:group file, then set appropriate permissions (644 for files, 755 for dirs)", 0.95, "Match the process user to file ownership", sources=["https://man7.org/linux/man-pages/man1/chmod.1.html"]),
         wa("Use a directory where the process has write access, like /tmp or a user-owned path", 0.88, "Redirect output to os.path.expanduser('~') or tempfile.mkdtemp()")],
    ))

    # ── Node ────────────────────────────────────────────────────────────
    c.append(canon(
        "node", "err-unknown-file-extension-ts", "node20-linux",
        "TypeError [ERR_UNKNOWN_FILE_EXTENSION]: Unknown file extension '.ts'",
        r"ERR_UNKNOWN_FILE_EXTENSION.*\.ts",
        "esm", "node", ">=18", "linux",
        "true", 0.94, 0.95,
        "Node.js cannot load .ts files natively; requires a loader or transpilation step.",
        [de("Adding type: module to package.json", "Node still doesn't understand .ts syntax; only changes module system", 0.80),
         de("Renaming .ts files to .js", "Loses TypeScript type checking entirely", 0.85)],
        [wa("Use tsx: npx tsx script.ts or register: node --import tsx script.ts", 0.95, "tsx is a fast TypeScript loader for Node.js", sources=["https://github.com/privatenumber/tsx"]),
         wa("Use ts-node with ESM loader: node --loader ts-node/esm script.ts", 0.88, "Requires tsconfig with module: nodenext or esnext")],
    ))

    c.append(canon(
        "node", "err-package-path-not-exported", "node20-linux",
        "Error [ERR_PACKAGE_PATH_NOT_EXPORTED]: Package subpath './internal' is not defined by exports",
        r"ERR_PACKAGE_PATH_NOT_EXPORTED.*not defined by.*exports",
        "esm", "node", ">=16", "linux",
        "true", 0.92, 0.94,
        "Importing a subpath that the package's exports map doesn't expose.",
        [de("Patching node_modules to add the export", "Will be overwritten on next npm install", 0.90),
         de("Using require.resolve with custom paths", "Bypasses package boundaries; may break with updates", 0.70)],
        [wa("Use the package's public API — check its package.json exports field for available paths", 0.93, "Import from the documented public paths, not internal modules"),
         wa("If the subpath was previously available, check the changelog for migration instructions", 0.85, "The maintainer likely moved it or removed it intentionally in a major version")],
    ))

    c.append(canon(
        "node", "err-import-assertion-type-missing", "node20-linux",
        "TypeError [ERR_IMPORT_ASSERTION_TYPE_MISSING]: Module needs an import attribute of type 'json'",
        r"ERR_IMPORT_ASSERTION_TYPE_MISSING",
        "esm", "node", ">=17.1", "linux",
        "true", 0.95, 0.96,
        "Importing a JSON module without the required import assertion in ESM mode.",
        [de("Converting the JSON file to a .js module that exports the data", "Extra build step; breaks co-located config patterns", 0.60),
         de("Switching back to CommonJS to use require()", "Loses ESM benefits for the whole project", 0.70)],
        [wa("Add import assertion: import data from './data.json' with { type: 'json' }", 0.96, "Node 20+ uses 'with' syntax; older versions use 'assert'", sources=["https://nodejs.org/api/esm.html#import-attributes"]),
         wa("Use fs.readFileSync + JSON.parse as an alternative", 0.88, "const data = JSON.parse(fs.readFileSync('./data.json', 'utf-8'))")],
    ))

    c.append(canon(
        "node", "err-socket-connection-refused", "node20-linux",
        "Error: connect ECONNREFUSED 127.0.0.1:3000",
        r"(ECONNREFUSED|connect ECONNREFUSED)",
        "network", "node", ">=14", "linux",
        "true", 0.95, 0.96,
        "TCP connection refused — the target server is not running or not listening on the expected port.",
        [de("Increasing timeout values", "The server is not running; waiting longer won't help", 0.85),
         de("Switching to a different HTTP client library", "The problem is the server, not the client", 0.90)],
        [wa("Verify the target server is running and listening on the expected host:port", 0.96, "Check with: ss -tlnp | grep 3000 or curl http://localhost:3000"),
         wa("Check if the port is correct and not bound to a different interface", 0.90, "Server may be listening on 0.0.0.0 vs 127.0.0.1 vs specific IP")],
    ))

    # ── Docker ──────────────────────────────────────────────────────────
    c.append(canon(
        "docker", "network-has-active-endpoints", "docker24-linux",
        "error: network has active endpoints",
        r"network.*has active endpoints",
        "networking", "docker", ">=20.10", "linux",
        "true", 0.94, 0.95,
        "Cannot remove a Docker network because containers are still connected to it.",
        [de("Force-removing the network", "May orphan container networking; containers lose connectivity", 0.70),
         de("Restarting Docker daemon", "Disruptive to all running containers", 0.80)],
        [wa("Disconnect all containers first: docker network disconnect -f <network> <container>", 0.95, "Then docker network rm <network> succeeds", sources=["https://docs.docker.com/reference/cli/docker/network/disconnect/"]),
         wa("Stop the containers using the network first, then remove it", 0.93, "docker compose down removes networks and containers together")],
    ))

    c.append(canon(
        "docker", "bind-address-already-in-use", "docker24-linux",
        "Error starting userland proxy: listen tcp4 0.0.0.0:80: bind: address already in use",
        r"bind: address already in use",
        "networking", "docker", ">=20.10", "linux",
        "true", 0.96, 0.97,
        "Host port is already occupied by another process or container.",
        [de("Killing random processes on the port", "May kill a critical service", 0.60),
         de("Disabling the host firewall", "Unrelated to port binding; security risk", 0.90)],
        [wa("Find the process using the port: ss -tlnp | grep :80 or lsof -i :80", 0.96, "Then stop the process or use a different port", sources=["https://man7.org/linux/man-pages/man8/ss.8.html"]),
         wa("Change the port mapping in Docker: -p 8080:80 instead of -p 80:80", 0.93, "Map to an available host port while keeping the container port the same")],
    ))

    c.append(canon(
        "docker", "context-canceled", "docker24-linux",
        "failed to solve: context canceled",
        r"failed to solve.*context canceled",
        "build", "docker", ">=20.10", "linux",
        "true", 0.88, 0.90,
        "Docker build was interrupted — usually Ctrl+C, OOM kill, or buildkit timeout.",
        [de("Increasing Docker memory limit without checking actual usage", "If the build legitimately needs more memory, this helps; but often it's a build cache issue", 0.50),
         de("Switching from buildkit to legacy builder", "Legacy builder is deprecated and slower", 0.75)],
        [wa("Clear build cache and retry: docker builder prune -f && docker build .", 0.90, "Stale cache layers can cause hangs that lead to cancellation"),
         wa("Check Docker daemon memory: docker system info and increase if needed", 0.85, "OOM kills appear as context canceled in buildkit logs")],
    ))

    # ── Git ──────────────────────────────────────────────────────────────
    c.append(canon(
        "git", "error-failed-to-push-some-refs", "git2-linux",
        "error: failed to push some refs to 'origin'",
        r"failed to push some refs",
        "remote", "git", ">=2.20", "linux",
        "true", 0.97, 0.98,
        "Remote has commits that the local branch doesn't — need to pull before pushing.",
        [de("Force pushing: git push -f", "Overwrites remote history; other collaborators' work may be lost", 0.90),
         de("Deleting the remote branch and pushing fresh", "Loses all remote-only commits and breaks other clones", 0.95)],
        [wa("Pull and rebase: git pull --rebase origin <branch> then git push", 0.96, "Replays your commits on top of remote changes", sources=["https://git-scm.com/docs/git-pull#_rebase"]),
         wa("Pull with merge: git pull origin <branch> then git push", 0.94, "Creates a merge commit combining local and remote changes")],
    ))

    c.append(canon(
        "git", "not-a-git-repository", "git2-linux",
        "fatal: not a git repository (or any of the parent directories): .git",
        r"not a git repository",
        "init", "git", ">=2.0", "linux",
        "true", 0.99, 0.99,
        "Running git commands outside of a git repository.",
        [de("Creating .git directory manually", "Corrupt empty .git directory won't function as a repo", 0.90),
         de("Setting GIT_DIR environment variable globally", "Affects all git operations system-wide", 0.85)],
        [wa("Initialize a new repo: git init", 0.95, "Creates a new .git directory in the current folder", sources=["https://git-scm.com/docs/git-init"]),
         wa("Navigate to the correct directory that contains the .git folder", 0.97, "You may be in a subdirectory that's not part of any repo")],
    ))

    c.append(canon(
        "git", "pathspec-did-not-match", "git2-linux",
        "error: pathspec 'branch-name' did not match any file(s) known to git",
        r"pathspec.*did not match any file",
        "checkout", "git", ">=2.20", "linux",
        "true", 0.96, 0.97,
        "Git cannot find the branch, tag, or file path specified in the command.",
        [de("Creating the branch locally with the same name", "May create an unrelated branch that doesn't track the remote", 0.55),
         de("Using --force to override", "checkout --force doesn't create branches; still fails", 0.85)],
        [wa("Fetch from remote first: git fetch origin then git checkout <branch>", 0.96, "Remote branches must be fetched before they can be checked out", sources=["https://git-scm.com/docs/git-fetch"]),
         wa("Check exact branch name: git branch -a to list all local and remote branches", 0.93, "Branch names are case-sensitive; verify spelling")],
    ))

    # ── TypeScript ──────────────────────────────────────────────────────
    c.append(canon(
        "typescript", "ts2307-cannot-find-module", "ts5-linux",
        "error TS2307: Cannot find module '@/components/Button' or its corresponding type declarations",
        r"TS2307.*Cannot find module",
        "module-resolution", "tsc", ">=4.5", "linux",
        "true", 0.95, 0.96,
        "TypeScript cannot resolve the import path — missing module, wrong path alias config, or missing type declarations.",
        [de("Adding skipLibCheck: true", "Skips type checking of .d.ts files but doesn't fix module resolution", 0.75),
         de("Adding // @ts-ignore above every import", "Silences all errors on those lines including real bugs", 0.85)],
        [wa("Configure paths in tsconfig.json to match your bundler's path aliases", 0.95, "Add paths: { '@/*': ['./src/*'] } and baseUrl: '.'", sources=["https://www.typescriptlang.org/tsconfig#paths"]),
         wa("Install the missing type declarations: npm install -D @types/<package>", 0.90, "Many npm packages need separate @types/ packages for TypeScript")],
    ))

    c.append(canon(
        "typescript", "ts2322-type-not-assignable", "ts5-linux",
        "error TS2322: Type 'string' is not assignable to type 'number'",
        r"TS2322.*Type.*is not assignable to type",
        "type-checking", "tsc", ">=4.5", "linux",
        "true", 0.97, 0.98,
        "Assigning a value of the wrong type to a variable or property.",
        [de("Using 'as unknown as TargetType' double assertion", "Bypasses type safety completely; runtime errors will follow", 0.85),
         de("Changing the variable type to 'any'", "Removes type checking for that variable and all its usages", 0.80)],
        [wa("Fix the value to match the expected type, or convert it properly", 0.97, "Use Number(str) or parseInt(str, 10) to convert string to number"),
         wa("Widen the type if both types are valid: field: string | number", 0.88, "Union types allow multiple valid types for a single field")],
    ))

    # ── Rust ────────────────────────────────────────────────────────────
    c.append(canon(
        "rust", "e0277-trait-not-implemented", "rust1-linux",
        "error[E0277]: the trait bound `MyType: Send` is not satisfied",
        r"E0277.*the trait bound.*is not satisfied",
        "trait-system", "rustc", ">=1.60", "linux",
        "true", 0.92, 0.94,
        "A type doesn't implement a required trait, commonly Send/Sync for async or Display for formatting.",
        [de("Using unsafe impl Send for MyType {}", "Lying to the compiler about thread safety causes data races", 0.95),
         de("Removing the async requirement", "May require major architectural changes just to avoid a trait bound", 0.60)],
        [wa("Implement the required trait: impl Send for MyType if the type is actually safe to send", 0.85, "Only if all fields are Send — verify before implementing"),
         wa("Wrap non-Send types in Arc<Mutex<T>> for shared ownership across threads", 0.90, "Arc<Mutex<T>> is Send + Sync if T is Send", sources=["https://doc.rust-lang.org/book/ch16-03-shared-state.html"])],
    ))

    c.append(canon(
        "rust", "e0599-no-method-named", "rust1-linux",
        "error[E0599]: no method named `foo` found for struct `Bar` in the current scope",
        r"E0599.*no method named.*found for",
        "methods", "rustc", ">=1.60", "linux",
        "true", 0.95, 0.96,
        "Calling a method that doesn't exist on the type, or the trait providing the method isn't in scope.",
        [de("Adding a blanket impl for the method on all types", "Overly broad; conflicts with existing implementations", 0.80),
         de("Casting to a different type that has the method", "Unsafe and lossy; the types may not be compatible", 0.75)],
        [wa("Bring the trait into scope: use SomeTrait; at the top of the file", 0.93, "Methods from traits are only available when the trait is imported", sources=["https://doc.rust-lang.org/book/ch10-02-traits.html"]),
         wa("Check the type's documentation for the correct method name or trait", 0.90, "Method may be named differently or require a different trait")],
    ))

    # ── Go ──────────────────────────────────────────────────────────────
    c.append(canon(
        "go", "cannot-use-as-type", "go121-linux",
        "cannot use x (variable of type T) as type U in argument",
        r"cannot use.*as type.*in (argument|assignment|return)",
        "type-system", "go", ">=1.18", "linux",
        "true", 0.96, 0.97,
        "Go strict type system rejects assignment or argument because types don't match, even if they're structurally similar.",
        [de("Using unsafe.Pointer to convert between types", "Bypasses type safety; leads to memory corruption if types differ", 0.90),
         de("Adding type conversion without checking compatibility", "Some conversions compile but lose data (e.g., int64 to int32)", 0.55)],
        [wa("Use explicit type conversion: U(x) if the types are convertible", 0.95, "Go allows conversion between compatible types like int32(x) or string(b)", sources=["https://go.dev/ref/spec#Conversions"]),
         wa("Implement the required interface on the type", 0.88, "If the target is an interface, add the missing methods to your type")],
    ))

    c.append(canon(
        "go", "import-cycle-not-allowed", "go121-linux",
        "import cycle not allowed",
        r"import cycle not allowed",
        "packages", "go", ">=1.18", "linux",
        "true", 0.92, 0.94,
        "Go packages have a circular dependency — package A imports B and B imports A.",
        [de("Merging the packages into one", "Creates a monolithic package; violates separation of concerns", 0.55),
         de("Using go:linkname to access unexported symbols", "Compiler directive abuse; breaks with Go updates", 0.90)],
        [wa("Extract shared types/interfaces into a third package imported by both", 0.95, "Create a types or models package with the shared definitions", sources=["https://go.dev/doc/effective_go#package-names"]),
         wa("Use interfaces to break the dependency: depend on abstractions, not implementations", 0.90, "Package A defines an interface; package B implements it")],
    ))

    # ── Kubernetes ──────────────────────────────────────────────────────
    c.append(canon(
        "kubernetes", "oomkilled", "k8s128-linux",
        "OOMKilled",
        r"OOMKilled",
        "resources", "kubernetes", ">=1.24", "linux",
        "true", 0.93, 0.95,
        "Container exceeded its memory limit and was killed by the OOM killer.",
        [de("Removing memory limits entirely", "Container can consume all node memory and affect other pods", 0.85),
         de("Setting memory limit to very high value", "Hides the memory leak; wastes cluster resources", 0.65)],
        [wa("Profile memory usage and set appropriate resource limits", 0.93, "Use kubectl top pod to see actual memory consumption, then set limits with some headroom", sources=["https://kubernetes.io/docs/concepts/configuration/manage-resources-containers/"]),
         wa("Check for memory leaks in the application before increasing limits", 0.90, "If memory grows linearly over time, there's a leak")],
    ))

    c.append(canon(
        "kubernetes", "forbidden-user", "k8s128-linux",
        "Error from server (Forbidden): pods is forbidden: User 'system:serviceaccount:default:default' cannot list resource 'pods'",
        r"Forbidden.*cannot (list|get|create|delete|update) resource",
        "rbac", "kubernetes", ">=1.24", "linux",
        "true", 0.94, 0.96,
        "Service account or user lacks RBAC permissions for the requested operation.",
        [de("Granting cluster-admin to the service account", "Excessive permissions; violates principle of least privilege", 0.85, sources=["https://kubernetes.io/docs/reference/access-authn-authz/rbac/"]),
         de("Disabling RBAC", "Removes all access control from the cluster", 0.95)],
        [wa("Create a Role and RoleBinding with the specific permissions needed", 0.95, "kubectl create role pod-reader --verb=get,list --resource=pods", sources=["https://kubernetes.io/docs/reference/access-authn-authz/rbac/"]),
         wa("Use ClusterRole for cluster-wide access or Role for namespace-scoped access", 0.90, "Match the scope of permissions to the actual need")],
    ))

    # ── Terraform ───────────────────────────────────────────────────────
    c.append(canon(
        "terraform", "provider-not-found", "tf115-linux",
        "Error: Failed to query available provider packages",
        r"Failed to query available provider packages",
        "providers", "terraform", ">=1.0", "linux",
        "true", 0.93, 0.95,
        "Terraform cannot find the specified provider in the configured registries.",
        [de("Manually downloading the provider binary", "Requires manual updates; breaks terraform init workflow", 0.70),
         de("Removing the provider version constraint", "May install an incompatible version", 0.60)],
        [wa("Run terraform init -upgrade to refresh the provider cache", 0.92, "Downloads the latest compatible provider version", sources=["https://developer.hashicorp.com/terraform/cli/commands/init"]),
         wa("Check the required_providers block for correct source and version constraints", 0.95, "Ensure source = 'hashicorp/aws' (not just 'aws') and version constraint is valid")],
    ))

    c.append(canon(
        "terraform", "resource-already-exists", "tf115-linux",
        "Error: A resource with the ID already exists",
        r"resource with the ID.*already exists",
        "state", "terraform", ">=1.0", "linux",
        "true", 0.91, 0.93,
        "Terraform tries to create a resource that already exists outside of its state.",
        [de("Deleting the existing resource manually", "May cause downtime; the resource may be in use by other systems", 0.70),
         de("Changing the resource name in Terraform to avoid the conflict", "Creates a duplicate resource instead of managing the existing one", 0.75)],
        [wa("Import the existing resource: terraform import <resource_addr> <resource_id>", 0.95, "Brings the existing resource under Terraform management", sources=["https://developer.hashicorp.com/terraform/cli/commands/import"]),
         wa("Use import blocks (Terraform 1.5+) for declarative import", 0.90, "import { to = aws_instance.web; id = 'i-12345' }")],
    ))

    # ── AWS ──────────────────────────────────────────────────────────────
    c.append(canon(
        "aws", "lambda-runtime-error", "aws-cli2-linux",
        "Runtime.ImportModuleError: Unable to import module 'handler'",
        r"Runtime\.(ImportModuleError|HandlerNotFound)",
        "lambda", "aws", ">=2.0", "linux",
        "true", 0.94, 0.96,
        "Lambda function cannot find the handler module — wrong handler path, missing dependencies, or wrong runtime.",
        [de("Increasing Lambda memory/timeout", "Handler import is a packaging issue, not a resource issue", 0.85),
         de("Changing the runtime version", "Rarely helps unless using runtime-specific syntax", 0.70)],
        [wa("Verify handler setting matches the file structure: module.function format", 0.95, "If handler.py has def main(), set handler to 'handler.main'", sources=["https://docs.aws.amazon.com/lambda/latest/dg/python-handler.html"]),
         wa("Ensure all dependencies are included in the deployment package or Lambda layer", 0.92, "pip install -t ./package -r requirements.txt then zip for deployment")],
    ))

    c.append(canon(
        "aws", "cloudwatch-log-group-exists", "aws-cli2-linux",
        "ResourceAlreadyExistsException: The specified log group already exists",
        r"ResourceAlreadyExistsException.*log group already exists",
        "cloudwatch", "aws", ">=2.0", "linux",
        "true", 0.96, 0.97,
        "Attempting to create a CloudWatch log group that already exists.",
        [de("Deleting the existing log group", "Loses all existing log data permanently", 0.85),
         de("Ignoring the error and continuing", "Works but masks potential naming conflicts", 0.40)],
        [wa("Add lifecycle ignore_changes or check existence before creating", 0.93, "In IaC: use data source to check if it exists; in CLI: describe-log-groups first"),
         wa("Use create_log_group with error handling for AlreadyExists", 0.90, "Catch the exception and continue if the group already exists")],
    ))

    # ── Next.js ──────────────────────────────────────────────────────────
    c.append(canon(
        "nextjs", "err-next-config-invalid", "next14-linux",
        "Error: Invalid next.config.js options detected",
        r"Invalid next\.config\.(js|mjs) options detected",
        "config", "next.js", ">=13", "linux",
        "true", 0.95, 0.96,
        "next.config.js contains invalid or deprecated configuration options.",
        [de("Downgrading Next.js to match the old config format", "Loses security patches and new features", 0.70),
         de("Suppressing the warning with typescript/eslint rules", "The config error is at build time, not lint time", 0.80)],
        [wa("Check Next.js migration guide for your version and update deprecated options", 0.95, "Each major version has a migration guide with config changes", sources=["https://nextjs.org/docs/app/building-your-application/upgrading"]),
         wa("Use the Next.js config type for autocomplete: /** @type {import('next').NextConfig} */", 0.90, "TypeScript-powered autocomplete catches invalid options before build")],
    ))

    c.append(canon(
        "nextjs", "module-not-found-client-component", "next14-linux",
        "Module not found: Can't resolve 'fs' in client component",
        r"Module not found.*Can't resolve '(fs|path|child_process|crypto)'",
        "app-router", "next.js", ">=13", "linux",
        "true", 0.95, 0.96,
        "Client component (use client) tries to import a Node.js-only module like fs, path, or child_process.",
        [de("Polyfilling the Node.js module for the browser", "fs and child_process cannot be meaningfully polyfilled in browsers", 0.80),
         de("Installing the module from npm", "fs is a built-in Node module; npm install fs installs a shim that doesn't work", 0.85)],
        [wa("Move the Node.js code to a Server Component or API route", 0.96, "Remove 'use client' from the component that needs Node.js APIs", sources=["https://nextjs.org/docs/app/building-your-application/rendering/composition-patterns"]),
         wa("Use dynamic import with { ssr: false } if the module is only needed on the server side of the component", 0.85, "Separate server-only logic into a separate module imported dynamically")],
    ))

    # ── React ────────────────────────────────────────────────────────────
    c.append(canon(
        "react", "objects-not-valid-as-child", "react18-linux",
        "Error: Objects are not valid as a React child",
        r"Objects are not valid as a React child",
        "rendering", "react", ">=17", "linux",
        "true", 0.97, 0.98,
        "Trying to render a plain object or Promise directly in JSX.",
        [de("Converting with JSON.stringify()", "Renders raw JSON in the UI; not a proper component", 0.65),
         de("Using .toString() on the object", "Shows '[object Object]' — not useful", 0.90)],
        [wa("Render specific properties: {obj.name} instead of {obj}", 0.97, "Access the specific string/number fields you want to display"),
         wa("For Promises, use React Suspense or useEffect + useState to resolve async data", 0.92, "const [data, setData] = useState(null); useEffect(() => fetch().then(setData), [])")],
    ))

    c.append(canon(
        "react", "maximum-update-depth-exceeded", "react18-linux",
        "Error: Maximum update depth exceeded. This can happen when a component calls setState inside useEffect",
        r"Maximum update depth exceeded",
        "rendering", "react", ">=17", "linux",
        "true", 0.95, 0.96,
        "useEffect triggers a state update that re-triggers the effect in an infinite loop.",
        [de("Adding a counter to limit the number of updates", "Adds complexity without fixing the root cause; effect still fires unnecessarily", 0.70),
         de("Removing the useEffect entirely", "May break the feature that needs the side effect", 0.60)],
        [wa("Add correct dependencies to the useEffect dependency array", 0.95, "Ensure deps don't change on every render — avoid object/array literals in deps", sources=["https://react.dev/reference/react/useEffect#removing-unnecessary-dependencies"]),
         wa("Use useMemo/useCallback for deps that are computed values or functions", 0.92, "Memoization prevents the dependency from changing on every render")],
    ))

    # ── CUDA ─────────────────────────────────────────────────────────────
    c.append(canon(
        "cuda", "illegal-memory-access", "cuda12-linux",
        "RuntimeError: CUDA error: an illegal memory access was encountered",
        r"CUDA error: an illegal memory access",
        "runtime", "cuda", ">=11.0", "linux",
        "true", 0.85, 0.88,
        "GPU kernel accessed invalid memory — buffer overrun, freed memory, or wrong tensor shape.",
        [de("Catching the error and continuing training", "GPU is in error state; all subsequent CUDA operations will fail", 0.90),
         de("Increasing GPU memory allocation", "Illegal access is about address validity, not memory quantity", 0.80)],
        [wa("Set CUDA_LAUNCH_BLOCKING=1 to get accurate error location", 0.93, "Synchronous execution pinpoints which kernel caused the error", sources=["https://docs.nvidia.com/cuda/cuda-c-programming-guide/index.html#error-handling"]),
         wa("Check tensor shapes and indices — off-by-one errors are the most common cause", 0.88, "Verify all indexing operations stay within tensor dimensions")],
    ))

    # ── pip ──────────────────────────────────────────────────────────────
    c.append(canon(
        "pip", "inconsistent-requirements", "pip23-linux",
        "ERROR: Cannot install package-a and package-b because these package versions have conflicting dependencies",
        r"(Cannot install.*conflicting dependencies|ResolutionImpossible)",
        "resolution", "pip", ">=22.0", "linux",
        "true", 0.89, 0.91,
        "pip cannot find a set of package versions that satisfies all dependency constraints.",
        [de("Using --force-reinstall", "Installs incompatible versions; imports will fail at runtime", 0.80),
         de("Removing version constraints from requirements.txt", "May install breaking versions of dependencies", 0.65)],
        [wa("Use pip install --dry-run to see the conflict, then pin compatible versions", 0.90, "pip install --dry-run package-a package-b shows which versions conflict"),
         wa("Use pipdeptree to visualize the dependency tree and find the conflict point", 0.88, "pipdeptree --warn silence shows the full tree; pipdeptree -p package shows deps for one package", sources=["https://github.com/tox-dev/pipdeptree"])],
    ))

    c.append(canon(
        "pip", "metadata-generation-failed", "pip23-linux",
        "error: metadata-generation-failed",
        r"metadata-generation-failed",
        "build", "pip", ">=22.0", "linux",
        "true", 0.88, 0.90,
        "pip cannot generate package metadata, usually because the setup.py/pyproject.toml has errors or missing build dependencies.",
        [de("Upgrading pip repeatedly", "The issue is in the package's build system, not pip itself", 0.70),
         de("Using --no-build-isolation", "May work but can conflict with system packages", 0.50)],
        [wa("Install build dependencies first: pip install wheel setuptools", 0.88, "Many packages need these to generate metadata"),
         wa("Install system-level build tools: sudo apt install python3-dev build-essential", 0.90, "C extensions need compilers and header files", sources=["https://pip.pypa.io/en/stable/reference/build-system/"])],
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
    print(f"Wave 12: wrote {written} new canons, skipped {skipped} existing")


if __name__ == "__main__":
    main()
