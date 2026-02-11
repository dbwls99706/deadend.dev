"""Wave 16: final 12+ canons to reach 500."""

import json
from generator.bulk_generate import (
    canon, de, wa, DATA_DIR,
)


def get_all_canons():
    c = []

    c.append(canon(
        "python", "oserror-errno98-address-in-use", "py310-linux",
        "OSError: [Errno 98] Address already in use",
        r"OSError: \[Errno 98\] Address already in use",
        "network", "cpython", ">=3.8", "linux",
        "true", 0.96, 0.97,
        "Attempting to bind a socket to a port that is already in use by another process.",
        [de("Killing the process on that port without checking what it is", "May kill a critical service", 0.55),
         de("Using SO_REUSEADDR as the only fix", "Masks the problem if the old process is still running and handling connections", 0.40)],
        [wa("Find and stop the process using the port: lsof -i :<port> or ss -tlnp | grep <port>", 0.95, "Identify the process, then decide whether to stop it or use a different port"),
         wa("Use SO_REUSEADDR and a different port as fallback: sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)", 0.88, "Allows reuse of TIME_WAIT ports", sources=["https://docs.python.org/3/library/socket.html"])],
    ))

    c.append(canon(
        "python", "modulenotfounderror-no-module-named", "py310-macos",
        "ModuleNotFoundError: No module named 'numpy'",
        r"ModuleNotFoundError: No module named",
        "import", "cpython", ">=3.8", "macos",
        "true", 0.97, 0.98,
        "Python cannot find the specified module — not installed, wrong environment, or wrong Python version.",
        [de("Installing globally with sudo pip install", "Installs in system Python which may be different from your project's Python", 0.75),
         de("Adding the module to sys.path manually", "Fragile; path changes break the import", 0.70)],
        [wa("Install in the correct virtual environment: pip install numpy (with venv activated)", 0.97, "Verify with: which python && pip list | grep numpy"),
         wa("Ensure you're using the right Python: python -m pip install numpy", 0.93, "python -m pip ensures pip matches the Python interpreter", sources=["https://docs.python.org/3/installing/index.html"])],
    ))

    c.append(canon(
        "node", "err-aborted", "node20-linux",
        "DOMException: The operation was aborted",
        r"(The operation was aborted|AbortError|ERR_ABORTED)",
        "async", "node", ">=16", "linux",
        "true", 0.93, 0.94,
        "Fetch or other async operation was cancelled via AbortController.",
        [de("Removing the AbortController to prevent the error", "Loses the ability to cancel long-running requests; potential memory leaks", 0.70),
         de("Catching and ignoring all AbortError", "May hide other abort-related bugs", 0.50)],
        [wa("Handle AbortError specifically: catch(e) { if (e.name === 'AbortError') return; throw e; }", 0.95, "Only ignore intentional abort errors; re-throw unexpected ones", sources=["https://developer.mozilla.org/en-US/docs/Web/API/AbortController"]),
         wa("Check signal.aborted before processing results", 0.88, "if (!signal.aborted) { processResult(data) } — guard against race conditions")],
    ))

    c.append(canon(
        "docker", "unauthorized-authentication-required", "docker24-linux",
        "Error response from daemon: unauthorized: authentication required",
        r"unauthorized: authentication required",
        "auth", "docker", ">=20.10", "linux",
        "true", 0.95, 0.96,
        "Docker registry requires authentication to pull or push images.",
        [de("Making the registry public", "Exposes all images to anyone; security risk", 0.90),
         de("Storing credentials in Dockerfile", "Credentials are baked into the image layer and visible to anyone", 0.95)],
        [wa("Login to the registry: docker login <registry-url>", 0.96, "Stores credentials in ~/.docker/config.json", sources=["https://docs.docker.com/reference/cli/docker/login/"]),
         wa("For CI/CD, use a credential helper or environment variables", 0.90, "echo $TOKEN | docker login -u user --password-stdin")],
    ))

    c.append(canon(
        "git", "already-on-branch", "git2-linux",
        "Already on 'main'",
        r"Already on '.*'",
        "checkout", "git", ">=2.0", "linux",
        "true", 0.99, 0.99,
        "Attempting to checkout the branch you're already on.",
        [de("Force-checking out the branch", "git checkout -f discards all uncommitted changes", 0.85)],
        [wa("This is informational, not an error — you're already where you want to be", 0.99, "No action needed; git is confirming the current branch"),
         wa("If you expected to switch branches, check the branch name spelling: git branch -a", 0.90, "You may have typed the wrong branch name")],
    ))

    c.append(canon(
        "go", "unused-import", "go121-linux",
        "imported and not used: 'fmt'",
        r"imported and not used:",
        "compilation", "go", ">=1.18", "linux",
        "true", 0.99, 0.99,
        "Go does not allow unused imports — a package was imported but never referenced.",
        [de("Aliasing to blank identifier permanently: _ 'fmt'", "Keeps unnecessary import; adds dead code", 0.50)],
        [wa("Remove the unused import", 0.97, "Delete the import line; goimports can do this automatically"),
         wa("Use goimports to auto-manage imports: goimports -w file.go", 0.95, "Adds missing imports and removes unused ones automatically", sources=["https://pkg.go.dev/golang.org/x/tools/cmd/goimports"])],
    ))

    c.append(canon(
        "kubernetes", "horizontal-pod-autoscaler-unable", "k8s128-linux",
        "unable to calculate desired number of replicas: missing request for cpu",
        r"unable to calculate.*missing request for (cpu|memory)",
        "autoscaling", "kubernetes", ">=1.24", "linux",
        "true", 0.94, 0.96,
        "HPA cannot scale because pods don't have CPU/memory resource requests defined.",
        [de("Setting arbitrary resource requests", "Over or under-provisioning; either wastes resources or causes OOM", 0.55),
         de("Using memory-based scaling instead", "Memory scaling is less responsive than CPU for most workloads", 0.45)],
        [wa("Add resource requests to the pod spec: resources.requests.cpu: 100m", 0.96, "HPA needs resource requests to calculate utilization percentage", sources=["https://kubernetes.io/docs/tasks/run-application/horizontal-pod-autoscale/"]),
         wa("Use metrics-server to verify metrics are available: kubectl top pods", 0.88, "HPA requires metrics-server to be installed and running")],
    ))

    c.append(canon(
        "terraform", "backend-initialization-required", "tf115-linux",
        "Error: Backend initialization required, please run 'terraform init'",
        r"Backend initialization required.*terraform init",
        "init", "terraform", ">=1.0", "linux",
        "true", 0.98, 0.98,
        "Terraform backend configuration changed but terraform init wasn't run to apply the change.",
        [de("Manually editing .terraform directory files", "May corrupt the local state cache", 0.85),
         de("Copying state files between backends manually", "Easy to lose state or corrupt it; use terraform init -migrate-state instead", 0.75)],
        [wa("Run terraform init to initialize the new backend", 0.97, "Terraform will prompt to migrate state if the backend changed", sources=["https://developer.hashicorp.com/terraform/cli/commands/init"]),
         wa("Use terraform init -migrate-state to move state between backends", 0.93, "Safely copies state from old backend to new backend during init")],
    ))

    c.append(canon(
        "aws", "sqs-message-too-large", "aws-cli2-linux",
        "An error occurred (InvalidParameterValue) when calling the SendMessage operation: message size exceeds the maximum allowed size",
        r"(message size exceeds|MessageTooBig|message too long)",
        "sqs", "aws", ">=2.0", "linux",
        "true", 0.94, 0.96,
        "SQS message exceeds the 256KB size limit.",
        [de("Compressing the message with gzip", "Adds complexity; consumer must decompress; base64 encoding increases size by 33%", 0.50),
         de("Splitting the message into parts", "Requires a reassembly mechanism; complex and error-prone", 0.55)],
        [wa("Store the payload in S3 and send the S3 reference in the SQS message", 0.95, "Use amazon-sqs-extended-client-lib for automatic S3 offloading", sources=["https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/sqs-s3-messages.html"]),
         wa("Review the message — reduce unnecessary data fields or use a more compact format", 0.85, "Switch from JSON to a more compact format, or remove redundant data")],
    ))

    c.append(canon(
        "nextjs", "err-next-static-generation-error", "next14-linux",
        "Error occurred prerendering page '/path'. Read more: https://nextjs.org/docs/messages/prerender-error",
        r"(Error occurred prerendering|prerender-error|getStaticProps)",
        "static-generation", "next.js", ">=13", "linux",
        "true", 0.93, 0.95,
        "Static page generation failed during next build — usually a data fetching error or runtime error in the page component.",
        [de("Adding try/catch to suppress the error and return empty props", "Publishes a page with no data; users see an empty or broken page", 0.65),
         de("Switching all pages to SSR to avoid static generation", "Loses static optimization; increases server load and TTFB", 0.60)],
        [wa("Check the specific error in the build output — it shows the root cause above the prerender error", 0.95, "Scroll up in the build log to find the actual error: API timeout, missing env var, etc."),
         wa("Use generateStaticParams or fallback: 'blocking' for dynamic routes", 0.88, "For dynamic pages, generate known paths statically and render new ones on demand", sources=["https://nextjs.org/docs/app/api-reference/functions/generate-static-params"])],
    ))

    c.append(canon(
        "react", "act-warning-test", "react18-linux",
        "Warning: An update to Component inside a test was not wrapped in act(...)",
        r"(not wrapped in act|act\(\.\.\.\))",
        "testing", "react", ">=17", "linux",
        "true", 0.94, 0.96,
        "State update during test happened outside of React's batching — test may not reflect the final rendered state.",
        [de("Wrapping every test in a global act()", "Masks the specific update that isn't being awaited", 0.60),
         de("Suppressing console.error in tests", "Hides real issues along with the act warning", 0.75)],
        [wa("Wrap the triggering action in act(): await act(async () => { fireEvent.click(button) })", 0.95, "Ensures React processes all state updates before assertions", sources=["https://react.dev/reference/react/act"]),
         wa("Use @testing-library/react's userEvent which handles act() automatically", 0.90, "import userEvent from '@testing-library/user-event'; await user.click(button)")],
    ))

    c.append(canon(
        "cuda", "nvcc-not-found", "cuda12-linux",
        "FileNotFoundError: nvcc not found. Please ensure CUDA is installed",
        r"(nvcc.*not found|No such file.*nvcc)",
        "build", "cuda", ">=11.0", "linux",
        "true", 0.94, 0.96,
        "CUDA compiler (nvcc) is not in PATH — CUDA toolkit not installed or not configured.",
        [de("Installing nvidia-driver instead of CUDA toolkit", "The driver enables GPU compute but doesn't include nvcc or development tools", 0.80),
         de("Adding a random path to PATH hoping it has nvcc", "Wrong CUDA version's nvcc may be incompatible", 0.70)],
        [wa("Install the CUDA toolkit: apt install nvidia-cuda-toolkit or download from NVIDIA", 0.93, "The toolkit includes nvcc, libraries, and headers", sources=["https://developer.nvidia.com/cuda-downloads"]),
         wa("Add CUDA to PATH: export PATH=/usr/local/cuda/bin:$PATH", 0.95, "Most installations put nvcc in /usr/local/cuda/bin")],
    ))

    c.append(canon(
        "pip", "requires-python-version", "pip23-linux",
        "ERROR: Package 'package' requires a different Python version: 3.8 not in '>=3.9'",
        r"requires a different Python version",
        "compatibility", "pip", ">=22.0", "linux",
        "true", 0.95, 0.96,
        "Package requires a newer Python version than what's currently running.",
        [de("Using --ignore-requires-python flag", "Package may use syntax/features not available in your Python; crashes at runtime", 0.75),
         de("Editing the package's metadata to remove the constraint", "Will be overwritten on next install; doesn't fix actual incompatibilities", 0.85)],
        [wa("Upgrade Python to the required version or use pyenv to manage versions", 0.95, "pyenv install 3.11 && pyenv local 3.11", sources=["https://github.com/pyenv/pyenv"]),
         wa("Use an older version of the package that supports your Python: pip install 'package<2.0'", 0.88, "Check the package's changelog for the last version supporting your Python")],
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
    print(f"Wave 16: wrote {written} new canons, skipped {skipped} existing")


if __name__ == "__main__":
    main()
