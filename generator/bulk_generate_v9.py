"""Bulk generate wave 9: +40 canons.

Usage: python -m generator.bulk_generate_v9
"""

import json
from generator.bulk_generate import (
    canon, de, wa, DATA_DIR,
)


def get_all_canons():
    c = []

    # ── PYTHON ──────────────────────────────────────────

    c.append(canon(
        "python", "keyboardinterrupt", "py311-linux",
        "KeyboardInterrupt",
        r"KeyboardInterrupt",
        "signal_error", "python", ">=3.11,<3.13", "linux",
        "true", 0.95, 0.95,
        "User pressed Ctrl+C. Program interrupted. Handle with signal or try/except for graceful shutdown.",
        [de("Catch and ignore KeyboardInterrupt",
            "User can't stop the program — bad UX", 0.80,
            sources=["https://docs.python.org/3/library/exceptions.html#KeyboardInterrupt"])],
        [wa("Add cleanup code: try/finally or atexit for graceful shutdown", 0.95,
            "try:\n    main()\nexcept KeyboardInterrupt:\n    print('\\nShutting down...')\n    cleanup()",
            sources=["https://docs.python.org/3/library/atexit.html"]),
         wa("Use signal.signal(signal.SIGINT, handler) for custom interrupt handling", 0.88,
            sources=["https://docs.python.org/3/library/signal.html"])],
        python=">=3.11,<3.13",
    ))

    c.append(canon(
        "python", "oserror-address-already-in-use", "py311-linux",
        "OSError: [Errno 98] Address already in use",
        r"OSError.*Address already in use|Errno 98|EADDRINUSE",
        "network_error", "python", ">=3.11,<3.13", "linux",
        "partial", 0.88, 0.90,
        "Port is occupied by another process. Common with Flask/Django dev servers after crash.",
        [de("Change the port number every time",
            "Inconvenient and doesn't free the stuck port", 0.60,
            sources=["https://docs.python.org/3/library/socket.html"]),
         de("Kill all Python processes",
            "May kill unrelated Python processes", 0.65,
            sources=["https://docs.python.org/3/library/socket.html"])],
        [wa("Find and kill the process using the port: lsof -i :PORT | kill", 0.95,
            "lsof -i :8000 | grep LISTEN\nkill -9 <PID>",
            sources=["https://docs.python.org/3/library/socket.html"]),
         wa("Set SO_REUSEADDR on the socket to allow immediate reuse", 0.90,
            "sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)",
            sources=["https://docs.python.org/3/library/socket.html#socket.socket.setsockopt"])],
        python=">=3.11,<3.13",
    ))

    c.append(canon(
        "python", "typeerror-not-json-serializable", "py311-linux",
        "TypeError: Object of type X is not JSON serializable",
        r"TypeError: Object of type .+ is not JSON serializable",
        "serialization_error", "python", ">=3.11,<3.13", "linux",
        "true", 0.95, 0.95,
        "json.dumps can't serialize the object. Common: datetime, set, numpy, Decimal, UUID.",
        [de("Use str() on everything before serializing",
            "Loses type information — can't deserialize back correctly", 0.60,
            sources=["https://docs.python.org/3/library/json.html"]),
         de("Use pickle instead of JSON",
            "Pickle is Python-only, insecure, and not human-readable", 0.75,
            sources=["https://docs.python.org/3/library/pickle.html"])],
        [wa("Write a custom encoder: class CustomEncoder(json.JSONEncoder)", 0.92,
            "class CustomEncoder(json.JSONEncoder):\n    def default(self, o):\n        if isinstance(o, datetime): return o.isoformat()\n        if isinstance(o, set): return list(o)\n        return super().default(o)",
            sources=["https://docs.python.org/3/library/json.html#json.JSONEncoder"]),
         wa("Convert the specific type before serializing: list(set), str(uuid)", 0.90,
            sources=["https://docs.python.org/3/library/json.html"])],
        python=">=3.11,<3.13",
    ))

    c.append(canon(
        "python", "indentationerror", "py311-linux",
        "IndentationError: unexpected indent",
        r"IndentationError: (unexpected indent|expected an indented block|unindent does not match)",
        "syntax_error", "python", ">=3.11,<3.13", "linux",
        "true", 0.98, 0.95,
        "Mixed tabs and spaces, or wrong indentation level.",
        [de("Auto-format with a random formatter",
            "Different formatters have different defaults — pick one and stick with it", 0.55,
            sources=["https://docs.python.org/3/reference/lexical_analysis.html#indentation"])],
        [wa("Use consistent indentation: 4 spaces (PEP 8 standard)", 0.98,
            sources=["https://peps.python.org/pep-0008/#indentation"]),
         wa("Configure your editor to convert tabs to spaces", 0.95,
            sources=["https://docs.python.org/3/reference/lexical_analysis.html#indentation"]),
         wa("Run: python -tt script.py to check for mixed tabs/spaces", 0.85,
            sources=["https://docs.python.org/3/using/cmdline.html#cmdoption-tt"])],
        python=">=3.11,<3.13",
    ))

    # ── NODE ──────────────────────────────────────────

    c.append(canon(
        "node", "err-require-async-module", "node20-linux",
        "Error [ERR_REQUIRE_ASYNC_MODULE]: require() of ES Module not supported with top-level await",
        r"ERR_REQUIRE_ASYNC_MODULE|require.*async module|top-level await.*require",
        "module_error", "node", ">=20,<23", "linux",
        "true", 0.88, 0.90,
        "Trying to require() a module that uses top-level await. Must use import() instead.",
        [de("Remove top-level await from the module",
            "May break the module's initialization logic", 0.65,
            sources=["https://nodejs.org/api/esm.html#top-level-await"])],
        [wa("Use dynamic import: const mod = await import('module')", 0.95,
            sources=["https://nodejs.org/api/esm.html#import-expressions"]),
         wa("Convert calling code to ESM with 'type': 'module' in package.json", 0.88,
            sources=["https://nodejs.org/api/packages.html#type"])],
    ))

    c.append(canon(
        "node", "memory-leak-warning", "node20-linux",
        "MaxListenersExceededWarning: Possible EventEmitter memory leak detected. 11 listeners added",
        r"MaxListenersExceededWarning|memory leak.*EventEmitter|11 .* listeners added",
        "memory_warning", "node", ">=20,<23", "linux",
        "true", 0.88, 0.90,
        "Too many event listeners on one emitter. Usually forgetting to remove listeners.",
        [de("Set maxListeners to Infinity",
            "Hides the memory leak — listeners accumulate without bound", 0.80,
            sources=["https://nodejs.org/api/events.html#emittersetmaxlistenersn"]),
         de("Suppress the warning",
            "The leak will grow until the process runs out of memory", 0.85,
            sources=["https://nodejs.org/api/events.html"])],
        [wa("Remove listeners when done: emitter.removeListener() or emitter.off()", 0.92,
            sources=["https://nodejs.org/api/events.html#emitterremovelistenereventname-listener"]),
         wa("Use { once: true } for one-time listeners: emitter.on('event', fn, { once: true })", 0.88,
            sources=["https://nodejs.org/api/events.html#emitteroneventname-listener"]),
         wa("Check for listeners added in loops or repeated function calls", 0.90,
            sources=["https://nodejs.org/api/events.html"])],
    ))

    c.append(canon(
        "node", "npm-peer-deps-conflict", "node20-linux",
        "npm error ERESOLVE could not resolve peer dependency conflict",
        r"ERESOLVE.*peer dep|could not resolve.*peer|peer dependency conflict",
        "dependency_error", "node", ">=20,<23", "linux",
        "true", 0.88, 0.90,
        "Two packages require incompatible versions of a shared dependency.",
        [de("Use --force flag",
            "Installs potentially broken dependencies — may cause runtime errors", 0.65,
            sources=["https://docs.npmjs.com/cli/v10/commands/npm-install#force"]),
         de("Delete package-lock.json and reinstall",
            "Lock file protects reproducibility — deleting it may introduce other issues", 0.60,
            sources=["https://docs.npmjs.com/cli/v10/configuring-npm/package-lock-json"])],
        [wa("Use --legacy-peer-deps to use npm v6 resolution (less strict)", 0.88,
            "npm install --legacy-peer-deps",
            sources=["https://docs.npmjs.com/cli/v10/commands/npm-install#legacy-peer-deps"]),
         wa("Check which packages conflict and update them: npm ls <dep>", 0.90,
            sources=["https://docs.npmjs.com/cli/v10/commands/npm-ls"]),
         wa("Add overrides in package.json to force a specific version", 0.82,
            '{ "overrides": { "conflicting-pkg": "^2.0.0" } }',
            sources=["https://docs.npmjs.com/cli/v10/configuring-npm/package-json#overrides"])],
    ))

    # ── TYPESCRIPT ──────────────────────────────────────────

    c.append(canon(
        "typescript", "ts2454-variable-used-before-assigned", "ts5-linux",
        "error TS2454: Variable 'x' is used before being assigned",
        r"TS2454.*used before being assigned",
        "type_error", "typescript", ">=5.0,<6.0", "linux",
        "true", 0.95, 0.95,
        "Variable accessed before all code paths assign it. TypeScript flow analysis detected a gap.",
        [de("Use ! non-null assertion: x!",
            "May cause runtime undefined access if the analysis is correct", 0.65,
            sources=["https://www.typescriptlang.org/docs/handbook/2/narrowing.html"])],
        [wa("Initialize the variable at declaration: let x: Type = defaultValue", 0.95,
            sources=["https://www.typescriptlang.org/docs/handbook/2/narrowing.html"]),
         wa("Restructure code so all branches assign before use", 0.90,
            sources=["https://www.typescriptlang.org/docs/handbook/2/narrowing.html"])],
    ))

    c.append(canon(
        "typescript", "ts2339-index-signature", "ts5-linux",
        "error TS7053: Element implicitly has an 'any' type because expression of type 'string' can't be used to index type",
        r"TS7053.*implicitly.*any.*can't be used to index",
        "type_error", "typescript", ">=5.0,<6.0", "linux",
        "true", 0.92, 0.92,
        "Dynamic property access on a typed object. TypeScript can't verify the key exists.",
        [de("Cast to any: (obj as any)[key]",
            "Loses all type safety for the access", 0.70,
            sources=["https://www.typescriptlang.org/docs/handbook/2/indexed-access-types.html"])],
        [wa("Add index signature: { [key: string]: ValueType }", 0.92,
            "interface MyObj { [key: string]: string | number; }",
            sources=["https://www.typescriptlang.org/docs/handbook/2/objects.html#index-signatures"]),
         wa("Use Record<string, T> type for key-value objects", 0.90,
            "const obj: Record<string, number> = {};",
            sources=["https://www.typescriptlang.org/docs/handbook/utility-types.html#recordkeys-type"]),
         wa("Use keyof typeof obj to restrict keys to known ones", 0.85,
            sources=["https://www.typescriptlang.org/docs/handbook/2/keyof-types.html"])],
    ))

    # ── REACT ──────────────────────────────────────────

    c.append(canon(
        "react", "jsx-element-type-not-assignable", "react18-linux",
        "Type 'Element | undefined' is not assignable to type 'ReactElement' (JSX return type)",
        r"not assignable to type.*ReactElement|JSX element type.*does not have.*construct|Element.*undefined.*ReactElement",
        "type_error", "react", ">=18,<20", "linux",
        "true", 0.90, 0.92,
        "Component might return undefined/null which isn't valid JSX. TypeScript strict mode.",
        [de("Wrap return in <></>",
            "Fragment doesn't fix undefined — you need to handle the null case", 0.65,
            sources=["https://react.dev/reference/react/Fragment"])],
        [wa("Ensure component always returns JSX or null (never undefined)", 0.95,
            "if (!data) return null;  // not: if (!data) return;",
            sources=["https://react.dev/learn/conditional-rendering"]),
         wa("Use conditional rendering: {condition && <Component />} or ternary", 0.90,
            sources=["https://react.dev/learn/conditional-rendering"])],
    ))

    # ── NEXT.JS ──────────────────────────────────────────

    c.append(canon(
        "nextjs", "parallel-routes-default", "nextjs14-linux",
        "Error: Missing default.tsx for parallel route slot",
        r"Missing.*default.*parallel|parallel route.*default|slot.*missing.*default",
        "routing_error", "nextjs", ">=14,<16", "linux",
        "true", 0.92, 0.92,
        "Parallel route slot needs a default.tsx fallback for unmatched routes.",
        [de("Remove the parallel route",
            "Loses the parallel rendering feature", 0.70,
            sources=["https://nextjs.org/docs/app/building-your-application/routing/parallel-routes"])],
        [wa("Create a default.tsx in the slot directory that returns null or a fallback", 0.95,
            "// @slot/default.tsx\nexport default function Default() { return null; }",
            sources=["https://nextjs.org/docs/app/building-your-application/routing/parallel-routes#defaultjs"]),
         wa("Add default.tsx to every parallel route slot that might not match", 0.90,
            sources=["https://nextjs.org/docs/app/building-your-application/routing/parallel-routes"])],
    ))

    c.append(canon(
        "nextjs", "cookies-headers-in-page", "nextjs14-linux",
        "Error: Dynamic server usage: cookies/headers() used in a page that will be statically generated",
        r"Dynamic server usage.*cookies|Dynamic server usage.*headers|cookies.*static.*generated",
        "rendering_error", "nextjs", ">=14,<16", "linux",
        "true", 0.90, 0.92,
        "Using cookies()/headers() makes the page dynamic, conflicting with static generation.",
        [de("Remove cookies/headers calls",
            "May break auth or personalization features", 0.60,
            sources=["https://nextjs.org/docs/app/api-reference/functions/cookies"])],
        [wa("Add export const dynamic = 'force-dynamic' to opt into dynamic rendering", 0.95,
            sources=["https://nextjs.org/docs/app/api-reference/file-conventions/route-segment-config#dynamic"]),
         wa("Move cookie/header access to middleware or API routes if possible", 0.85,
            sources=["https://nextjs.org/docs/app/building-your-application/routing/middleware"])],
    ))

    # ── DOCKER ──────────────────────────────────────────

    c.append(canon(
        "docker", "build-arg-not-set", "docker27-linux",
        "WARNING: One or more build-args were not consumed: ARG_NAME",
        r"build-args? were not consumed|ARG.*not used|undefined.*ARG",
        "build_warning", "docker", ">=27,<28", "linux",
        "true", 0.90, 0.90,
        "Docker build-arg passed but not used in Dockerfile. Typo or missing ARG instruction.",
        [de("Ignore the warning",
            "The build-arg is probably needed — something is misconfigured", 0.55,
            sources=["https://docs.docker.com/reference/dockerfile/#arg"])],
        [wa("Add ARG instruction in the Dockerfile: ARG ARG_NAME", 0.95,
            "ARG ARG_NAME\nRUN echo $ARG_NAME",
            sources=["https://docs.docker.com/reference/dockerfile/#arg"]),
         wa("Check for typos between --build-arg name and ARG name in Dockerfile", 0.92,
            sources=["https://docs.docker.com/reference/dockerfile/#arg"]),
         wa("In multi-stage builds, ARG must be declared in each stage that uses it", 0.88,
            sources=["https://docs.docker.com/reference/dockerfile/#understand-how-arg-and-from-interact"])],
    ))

    c.append(canon(
        "docker", "compose-service-depends-on", "docker27-linux",
        "dependency failed to start: container exited (depends_on service failed)",
        r"dependency failed|depends_on.*failed|service.*failed to start.*depends",
        "orchestration_error", "docker", ">=27,<28", "linux",
        "partial", 0.82, 0.85,
        "depends_on service crashed. The dependency container exited before the dependent started.",
        [de("Remove depends_on",
            "Service may start before its dependency, causing connection errors", 0.65,
            sources=["https://docs.docker.com/reference/compose-file/services/#depends_on"])],
        [wa("Use depends_on with condition: service_healthy and add healthcheck", 0.95,
            "depends_on:\n  db:\n    condition: service_healthy",
            sources=["https://docs.docker.com/reference/compose-file/services/#depends_on"]),
         wa("Fix the dependency container's error first — check its logs: docker compose logs <service>", 0.92,
            sources=["https://docs.docker.com/reference/cli/docker/compose/logs/"])],
    ))

    # ── GIT ──────────────────────────────────────────

    c.append(canon(
        "git", "tag-already-exists", "git2-linux",
        "fatal: tag 'v1.0.0' already exists",
        r"fatal: tag .+ already exists",
        "tag_error", "git", ">=2.30,<3.0", "linux",
        "true", 0.95, 0.95,
        "Tag name already in use. Tags are unique identifiers.",
        [de("Delete all tags and recreate",
            "May break CI/CD and release references", 0.75,
            sources=["https://git-scm.com/docs/git-tag"])],
        [wa("Use git tag -f to force update an existing tag (local)", 0.88,
            "git tag -f v1.0.0\ngit push origin -f v1.0.0  # update remote too",
            sources=["https://git-scm.com/docs/git-tag#Documentation/git-tag.txt--f"]),
         wa("Use a different tag name: v1.0.1, v1.0.0-rc2, etc.", 0.92,
            sources=["https://git-scm.com/docs/git-tag"])],
    ))

    c.append(canon(
        "git", "worktree-locked", "git2-linux",
        "fatal: 'path' is a missing but locked worktree",
        r"locked worktree|worktree.*locked|fatal.*missing.*locked",
        "worktree_error", "git", ">=2.30,<3.0", "linux",
        "true", 0.90, 0.90,
        "Git worktree was deleted from disk but git still tracks it as locked.",
        [de("Delete .git/worktrees manually",
            "May break other valid worktrees", 0.70,
            sources=["https://git-scm.com/docs/git-worktree"])],
        [wa("Unlock and remove: git worktree unlock <path> && git worktree prune", 0.95,
            sources=["https://git-scm.com/docs/git-worktree"]),
         wa("Use git worktree prune to clean up stale worktree entries", 0.92,
            sources=["https://git-scm.com/docs/git-worktree#Documentation/git-worktree.txt-prune"])],
    ))

    # ── KUBERNETES ──────────────────────────────────────────

    c.append(canon(
        "kubernetes", "pod-terminating-stuck", "k8s1-linux",
        "Pod stuck in Terminating state",
        r"Terminating.*stuck|stuck.*Terminating|pod.*terminating.*timeout",
        "lifecycle_error", "kubernetes", ">=1.28,<2.0", "linux",
        "partial", 0.82, 0.85,
        "Pod won't terminate. Finalizers, stuck containers, or graceful shutdown timeout.",
        [de("Set terminationGracePeriodSeconds to 0",
            "Skips graceful shutdown — data loss risk", 0.65,
            sources=["https://kubernetes.io/docs/concepts/workloads/pods/pod-lifecycle/#pod-termination"])],
        [wa("Force delete: kubectl delete pod <name> --grace-period=0 --force", 0.90,
            sources=["https://kubernetes.io/docs/tasks/run-application/force-delete-stateful-set-pod/"]),
         wa("Check for finalizers preventing deletion: kubectl get pod <name> -o json | jq '.metadata.finalizers'", 0.88,
            sources=["https://kubernetes.io/docs/concepts/overview/working-with-objects/finalizers/"]),
         wa("Check if the container's SIGTERM handler is stuck — may need code fix", 0.82,
            sources=["https://kubernetes.io/docs/concepts/workloads/pods/pod-lifecycle/#pod-termination"])],
    ))

    c.append(canon(
        "kubernetes", "horizontal-pod-autoscaler-unable", "k8s1-linux",
        "HPA unable to fetch metrics: missing request for cpu/memory",
        r"unable to (fetch|get) metrics|missing request for (cpu|memory)|FailedGetResourceMetric",
        "autoscaling_error", "kubernetes", ">=1.28,<2.0", "linux",
        "true", 0.88, 0.90,
        "HPA can't autoscale because pods don't have resource requests defined.",
        [de("Remove the HPA",
            "Loses autoscaling capability", 0.70,
            sources=["https://kubernetes.io/docs/tasks/run-application/horizontal-pod-autoscale/"])],
        [wa("Add resource requests to pod spec — HPA needs them to calculate utilization", 0.95,
            "resources:\n  requests:\n    cpu: 200m\n    memory: 256Mi",
            sources=["https://kubernetes.io/docs/tasks/run-application/horizontal-pod-autoscale/"]),
         wa("Ensure metrics-server is installed and running: kubectl top pods", 0.90,
            sources=["https://kubernetes.io/docs/tasks/debug/debug-cluster/resource-metrics-pipeline/"])],
    ))

    # ── CUDA ──────────────────────────────────────────

    c.append(canon(
        "cuda", "nccl-unhandled-system-error", "torch2.1-multi-gpu",
        "RuntimeError: NCCL error: unhandled system error, NCCL version",
        r"NCCL.*unhandled system error|NCCL.*system error|nccl.*SystemError",
        "distributed_error", "cuda", ">=12.0,<13.0", "linux",
        "partial", 0.75, 0.82,
        "NCCL multi-GPU communication failed. Network, driver, or IPC issue.",
        [de("Set NCCL_DEBUG=INFO for more details (and stop there)",
            "DEBUG helps diagnose but doesn't fix the issue", 0.50,
            sources=["https://docs.nvidia.com/deeplearning/nccl/user-guide/docs/env.html"])],
        [wa("Set NCCL_SOCKET_IFNAME to the correct network interface", 0.88,
            "export NCCL_SOCKET_IFNAME=eth0",
            sources=["https://docs.nvidia.com/deeplearning/nccl/user-guide/docs/env.html#nccl-socket-ifname"]),
         wa("Update NVIDIA driver and NCCL to latest compatible versions", 0.85,
            sources=["https://docs.nvidia.com/deeplearning/nccl/install-guide/index.html"]),
         wa("Try NCCL_P2P_DISABLE=1 if peer-to-peer GPU communication fails", 0.80,
            sources=["https://docs.nvidia.com/deeplearning/nccl/user-guide/docs/env.html"])],
        gpu="multi-gpu",
    ))

    # ── RUST ──────────────────────────────────────────

    c.append(canon(
        "rust", "e0499-mutable-borrow-twice", "rust1-linux",
        "error[E0499]: cannot borrow `x` as mutable more than once at a time",
        r"E0499.*cannot borrow.*mutable more than once",
        "ownership_error", "rust", ">=1.70,<2.0", "linux",
        "true", 0.88, 0.90,
        "Two mutable borrows active simultaneously. Rust enforces exclusive mutable access.",
        [de("Use unsafe to bypass the borrow checker",
            "Causes undefined behavior if two mutable references overlap", 0.95,
            sources=["https://doc.rust-lang.org/error_codes/E0499.html"])],
        [wa("Split the operation so only one mutable borrow exists at a time", 0.92,
            "let val = map.get(&key).cloned();\nmap.insert(key, transform(val));  // borrows don't overlap",
            sources=["https://doc.rust-lang.org/book/ch04-02-references-and-borrowing.html"]),
         wa("Use RefCell for runtime borrow checking when compile-time is too restrictive", 0.85,
            "use std::cell::RefCell;\nlet data = RefCell::new(vec![]);\ndata.borrow_mut().push(1);",
            sources=["https://doc.rust-lang.org/std/cell/struct.RefCell.html"])],
    ))

    # ── GO ──────────────────────────────────────────

    c.append(canon(
        "go", "channel-deadlock", "go1-linux",
        "fatal error: all goroutines are asleep - deadlock!",
        r"all goroutines are asleep.*deadlock|fatal error.*deadlock",
        "concurrency_error", "go", ">=1.21,<2.0", "linux",
        "true", 0.88, 0.90,
        "All goroutines blocked waiting on channels. No goroutine can make progress.",
        [de("Use buffered channels with large buffer",
            "Large buffers just delay the deadlock", 0.65,
            sources=["https://go.dev/ref/spec#Channel_types"])],
        [wa("Ensure every channel send has a corresponding receive (and vice versa)", 0.92,
            sources=["https://go.dev/doc/effective_go#channels"]),
         wa("Use select with default case for non-blocking channel operations", 0.88,
            "select {\ncase msg := <-ch:\n    handle(msg)\ndefault:\n    // don't block\n}",
            sources=["https://go.dev/ref/spec#Select_statements"]),
         wa("Close channels when done sending: close(ch)", 0.85,
            sources=["https://go.dev/ref/spec#Close"])],
    ))

    c.append(canon(
        "go", "json-unmarshal-wrong-type", "go1-linux",
        "json: cannot unmarshal string into Go struct field X of type int",
        r"json: cannot unmarshal .+ into Go (struct field|value of type)",
        "serialization_error", "go", ">=1.21,<2.0", "linux",
        "true", 0.92, 0.92,
        "JSON field type doesn't match Go struct type. API returns string '123' but struct expects int.",
        [de("Use interface{} for all struct fields",
            "Loses all type safety — every field needs type assertion", 0.75,
            sources=["https://pkg.go.dev/encoding/json#Unmarshal"])],
        [wa("Use json.Number or custom UnmarshalJSON for flexible types", 0.90,
            "type MyStruct struct {\n    Count json.Number `json:\"count\"`\n}",
            sources=["https://pkg.go.dev/encoding/json#Number"]),
         wa("Match struct field types to actual JSON — use string if API sends strings", 0.92,
            sources=["https://pkg.go.dev/encoding/json#Unmarshal"]),
         wa("Use string tag for numeric fields that come as strings: `json:\"id,string\"`", 0.88,
            sources=["https://pkg.go.dev/encoding/json#Marshal"])],
    ))

    # ── PIP ──────────────────────────────────────────

    c.append(canon(
        "pip", "no-space-left-during-install", "pip24-linux",
        "ERROR: Could not install packages due to an OSError: [Errno 28] No space left on device",
        r"No space left on device.*pip|pip.*Errno 28|Could not install.*No space",
        "disk_error", "pip", ">=24,<25", "linux",
        "partial", 0.80, 0.85,
        "Disk full during pip install. /tmp or pip cache filling up.",
        [de("Use --no-cache-dir to skip caching",
            "Helps but the package itself may need space for extraction", 0.55,
            sources=["https://pip.pypa.io/en/stable/cli/pip_install/#cmdoption-no-cache-dir"])],
        [wa("Clear pip cache: pip cache purge", 0.92,
            sources=["https://pip.pypa.io/en/stable/cli/pip_cache/"]),
         wa("Set TMPDIR to a volume with more space: export TMPDIR=/path/with/space", 0.88,
            sources=["https://pip.pypa.io/en/stable/topics/configuration/"]),
         wa("Free disk space: remove old virtualenvs, Docker images, or old log files", 0.85,
            sources=["https://pip.pypa.io/en/stable/cli/pip_cache/"])],
    ))

    # ── AWS ──────────────────────────────────────────

    c.append(canon(
        "aws", "lambda-timeout", "awscli2-linux",
        "Task timed out after X.XX seconds (Lambda timeout)",
        r"Task timed out|Lambda.*timeout|Execution timed out",
        "timeout_error", "aws", ">=2.0,<3.0", "linux",
        "partial", 0.82, 0.85,
        "Lambda function exceeded its timeout. Default is 3 seconds, max 15 minutes.",
        [de("Set timeout to 15 minutes for everything",
            "Long timeouts waste money and may indicate a performance issue", 0.60,
            sources=["https://docs.aws.amazon.com/lambda/latest/dg/configuration-function-common.html#configuration-timeout"])],
        [wa("Increase timeout in function config to match expected execution time", 0.90,
            "aws lambda update-function-configuration --function-name X --timeout 30",
            sources=["https://docs.aws.amazon.com/lambda/latest/dg/configuration-function-common.html#configuration-timeout"]),
         wa("Check what's slow: cold start, DB connections, external API calls", 0.88,
            sources=["https://docs.aws.amazon.com/lambda/latest/dg/lambda-troubleshooting.html"]),
         wa("Use provisioned concurrency to eliminate cold start delays", 0.80,
            sources=["https://docs.aws.amazon.com/lambda/latest/dg/provisioned-concurrency.html"])],
    ))

    c.append(canon(
        "aws", "ecr-login-required", "awscli2-linux",
        "Error: pull access denied or repository does not exist (ECR login required)",
        r"pull access denied.*ECR|ecr.*login|authorization token.*ecr|denied.*repository",
        "auth_error", "aws", ">=2.0,<3.0", "linux",
        "true", 0.92, 0.92,
        "ECR pull requires authentication. Docker login token expires after 12 hours.",
        [de("Make the ECR repository public",
            "Security risk — exposes private images to everyone", 0.85,
            sources=["https://docs.aws.amazon.com/AmazonECR/latest/userguide/repository-policies.html"])],
        [wa("Login to ECR: aws ecr get-login-password | docker login --username AWS --password-stdin <account>.dkr.ecr.<region>.amazonaws.com", 0.95,
            sources=["https://docs.aws.amazon.com/AmazonECR/latest/userguide/registry_auth.html"]),
         wa("For Kubernetes, create an ECR pull secret or use IRSA for EKS", 0.88,
            sources=["https://docs.aws.amazon.com/AmazonECR/latest/userguide/registry_auth.html"]),
         wa("Add ECR login to CI/CD pipeline — token expires every 12 hours", 0.85,
            sources=["https://docs.aws.amazon.com/AmazonECR/latest/userguide/registry_auth.html"])],
    ))

    # ── TERRAFORM ──────────────────────────────────────────

    c.append(canon(
        "terraform", "count-and-for-each-conflict", "tf1-linux",
        "Error: Invalid combination of 'count' and 'for_each'",
        r"Invalid combination.*count.*for_each|count.*for_each.*mutually exclusive",
        "config_error", "terraform", ">=1.5,<2.0", "linux",
        "true", 0.95, 0.95,
        "Can't use both count and for_each on the same resource. They're mutually exclusive.",
        [de("Nest resources inside dynamic blocks",
            "Dynamic blocks are for nested blocks, not resource iteration", 0.70,
            sources=["https://developer.hashicorp.com/terraform/language/meta-arguments/count"])],
        [wa("Choose one: use for_each for maps/sets, count for simple numeric iteration", 0.95,
            sources=["https://developer.hashicorp.com/terraform/language/meta-arguments/for_each"]),
         wa("Convert count to for_each: for_each = toset(range(var.instance_count))", 0.88,
            sources=["https://developer.hashicorp.com/terraform/language/meta-arguments/for_each"])],
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
    print(f"Wave 9: wrote {written} new canons, skipped {skipped} existing")


if __name__ == "__main__":
    main()
