"""Bulk generate wave 5: +50 canons (target: ~238 total).

Usage: python -m generator.bulk_generate_v5
"""

import json
from generator.bulk_generate import (
    canon, de, wa, DATA_DIR,
)


def get_all_canons():
    c = []

    # ── PYTHON ──────────────────────────────────────────

    c.append(canon(
        "python", "overflowerror", "py311-linux",
        "OverflowError: Python int too large to convert to C long",
        r"OverflowError.*too large to convert",
        "math_error", "python", ">=3.11,<3.13", "linux",
        "true", 0.92, 0.92,
        "Python int exceeds C long range. Common with numpy/pandas indexing or struct packing.",
        [de("Cast to int() to fix",
            "It's already an int — the issue is it's too large for C representation", 0.80,
            sources=["https://docs.python.org/3/library/exceptions.html#OverflowError"]),
         de("Use sys.maxsize as limit",
            "Doesn't fix the underlying large number — just masks it", 0.65,
            sources=["https://docs.python.org/3/library/sys.html#sys.maxsize"])],
        [wa("Use Python's arbitrary precision int instead of numpy int64 for large numbers", 0.92,
            sources=["https://docs.python.org/3/library/stdtypes.html#numeric-types-int-float-complex"]),
         wa("For numpy, use dtype=object or dtype=np.int64 explicitly and check bounds", 0.88,
            sources=["https://numpy.org/doc/stable/reference/arrays.scalars.html"])],
        python=">=3.11,<3.13",
    ))

    c.append(canon(
        "python", "typeerror-no-len", "py311-linux",
        "TypeError: object of type 'NoneType' has no len()",
        r"TypeError: object of type '(\w+)' has no len\(\)",
        "type_error", "python", ">=3.11,<3.13", "linux",
        "true", 0.95, 0.95,
        "Calling len() on an object that doesn't support it. Usually None from a function that returns nothing.",
        [de("Add __len__ to the class",
            "Usually the variable is wrong type, not missing __len__", 0.70,
            sources=["https://docs.python.org/3/reference/datamodel.html#object.__len__"]),
         de("Check if len() > 0 with try/except",
            "Hides the root cause — variable shouldn't be None", 0.75,
            sources=["https://docs.python.org/3/library/functions.html#len"])],
        [wa("The variable is probably None — check function that assigns it (many list methods return None)", 0.95,
            "# Bad: my_list = my_list.sort()  # .sort() returns None!\n# Good: my_list.sort()  # sorts in place",
            sources=["https://docs.python.org/3/library/stdtypes.html#list.sort"]),
         wa("Add None check before calling len(): if obj is not None: len(obj)", 0.88,
            sources=["https://docs.python.org/3/library/functions.html#len"])],
        python=">=3.11,<3.13",
    ))

    c.append(canon(
        "python", "fileexistserror", "py311-linux",
        "FileExistsError: [Errno 17] File exists",
        r"FileExistsError.*File exists",
        "filesystem_error", "python", ">=3.11,<3.13", "linux",
        "true", 0.95, 0.95,
        "File or directory already exists. Common with os.makedirs() or shutil.copy().",
        [de("Delete the file/directory first",
            "Race condition — another process may recreate it", 0.60,
            sources=["https://docs.python.org/3/library/os.html#os.makedirs"]),
         de("Use try/except to ignore the error globally",
            "May hide other FileExistsError from different operations", 0.55,
            sources=["https://docs.python.org/3/library/exceptions.html#FileExistsError"])],
        [wa("Use exist_ok=True: os.makedirs(path, exist_ok=True)", 0.95,
            sources=["https://docs.python.org/3/library/os.html#os.makedirs"]),
         wa("Use pathlib: Path(path).mkdir(parents=True, exist_ok=True)", 0.95,
            sources=["https://docs.python.org/3/library/pathlib.html#pathlib.Path.mkdir"])],
        python=">=3.11,<3.13",
    ))

    c.append(canon(
        "python", "brokenpipeerror", "py311-linux",
        "BrokenPipeError: [Errno 32] Broken pipe",
        r"BrokenPipeError.*Broken pipe",
        "io_error", "python", ">=3.11,<3.13", "linux",
        "partial", 0.80, 0.85,
        "Writing to a pipe/socket that was closed by the reader. Common: piping Python output to head/grep.",
        [de("Increase buffer size",
            "Buffer size doesn't matter — the reader has disconnected", 0.75,
            sources=["https://docs.python.org/3/library/signal.html#note-on-sigpipe"]),
         de("Wrap every print in try/except",
            "Verbose and error-prone — use signal handling instead", 0.60,
            sources=["https://docs.python.org/3/library/exceptions.html#BrokenPipeError"])],
        [wa("For CLI tools, handle SIGPIPE: signal.signal(signal.SIGPIPE, signal.SIG_DFL)", 0.90,
            "import signal\nsignal.signal(signal.SIGPIPE, signal.SIG_DFL)",
            sources=["https://docs.python.org/3/library/signal.html#note-on-sigpipe"]),
         wa("For network code, handle the error gracefully — the client disconnected", 0.85,
            sources=["https://docs.python.org/3/library/exceptions.html#BrokenPipeError"])],
        python=">=3.11,<3.13",
    ))

    c.append(canon(
        "python", "pandas-settingwithcopywarning", "py311-linux",
        "SettingWithCopyWarning: A value is trying to be set on a copy of a slice from a DataFrame",
        r"SettingWithCopyWarning.*copy of a slice",
        "data_warning", "python", ">=3.11,<3.13", "linux",
        "true", 0.90, 0.90,
        "Pandas chained assignment. The write may not propagate to the original DataFrame.",
        [de("Suppress the warning with pd.options.mode.chained_assignment = None",
            "Silences the warning but the bug remains — data may not be modified", 0.80,
            sources=["https://pandas.pydata.org/docs/user_guide/indexing.html#returning-a-view-versus-a-copy"]),
         de("Add .copy() everywhere",
            "Overkill and wastes memory — only copy when needed", 0.55,
            sources=["https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.copy.html"])],
        [wa("Use .loc[] for assignment: df.loc[mask, 'col'] = value", 0.95,
            "# Bad:  df[df['a'] > 0]['b'] = 1\n# Good: df.loc[df['a'] > 0, 'b'] = 1",
            sources=["https://pandas.pydata.org/docs/user_guide/indexing.html#returning-a-view-versus-a-copy"]),
         wa("If you intentionally want a copy, make it explicit: subset = df[mask].copy()", 0.90,
            sources=["https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.copy.html"])],
        python=">=3.11,<3.13",
    ))

    c.append(canon(
        "python", "notimplementederror", "py311-linux",
        "NotImplementedError",
        r"NotImplementedError",
        "runtime_error", "python", ">=3.11,<3.13", "linux",
        "true", 0.90, 0.90,
        "Abstract method not implemented in subclass. The parent class requires you to override this method.",
        [de("Call super() to use parent implementation",
            "Parent raises NotImplementedError — there is no implementation to call", 0.85,
            sources=["https://docs.python.org/3/library/exceptions.html#NotImplementedError"]),
         de("Remove the abstract method from parent",
            "Other subclasses may depend on the abstract contract", 0.70,
            sources=["https://docs.python.org/3/library/abc.html"])],
        [wa("Implement the method in your subclass with the correct signature", 0.95,
            sources=["https://docs.python.org/3/library/abc.html#abc.abstractmethod"]),
         wa("If you don't need this method, provide a no-op: def method(self): pass", 0.85,
            sources=["https://docs.python.org/3/library/exceptions.html#NotImplementedError"])],
        python=">=3.11,<3.13",
    ))

    c.append(canon(
        "python", "typeerror-string-indices", "py311-linux",
        "TypeError: string indices must be integers, not 'str'",
        r"TypeError: string indices must be integers",
        "type_error", "python", ">=3.11,<3.13", "linux",
        "true", 0.95, 0.95,
        "Treating a string as a dict. Usually JSON wasn't parsed, or iterating dict gives keys not items.",
        [de("Convert string to dict with dict()",
            "dict() can't parse JSON strings — use json.loads()", 0.85,
            sources=["https://docs.python.org/3/library/json.html#json.loads"]),
         de("Use int() on the index",
            "The index is correct type — the object is wrong type", 0.80,
            sources=["https://docs.python.org/3/library/stdtypes.html#str"])],
        [wa("If working with JSON, parse it first: data = json.loads(text)", 0.95,
            sources=["https://docs.python.org/3/library/json.html#json.loads"]),
         wa("If iterating a dict, use .items() — for k in dict gives keys (strings), not dicts", 0.90,
            "for item in data:  # item is a string key, not a dict!\nfor key, value in data.items():  # correct",
            sources=["https://docs.python.org/3/library/stdtypes.html#dict.items"])],
        python=">=3.11,<3.13",
    ))

    # ── NODE ──────────────────────────────────────────

    c.append(canon(
        "node", "econnreset", "node20-linux",
        "Error: read ECONNRESET",
        r"ECONNRESET|Connection reset by peer",
        "network_error", "node", ">=20,<23", "linux",
        "partial", 0.80, 0.85,
        "TCP connection forcibly closed by remote. Server crashed, timeout, or load balancer dropped connection.",
        [de("Increase socket timeout to very large value",
            "If server crashed, waiting longer won't help", 0.70,
            sources=["https://nodejs.org/api/net.html#socketsettimeouttimeout-callback"]),
         de("Disable keep-alive",
            "Keep-alive isn't the cause — the server actively reset the connection", 0.65,
            sources=["https://nodejs.org/api/http.html#httpagent"])],
        [wa("Add retry logic with exponential backoff for transient network issues", 0.90,
            sources=["https://nodejs.org/api/errors.html#common-system-errors"]),
         wa("Check server-side logs — the server is closing the connection", 0.88,
            sources=["https://nodejs.org/api/errors.html#common-system-errors"]),
         wa("If behind a proxy/LB, check its timeout settings", 0.82,
            sources=["https://nodejs.org/api/http.html#httpagent"])],
    ))

    c.append(canon(
        "node", "typeerror-callback-not-function", "node20-linux",
        "TypeError: callback is not a function",
        r"TypeError:.*callback.*is not a function|TypeError:.*is not a function",
        "type_error", "node", ">=20,<23", "linux",
        "true", 0.92, 0.92,
        "Callback argument is undefined. Common when using promisified API with callback style, or missing argument.",
        [de("Add a no-op callback: () => {}",
            "Hides the real issue — the function signature changed", 0.65,
            sources=["https://nodejs.org/api/util.html#utilcallbackifyoriginal"]),
         de("Wrap in try/catch",
            "The error is thrown synchronously before the callback — catch won't help async flow", 0.70,
            sources=["https://nodejs.org/api/errors.html"])],
        [wa("Check if you're mixing callback and promise APIs — use await or .then() instead", 0.95,
            "// Old: fs.readFile(path, callback)\n// New: const data = await fs.promises.readFile(path)",
            sources=["https://nodejs.org/api/fs.html#promise-example"]),
         wa("Verify all required arguments are passed — the callback might be a missing middle argument", 0.88,
            sources=["https://nodejs.org/api/errors.html#class-typeerror"])],
    ))

    c.append(canon(
        "node", "abort-error", "node20-linux",
        "AbortError: The operation was aborted",
        r"AbortError.*operation was aborted",
        "runtime_error", "node", ">=20,<23", "linux",
        "true", 0.88, 0.88,
        "AbortController signal triggered. Intentional timeout or cancellation.",
        [de("Remove the AbortController",
            "AbortController was added for a reason — removing it may cause resource leaks", 0.70,
            sources=["https://nodejs.org/api/globals.html#class-abortcontroller"]),
         de("Increase timeout to a very large value",
            "May cause resource exhaustion if operations genuinely hang", 0.60,
            sources=["https://nodejs.org/api/globals.html#class-abortsignal"])],
        [wa("Increase the timeout if it's too aggressive: AbortSignal.timeout(30000)", 0.90,
            sources=["https://nodejs.org/api/globals.html#abortsignaltimeoutdelay"]),
         wa("Handle the AbortError in catch block — it's expected behavior for cancellation", 0.88,
            "try { await fetch(url, { signal }) } catch(e) { if (e.name === 'AbortError') { /* timeout */ } }",
            sources=["https://nodejs.org/api/globals.html#class-abortcontroller"])],
    ))

    c.append(canon(
        "node", "err-stream-premature-close", "node20-linux",
        "Error [ERR_STREAM_PREMATURE_CLOSE]: Premature close",
        r"ERR_STREAM_PREMATURE_CLOSE|Premature close",
        "stream_error", "node", ">=20,<23", "linux",
        "partial", 0.82, 0.85,
        "Stream closed before it was consumed. Common with pipeline(), file uploads, or HTTP responses.",
        [de("Increase highWaterMark to buffer more data",
            "The stream was closed, not slow — buffering doesn't help", 0.70,
            sources=["https://nodejs.org/api/stream.html#buffering"]),
         de("Pipe to a PassThrough stream first",
            "Extra complexity without fixing the root cause", 0.65,
            sources=["https://nodejs.org/api/stream.html#class-streampassthrough"])],
        [wa("Ensure the writable stream isn't destroyed before the readable finishes", 0.90,
            sources=["https://nodejs.org/api/stream.html#streamfinishedstream-options-callback"]),
         wa("Use stream.pipeline() instead of .pipe() — it handles cleanup automatically", 0.92,
            "const { pipeline } = require('stream/promises');\nawait pipeline(readable, transform, writable);",
            sources=["https://nodejs.org/api/stream.html#streampipelinesource-transforms-destination-callback"]),
         wa("For HTTP responses, ensure client doesn't disconnect before response completes", 0.80,
            sources=["https://nodejs.org/api/http.html#event-close"])],
    ))

    c.append(canon(
        "node", "enomem", "node20-linux",
        "Error: ENOMEM: not enough memory",
        r"ENOMEM.*not enough memory|Cannot allocate memory",
        "system_error", "node", ">=20,<23", "linux",
        "partial", 0.75, 0.85,
        "System out of memory. Node process or system-wide memory exhaustion.",
        [de("Increase --max-old-space-size to very large value",
            "If system RAM is exhausted, increasing V8 heap won't help", 0.70,
            sources=["https://nodejs.org/api/cli.html#--max-old-space-sizesize-in-megabytes"]),
         de("Add swap space",
            "Swap is extremely slow — fix the memory usage instead", 0.60,
            sources=["https://nodejs.org/api/os.html#osfreemem"])],
        [wa("Profile memory usage to find leaks: node --inspect + Chrome DevTools", 0.90,
            sources=["https://nodejs.org/en/learn/diagnostics/memory/using-heap-snapshot"]),
         wa("Process data in streams instead of loading everything into memory", 0.88,
            sources=["https://nodejs.org/api/stream.html"]),
         wa("Check for common leaks: growing arrays, unclosed connections, event listener accumulation", 0.85,
            sources=["https://nodejs.org/en/learn/diagnostics/memory"])],
    ))

    # ── TYPESCRIPT ──────────────────────────────────────────

    c.append(canon(
        "typescript", "ts2694-no-exported-member", "ts5-linux",
        "error TS2694: Namespace 'X' has no exported member 'Y'",
        r"TS2694.*has no exported member",
        "import_error", "typescript", ">=5.0,<6.0", "linux",
        "true", 0.90, 0.90,
        "Named export doesn't exist in the module. Common after library updates or wrong import syntax.",
        [de("Use import * as X to get everything",
            "Loses tree-shaking and may not fix the issue if the export was removed", 0.65,
            sources=["https://www.typescriptlang.org/docs/handbook/modules/reference.html"]),
         de("Downgrade the package",
            "The export may have been intentionally removed — check migration guide", 0.55,
            sources=["https://www.typescriptlang.org/docs/handbook/modules/reference.html"])],
        [wa("Check the library's changelog/migration guide for renamed or removed exports", 0.92,
            sources=["https://www.typescriptlang.org/docs/handbook/modules/reference.html"]),
         wa("Use IDE Go to Definition to find the actual export path", 0.90,
            sources=["https://www.typescriptlang.org/docs/handbook/modules/reference.html"]),
         wa("Check if import path changed: import { X } from 'lib' vs 'lib/subpath'", 0.88,
            sources=["https://www.typescriptlang.org/docs/handbook/modules/reference.html"])],
    ))

    c.append(canon(
        "typescript", "ts2564-no-initializer", "ts5-linux",
        "error TS2564: Property 'X' has no initializer and is not definitely assigned in the constructor",
        r"TS2564.*has no initializer.*not definitely assigned",
        "type_error", "typescript", ">=5.0,<6.0", "linux",
        "true", 0.95, 0.95,
        "Class property declared but not initialized. strictPropertyInitialization is enabled.",
        [de("Set strictPropertyInitialization to false",
            "Disables a useful safety check across the entire project", 0.70,
            sources=["https://www.typescriptlang.org/tsconfig/#strictPropertyInitialization"]),
         de("Add ! to suppress: property!: Type",
            "Suppresses the check but may cause runtime undefined access", 0.60,
            sources=["https://www.typescriptlang.org/docs/handbook/2/classes.html#--strictpropertyinitialization"])],
        [wa("Initialize in the constructor or at declaration: property: Type = defaultValue", 0.95,
            sources=["https://www.typescriptlang.org/docs/handbook/2/classes.html#--strictpropertyinitialization"]),
         wa("Use definite assignment assertion (!) only when you're SURE it's set before use (e.g., DI)", 0.80,
            "class Foo { @Inject() service!: Service; }  // OK: framework sets it",
            sources=["https://www.typescriptlang.org/docs/handbook/2/classes.html"])],
    ))

    c.append(canon(
        "typescript", "ts6133-declared-not-read", "ts5-linux",
        "error TS6133: 'x' is declared but its value is never read",
        r"TS6133.*declared but.*never read",
        "lint_error", "typescript", ">=5.0,<6.0", "linux",
        "true", 0.98, 0.95,
        "Unused variable or import. TypeScript reports this when noUnusedLocals/noUnusedParameters is enabled.",
        [de("Disable noUnusedLocals in tsconfig",
            "Disables a useful lint rule across the entire project", 0.65,
            sources=["https://www.typescriptlang.org/tsconfig/#noUnusedLocals"]),
         de("Assign to void: void unusedVar",
            "Obscure and confusing — just remove or prefix with underscore", 0.70,
            sources=["https://www.typescriptlang.org/docs/handbook/2/basic-types.html"])],
        [wa("Remove the unused variable or import", 0.98,
            sources=["https://www.typescriptlang.org/tsconfig/#noUnusedLocals"]),
         wa("Prefix with underscore if intentionally unused: _unusedParam", 0.92,
            "function handler(_req: Request, res: Response) { ... }",
            sources=["https://www.typescriptlang.org/tsconfig/#noUnusedParameters"])],
    ))

    # ── REACT ──────────────────────────────────────────

    c.append(canon(
        "react", "rendered-more-hooks", "react18-linux",
        "Rendered more hooks than during the previous render",
        r"Rendered more hooks than during the previous render",
        "hook_error", "react", ">=18,<20", "linux",
        "true", 0.90, 0.90,
        "Hooks called conditionally or in different order between renders. Violates Rules of Hooks.",
        [de("Move the conditional inside the hook",
            "Some hooks don't support conditional logic internally", 0.55,
            sources=["https://react.dev/reference/rules/rules-of-hooks"]),
         de("Use useRef to track which hooks to skip",
            "Over-engineering — just follow Rules of Hooks", 0.75,
            sources=["https://react.dev/reference/react/useRef"])],
        [wa("Hooks must be called in the same order every render — move conditionals INSIDE hooks, not around them", 0.95,
            "// Bad: if (cond) { useState(...) }\n// Good: const [val] = useState(cond ? x : y)",
            sources=["https://react.dev/reference/rules/rules-of-hooks"]),
         wa("If a component conditionally needs a hook, split into two components", 0.88,
            sources=["https://react.dev/reference/rules/rules-of-hooks"]),
         wa("Check for early returns before hooks — all hooks must run before any return", 0.90,
            sources=["https://react.dev/reference/rules/rules-of-hooks"])],
    ))

    c.append(canon(
        "react", "cannot-find-react-dom-client", "react18-linux",
        "Module not found: Can't resolve 'react-dom/client'",
        r"Can't resolve 'react-dom/client'|Cannot find module 'react-dom/client'",
        "module_error", "react", ">=18,<20", "linux",
        "true", 0.95, 0.95,
        "react-dom/client is React 18+ API. Using React 17 or older react-dom.",
        [de("Import from 'react-dom' instead",
            "ReactDOM.render is deprecated in React 18+", 0.60,
            sources=["https://react.dev/blog/2022/03/08/react-18-upgrade-guide"]),
         de("Downgrade to React 17 to use old API",
            "Loses React 18 features (concurrent mode, automatic batching)", 0.55,
            sources=["https://react.dev/blog/2022/03/08/react-18-upgrade-guide"])],
        [wa("Upgrade react-dom to version 18+: npm install react-dom@latest", 0.95,
            "npm install react@latest react-dom@latest",
            sources=["https://react.dev/blog/2022/03/08/react-18-upgrade-guide"]),
         wa("If already v18, check for version mismatch between react and react-dom", 0.90,
            "npm ls react react-dom",
            sources=["https://react.dev/blog/2022/03/08/react-18-upgrade-guide"])],
    ))

    c.append(canon(
        "react", "text-content-mismatch", "react18-linux",
        "Warning: Text content did not match. Server: 'X' Client: 'Y'",
        r"Text content did not match|Hydration failed.*text content",
        "hydration_error", "react", ">=18,<20", "linux",
        "true", 0.88, 0.90,
        "SSR hydration mismatch. Server and client render different text. Common: dates, random values, browser APIs.",
        [de("suppressHydrationWarning on every element",
            "Hides the warning but the mismatch still causes visual flicker", 0.70,
            sources=["https://react.dev/reference/react-dom/client/hydrateRoot#suppressing-unavoidable-hydration-mismatch-errors"]),
         de("Disable SSR entirely",
            "Loses SEO and initial load performance", 0.65,
            sources=["https://react.dev/reference/react-dom/server"])],
        [wa("Use useEffect for browser-only values (dates, localStorage, window size)", 0.95,
            "const [time, setTime] = useState('');\nuseEffect(() => setTime(new Date().toLocaleString()), []);",
            sources=["https://react.dev/reference/react/useEffect"]),
         wa("Use suppressHydrationWarning only on the specific element with dynamic content", 0.85,
            sources=["https://react.dev/reference/react-dom/client/hydrateRoot"]),
         wa("Ensure server and client use the same data — pass SSR data via props, not new fetches", 0.88,
            sources=["https://react.dev/reference/react-dom/server"])],
    ))

    # ── NEXT.JS ──────────────────────────────────────────

    c.append(canon(
        "nextjs", "next-router-app-dir", "nextjs14-linux",
        "Error: NextRouter was not mounted",
        r"NextRouter was not mounted|next/router.*is not supported.*app",
        "migration_error", "nextjs", ">=14,<16", "linux",
        "true", 0.95, 0.95,
        "Using next/router in App Router. App Router uses next/navigation instead.",
        [de("Wrap with RouterContext.Provider",
            "Hack that doesn't work — App Router has a different router", 0.85,
            sources=["https://nextjs.org/docs/app/building-your-application/upgrading/app-router-migration#step-5-migrating-routing-hooks"]),
         de("Move the file to pages/ directory",
            "Defeats the purpose of migrating to App Router", 0.60,
            sources=["https://nextjs.org/docs/app/building-your-application/upgrading/app-router-migration"])],
        [wa("Replace next/router with next/navigation", 0.95,
            "// Old: import { useRouter } from 'next/router'\n// New: import { useRouter } from 'next/navigation'",
            sources=["https://nextjs.org/docs/app/building-your-application/upgrading/app-router-migration#step-5-migrating-routing-hooks"]),
         wa("Replace router.query with useSearchParams() and useParams()", 0.92,
            "import { useSearchParams, useParams } from 'next/navigation';",
            sources=["https://nextjs.org/docs/app/api-reference/functions/use-search-params"])],
    ))

    c.append(canon(
        "nextjs", "generatestaticparams-error", "nextjs14-linux",
        "Error: Page is missing generateStaticParams()",
        r"missing.*generateStaticParams|generateStaticParams.*required",
        "build_error", "nextjs", ">=14,<16", "linux",
        "true", 0.92, 0.92,
        "Dynamic route with output: 'export' requires generateStaticParams to know all possible paths.",
        [de("Remove the dynamic route segment",
            "You need the dynamic route — removing it changes the URL structure", 0.80,
            sources=["https://nextjs.org/docs/app/api-reference/functions/generate-static-params"]),
         de("Set output: 'standalone' to avoid static generation",
            "Changes deployment model entirely", 0.60,
            sources=["https://nextjs.org/docs/app/api-reference/config/next-config-js/output"])],
        [wa("Add generateStaticParams to return all possible params", 0.95,
            "export async function generateStaticParams() {\n  const posts = await getPosts();\n  return posts.map(p => ({ slug: p.slug }));\n}",
            sources=["https://nextjs.org/docs/app/api-reference/functions/generate-static-params"]),
         wa("Use dynamicParams = false to return 404 for unknown params, or true (default) for ISR", 0.88,
            sources=["https://nextjs.org/docs/app/api-reference/file-conventions/route-segment-config#dynamicparams"])],
    ))

    c.append(canon(
        "nextjs", "middleware-redirect-loop", "nextjs14-linux",
        "Error: ERR_TOO_MANY_REDIRECTS / redirect loop in middleware",
        r"ERR_TOO_MANY_REDIRECTS|redirect loop|too many redirects",
        "routing_error", "nextjs", ">=14,<16", "linux",
        "true", 0.90, 0.90,
        "Middleware redirects to a URL that triggers the middleware again, causing infinite loop.",
        [de("Add a redirect counter in cookies",
            "Over-engineering — fix the matcher config instead", 0.75,
            sources=["https://nextjs.org/docs/app/building-your-application/routing/middleware"]),
         de("Disable the middleware temporarily",
            "Doesn't fix the issue — it'll come back when re-enabled", 0.70,
            sources=["https://nextjs.org/docs/app/building-your-application/routing/middleware"])],
        [wa("Add matcher config to exclude the redirect destination from middleware", 0.95,
            "export const config = { matcher: ['/((?!login|_next|api|static).*)'] };",
            sources=["https://nextjs.org/docs/app/building-your-application/routing/middleware#matcher"]),
         wa("Check for the redirect destination in the condition: if (url !== '/login') redirect('/login')", 0.92,
            sources=["https://nextjs.org/docs/app/building-your-application/routing/middleware"])],
    ))

    # ── DOCKER ──────────────────────────────────────────

    c.append(canon(
        "docker", "volume-mount-permission-denied", "docker27-linux",
        "Error: EACCES: permission denied (inside container with volume mount)",
        r"EACCES.*permission denied|Permission denied.*volume|chown.*Operation not permitted",
        "permission_error", "docker", ">=27,<28", "linux",
        "partial", 0.82, 0.85,
        "Container process can't write to mounted volume due to UID/GID mismatch.",
        [de("Run container as root",
            "Security risk and may not fix file ownership on the host", 0.65,
            sources=["https://docs.docker.com/engine/security/#docker-daemon-attack-surface"]),
         de("chmod 777 on host directory",
            "Major security risk — opens directory to all users", 0.80,
            sources=["https://docs.docker.com/engine/storage/volumes/"])],
        [wa("Match container user UID to host user UID: docker run --user $(id -u):$(id -g)", 0.92,
            sources=["https://docs.docker.com/engine/reference/run/#user"]),
         wa("Set ownership in Dockerfile: RUN chown -R appuser:appgroup /app", 0.88,
            sources=["https://docs.docker.com/reference/dockerfile/#user"]),
         wa("Use named volumes instead of bind mounts for data that doesn't need host access", 0.80,
            sources=["https://docs.docker.com/engine/storage/volumes/"])],
    ))

    c.append(canon(
        "docker", "dns-resolution-failed", "docker27-linux",
        "Could not resolve host / Temporary failure in name resolution",
        r"Could not resolve host|Temporary failure in name resolution|getaddrinfo.*ENOTFOUND",
        "network_error", "docker", ">=27,<28", "linux",
        "partial", 0.80, 0.85,
        "Container can't resolve DNS. Common during build (apt-get) or runtime (API calls).",
        [de("Hardcode IP addresses",
            "IPs change — this is fragile and breaks when servers move", 0.80,
            sources=["https://docs.docker.com/engine/daemon/networking/"]),
         de("Disable network isolation",
            "Loses container network security", 0.70,
            sources=["https://docs.docker.com/engine/network/"])],
        [wa("Specify DNS server: docker run --dns 8.8.8.8", 0.90,
            sources=["https://docs.docker.com/engine/daemon/networking/#dns-services"]),
         wa("Check Docker daemon DNS config in /etc/docker/daemon.json", 0.88,
            '{"dns": ["8.8.8.8", "8.8.4.4"]}',
            sources=["https://docs.docker.com/engine/daemon/networking/#dns-services"]),
         wa("If on corporate VPN, use VPN's DNS server instead of public DNS", 0.82,
            sources=["https://docs.docker.com/engine/daemon/networking/"])],
    ))

    # ── GIT ──────────────────────────────────────────

    c.append(canon(
        "git", "stash-pop-conflict", "git2-linux",
        "error: Your local changes to the following files would be overwritten by merge (stash pop)",
        r"CONFLICT.*stash|stash.*conflict|could not restore untracked files from stash",
        "stash_error", "git", ">=2.30,<3.0", "linux",
        "true", 0.90, 0.90,
        "Stash pop conflicts with current changes. Stash is not dropped on conflict.",
        [de("Force drop the stash: git stash drop",
            "Loses the stashed changes — they may still be needed", 0.80,
            sources=["https://git-scm.com/docs/git-stash"]),
         de("Reset working directory and try again",
            "Loses current uncommitted work", 0.85,
            sources=["https://git-scm.com/docs/git-stash"])],
        [wa("Resolve conflicts like a merge — edit files, mark resolved, then git stash drop", 0.92,
            "# After resolving:\ngit add <resolved-files>\ngit stash drop",
            sources=["https://git-scm.com/docs/git-stash#_discussion"]),
         wa("Use git stash apply instead of pop — apply doesn't auto-drop on success either way", 0.85,
            sources=["https://git-scm.com/docs/git-stash#Documentation/git-stash.txt-apply"])],
    ))

    c.append(canon(
        "git", "rebase-conflict", "git2-linux",
        "CONFLICT (content): Merge conflict during rebase",
        r"CONFLICT.*rebase|rebase.*CONFLICT|Could not apply.*during rebase",
        "rebase_error", "git", ">=2.30,<3.0", "linux",
        "true", 0.88, 0.90,
        "Rebase stopped due to conflict. Must resolve before continuing.",
        [de("Use git rebase --skip on every conflict",
            "Skips your commits — you'll lose changes", 0.85,
            sources=["https://git-scm.com/docs/git-rebase#_options"]),
         de("Abort and merge instead every time",
            "Merge creates noise in history — rebase conflicts are normal and resolvable", 0.50,
            sources=["https://git-scm.com/docs/git-rebase"])],
        [wa("Resolve conflict in each file, then git add <file> && git rebase --continue", 0.95,
            "# Edit conflicting files\ngit add <resolved-files>\ngit rebase --continue",
            sources=["https://git-scm.com/docs/git-rebase#_resolving_conflicts"]),
         wa("Use git rebase --abort to start over if things go wrong", 0.90,
            sources=["https://git-scm.com/docs/git-rebase#_options"]),
         wa("Consider git rerere to auto-resolve recurring conflicts", 0.78,
            "git config rerere.enabled true",
            sources=["https://git-scm.com/docs/git-rerere"])],
    ))

    # ── KUBERNETES ──────────────────────────────────────────

    c.append(canon(
        "kubernetes", "readiness-probe-failed", "k8s1-linux",
        "Warning Unhealthy: Readiness probe failed",
        r"Readiness probe failed|Liveness probe failed|probe.*failed",
        "health_error", "kubernetes", ">=1.28,<2.0", "linux",
        "partial", 0.82, 0.85,
        "Container health check failing. App may be slow to start or the probe config is wrong.",
        [de("Remove the readiness probe",
            "Kubernetes will route traffic to unhealthy pods", 0.80,
            sources=["https://kubernetes.io/docs/tasks/configure-pod-container/configure-liveness-readiness-startup-probes/"]),
         de("Set failureThreshold very high",
            "Delays detection of genuinely unhealthy pods", 0.60,
            sources=["https://kubernetes.io/docs/tasks/configure-pod-container/configure-liveness-readiness-startup-probes/"])],
        [wa("Increase initialDelaySeconds if the app needs time to start", 0.92,
            "readinessProbe:\n  httpGet: { path: /health, port: 8080 }\n  initialDelaySeconds: 30\n  periodSeconds: 10",
            sources=["https://kubernetes.io/docs/tasks/configure-pod-container/configure-liveness-readiness-startup-probes/"]),
         wa("Use a startup probe for slow-starting apps instead of long initialDelaySeconds", 0.88,
            sources=["https://kubernetes.io/docs/tasks/configure-pod-container/configure-liveness-readiness-startup-probes/#define-startup-probes"]),
         wa("Verify the probe endpoint path and port match what the app actually serves", 0.90,
            "kubectl exec <pod> -- curl -v localhost:8080/health",
            sources=["https://kubernetes.io/docs/tasks/configure-pod-container/configure-liveness-readiness-startup-probes/"])],
    ))

    c.append(canon(
        "kubernetes", "back-off-pulling-image", "k8s1-linux",
        "Warning: Back-off pulling image",
        r"Back-off pulling image|ErrImagePull|Failed to pull image",
        "image_error", "kubernetes", ">=1.28,<2.0", "linux",
        "true", 0.90, 0.90,
        "Can't pull container image. Wrong tag, private registry auth, or image doesn't exist.",
        [de("Use :latest tag to always get newest",
            ":latest may not exist or may be outdated — use specific version tags", 0.65,
            sources=["https://kubernetes.io/docs/concepts/containers/images/#image-names"]),
         de("Disable image pull policy",
            "imagePullPolicy: Never only works if image is pre-loaded on node", 0.70,
            sources=["https://kubernetes.io/docs/concepts/containers/images/#image-pull-policy"])],
        [wa("Verify image name and tag exist: docker pull <image>:<tag> locally first", 0.95,
            sources=["https://kubernetes.io/docs/concepts/containers/images/"]),
         wa("For private registries, create imagePullSecret and reference it in the pod spec", 0.92,
            "kubectl create secret docker-registry regcred --docker-server=<url> --docker-username=<user> --docker-password=<pass>",
            sources=["https://kubernetes.io/docs/tasks/configure-pod-container/pull-image-private-registry/"]),
         wa("Check Events: kubectl describe pod <name> to see the exact pull error", 0.90,
            sources=["https://kubernetes.io/docs/reference/kubectl/generated/kubectl_describe/"])],
    ))

    # ── CUDA ──────────────────────────────────────────

    c.append(canon(
        "cuda", "cuda-driver-insufficient", "cuda12-linux",
        "RuntimeError: The NVIDIA driver on your system is too old",
        r"NVIDIA driver.*too old|CUDA driver version is insufficient|Driver Version.*CUDA",
        "driver_error", "cuda", ">=12.0,<13.0", "linux",
        "true", 0.90, 0.90,
        "Installed CUDA toolkit requires a newer GPU driver. Driver must meet minimum version for CUDA.",
        [de("Reinstall CUDA toolkit",
            "CUDA toolkit is fine — the GPU driver needs updating", 0.80,
            sources=["https://docs.nvidia.com/cuda/cuda-toolkit-release-notes/index.html"]),
         de("Downgrade PyTorch to match old driver",
            "Old PyTorch misses important features and bug fixes", 0.55,
            sources=["https://pytorch.org/get-started/previous-versions/"])],
        [wa("Update GPU driver: apt install nvidia-driver-545 or download from nvidia.com", 0.95,
            "ubuntu-drivers autoinstall  # or: apt install nvidia-driver-545",
            sources=["https://docs.nvidia.com/cuda/cuda-toolkit-release-notes/index.html#id5"]),
         wa("Check the CUDA/driver compatibility matrix to find minimum driver version", 0.90,
            sources=["https://docs.nvidia.com/cuda/cuda-toolkit-release-notes/index.html#id5"])],
        gpu="any",
    ))

    # ── RUST ──────────────────────────────────────────

    c.append(canon(
        "rust", "e0106-missing-lifetime", "rust1-linux",
        "error[E0106]: missing lifetime specifier",
        r"E0106.*missing lifetime specifier",
        "lifetime_error", "rust", ">=1.70,<2.0", "linux",
        "true", 0.85, 0.90,
        "Function returns a reference but Rust can't infer the lifetime. Need explicit lifetime annotation.",
        [de("Use 'static lifetime on everything",
            "'static means lives forever — wrong for most references", 0.80,
            sources=["https://doc.rust-lang.org/error_codes/E0106.html"]),
         de("Return an owned value (String instead of &str) as a quick fix",
            "May work but cloning every time can be expensive", 0.45,
            sources=["https://doc.rust-lang.org/book/ch10-03-lifetime-syntax.html"])],
        [wa("Add lifetime parameter: fn foo<'a>(s: &'a str) -> &'a str", 0.92,
            sources=["https://doc.rust-lang.org/book/ch10-03-lifetime-syntax.html"]),
         wa("If function has one reference input, the compiler can infer (lifetime elision rules)", 0.85,
            sources=["https://doc.rust-lang.org/reference/lifetime-elision.html"]),
         wa("Consider returning an owned type (String, Vec) if lifetime complexity isn't worth it", 0.80,
            sources=["https://doc.rust-lang.org/book/ch10-03-lifetime-syntax.html"])],
    ))

    c.append(canon(
        "rust", "e0015-non-const-fn", "rust1-linux",
        "error[E0015]: cannot call non-const fn in const context",
        r"E0015.*cannot call non-const fn",
        "const_error", "rust", ">=1.70,<2.0", "linux",
        "true", 0.88, 0.90,
        "Calling a runtime function in a const/static context. Not all functions can run at compile time.",
        [de("Make every function const",
            "Most functions can't be const — they allocate, do IO, or have side effects", 0.80,
            sources=["https://doc.rust-lang.org/error_codes/E0015.html"]),
         de("Use unsafe to bypass const restrictions",
            "unsafe doesn't override const restrictions", 0.90,
            sources=["https://doc.rust-lang.org/reference/const_eval.html"])],
        [wa("Use lazy_static! or std::sync::LazyLock for runtime-initialized global values", 0.92,
            "use std::sync::LazyLock;\nstatic CACHE: LazyLock<HashMap<String, i32>> = LazyLock::new(|| HashMap::new());",
            sources=["https://doc.rust-lang.org/std/sync/struct.LazyLock.html"]),
         wa("Move initialization from const/static to a function that runs at startup", 0.85,
            sources=["https://doc.rust-lang.org/reference/const_eval.html"])],
    ))

    # ── GO ──────────────────────────────────────────

    c.append(canon(
        "go", "interface-nil-not-nil", "go1-linux",
        "panic: interface conversion: interface is nil, not T",
        r"interface conversion.*interface is nil|interface.*nil.*not",
        "runtime_error", "go", ">=1.21,<2.0", "linux",
        "true", 0.90, 0.90,
        "Type assertion on nil interface. Common with error interfaces and empty interface{}.",
        [de("Use recover() to catch the panic",
            "Hides the bug — nil interface means logic error", 0.75,
            sources=["https://go.dev/blog/defer-panic-and-recover"]),
         de("Initialize to empty value of the type",
            "May hide cases where nil is a valid/expected state", 0.60,
            sources=["https://go.dev/ref/spec#Interface_types"])],
        [wa("Use comma-ok pattern for safe type assertion: val, ok := iface.(Type)", 0.95,
            "if val, ok := iface.(MyType); ok {\n    // use val\n}",
            sources=["https://go.dev/ref/spec#Type_assertions"]),
         wa("Check for nil before type assertion: if iface != nil { ... }", 0.90,
            sources=["https://go.dev/ref/spec#Type_assertions"])],
    ))

    c.append(canon(
        "go", "no-required-module", "go1-linux",
        "no required module provides package X; to add it: go get X",
        r"no required module provides package|missing go.sum entry",
        "module_error", "go", ">=1.21,<2.0", "linux",
        "true", 0.95, 0.95,
        "Go module dependency not in go.mod. Need to add the dependency.",
        [de("Manually edit go.mod to add the dependency",
            "go.sum won't be updated — use go get instead", 0.70,
            sources=["https://go.dev/ref/mod#go-get"]),
         de("Disable Go modules with GO111MODULE=off",
            "Go modules are the standard — GOPATH mode is deprecated", 0.85,
            sources=["https://go.dev/ref/mod"])],
        [wa("Run: go get <package>@latest", 0.95,
            "go get github.com/some/package@latest",
            sources=["https://go.dev/ref/mod#go-get"]),
         wa("Run go mod tidy to clean up and add all missing dependencies", 0.92,
            sources=["https://go.dev/ref/mod#go-mod-tidy"])],
    ))

    # ── PIP ──────────────────────────────────────────

    c.append(canon(
        "pip", "hash-mismatch", "pip24-linux",
        "ERROR: THESE PACKAGES DO NOT MATCH THE HASHES FROM THE REQUIREMENTS FILE",
        r"PACKAGES DO NOT MATCH THE HASHES|hash.*mismatch|HashMismatchError",
        "security_error", "pip", ">=24,<25", "linux",
        "true", 0.90, 0.90,
        "Package hash doesn't match requirements file. Package was updated or corrupted.",
        [de("Use --no-cache-dir and retry",
            "Cache isn't the issue — the hash in requirements file is wrong", 0.60,
            sources=["https://pip.pypa.io/en/stable/topics/caching/"]),
         de("Remove --require-hashes flag",
            "Removes security protection — hashes prevent supply chain attacks", 0.70,
            sources=["https://pip.pypa.io/en/stable/topics/secure-installs/"])],
        [wa("Regenerate hashes: pip-compile --generate-hashes requirements.in", 0.92,
            sources=["https://pip.pypa.io/en/stable/topics/secure-installs/#hash-checking-mode"]),
         wa("Pin exact versions with hashes: pip hash <package>.whl", 0.88,
            sources=["https://pip.pypa.io/en/stable/cli/pip_hash/"]),
         wa("Check if the package was yanked/replaced on PyPI — this could be a security issue", 0.85,
            sources=["https://pip.pypa.io/en/stable/topics/secure-installs/"])],
    ))

    # ── AWS ──────────────────────────────────────────

    c.append(canon(
        "aws", "resource-already-exists", "awscli2-linux",
        "An error occurred (ResourceAlreadyExistsException)",
        r"ResourceAlreadyExistsException|EntityAlreadyExists|BucketAlreadyOwnedByYou",
        "conflict_error", "aws", ">=2.0,<3.0", "linux",
        "true", 0.92, 0.92,
        "AWS resource with that name already exists. Use existing or choose different name.",
        [de("Delete and recreate the resource",
            "May lose data, configurations, or dependent resources", 0.75,
            sources=["https://docs.aws.amazon.com/general/latest/gr/error-responses.html"]),
         de("Add a random suffix to the name",
            "Makes resource names unpredictable and hard to manage", 0.60,
            sources=["https://docs.aws.amazon.com/general/latest/gr/error-responses.html"])],
        [wa("Use the existing resource — describe/get it to verify it matches your needs", 0.92,
            sources=["https://docs.aws.amazon.com/general/latest/gr/error-responses.html"]),
         wa("For IaC (Terraform/CloudFormation), import the existing resource into your state", 0.88,
            "terraform import aws_s3_bucket.example my-bucket",
            sources=["https://developer.hashicorp.com/terraform/cli/commands/import"]),
         wa("Use data sources to reference existing resources instead of creating new ones", 0.85,
            sources=["https://docs.aws.amazon.com/general/latest/gr/error-responses.html"])],
    ))

    c.append(canon(
        "aws", "service-unavailable", "awscli2-linux",
        "An error occurred (ServiceUnavailableException) when calling the X operation",
        r"ServiceUnavailableException|Service Unavailable|503",
        "availability_error", "aws", ">=2.0,<3.0", "linux",
        "partial", 0.75, 0.85,
        "AWS service is temporarily unavailable. Usually a transient issue.",
        [de("Switch to a different AWS service",
            "Likely a temporary issue — switching services is a massive change", 0.90,
            sources=["https://docs.aws.amazon.com/general/latest/gr/api-retries.html"]),
         de("Increase request timeout",
            "The service is unavailable — waiting longer per-request doesn't help", 0.65,
            sources=["https://docs.aws.amazon.com/general/latest/gr/api-retries.html"])],
        [wa("Implement exponential backoff with jitter and retry", 0.92,
            sources=["https://docs.aws.amazon.com/general/latest/gr/api-retries.html"]),
         wa("Check AWS Health Dashboard for ongoing service incidents", 0.90,
            sources=["https://health.aws.amazon.com/health/status"]),
         wa("If persistent, try a different AWS region as failover", 0.78,
            sources=["https://docs.aws.amazon.com/general/latest/gr/rande.html"])],
    ))

    # ── TERRAFORM ──────────────────────────────────────────

    c.append(canon(
        "terraform", "state-lock-dynamodb", "tf1-linux",
        "Error acquiring the state lock: ConditionalCheckFailedException",
        r"Error acquiring the state lock|ConditionalCheckFailedException|Lock Info",
        "state_error", "terraform", ">=1.5,<2.0", "linux",
        "partial", 0.85, 0.88,
        "Another Terraform process holds the state lock (DynamoDB). Wait or force-unlock.",
        [de("Delete the DynamoDB lock item directly",
            "May cause state corruption if another process is running", 0.80,
            sources=["https://developer.hashicorp.com/terraform/language/state/locking"]),
         de("Disable state locking with -lock=false",
            "Risks concurrent state modifications — data corruption", 0.85,
            sources=["https://developer.hashicorp.com/terraform/language/state/locking"])],
        [wa("Wait for the other process to finish — check the Lock Info in the error for who holds it", 0.90,
            sources=["https://developer.hashicorp.com/terraform/language/state/locking"]),
         wa("If the lock is stale (crashed process), force-unlock: terraform force-unlock <LOCK_ID>", 0.88,
            sources=["https://developer.hashicorp.com/terraform/cli/commands/force-unlock"]),
         wa("Check CI/CD for parallel Terraform runs that need serialization", 0.82,
            sources=["https://developer.hashicorp.com/terraform/language/state/locking"])],
    ))

    c.append(canon(
        "terraform", "module-not-installed", "tf1-linux",
        "Error: Module not installed",
        r"Module not installed|Module source has changed|terraform init",
        "module_error", "terraform", ">=1.5,<2.0", "linux",
        "true", 0.95, 0.95,
        "Module source not downloaded. Need terraform init to download modules.",
        [de("Copy module source manually into .terraform/",
            "Terraform manages .terraform/ — manual changes will be overwritten", 0.85,
            sources=["https://developer.hashicorp.com/terraform/cli/commands/init"]),
         de("Change module source to a local path",
            "Defeats the purpose of using versioned modules", 0.65,
            sources=["https://developer.hashicorp.com/terraform/language/modules/sources"])],
        [wa("Run terraform init to download modules", 0.98,
            sources=["https://developer.hashicorp.com/terraform/cli/commands/init"]),
         wa("If module source changed, run terraform init -upgrade to fetch new version", 0.92,
            sources=["https://developer.hashicorp.com/terraform/cli/commands/init"]),
         wa("For CI/CD, ensure terraform init runs before plan/apply", 0.90,
            sources=["https://developer.hashicorp.com/terraform/cli/commands/init"])],
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
    print(f"Wave 5: wrote {written} new canons, skipped {skipped} existing")


if __name__ == "__main__":
    main()
