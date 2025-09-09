# OSINT Live Dashboard

Modular Streamlit dashboard with selectable OSINT modules.

## Quick start
```bash
pip install -r requirements.txt
streamlit run app.py
```

## Structure
```
osint-dashboard/
  app.py
  core.py
  modules/
    __init__.py
    rss.py
    cve_nvd.py
  .env.example
```

- Add new modules by dropping a `.py` file in `modules/` that exposes a `module` object with:
  - `id`, `name`, `config_schema`, `default_refresh_sec`
  - `async def fetch(cfg)` → dict
  - `def render(st, data)` → None

## Notes
- Designed for public/open feeds. Respect each source's ToS and rate limits.
- For production: consider FastAPI backend, Redis cache, Postgres storage, and auth.


## Debian quick install
```bash
unzip osint-dashboard.zip && cd osint-dashboard
bash install_debian.sh
```

### Run as a service
```bash
sudo cp systemd/osint-dashboard.service /etc/systemd/system/osint-dashboard@YOURUSER.service
sudo systemctl daemon-reload
sudo systemctl enable --now osint-dashboard@YOURUSER
```

### Optional reverse proxy (Nginx)
See `NGINX_SAMPLE.conf`.
