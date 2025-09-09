import json
from pathlib import Path

import pandas as pd
import streamlit as st

st.title("OSINT Dashboard")
st.write("Sample data from seeded files.")

DATA_DIR = Path(__file__).resolve().parents[2] / "data"

entities = pd.read_csv(DATA_DIR / "entities.csv")
st.subheader("Entities")
st.dataframe(entities)

links = pd.read_csv(DATA_DIR / "links.csv")
st.subheader("Links")
st.dataframe(links)

with open(DATA_DIR / "incidents.json", "r", encoding="utf-8") as f:
    incidents = json.load(f)
incidents_df = pd.DataFrame(incidents)

st.subheader("Incidents")
st.dataframe(incidents_df)
