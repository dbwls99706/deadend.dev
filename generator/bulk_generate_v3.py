"""Bulk generate wave 3: +50 canons (target: 152 total).

Usage: python -m generator.bulk_generate_v3
"""

import json
from generator.bulk_generate import (
    canon, de, wa, leads, preceded, confused, DATA_DIR,
)


def get_all_canons():
    c = []

    # ── PYTHON ──────────────────────────────────────────

    c.append(canon(
        "python", "zerodivisionerror", "py311-linux",
        "ZeroDivisionError: division by zero",
        r"ZeroDivisionError: (division|integer division|modulo) by zero",
        "math_error", "python", ">=3.11,<3.13", "linux",
        "true", 0.95, 0.95,
        "Division by zero. Common in averages, ratios, normalization.",
        [de("Wrap in try/except and return 0",
            "Silently returns wrong result", 0.70,
            sources=["https://docs.python.org/3/library/exceptions.html#ZeroDivisionError"]),
         de("Add epsilon (1e-10) to denominator",
            "Masks data issues, can produce huge values", 0.55,
            sources=["https://docs.python.org/3/tutorial/floatingpoint.html"])],
        [wa("Check denominator before dividing, handle the zero case explicitly", 0.95,
            "avg = total / count if count else 0.0",
            sources=["https://docs.python.org/3/library/exceptions.html#ZeroDivisionError"]),
         wa("Investigate why denominator is zero — usually missing/filtered data", 0.90,
            sources=["https://docs.python.org/3/library/functions.html#breakpoint"])],
        python=">=3.11,<3.13",
    ))

    c.append(canon(
        "python", "typeerror-missing-argument", "py311-linux",
        "TypeError: function() missing 1 required positional argument",
        r"TypeError: \w+\(\) missing \d+ required positional argument",
        "type_error", "python", ">=3.11,<3.13", "linux",
        "true", 0.95, 0.95,
        "Function called with wrong number of args. Common after refactoring or missing self.",
        [de("Add default=None to all params",
            "Hides the real issue — caller should provide the value", 0.65,
            sources=["https://docs.python.org/3/tutorial/controlflow.html#default-argument-values"]),
         de("Use *args/**kwargs to accept anything",
            "Loses function signature, makes bugs harder to find", 0.75,
            sources=["https://docs.python.org/3/tutorial/controlflow.html#arbitrary-argument-lists"])],
        [wa("Check if calling instance method without self, or missing args after refactor", 0.95,
            sources=["https://docs.python.org/3/tutorial/classes.html#method-objects"]),
         wa("Compare call site args with function signature", 0.92,
            sources=["https://docs.python.org/3/library/inspect.html#inspect.signature"])],
        python=">=3.11,<3.13",
    ))

    c.append(canon(
        "python", "importerror-cannot-import-name", "py311-linux",
        "ImportError: cannot import name 'X' from 'module'",
        r"ImportError: cannot import name '(.+?)' from '(.+?)'",
        "import_error", "python", ">=3.11,<3.13", "linux",
        "true", 0.88, 0.90,
        "Circular import or name doesn't exist in module. Very common in Django/Flask projects.",
        [de("Move import to top of file",
            "May worsen circular import", 0.60,
            sources=["https://docs.python.org/3/reference/import.html"]),
         de("Rename conflicting module",
            "Doesn't fix the circular dependency", 0.50,
            sources=["https://docs.python.org/3/faq/programming.html#what-are-the-best-practices-for-using-import-in-a-module"])],
        [wa("Use lazy import inside function to break circular dependency", 0.90,
            "def func():\n    from module import name",
            sources=["https://docs.python.org/3/reference/import.html"]),
         wa("Restructure modules to eliminate circular dependency", 0.88,
            sources=["https://docs.python.org/3/faq/programming.html#what-are-the-best-practices-for-using-import-in-a-module"])],
        python=">=3.11,<3.13",
    ))

    c.append(canon(
        "python", "oserror-too-many-open-files", "py311-linux",
        "OSError: [Errno 24] Too many open files",
        r"OSError: \[Errno 24\] Too many open files",
        "os_error", "python", ">=3.11,<3.13", "linux",
        "true", 0.85, 0.88,
        "Process exceeded file descriptor limit. Common in servers and data pipelines.",
        [de("Increase ulimit to very high value",
            "Band-aid — the real issue is file descriptor leak", 0.60,
            sources=["https://docs.python.org/3/library/resource.html"]),
         de("Ignore the error and retry",
            "Makes the leak worse over time", 0.80,
            sources=["https://docs.python.org/3/library/exceptions.html#OSError"])],
        [wa("Use context managers (with statement) to ensure files are closed", 0.95,
            "with open(path) as f: data = f.read()",
            sources=["https://docs.python.org/3/reference/compound_stmts.html#the-with-statement"]),
         wa("Find leaked file descriptors with lsof or /proc/self/fd", 0.85,
            "ls -la /proc/self/fd | wc -l",
            sources=["https://docs.python.org/3/library/os.html#os.listdir"])],
        python=">=3.11,<3.13",
    ))

    c.append(canon(
        "python", "timeouterror", "py311-linux",
        "TimeoutError: [Errno 110] Connection timed out",
        r"TimeoutError|timed? ?out",
        "network_error", "python", ">=3.11,<3.13", "linux",
        "true", 0.80, 0.82,
        "Network connection or operation timed out.",
        [de("Increase timeout to very large value",
            "Just delays the failure, doesn't fix the network issue", 0.65,
            sources=["https://docs.python.org/3/library/socket.html#socket.settimeout"]),
         de("Remove timeout entirely",
            "Process hangs forever on unreachable hosts", 0.85,
            sources=["https://docs.python.org/3/library/socket.html"])],
        [wa("Add retry with exponential backoff for transient failures", 0.90,
            sources=["https://docs.python.org/3/library/urllib.request.html"]),
         wa("Verify target host is reachable: DNS, firewall, port", 0.88,
            sources=["https://docs.python.org/3/library/socket.html#socket.create_connection"])],
        python=">=3.11,<3.13",
    ))

    c.append(canon(
        "python", "runtimeerror-event-loop", "py311-linux",
        "RuntimeError: This event loop is already running",
        r"RuntimeError: This event loop is already running",
        "async_error", "python", ">=3.11,<3.13", "linux",
        "true", 0.82, 0.85,
        "Calling asyncio.run() inside an already-running loop. Common in Jupyter and web frameworks.",
        [de("Use nest_asyncio.apply()",
            "Monkey-patches asyncio, can cause subtle bugs in production", 0.55,
            sources=["https://docs.python.org/3/library/asyncio-eventloop.html"]),
         de("Create new event loop in thread",
            "Complex, error-prone, usually unnecessary", 0.65,
            sources=["https://docs.python.org/3/library/asyncio-eventloop.html#asyncio.new_event_loop"])],
        [wa("Use await directly instead of asyncio.run() when already in async context", 0.92,
            "result = await async_function()",
            sources=["https://docs.python.org/3/library/asyncio-task.html"]),
         wa("In Jupyter: use await directly (Jupyter runs its own event loop)", 0.90,
            sources=["https://docs.python.org/3/library/asyncio-runner.html"])],
        python=">=3.11,<3.13",
    ))

    c.append(canon(
        "python", "typeerror-unhashable-list", "py311-linux",
        "TypeError: unhashable type: 'list'",
        r"TypeError: unhashable type: '(list|dict|set)'",
        "type_error", "python", ">=3.11,<3.13", "linux",
        "true", 0.92, 0.93,
        "Using mutable type as dict key or set element.",
        [de("Convert list to str for hashing",
            "str representation can collide: [1,2] vs [12]", 0.55,
            sources=["https://docs.python.org/3/glossary.html#term-hashable"]),
         de("Use id() as key",
            "id changes across runs, not based on content", 0.70,
            sources=["https://docs.python.org/3/library/functions.html#id"])],
        [wa("Convert list to tuple for use as dict key or set element", 0.95,
            "d[tuple(my_list)] = value",
            sources=["https://docs.python.org/3/glossary.html#term-hashable"]),
         wa("Use frozenset for set-of-sets patterns", 0.88,
            sources=["https://docs.python.org/3/library/stdtypes.html#frozenset"])],
        python=">=3.11,<3.13",
    ))

    c.append(canon(
        "python", "valueerror-too-many-values-unpack", "py311-linux",
        "ValueError: too many values to unpack (expected 2)",
        r"ValueError: (too many|not enough) values to unpack",
        "value_error", "python", ">=3.11,<3.13", "linux",
        "true", 0.92, 0.93,
        "Unpacking assignment count mismatch. Common with CSV, split(), and tuple returns.",
        [de("Pad or truncate the iterable",
            "Silently drops or fabricates data", 0.70,
            sources=["https://docs.python.org/3/tutorial/datastructures.html#tuples-and-sequences"]),
         de("Catch ValueError and skip the row",
            "Loses data without understanding why", 0.60,
            sources=["https://docs.python.org/3/library/exceptions.html#ValueError"])],
        [wa("Check actual length of data; use *rest for variable-length unpacking", 0.92,
            "first, *rest = line.split(',')",
            sources=["https://docs.python.org/3/tutorial/datastructures.html#tuples-and-sequences"]),
         wa("Validate data format before unpacking", 0.88,
            sources=["https://docs.python.org/3/library/csv.html"])],
        python=">=3.11,<3.13",
    ))

    # ── NODE ────────────────────────────────────────────

    c.append(canon(
        "node", "err-invalid-arg-type", "node20-linux",
        "TypeError [ERR_INVALID_ARG_TYPE]: The argument must be of type string",
        r"ERR_INVALID_ARG_TYPE",
        "type_error", "node", ">=20,<23", "linux",
        "true", 0.90, 0.90,
        "Wrong argument type passed to Node.js API. Common with Buffer/string confusion.",
        [de("Force cast with String() or Buffer.from()",
            "Hides the real source of wrong type", 0.60,
            sources=["https://nodejs.org/api/errors.html#err_invalid_arg_type"]),
         de("Use any type and bypass checks",
            "Pushes error downstream", 0.70,
            sources=["https://nodejs.org/api/errors.html"])],
        [wa("Check the calling code — trace where wrong type originates", 0.92,
            sources=["https://nodejs.org/api/errors.html#err_invalid_arg_type"]),
         wa("Add TypeScript or JSDoc types to catch at compile time", 0.85,
            sources=["https://www.typescriptlang.org/docs/handbook/jsdoc-supported-types.html"])],
    ))

    c.append(canon(
        "node", "unhandled-promise-rejection", "node20-linux",
        "UnhandledPromiseRejectionWarning: Error: something failed",
        r"UnhandledPromiseRejection|unhandled promise rejection",
        "async_error", "node", ">=20,<23", "linux",
        "true", 0.88, 0.90,
        "Promise rejected without .catch() or try/catch in async. Crashes process in Node 15+.",
        [de("Add process.on('unhandledRejection') global handler",
            "Catches everything, makes individual errors hard to debug", 0.55,
            sources=["https://nodejs.org/api/process.html#event-unhandledrejection"]),
         de("Add .catch(() => {}) to silence",
            "Swallows all errors silently", 0.85,
            sources=["https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Promise/catch"])],
        [wa("Add try/catch in async functions or .catch() with proper error handling", 0.92,
            "try { await fn() } catch(e) { logger.error(e) }",
            sources=["https://nodejs.org/api/process.html#event-unhandledrejection"]),
         wa("Use Promise.allSettled() for parallel promises that may individually fail", 0.85,
            sources=["https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Promise/allSettled"])],
    ))

    c.append(canon(
        "node", "enospc-watchers", "node20-linux",
        "Error: ENOSPC: System limit for number of file watchers reached",
        r"ENOSPC.*file watchers|inotify.*limit",
        "system_error", "node", ">=20,<23", "linux",
        "true", 0.90, 0.92,
        "Linux inotify watcher limit hit. Common with webpack/vite dev servers in large projects.",
        [de("Restart the dev server repeatedly",
            "Same limit hit again immediately", 0.85,
            sources=["https://nodejs.org/api/errors.html#common-system-errors"]),
         de("Disable file watching entirely",
            "Loses hot reload, defeats purpose of dev server", 0.60,
            sources=["https://nodejs.org/api/fs.html#fswatchfilename-options-listener"])],
        [wa("Increase inotify limit: echo 65536 | sudo tee /proc/sys/fs/inotify/max_user_watches", 0.95,
            "echo fs.inotify.max_user_watches=65536 | sudo tee -a /etc/sysctl.conf && sudo sysctl -p",
            sources=["https://nodejs.org/api/fs.html#caveats"]),
         wa("Exclude node_modules from watching in bundler config", 0.88,
            sources=["https://vitejs.dev/config/server-options.html#server-watch"])],
    ))

    c.append(canon(
        "node", "err-unknown-file-extension", "node20-linux",
        "TypeError [ERR_UNKNOWN_FILE_EXTENSION]: Unknown file extension '.ts'",
        r"ERR_UNKNOWN_FILE_EXTENSION",
        "module_error", "node", ">=20,<23", "linux",
        "true", 0.88, 0.90,
        "Node.js can't handle .ts/.jsx file directly. Need loader or compilation step.",
        [de("Rename .ts to .js",
            "Loses TypeScript type checking entirely", 0.80,
            sources=["https://nodejs.org/api/errors.html#err_unknown_file_extension"]),
         de("Add type:module to package.json",
            "Doesn't help — Node still can't parse TypeScript", 0.70,
            sources=["https://nodejs.org/api/packages.html#type"])],
        [wa("Use tsx or ts-node for TypeScript execution", 0.95,
            "npx tsx script.ts",
            sources=["https://nodejs.org/api/typescript.html"]),
         wa("Use --loader flag with ts-node/esm", 0.85,
            "node --loader ts-node/esm script.ts",
            sources=["https://nodejs.org/api/esm.html#loaders"])],
    ))

    # ── TYPESCRIPT ───────────────────────────────────────

    c.append(canon(
        "typescript", "ts2339-property-not-exist", "ts5-linux",
        "error TS2339: Property 'x' does not exist on type 'Y'",
        r"error TS2339: Property '(.+?)' does not exist on type",
        "type_error", "typescript", ">=5.0,<6.0", "linux",
        "true", 0.90, 0.92,
        "Accessing property not in type definition. Common with API responses and DOM.",
        [de("Cast to any",
            "Removes all type safety", 0.80,
            sources=["https://www.typescriptlang.org/docs/handbook/2/everyday-types.html#any"]),
         de("Add // @ts-expect-error",
            "Silences compiler without fixing the type", 0.75,
            sources=["https://www.typescriptlang.org/docs/handbook/release-notes/typescript-3-9.html"])],
        [wa("Extend the type definition or use type assertion with proper type", 0.92,
            "interface Extended extends Base { newProp: string }",
            sources=["https://www.typescriptlang.org/docs/handbook/2/objects.html#extending-types"]),
         wa("Use 'in' operator for type narrowing", 0.88,
            "if ('prop' in obj) { obj.prop }",
            sources=["https://www.typescriptlang.org/docs/handbook/2/narrowing.html#the-in-operator-narrowing"])],
    ))

    c.append(canon(
        "typescript", "ts2741-missing-property", "ts5-linux",
        "error TS2741: Property 'x' is missing in type 'A' but required in type 'B'",
        r"error TS2741: Property '(.+?)' is missing in type",
        "type_error", "typescript", ">=5.0,<6.0", "linux",
        "true", 0.92, 0.93,
        "Object literal missing required property. Common with React props and API payloads.",
        [de("Make all properties optional with Partial<T>",
            "Removes all required field guarantees", 0.70,
            sources=["https://www.typescriptlang.org/docs/handbook/utility-types.html#partialtype"]),
         de("Add as Type assertion",
            "Bypasses check, will fail at runtime", 0.75,
            sources=["https://www.typescriptlang.org/docs/handbook/2/everyday-types.html#type-assertions"])],
        [wa("Add the missing property to the object", 0.95,
            sources=["https://www.typescriptlang.org/docs/handbook/2/objects.html"]),
         wa("If intentionally optional, mark with ? in the type definition", 0.88,
            "interface Props { required: string; optional?: number }",
            sources=["https://www.typescriptlang.org/docs/handbook/2/objects.html#optional-properties"])],
    ))

    # ── REACT ───────────────────────────────────────────

    c.append(canon(
        "react", "objects-not-valid-as-child", "react18-linux",
        "Error: Objects are not valid as a React child",
        r"Objects are not valid as a React child",
        "render_error", "react", ">=18,<20", "linux",
        "true", 0.90, 0.92,
        "Trying to render a plain object in JSX. Common with Date objects, API responses.",
        [de("Use JSON.stringify() in JSX",
            "Shows raw JSON to users, not a real UI", 0.65,
            sources=["https://react.dev/reference/react/Children"]),
         de("Wrap object in String()",
            "Shows [object Object]", 0.80,
            sources=["https://react.dev/learn/rendering-lists"])],
        [wa("Render specific properties of the object, not the object itself", 0.95,
            "<p>{user.name}</p> instead of <p>{user}</p>",
            sources=["https://react.dev/learn/rendering-lists"]),
         wa("For arrays, use .map() to render each element", 0.90,
            "{items.map(item => <li key={item.id}>{item.name}</li>)}",
            sources=["https://react.dev/learn/rendering-lists"])],
    ))

    c.append(canon(
        "react", "each-child-unique-key", "react18-linux",
        "Warning: Each child in a list should have a unique 'key' prop",
        r"Each child in a list should have a unique .key. prop",
        "render_warning", "react", ">=18,<20", "linux",
        "true", 0.95, 0.95,
        "Missing or non-unique key prop on list items. Causes incorrect re-renders.",
        [de("Use array index as key",
            "Causes bugs when list is reordered/filtered/sorted", 0.65,
            sources=["https://react.dev/learn/rendering-lists#keeping-list-items-in-order-with-key"]),
         de("Use Math.random() as key",
            "New key every render, destroys all component state", 0.90,
            sources=["https://react.dev/learn/rendering-lists#rules-of-keys"])],
        [wa("Use a stable unique identifier from data (id, slug, etc.)", 0.95,
            "{items.map(item => <Item key={item.id} {...item} />)}",
            sources=["https://react.dev/learn/rendering-lists#where-to-get-your-key"]),
         wa("If no ID exists, generate stable keys from content hash", 0.82,
            sources=["https://react.dev/learn/rendering-lists#rules-of-keys"])],
    ))

    c.append(canon(
        "react", "useeffect-missing-dependency", "react18-linux",
        "React Hook useEffect has a missing dependency",
        r"React Hook use\w+ has a missing dependency",
        "hook_warning", "react", ">=18,<20", "linux",
        "true", 0.85, 0.88,
        "ESLint exhaustive-deps rule warning. Tricky — blindly adding deps can cause infinite loops.",
        [de("Disable the ESLint rule",
            "Hides real bugs — stale closures cause subtle issues", 0.65,
            sources=["https://react.dev/reference/react/useEffect#specifying-reactive-dependencies"]),
         de("Add all listed deps immediately",
            "Can cause infinite re-render if dep is object/array created in render", 0.55,
            sources=["https://react.dev/reference/react/useEffect"])],
        [wa("Memoize object/array deps with useMemo, or move them inside useEffect", 0.90,
            sources=["https://react.dev/reference/react/useMemo"]),
         wa("Extract the function used in useEffect to useCallback if it's a dep", 0.85,
            sources=["https://react.dev/reference/react/useCallback"])],
    ))

    # ── NEXTJS ──────────────────────────────────────────

    c.append(canon(
        "nextjs", "dynamic-server-usage", "nextjs14-linux",
        "Error: Dynamic server usage: Route couldn't be rendered statically",
        r"Dynamic server usage|couldn't be rendered statically",
        "build_error", "nextjs", ">=14,<16", "linux",
        "true", 0.85, 0.88,
        "Using dynamic APIs (cookies, headers, searchParams) in statically rendered route.",
        [de("Add export const dynamic = 'force-dynamic' to everything",
            "Disables all static optimization, defeats Next.js purpose", 0.60,
            sources=["https://nextjs.org/docs/app/api-reference/file-conventions/route-segment-config"]),
         de("Wrap in try/catch and return fallback",
            "Returns wrong data to users", 0.70,
            sources=["https://nextjs.org/docs/app/building-your-application/rendering"])],
        [wa("Use dynamic = 'force-dynamic' only on routes that genuinely need it", 0.90,
            sources=["https://nextjs.org/docs/app/api-reference/file-conventions/route-segment-config"]),
         wa("Move dynamic data fetching to client components with useEffect", 0.85,
            sources=["https://nextjs.org/docs/app/building-your-application/rendering/client-components"])],
    ))

    c.append(canon(
        "nextjs", "cannot-read-properties-searchparams", "nextjs14-linux",
        "TypeError: Cannot read properties of undefined (reading 'searchParams')",
        r"Cannot read properties of undefined.*searchParams",
        "type_error", "nextjs", ">=14,<16", "linux",
        "true", 0.88, 0.88,
        "searchParams is now a Promise in Next.js 15+, or page component not receiving props correctly.",
        [de("Use window.location.search instead",
            "Doesn't work in server components", 0.75,
            sources=["https://nextjs.org/docs/app/api-reference/file-conventions/page"]),
         de("Default to empty object",
            "Silently ignores URL parameters", 0.60,
            sources=["https://nextjs.org/docs/app/api-reference/functions/use-search-params"])],
        [wa("Ensure page component accepts { searchParams } prop correctly", 0.92,
            "export default function Page({ searchParams }: { searchParams: { q?: string } })",
            sources=["https://nextjs.org/docs/app/api-reference/file-conventions/page"]),
         wa("Use useSearchParams() hook in client components", 0.88,
            sources=["https://nextjs.org/docs/app/api-reference/functions/use-search-params"])],
    ))

    # ── DOCKER ──────────────────────────────────────────

    c.append(canon(
        "docker", "apt-get-update-failed", "docker27-linux",
        "E: Failed to fetch http://archive.ubuntu.com/... 404 Not Found",
        r"E: Failed to fetch|apt-get update.*failed|404.*Not Found.*archive",
        "build_error", "docker", ">=27,<28", "linux",
        "true", 0.88, 0.90,
        "apt package cache stale in Docker build. Common with cached layers.",
        [de("Pin specific mirror URL",
            "Mirrors change too; doesn't fix stale cache layer", 0.60,
            sources=["https://docs.docker.com/build/cache/"]),
         de("Use --no-cache for entire build",
            "Rebuilds everything, very slow", 0.50,
            sources=["https://docs.docker.com/build/cache/"])],
        [wa("Always run apt-get update && apt-get install in same RUN layer", 0.95,
            "RUN apt-get update && apt-get install -y pkg && rm -rf /var/lib/apt/lists/*",
            sources=["https://docs.docker.com/build/building/best-practices/#apt-get"]),
         wa("Use specific base image tags, not :latest", 0.85,
            sources=["https://docs.docker.com/build/building/best-practices/#from"])],
    ))

    c.append(canon(
        "docker", "context-too-large", "docker27-linux",
        "Sending build context to Docker daemon: extremely slow / OOM",
        r"Sending build context.*daemon|context.*too (large|big)|\.dockerignore",
        "build_error", "docker", ">=27,<28", "linux",
        "true", 0.90, 0.92,
        "Docker build context includes unnecessary files (node_modules, .git, data).",
        [de("Increase Docker daemon memory",
            "Doesn't fix the root cause, still slow", 0.65,
            sources=["https://docs.docker.com/build/building/context/"]),
         de("Move Dockerfile to empty directory",
            "Breaks COPY commands, loses project context", 0.70,
            sources=["https://docs.docker.com/build/building/context/"])],
        [wa("Add .dockerignore with node_modules, .git, and data dirs", 0.95,
            "echo 'node_modules\\n.git\\n*.log' > .dockerignore",
            sources=["https://docs.docker.com/build/building/context/#dockerignore-files"]),
         wa("Use multi-stage builds to only copy needed files", 0.88,
            sources=["https://docs.docker.com/build/building/multi-stage/"])],
    ))

    c.append(canon(
        "docker", "healthcheck-unhealthy", "docker27-linux",
        "Container health status: unhealthy",
        r"health(check|y|status).*unhealthy|unhealthy.*container",
        "runtime_error", "docker", ">=27,<28", "linux",
        "true", 0.82, 0.85,
        "Container healthcheck failing. App may be starting slow or endpoint misconfigured.",
        [de("Remove healthcheck entirely",
            "Orchestrator can't detect failures, routes traffic to dead containers", 0.80,
            sources=["https://docs.docker.com/reference/dockerfile/#healthcheck"]),
         de("Set very long timeout/interval",
            "Delays failure detection, slow recovery", 0.55,
            sources=["https://docs.docker.com/reference/dockerfile/#healthcheck"])],
        [wa("Check healthcheck command matches actual app endpoint and port", 0.92,
            "docker inspect --format='{{json .State.Health}}' container_name",
            sources=["https://docs.docker.com/reference/dockerfile/#healthcheck"]),
         wa("Add start-period to allow for slow startup", 0.85,
            "HEALTHCHECK --start-period=30s --interval=10s CMD curl -f http://localhost:8080/health",
            sources=["https://docs.docker.com/reference/dockerfile/#healthcheck"])],
    ))

    # ── GIT ─────────────────────────────────────────────

    c.append(canon(
        "git", "detached-head", "git2-linux",
        "You are in 'detached HEAD' state",
        r"detached HEAD|HEAD detached at",
        "state_warning", "git", ">=2.30,<3.0", "linux",
        "true", 0.92, 0.93,
        "HEAD not on a branch. Commits may be lost if you switch branches.",
        [de("Just checkout another branch",
            "Loses any commits made in detached state", 0.80,
            sources=["https://git-scm.com/docs/git-checkout#_detached_head"]),
         de("Ignore the warning",
            "Commits become orphaned and eventually garbage collected", 0.75,
            sources=["https://git-scm.com/docs/git-checkout#_detached_head"])],
        [wa("Create a branch from current position: git checkout -b new-branch", 0.95,
            "git checkout -b my-work",
            sources=["https://git-scm.com/docs/git-checkout#_detached_head"]),
         wa("If already lost commits, find with git reflog and cherry-pick", 0.88,
            "git reflog | head -20",
            sources=["https://git-scm.com/docs/git-reflog"])],
    ))

    c.append(canon(
        "git", "permission-denied-publickey", "git2-linux",
        "Permission denied (publickey). fatal: Could not read from remote repository.",
        r"Permission denied \(publickey\)",
        "auth_error", "git", ">=2.30,<3.0", "linux",
        "true", 0.88, 0.90,
        "SSH key not configured or not added to SSH agent.",
        [de("Switch to HTTPS and enter password every time",
            "Tedious, and GitHub disabled password auth in 2021", 0.70,
            sources=["https://docs.github.com/en/authentication/connecting-to-github-with-ssh"]),
         de("Generate new key pair every time",
            "Doesn't help if the key isn't added to GitHub/agent", 0.60,
            sources=["https://docs.github.com/en/authentication/connecting-to-github-with-ssh/generating-a-new-ssh-key-and-adding-it-to-the-ssh-agent"])],
        [wa("Add SSH key to agent and verify: ssh-add, then ssh -T git@github.com", 0.92,
            "eval $(ssh-agent) && ssh-add ~/.ssh/id_ed25519 && ssh -T git@github.com",
            sources=["https://docs.github.com/en/authentication/connecting-to-github-with-ssh/testing-your-ssh-connection"]),
         wa("Use HTTPS with personal access token or gh auth login", 0.88,
            "gh auth login",
            sources=["https://cli.github.com/manual/gh_auth_login"])],
    ))

    c.append(canon(
        "git", "cannot-lock-ref", "git2-linux",
        "error: cannot lock ref: ref already exists",
        r"cannot lock ref|ref already exists|unable to create.*lock",
        "ref_error", "git", ">=2.30,<3.0", "linux",
        "true", 0.85, 0.88,
        "Stale lock file or conflicting ref. Common after interrupted operations.",
        [de("Delete .git/refs manually",
            "Can corrupt repository if wrong files removed", 0.80,
            sources=["https://git-scm.com/docs/git-gc"]),
         de("Re-clone the repository",
            "Loses local branches and stashes", 0.70,
            sources=["https://git-scm.com/docs/git-clone"])],
        [wa("Run git gc --prune=now to clean up stale refs", 0.90,
            "git gc --prune=now && git remote prune origin",
            sources=["https://git-scm.com/docs/git-gc"]),
         wa("Delete specific stale .lock file if present", 0.88,
            "rm -f .git/refs/heads/branch.lock",
            sources=["https://git-scm.com/docs/git-gc"])],
    ))

    # ── KUBERNETES ──────────────────────────────────────

    c.append(canon(
        "kubernetes", "createcontainerconfigerror", "k8s1-linux",
        "CreateContainerConfigError: secret not found",
        r"CreateContainerConfigError|secret.*not found|configmap.*not found",
        "config_error", "kubernetes", ">=1.28,<1.32", "linux",
        "true", 0.90, 0.92,
        "Pod references a Secret or ConfigMap that doesn't exist in the namespace.",
        [de("Create empty secret as placeholder",
            "App starts but with wrong/missing config, causes runtime errors", 0.60,
            sources=["https://kubernetes.io/docs/concepts/configuration/secret/"]),
         de("Set optional: true on the volume mount",
            "App runs without expected config, fails in unexpected ways", 0.55,
            sources=["https://kubernetes.io/docs/concepts/configuration/secret/#optional-secrets"])],
        [wa("Create the missing secret/configmap in the correct namespace", 0.95,
            "kubectl create secret generic my-secret --from-literal=key=value -n namespace",
            sources=["https://kubernetes.io/docs/concepts/configuration/secret/"]),
         wa("Check namespace — resources are namespace-scoped", 0.88,
            "kubectl get secrets -n target-namespace",
            sources=["https://kubernetes.io/docs/concepts/overview/working-with-objects/namespaces/"])],
    ))

    c.append(canon(
        "kubernetes", "evicted-pod", "k8s1-linux",
        "Pod status: Evicted — The node was low on resource: ephemeral-storage",
        r"Evicted|DiskPressure|ephemeral-storage",
        "resource_error", "kubernetes", ">=1.28,<1.32", "linux",
        "true", 0.82, 0.85,
        "Pod evicted due to node resource pressure (disk, memory).",
        [de("Just recreate the pod",
            "Will be evicted again if resource issue persists", 0.70,
            sources=["https://kubernetes.io/docs/concepts/scheduling-eviction/node-pressure-eviction/"]),
         de("Disable eviction in kubelet config",
            "Node can run out of resources entirely, affecting all pods", 0.85,
            sources=["https://kubernetes.io/docs/concepts/scheduling-eviction/node-pressure-eviction/"])],
        [wa("Set resource requests/limits and clean up ephemeral storage (logs, tmp files)", 0.90,
            sources=["https://kubernetes.io/docs/concepts/configuration/manage-resources-containers/"]),
         wa("Use emptyDir sizeLimit to prevent individual pods from consuming too much disk", 0.85,
            sources=["https://kubernetes.io/docs/concepts/storage/volumes/#emptydir"])],
    ))

    c.append(canon(
        "kubernetes", "service-not-found", "k8s1-linux",
        "couldn't find service: default/my-service",
        r"couldn't find service|service.*not found|no endpoints available",
        "network_error", "kubernetes", ">=1.28,<1.32", "linux",
        "true", 0.88, 0.90,
        "Service doesn't exist or has no backing pods (no matching selector).",
        [de("Create service without selector",
            "Service exists but routes to nothing", 0.70,
            sources=["https://kubernetes.io/docs/concepts/services-networking/service/"]),
         de("Use pod IP directly",
            "Pod IP changes on restart, breaks connectivity", 0.80,
            sources=["https://kubernetes.io/docs/concepts/services-networking/service/"])],
        [wa("Verify service exists and selector matches pod labels", 0.95,
            "kubectl get svc my-service -o yaml | grep selector && kubectl get pods -l app=my-app",
            sources=["https://kubernetes.io/docs/concepts/services-networking/service/"]),
         wa("Check endpoints: kubectl get endpoints my-service", 0.88,
            sources=["https://kubernetes.io/docs/concepts/services-networking/service/#endpoints"])],
    ))

    # ── CUDA ────────────────────────────────────────────

    c.append(canon(
        "cuda", "illegal-memory-access", "cuda12-a100",
        "CUDA error: an illegal memory access was encountered",
        r"CUDA error.*illegal memory access|RuntimeError.*CUDA.*illegal",
        "runtime_error", "cuda", ">=12.0,<13.0", "linux",
        "true", 0.75, 0.80,
        "GPU kernel accessed invalid memory. Hard to debug — error often reported asynchronously.",
        [de("Set CUDA_LAUNCH_BLOCKING=1 to find the error",
            "Only helps locate it, doesn't fix it; also makes training much slower", 0.40,
            sources=["https://docs.nvidia.com/cuda/cuda-c-programming-guide/index.html"]),
         de("Restart and hope it doesn't recur",
            "Memory corruption bugs are deterministic, will recur", 0.80,
            sources=["https://docs.nvidia.com/cuda/cuda-memcheck/index.html"])],
        [wa("Run with compute-sanitizer to find exact kernel and line", 0.85,
            "compute-sanitizer --tool memcheck python train.py",
            sources=["https://docs.nvidia.com/cuda/compute-sanitizer/index.html"]),
         wa("Check for index out of bounds in custom CUDA kernels or wrong tensor shapes", 0.82,
            sources=["https://docs.nvidia.com/cuda/cuda-c-programming-guide/index.html"])],
        gpu="A100-40GB",
    ))

    c.append(canon(
        "cuda", "cudnn-not-compiled", "cuda12-a100",
        "RuntimeError: cuDNN error: CUDNN_STATUS_NOT_INITIALIZED",
        r"cuDNN error|CUDNN_STATUS_(NOT_INITIALIZED|EXECUTION_FAILED|INTERNAL_ERROR)",
        "library_error", "cuda", ">=12.0,<13.0", "linux",
        "true", 0.80, 0.82,
        "cuDNN library not properly initialized. Version mismatch with CUDA or PyTorch.",
        [de("Reinstall cuDNN manually from NVIDIA",
            "Version must match exact CUDA version, easy to get wrong", 0.55,
            sources=["https://docs.nvidia.com/deeplearning/cudnn/installation/overview.html"]),
         de("Set torch.backends.cudnn.enabled = False",
            "Disables GPU acceleration for convolutions, much slower", 0.60,
            sources=["https://pytorch.org/docs/stable/backends.html#torch.backends.cudnn"])],
        [wa("Install PyTorch with matching CUDA version from official channel", 0.92,
            "pip install torch --index-url https://download.pytorch.org/whl/cu121",
            sources=["https://pytorch.org/get-started/locally/"]),
         wa("Use torch.backends.cudnn.benchmark = True after fixing version match", 0.80,
            sources=["https://pytorch.org/docs/stable/backends.html#torch.backends.cudnn"])],
        gpu="A100-40GB",
    ))

    # ── RUST ────────────────────────────────────────────

    c.append(canon(
        "rust", "e0599-no-method-named", "rust1-linux",
        "error[E0599]: no method named `method` found for struct `Type`",
        r"error\[E0599\]: no method named .+ found for",
        "type_error", "rust", ">=1.70,<2.0", "linux",
        "true", 0.90, 0.92,
        "Method doesn't exist on type, or trait not imported.",
        [de("Implement the method manually on the struct",
            "May already exist in a trait that just needs importing", 0.50,
            sources=["https://doc.rust-lang.org/book/ch05-03-method-syntax.html"]),
         de("Cast to a different type",
            "Type mismatch is the symptom, not the solution", 0.65,
            sources=["https://doc.rust-lang.org/reference/expressions/operator-expr.html#type-cast-expressions"])],
        [wa("Check if you need to use a trait: use TraitName;", 0.92,
            "use std::io::Read;  // now .read() works",
            sources=["https://doc.rust-lang.org/book/ch10-02-traits.html"]),
         wa("Check the type — you may have the wrong type; use compiler suggestions", 0.88,
            sources=["https://doc.rust-lang.org/error_codes/E0599.html"])],
    ))

    c.append(canon(
        "rust", "e0425-unresolved-name", "rust1-linux",
        "error[E0425]: cannot find value `x` in this scope",
        r"error\[E0425\]: cannot find (value|function) .+ in this scope",
        "name_error", "rust", ">=1.70,<2.0", "linux",
        "true", 0.92, 0.93,
        "Name not in scope. Missing import, typo, or wrong module path.",
        [de("Make everything pub",
            "Breaks encapsulation without fixing the import", 0.60,
            sources=["https://doc.rust-lang.org/book/ch07-03-paths-for-referring-to-an-item-in-the-module-tree.html"]),
         de("Copy the function definition locally",
            "Code duplication, will diverge from original", 0.70,
            sources=["https://doc.rust-lang.org/book/ch07-02-defining-modules-to-control-scope-and-privacy.html"])],
        [wa("Add the correct use statement for the module/function", 0.95,
            "use crate::module::function_name;",
            sources=["https://doc.rust-lang.org/book/ch07-04-bringing-paths-into-scope-with-the-use-keyword.html"]),
         wa("Check for typos in name and verify module visibility (pub)", 0.88,
            sources=["https://doc.rust-lang.org/error_codes/E0425.html"])],
    ))

    # ── GO ──────────────────────────────────────────────

    c.append(canon(
        "go", "declared-not-used", "go1-linux",
        "declared and not used: variable",
        r"declared and not used",
        "compile_error", "go", ">=1.21,<1.24", "linux",
        "true", 0.98, 0.98,
        "Go doesn't allow unused variables. Compile error, not warning.",
        [de("Assign to _ everywhere",
            "If variable is needed later, you'll forget it exists", 0.50,
            sources=["https://go.dev/doc/effective_go#blank"]),
         de("Comment out the variable",
            "May break code that depends on its side effects", 0.55,
            sources=["https://go.dev/ref/spec#Blank_identifier"])],
        [wa("Remove the unused variable, or use _ if return value intentionally discarded", 0.95,
            "_, err := someFunc()  // intentionally discard first return",
            sources=["https://go.dev/doc/effective_go#blank"]),
         wa("If debugging, use _ = variable to suppress temporarily", 0.82,
            sources=["https://go.dev/ref/spec#Blank_identifier"])],
    ))

    c.append(canon(
        "go", "multiple-value-in-single-context", "go1-linux",
        "multiple-value func() (used as single value, error) in single-value context",
        r"multiple-value .+ in single-value context",
        "type_error", "go", ">=1.21,<1.24", "linux",
        "true", 0.95, 0.95,
        "Function returns (value, error) but only one variable used.",
        [de("Wrap in a helper that drops the error",
            "Silently ignores errors, Go's biggest anti-pattern", 0.85,
            sources=["https://go.dev/doc/effective_go#errors"]),
         de("Use only the first return value",
            "Go doesn't allow this syntactically", 0.95,
            sources=["https://go.dev/ref/spec#Assignment_statements"])],
        [wa("Capture both return values: val, err := func()", 0.98,
            "val, err := someFunc()\nif err != nil { return err }",
            sources=["https://go.dev/doc/effective_go#errors"]),
         wa("Use _ to explicitly discard error only when truly safe", 0.80,
            "val, _ := strconv.Atoi(knownGoodString)",
            sources=["https://go.dev/doc/effective_go#blank"])],
    ))

    c.append(canon(
        "go", "cannot-convert-type", "go1-linux",
        "cannot convert x (variable of type string) to type int",
        r"cannot convert .+ to type",
        "type_error", "go", ">=1.21,<1.24", "linux",
        "true", 0.92, 0.93,
        "Direct type conversion not possible. Need strconv or encoding.",
        [de("Use unsafe.Pointer for conversion",
            "Undefined behavior, corrupts data", 0.90,
            sources=["https://pkg.go.dev/unsafe"]),
         de("Convert via interface{}",
            "Runtime panic on wrong assertion", 0.65,
            sources=["https://go.dev/doc/effective_go#interface_conversions"])],
        [wa("Use strconv package for string ↔ number conversions", 0.95,
            "n, err := strconv.Atoi(s)  // string to int\ns := strconv.Itoa(n)  // int to string",
            sources=["https://pkg.go.dev/strconv"]),
         wa("Use encoding/json for complex struct conversions", 0.85,
            sources=["https://pkg.go.dev/encoding/json"])],
    ))

    # ── PIP ─────────────────────────────────────────────

    c.append(canon(
        "pip", "externally-managed-environment", "pip24-linux",
        "error: externally-managed-environment",
        r"externally-managed-environment",
        "env_error", "pip", ">=24,<25", "linux",
        "true", 0.92, 0.93,
        "PEP 668: system Python rejects pip install. New in Debian 12, Ubuntu 23+, Fedora 38+.",
        [de("Remove EXTERNALLY-MANAGED file",
            "Breaks system Python and apt/dnf package manager", 0.85,
            sources=["https://peps.python.org/pep-0668/"]),
         de("Use --break-system-packages flag",
            "Can corrupt system Python, break OS tools", 0.75,
            sources=["https://pip.pypa.io/en/stable/cli/pip_install/"])],
        [wa("Use virtual environment: python -m venv .venv && source .venv/bin/activate", 0.98,
            "python3 -m venv .venv && source .venv/bin/activate && pip install package",
            sources=["https://peps.python.org/pep-0668/"]),
         wa("Use pipx for CLI tools: pipx install tool-name", 0.90,
            sources=["https://pipx.pypa.io/"])],
    ))

    c.append(canon(
        "pip", "metadata-generation-failed", "pip24-linux",
        "error: metadata-generation-failed",
        r"metadata-generation-failed|setup\.py.*error",
        "build_error", "pip", ">=24,<25", "linux",
        "true", 0.78, 0.82,
        "Package setup.py or pyproject.toml has errors. Common with packages needing C compilation.",
        [de("Downgrade pip to old version",
            "Old pip has worse dependency resolution and security issues", 0.60,
            sources=["https://pip.pypa.io/en/stable/news/"]),
         de("Use --no-build-isolation",
            "Can cause dependency conflicts between build and runtime", 0.55,
            sources=["https://pip.pypa.io/en/stable/cli/pip_install/#cmdoption-no-build-isolation"])],
        [wa("Install build dependencies first: C compiler, python-dev headers", 0.88,
            "sudo apt install python3-dev build-essential",
            sources=["https://pip.pypa.io/en/stable/cli/pip_install/"]),
         wa("Check if a pre-built wheel exists for your platform", 0.85,
            "pip install --only-binary=:all: package-name",
            sources=["https://pip.pypa.io/en/stable/cli/pip_install/#cmdoption-only-binary"])],
    ))

    # ── AWS ─────────────────────────────────────────────

    c.append(canon(
        "aws", "no-credentials-error", "awscli2-linux",
        "botocore.exceptions.NoCredentialsError: Unable to locate credentials",
        r"NoCredentialsError|Unable to locate credentials",
        "auth_error", "aws", ">=2.0", "linux",
        "true", 0.90, 0.92,
        "AWS SDK can't find credentials. Missing env vars, config, or IAM role.",
        [de("Hardcode credentials in source code",
            "Security risk — credentials in git history", 0.95,
            sources=["https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-files.html"]),
         de("Set AWS_ACCESS_KEY_ID in .env and commit",
            "Same security risk as hardcoding", 0.90,
            sources=["https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-envvars.html"])],
        [wa("Configure credentials: aws configure, or set env vars, or use IAM role", 0.95,
            "aws configure  # sets ~/.aws/credentials",
            sources=["https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-files.html"]),
         wa("In EC2/ECS/Lambda: use IAM role (no credentials needed)", 0.92,
            sources=["https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/iam-roles-for-amazon-ec2.html"])],
    ))

    c.append(canon(
        "aws", "invalid-security-token", "awscli2-linux",
        "An error occurred (InvalidClientTokenId): The security token is invalid",
        r"InvalidClientTokenId|security token.*invalid|SignatureDoesNotMatch",
        "auth_error", "aws", ">=2.0", "linux",
        "true", 0.88, 0.90,
        "AWS credentials are wrong or expired. Common with temporary session tokens.",
        [de("Regenerate all access keys",
            "May be unnecessary if it's just an expired session token", 0.50,
            sources=["https://docs.aws.amazon.com/IAM/latest/UserGuide/id_credentials_access-keys.html"]),
         de("Disable MFA requirement",
            "Severe security downgrade, doesn't fix the token", 0.85,
            sources=["https://docs.aws.amazon.com/IAM/latest/UserGuide/id_credentials_mfa.html"])],
        [wa("Check if using temporary credentials that expired; refresh with aws sts get-session-token", 0.90,
            sources=["https://docs.aws.amazon.com/cli/latest/reference/sts/get-session-token.html"]),
         wa("Verify correct AWS_PROFILE is set, check ~/.aws/credentials", 0.88,
            "aws sts get-caller-identity  # shows which identity is being used",
            sources=["https://docs.aws.amazon.com/cli/latest/reference/sts/get-caller-identity.html"])],
    ))

    # ── TERRAFORM ───────────────────────────────────────

    c.append(canon(
        "terraform", "plugin-crashed", "tf1-linux",
        "Error: Plugin did not respond: plugin process exited unexpectedly",
        r"Plugin did not respond|plugin.*crashed|plugin.*exited",
        "provider_error", "terraform", ">=1.5,<2.0", "linux",
        "true", 0.78, 0.82,
        "Terraform provider plugin crashed. Version incompatibility or resource limit.",
        [de("Downgrade Terraform version",
            "May introduce other incompatibilities", 0.55,
            sources=["https://developer.hashicorp.com/terraform/cli/commands/providers"]),
         de("Remove .terraform and reinitialize",
            "Downloads same broken version again", 0.60,
            sources=["https://developer.hashicorp.com/terraform/cli/commands/init"])],
        [wa("Update provider to latest patch version in required_providers block", 0.88,
            "terraform init -upgrade",
            sources=["https://developer.hashicorp.com/terraform/cli/commands/init"]),
         wa("Check system resources (memory) — large state files can OOM the provider", 0.82,
            sources=["https://developer.hashicorp.com/terraform/cli/commands/providers"])],
    ))

    c.append(canon(
        "terraform", "invalid-reference", "tf1-linux",
        "Error: Reference to undeclared resource",
        r"Reference to undeclared (resource|module|variable|input)",
        "config_error", "terraform", ">=1.5,<2.0", "linux",
        "true", 0.92, 0.93,
        "Terraform config references a resource that doesn't exist. Typo or missing module.",
        [de("Create a dummy resource to satisfy the reference",
            "Creates unneeded infrastructure, costs money", 0.70,
            sources=["https://developer.hashicorp.com/terraform/language/resources"]),
         de("Comment out the reference",
            "Breaks dependent resources", 0.65,
            sources=["https://developer.hashicorp.com/terraform/language/expressions/references"])],
        [wa("Check for typos in resource name and verify resource block exists", 0.95,
            "grep -r 'resource \"aws_instance\"' .",
            sources=["https://developer.hashicorp.com/terraform/language/expressions/references"]),
         wa("If in module, ensure output is declared and module source is correct", 0.88,
            sources=["https://developer.hashicorp.com/terraform/language/modules"])],
    ))

    return c


def main():
    generated = 0
    skipped = 0
    for entry in get_all_canons():
        parts = entry["id"].split("/")
        out_dir = DATA_DIR / parts[0] / parts[1]
        out_file = out_dir / f"{parts[2]}.json"

        if out_file.exists():
            skipped += 1
            continue

        out_dir.mkdir(parents=True, exist_ok=True)
        out_file.write_text(
            json.dumps(entry, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        generated += 1
        print(f"  Created: {entry['id']}")

    print(f"\nDone: {generated} created, {skipped} skipped (already exist)")


if __name__ == "__main__":
    main()
