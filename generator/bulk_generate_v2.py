"""Bulk generate additional ErrorCanon JSON files (wave 2).

Adds ~15 high-frequency errors to reach 100+ total canons.

Usage: python -m generator.bulk_generate_v2
"""

from generator.bulk_generate import (
    canon, de, wa, leads, preceded, confused, main as _write_canons,
    DATA_DIR,
)
import json


def get_all_canons() -> list[dict]:
    canons = []

    # === PYTHON: IndexError ===
    canons.append(canon(
        "python", "indexerror-list-out-of-range", "py311-linux",
        "IndexError: list index out of range",
        r"IndexError: list index out of range",
        "index_error", "python", ">=3.11,<3.13", "linux", "true", 0.90, 0.92,
        "Accessing a list index that doesn't exist. Common in loops, API responses, and off-by-one errors.",
        [de("Wrap in try/except IndexError", "Masks the real issue — the list is shorter than expected", 0.70,
            sources=["https://docs.python.org/3/tutorial/errors.html"]),
         de("Pad list with None values", "Introduces None downstream which causes TypeError later", 0.60,
            sources=["https://docs.python.org/3/library/exceptions.html#IndexError"])],
        [wa("Check len() before access or use try/except with clear fallback logic", 0.92,
            "if idx < len(items): val = items[idx]",
            sources=["https://docs.python.org/3/library/functions.html#len"]),
         wa("Use negative indexing or slice notation for safe tail access", 0.88,
            "last = items[-1] if items else default",
            sources=["https://docs.python.org/3/library/stdtypes.html#sequence-types-list-tuple-range"])],
        python=">=3.11,<3.13",
        leads_to=[leads("python/typeerror-nonetype-not-subscriptable/py311-linux", 0.25, "Safe access returns None which is then used unsafely")],
        preceded_by=[preceded("python/keyerror/py311-linux", 0.15, "Data structure changed from dict to list")],
    ))

    # === PYTHON: NameError ===
    canons.append(canon(
        "python", "nameerror-not-defined", "py311-linux",
        "NameError: name 'variable' is not defined",
        r"NameError: name '(.+?)' is not defined",
        "name_error", "python", ">=3.11,<3.13", "linux", "true", 0.95, 0.95,
        "Variable or function referenced before assignment. Common after refactoring, conditional assignments, or typos.",
        [de("Add global declaration", "Usually masks a scoping issue rather than fixing it", 0.65,
            sources=["https://docs.python.org/3/reference/simple_stmts.html#the-global-statement"]),
         de("Initialize variable to None at module level", "Hides the real bug — the variable should come from specific logic", 0.60,
            sources=["https://docs.python.org/3/reference/executionmodel.html#naming-and-binding"])],
        [wa("Check for typos and ensure variable is assigned in all code paths", 0.95,
            sources=["https://docs.python.org/3/reference/executionmodel.html#naming-and-binding"]),
         wa("Move import or assignment before first use; check conditional branches all assign", 0.90,
            sources=["https://docs.python.org/3/tutorial/controlflow.html"])],
        python=">=3.11,<3.13",
    ))

    # === PYTHON: AttributeError ===
    canons.append(canon(
        "python", "attributeerror-no-attribute", "py311-linux",
        "AttributeError: 'NoneType' object has no attribute 'method'",
        r"AttributeError: '(\w+)' object has no attribute '(\w+)'",
        "attribute_error", "python", ">=3.11,<3.13", "linux", "true", 0.88, 0.90,
        "Calling method/attribute on wrong type or None. Common when function returns None unexpectedly.",
        [de("Add hasattr() check before every access", "Defensive coding that hides the root cause", 0.65,
            sources=["https://docs.python.org/3/library/functions.html#hasattr"]),
         de("Catch AttributeError broadly", "Silences real bugs, makes debugging harder", 0.70,
            sources=["https://docs.python.org/3/tutorial/errors.html"])],
        [wa("Trace where the object becomes None/wrong type and fix the source", 0.92,
            sources=["https://docs.python.org/3/library/functions.html#breakpoint"]),
         wa("Add type hints and use mypy/pyright to catch statically", 0.85,
            sources=["https://docs.python.org/3/library/typing.html"])],
        python=">=3.11,<3.13",
        leads_to=[leads("python/typeerror-nonetype-not-subscriptable/py311-linux", 0.3, "Same root cause: None where object expected")],
    ))

    # === PYTHON: SyntaxError ===
    canons.append(canon(
        "python", "syntaxerror-invalid-syntax", "py311-linux",
        "SyntaxError: invalid syntax",
        r"SyntaxError: invalid syntax",
        "syntax_error", "python", ">=3.11,<3.13", "linux", "true", 0.98, 0.98,
        "Python parser cannot understand the code. Often points to the line AFTER the actual error.",
        [de("Fix only the reported line", "The real error is often on the PREVIOUS line (missing colon, paren, bracket)", 0.75,
            sources=["https://docs.python.org/3/tutorial/errors.html#syntax-errors"]),
         de("Assume Python version mismatch", "Usually it's just a typo, not a version issue", 0.55,
            sources=["https://docs.python.org/3/reference/lexical_analysis.html"])],
        [wa("Check the line BEFORE the reported error for missing colons, parentheses, or brackets", 0.95,
            sources=["https://docs.python.org/3/tutorial/errors.html#syntax-errors"]),
         wa("Use an editor with syntax highlighting or run py_compile to get precise location", 0.90,
            "python -m py_compile script.py",
            sources=["https://docs.python.org/3/library/py_compile.html"])],
        python=">=3.11,<3.13",
    ))

    # === PYTHON: JSONDecodeError ===
    canons.append(canon(
        "python", "jsondecodeerror", "py311-linux",
        "json.decoder.JSONDecodeError: Expecting value",
        r"json\.decoder\.JSONDecodeError: (.+)",
        "parse_error", "python", ">=3.11,<3.13", "linux", "true", 0.90, 0.88,
        "Invalid JSON input. Common with empty API responses, HTML error pages, or BOM-prefixed files.",
        [de("Wrap json.loads in try/except and return empty dict", "Silently drops real data errors", 0.68,
            sources=["https://docs.python.org/3/library/json.html#json.JSONDecodeError"]),
         de("Use eval() instead of json.loads()", "Massive security vulnerability — never eval untrusted data", 0.95,
            sources=["https://docs.python.org/3/library/functions.html#eval"])],
        [wa("Check response status and content-type before parsing", 0.92,
            "if resp.status_code == 200 and 'json' in resp.headers.get('content-type', ''): data = resp.json()",
            sources=["https://docs.python.org/3/library/json.html"]),
         wa("Log the raw content to identify what's actually being returned", 0.88,
            sources=["https://docs.python.org/3/library/logging.html"])],
        python=">=3.11,<3.13",
    ))

    # === NODE: TypeError cannot read properties of undefined ===
    canons.append(canon(
        "node", "typeerror-cannot-read-undefined", "node20-linux",
        "TypeError: Cannot read properties of undefined (reading 'property')",
        r"TypeError: Cannot read propert(y|ies) of (undefined|null)",
        "type_error", "node", ">=20,<23", "linux", "true", 0.88, 0.90,
        "Accessing property on undefined/null. The #1 JavaScript runtime error worldwide.",
        [de("Add optional chaining (?.) everywhere", "Masks bugs — undefined propagates silently through the chain", 0.60,
            sources=["https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Operators/Optional_chaining"]),
         de("Default to empty object with || {}", "Fails for falsy values (0, '', false)", 0.55,
            sources=["https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Operators/Logical_OR"])],
        [wa("Trace where the variable becomes undefined — check async timing, missing return, wrong key name", 0.92,
            sources=["https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Errors/Cant_access_property"]),
         wa("Use nullish coalescing (??) with explicit defaults at the source, not at every usage", 0.85,
            "const value = response?.data ?? defaultValue;",
            sources=["https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Operators/Nullish_coalescing"])],
    ))

    # === NODE: ECONNREFUSED ===
    canons.append(canon(
        "node", "econnrefused", "node20-linux",
        "Error: connect ECONNREFUSED 127.0.0.1:3000",
        r"Error: connect ECONNREFUSED [\d.:]+",
        "network_error", "node", ">=20,<23", "linux", "true", 0.85, 0.88,
        "Target server is not running or not accepting connections on the expected port.",
        [de("Increase connection timeout", "Server isn't running — waiting longer won't help", 0.80,
            sources=["https://nodejs.org/api/errors.html#common-system-errors"]),
         de("Change to 0.0.0.0 binding", "Confuses listen address with connect address", 0.65,
            sources=["https://nodejs.org/api/net.html"])],
        [wa("Verify the target service is running: check process, port, and network", 0.95,
            "lsof -i :3000 || netstat -tlnp | grep 3000",
            sources=["https://nodejs.org/api/errors.html#common-system-errors"]),
         wa("In Docker/K8s: use service name instead of localhost, check network connectivity", 0.88,
            sources=["https://docs.docker.com/network/"])],
    ))

    # === TYPESCRIPT: TS2304 Cannot find name ===
    canons.append(canon(
        "typescript", "ts2304-cannot-find-name", "ts5-linux",
        "error TS2304: Cannot find name 'identifier'",
        r"error TS2304: Cannot find name '(.+?)'",
        "type_error", "typescript", ">=5.0,<6.0", "linux", "true", 0.90, 0.92,
        "TypeScript can't resolve a name. Missing import, missing type declaration, or wrong tsconfig.",
        [de("Add // @ts-ignore above the line", "Disables all type checking for that line, hiding real errors", 0.85,
            sources=["https://www.typescriptlang.org/docs/handbook/release-notes/typescript-2-6.html"]),
         de("Cast to any", "Defeats the purpose of TypeScript", 0.80,
            sources=["https://www.typescriptlang.org/docs/handbook/2/everyday-types.html#any"])],
        [wa("Add the missing import or install @types package", 0.95,
            "npm install -D @types/package-name",
            sources=["https://www.typescriptlang.org/docs/handbook/2/type-declarations.html"]),
         wa("Check tsconfig include/exclude paths and module resolution settings", 0.85,
            sources=["https://www.typescriptlang.org/tsconfig#include"])],
    ))

    # === DOCKER: image not found / manifest unknown ===
    canons.append(canon(
        "docker", "manifest-not-found", "docker27-linux",
        "Error response from daemon: manifest for image:tag not found",
        r"manifest for .+ not found|manifest unknown",
        "image_error", "docker", ">=27,<28", "linux", "true", 0.88, 0.90,
        "Docker image tag doesn't exist in registry. Common after version bumps or architecture mismatches.",
        [de("Pull with --platform flag blindly", "May pull wrong arch image causing exec format error at runtime", 0.55,
            sources=["https://docs.docker.com/reference/cli/docker/image/pull/"]),
         de("Use :latest tag instead", "latest is mutable, unpredictable, and may not exist for all images", 0.60,
            sources=["https://docs.docker.com/reference/cli/docker/image/pull/"])],
        [wa("Check available tags on Docker Hub or registry and use exact version", 0.95,
            "docker manifest inspect image:tag",
            sources=["https://docs.docker.com/reference/cli/docker/manifest/inspect/"]),
         wa("Verify image name spelling and registry URL (docker.io vs ghcr.io vs ecr)", 0.88,
            sources=["https://docs.docker.com/reference/cli/docker/image/pull/"])],
        leads_to=[leads("docker/exec-format-error/docker27-linux", 0.3, "Wrong platform image pulled")],
    ))

    # === GIT: merge conflict ===
    canons.append(canon(
        "git", "merge-conflict", "git2-linux",
        "CONFLICT (content): Merge conflict in file.txt",
        r"CONFLICT \(content\): Merge conflict in (.+)",
        "merge_error", "git", ">=2.30,<3.0", "linux", "true", 0.95, 0.95,
        "Same file modified on both branches. Must be resolved manually.",
        [de("Use --force to overwrite", "Loses changes from one side entirely", 0.90,
            sources=["https://git-scm.com/docs/git-merge"]),
         de("Delete and re-clone the repo", "Loses all uncommitted work and local branches", 0.95,
            sources=["https://git-scm.com/book/en/v2/Git-Branching-Basic-Branching-and-Merging"])],
        [wa("Open conflicting files, resolve <<<< ==== >>>> markers, then git add and commit", 0.95,
            sources=["https://git-scm.com/book/en/v2/Git-Branching-Basic-Branching-and-Merging"]),
         wa("Use git mergetool or IDE merge UI for complex conflicts", 0.88,
            "git mergetool",
            sources=["https://git-scm.com/docs/git-mergetool"])],
        preceded_by=[preceded("git/failed-to-push-refs/git2-linux", 0.4, "Push rejected, pull causes merge conflict")],
    ))

    # === KUBERNETES: pod pending ===
    canons.append(canon(
        "kubernetes", "pod-pending", "k8s1-linux",
        "Pod status: Pending — 0/N nodes are available",
        r"0/\d+ nodes are available|Insufficient (cpu|memory)|Unschedulable",
        "scheduling_error", "kubernetes", ">=1.28,<1.32", "linux", "true", 0.85, 0.88,
        "Pod can't be scheduled. Insufficient resources, node taints, or affinity constraints.",
        [de("Delete and recreate the pod", "Same scheduling constraints apply, pod will be Pending again", 0.80,
            sources=["https://kubernetes.io/docs/concepts/scheduling-eviction/assign-pod-node/"]),
         de("Remove all resource requests/limits", "Pod runs but can OOMKill or starve other workloads", 0.65,
            sources=["https://kubernetes.io/docs/concepts/configuration/manage-resources-containers/"])],
        [wa("Check kubectl describe pod for scheduling failure reason, then fix resources or node capacity", 0.92,
            "kubectl describe pod <name> | grep -A5 Events",
            sources=["https://kubernetes.io/docs/concepts/scheduling-eviction/assign-pod-node/"]),
         wa("Scale up node pool or reduce resource requests to fit available capacity", 0.85,
            sources=["https://kubernetes.io/docs/concepts/configuration/manage-resources-containers/"])],
        preceded_by=[preceded("kubernetes/oomkilled/k8s1-linux", 0.2, "Increased memory limits made pod unschedulable")],
        confused_with=[confused("kubernetes/crashloopbackoff/k8s1-linux", "CrashLoopBackOff means pod runs and crashes; Pending means pod never starts")],
    ))

    # === RUST: E0502 borrow conflict ===
    canons.append(canon(
        "rust", "e0502-mutable-immutable-borrow", "rust1-linux",
        "error[E0502]: cannot borrow `x` as mutable because it is also borrowed as immutable",
        r"error\[E0502\]: cannot borrow .+ as mutable because it is also borrowed as immutable",
        "borrow_error", "rust", ">=1.70,<2.0", "linux", "true", 0.85, 0.88,
        "Rust's borrow checker prevents simultaneous mutable and immutable borrows.",
        [de("Use unsafe to bypass borrow checker", "Introduces undefined behavior, defeats Rust's safety guarantees", 0.90,
            sources=["https://doc.rust-lang.org/book/ch19-01-unsafe-rust.html"]),
         de("Clone everything to avoid borrows", "Unnecessary allocations, may not fix the design issue", 0.55,
            sources=["https://doc.rust-lang.org/std/clone/trait.Clone.html"])],
        [wa("Restructure code to separate mutable and immutable borrow scopes", 0.90,
            "{ let r = &x; use(r); } // immutable borrow ends\nx.mutate(); // mutable borrow starts",
            sources=["https://doc.rust-lang.org/book/ch04-02-references-and-borrowing.html"]),
         wa("Use interior mutability (RefCell, Mutex) when borrow splitting isn't possible", 0.82,
            sources=["https://doc.rust-lang.org/book/ch15-05-interior-mutability.html"])],
        confused_with=[confused("rust/e0382-borrow-moved-value/rust1-linux", "E0382 is use-after-move; E0502 is simultaneous mutable+immutable borrow")],
    ))

    # === GO: nil pointer dereference ===
    canons.append(canon(
        "go", "nil-pointer-dereference", "go1-linux",
        "runtime error: invalid memory address or nil pointer dereference",
        r"nil pointer dereference|invalid memory address",
        "runtime_error", "go", ">=1.21,<1.24", "linux", "true", 0.88, 0.90,
        "Dereferencing a nil pointer. Common with uninitialized structs, failed type assertions, and error-ignored returns.",
        [de("Add nil check before every pointer use", "Defensive checks everywhere obscure the real bug", 0.55,
            sources=["https://go.dev/doc/faq#nil_error"]),
         de("Use recover() to catch the panic", "Masks the bug, doesn't fix the nil source", 0.70,
            sources=["https://go.dev/blog/defer-panic-and-recover"])],
        [wa("Find where the nil value originates — check error returns, interface assertions, and struct init", 0.92,
            sources=["https://go.dev/doc/effective_go#errors"]),
         wa("Use the comma-ok pattern for type assertions and map lookups", 0.88,
            "val, ok := m[key]; if !ok { handle() }",
            sources=["https://go.dev/doc/effective_go#interface_conversions"])],
    ))

    # === AWS: throttling exception ===
    canons.append(canon(
        "aws", "throttling-exception", "awscli2-linux",
        "An error occurred (ThrottlingException): Rate exceeded",
        r"(ThrottlingException|Throttling|Rate exceeded|Too Many Requests)",
        "api_error", "aws", ">=2.0", "linux", "true", 0.90, 0.92,
        "AWS API rate limit hit. Common in automation scripts, Lambda bursts, and CI/CD pipelines.",
        [de("Add sleep(1) between every API call", "Fixed delay is inefficient — too slow for normal, too fast for bursts", 0.60,
            sources=["https://docs.aws.amazon.com/general/latest/gr/api-retries.html"]),
         de("Increase service quota immediately", "Quota increase takes time and may not be the bottleneck", 0.50,
            sources=["https://docs.aws.amazon.com/servicequotas/latest/userguide/request-quota-increase.html"])],
        [wa("Implement exponential backoff with jitter", 0.95,
            "Use boto3 built-in retry config: config=Config(retries={'max_attempts': 10, 'mode': 'adaptive'})",
            sources=["https://docs.aws.amazon.com/general/latest/gr/api-retries.html"]),
         wa("Batch API calls and spread requests across time windows", 0.85,
            sources=["https://docs.aws.amazon.com/general/latest/gr/api-retries.html"])],
    ))

    # === TERRAFORM: resource already exists ===
    canons.append(canon(
        "terraform", "resource-already-exists", "tf1-linux",
        "Error: creating resource: already exists",
        r"(already exists|AlreadyExists|ConflictException|EntityAlreadyExists)",
        "state_error", "terraform", ">=1.5,<2.0", "linux", "true", 0.82, 0.85,
        "Cloud resource exists but not in Terraform state. Common after manual changes or failed applies.",
        [de("Delete the resource manually and re-apply", "Causes downtime and may delete data", 0.85,
            sources=["https://developer.hashicorp.com/terraform/cli/commands/import"]),
         de("Use terraform taint to force recreation", "Destroys and recreates, causing downtime", 0.75,
            sources=["https://developer.hashicorp.com/terraform/cli/commands/taint"])],
        [wa("Import existing resource into state: terraform import", 0.92,
            "terraform import aws_instance.example i-1234567890abcdef0",
            sources=["https://developer.hashicorp.com/terraform/cli/commands/import"]),
         wa("Use import blocks (TF 1.5+) for declarative imports", 0.88,
            "import { to = aws_instance.example; id = \"i-123\" }",
            sources=["https://developer.hashicorp.com/terraform/language/import"])],
        preceded_by=[preceded("terraform/state-lock-error/tf1-linux", 0.2, "Lock error caused partial apply, resource created but not in state")],
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
