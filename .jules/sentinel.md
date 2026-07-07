## 2026-06-28 - Exception Handling Code Health
**Learning:** Empty exception blocks (`except Exception: pass`) obscure potential runtime issues and make debugging difficult.
**Action:** When working with Streamlit UI code or Backend API health checks, always ensure exceptions are appropriately logged (using `.debug()` for UI extraction fallbacks or `.warning()` for external endpoint access failures) so issues can be traced without crashing the application.
