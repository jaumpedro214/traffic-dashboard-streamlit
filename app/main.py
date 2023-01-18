import streamlit as st
import pandas as pd
import numpy as np

MIN_DATE = pd.to_datetime("2022-01-01")
MAX_DATE = pd.to_datetime("2022-02-28")

def dates_range():
    lateral_columns = st.sidebar.columns([1, 1])
    min_date = lateral_columns[0].date_input(
        "From", MIN_DATE, 
        min_value=MIN_DATE, 
        max_value=MAX_DATE
    )
    max_date = lateral_columns[1].date_input(
        "To", MAX_DATE,
        min_value=MIN_DATE,
        max_value=MAX_DATE
    )

    return min_date, max_date

def vehicle_class():
    vehicle_type = st.sidebar.multiselect(
        "Vehicle Class",
        ["BUS/TRUCK", "CAR", "MOTORCYCLE", "UNDEFINED"],
        ["BUS/TRUCK", "CAR", "MOTORCYCLE", "UNDEFINED"]
    )

    return vehicle_type

def hour_range():

    # slider with the hour and minute
    columns = st.sidebar.columns([2, 20, 1])
    columns[0].write(":sunrise:")
    columns[1].slider(
        "",
        pd.datetime(2019, 1, 1, 0, 0),
        pd.datetime(2019, 1, 1, 23, 59),
        (pd.datetime(2019, 1, 1, 0, 0), pd.datetime(2019, 1, 1, 23, 59)),
        format="HH:mm",
        label_visibility="collapsed"
    )
    columns[2].write(":night_with_stars:")

if __name__ == "__main__":

    st.title("Traffic in Belo Horizonte - MG")

    vehicle_class()
    dates_range()
    hour_range()
