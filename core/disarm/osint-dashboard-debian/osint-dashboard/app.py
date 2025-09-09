import asyncio, time
import streamlit as st
from pydantic import BaseModel
from dotenv import load_dotenv
from core import discover_modules

load_dotenv()

st.set_page_config(page_title="OSINT Live", layout="wide")
st.title("OSINT Live Dashboard")

# Discover available modules
modules = discover_modules()
mod_map = {m.name: m for m in modules}

# Sidebar controls
with st.sidebar:
    st.header("Modules")
    chosen = st.multiselect(
        "Select modules to show",
        list(mod_map.keys()),
        default=list(mod_map.keys())[:2] if modules else []
    )
    cfg_values = {}
    refresh_overrides = {}

    for name in chosen:
        m = mod_map[name]
        st.markdown(f"**{name}**")
        # FIX: Access model_fields on the class, not instance (Pydantic 2.11+ change).
        for field, model_field in type(m.config_schema).model_fields.items():
            default = getattr(m.config_schema, field)
            if isinstance(default, int):
                val = st.number_input(f"{name}:{field}", value=default, step=1)
            elif isinstance(default, float):
                val = st.number_input(f"{name}:{field}", value=default)
            else:
                val = st.text_input(f"{name}:{field}", value=str(default))
                try:
                    val = type(default)(val)
                except Exception:
                    pass
            cfg_values.setdefault(m.id, {})[field] = val

        refresh_overrides[m.id] = st.number_input(
            f"{name} refresh (sec)",
            min_value=5, max_value=3600,
            value=int(m.default_refresh_sec), step=5
        )

    st.divider()
    auto = st.toggle("Auto-refresh", value=False)
    global_interval = st.slider("Global refresh (sec)", 10, 120, 30, step=5)
    st.caption("Tip: Toggle auto-refresh or click the 'Refresh now' button below.")
    refresh_now = st.button("Refresh now")

async def fetch_all():
    tasks = []
    cfg_models = []
    for name in chosen:
        m = mod_map[name]
        cfg_model = type(m.config_schema)(**cfg_values.get(m.id, {}))
        cfg_models.append((m, cfg_model))
        tasks.append(m.fetch(cfg_model))
    results = await asyncio.gather(*tasks, return_exceptions=True)
    return list(zip([m for m, _ in cfg_models], results))

# Rerun timer (replace st.autorefresh)
if "last_run_ts" not in st.session_state:
    st.session_state.last_run_ts = 0.0

now = time.time()
should_rerun = False
if auto:
    if now - st.session_state.last_run_ts >= global_interval:
        # mark and proceed (this run will render, next run will be scheduled)
        st.session_state.last_run_ts = now
    else:
        # sleep just enough then rerun
        time.sleep(max(0.1, global_interval - (now - st.session_state.last_run_ts)))
        st.session_state.last_run_ts = time.time()
        st.experimental_rerun()

if refresh_now:
    st.session_state.last_run_ts = time.time()

# One render pass
results = asyncio.run(fetch_all()) if chosen else []

# Layout: up to 3 columns
if results:
    cols = st.columns(max(1, min(len(results), 3)))
    for i, (m, res) in enumerate(results):
        with cols[i % len(cols)]:
            box = st.container(border=True)
            if isinstance(res, Exception):
                box.error(f"{m.name}: {res}")
            else:
                m.render(box, res)
else:
    st.info("Select one or more modules from the sidebar to begin.")
