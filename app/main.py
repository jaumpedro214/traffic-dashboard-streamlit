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
    columns = st.sidebar.columns([1, 20, 1])
    columns[0].write(":city_sunset:")
    min_hour, max_hour = columns[1].slider(
        "",
        pd.datetime(2019, 1, 1, 0, 0),
        pd.datetime(2019, 1, 1, 23, 59),
        (pd.datetime(2019, 1, 1, 0, 0), pd.datetime(2019, 1, 1, 23, 59)),
        format="HH:mm",
        label_visibility="collapsed"
    )
    columns[2].write(":night_with_stars:")

    return min_hour, max_hour


def read_data(
    min_date, max_date, min_hour, max_hour, vehicle_classes
):
    df_traffic = pd.read_parquet("/data/vehicles_count.parquet")

    # translate the vehicle classes
    vehicle_classes_translate = {
        "BUS/TRUCK": "CAMINHAO_ONIBUS",
        "CAR": "AUTOMOVEL",
        "MOTORCYCLE": "MOTOCICLETA",
        "UNDEFINED": "INDEFINIDO"
    }

    vehicle_classes = [
        vehicle_classes_translate[vehicle_class]
        for vehicle_class in vehicle_classes
    ]

    # filter by vehicle class
    df_traffic = df_traffic.query(
        "CLASS in @vehicle_classes"
    )

    # filter by date
    df_traffic = df_traffic.query(
        "MIN_TIME >= @min_date and MIN_TIME <= @max_date"
    )

    # filter by hour
    df_traffic['HOUR'] = df_traffic['MIN_TIME'].dt.hour
    df_traffic = df_traffic.query(
        "HOUR >= @min_hour.hour and HOUR <= @max_hour.hour"
    )

    # group by LONGITUDE, LATITUDE
    df_traffic = (
        df_traffic
        .groupby(["LONGITUDE", "LATITUDE"])
        .agg({"COUNT": "sum"})
        .reset_index()
    )

    st.dataframe(df_traffic)

    return df_traffic


if __name__ == "__main__":

    st.title("Traffic in Belo Horizonte - MG")

    vehicle_classes = vehicle_class()
    min_date, max_date = dates_range()
    min_hour, max_hour = hour_range()

    df_traffic = read_data(
        min_date, max_date,
        min_hour, max_hour,
        vehicle_classes
    )
