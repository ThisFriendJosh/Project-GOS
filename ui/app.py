import pandas as pd
import streamlit as st

st.set_page_config(page_title="Project GOS UI")

st.title("Placeholder Dataset")

# Sample dataset
data = pd.DataFrame(
    {
        "Column A": [1, 2, 3],
        "Column B": ["a", "b", "c"],
    }
)

st.table(data)
