## 2026-06-27 - Hardcoded Admin and Cron Secrets in main.py
**Vulnerability:** The application was using weak hardcoded fallback secrets for `ADMIN_SECRET_KEY` and `CRON_SECRET_KEY` via `os.getenv` default values. If these environment variables were omitted during deployment, an attacker could trivially bypass authentication using the known default strings.
**Learning:** Hardcoded fallbacks for sensitive credentials in Python code (e.g., `os.getenv('KEY', 'fallback')`) silently create critical vulnerabilities if proper configuration fails. Systems must fail closed and secure when configuration is missing.
**Prevention:** Remove fallback values for secrets. Instead, check if the environment variable is present; if it is missing, log an internal error specifying the missing key and throw an HTTP 500 Server Configuration Error to the client without leaking configuration details.
## 2026-06-28 - Regex Optimization Performance Improvement

**Learning:** Consolidating multiple dictionary loop regex patterns into a single combined regex using named capture groups reduces extraction time by eliminating the $O(N \times M)$ processing overhead. Sorting all keywords globally by length (descending) before compiling the pattern correctly enforces the Maximum Munch algorithm while avoiding cross-category pattern overlap fragilities inherent in eager regex alternations (`|`).
**Action:** When asked to optimize iterative pattern matching paths, look for opportunities to compile single-pass `re` objects with named capturing groups mapped dynamically back to the requested entity structures.
## 2026-06-28 - Exception Handling Code Health
**Learning:** Empty exception blocks (`except Exception: pass`) obscure potential runtime issues and make debugging difficult.
**Action:** When working with Streamlit UI code or Backend API health checks, always ensure exceptions are appropriately logged (using `.debug()` for UI extraction fallbacks or `.warning()` for external endpoint access failures) so issues can be traced without crashing the application.
