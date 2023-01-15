import streamlit as st
import pandas as pd
import numpy as np

st.title("Traffic in Belo Horizonte - MG")

# calendar 
st.date_input("Select a date", pd.to_datetime("2019-01-01"))

# Slider with date
st.slider(
    "Select a range of values", 
    pd.datetime(2019, 1, 1), 
    pd.datetime(2019, 1, 31),
    (pd.datetime(2019, 1, 1), pd.datetime(2019, 1, 31))
)

# slider with the hour and minute
columns = st.columns([1,20,1])
columns[0].write(":sunrise:")
columns[1].slider(
    "",
    pd.datetime(2019, 1, 1, 0, 0),
    pd.datetime(2019, 1, 1, 23, 59),
    (pd.datetime(2019, 1, 1, 0, 0), pd.datetime(2019, 1, 1, 23, 59)),
    format="HH:mm",
    label_visibility = "collapsed"
)
columns[2].write(":night_with_stars:")