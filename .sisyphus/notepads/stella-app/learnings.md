
## Task 9 — Auth Middleware

### Circular import pattern (deps.py ↔ auth.py)
- `deps.py` defines `get_db` first, then imports `get_current_user` from `auth.py` at the bottom
- `auth.py` imports `get_db` from `deps.py` at the top
- Works because when `deps.py` is imported first, by the time `auth.py` is triggered, `get_db` is already in the partial module
- Import order critical: ensure `deps.py` is always imported before `auth.py` (FastAPI routers using `require_registered_user` from `deps.py` guarantee this)

### aiogram initData validation
- Use `aiogram.utils.web_app.safe_parse_webapp_init_data(token=..., init_data=...)`
- Raises `ValueError` on invalid data — catch and return 401
- `data.auth_date` is a datetime; use `.timestamp()` to compare with `time.time()`
- Auth scheme: `Authorization: tma <raw_initData>` (prefix "tma ")
- Expiry: 3600 seconds (1 hour)

### SQLAlchemy async engine in FastAPI lifespan
- `engine` variable defined in lifespan startup survives across `yield` for shutdown `dispose()`
- `async_sessionmaker(engine, expire_on_commit=False)` stored on `app.state.sessionmaker`
- `get_db` uses `request.app.state.sessionmaker()` as an async context manager

### config.py fields confirmed present
- `bot_token`, `database_url` (postgresql+psycopg), `admin_telegram_ids: list[int]`
