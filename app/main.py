import streamlit as st

import geopandas as gpd
import contextily as cx

import numpy as np
import pandas as pd
import pyarrow.parquet as pq

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


def read_traffic_count_data(
    min_date, max_date, min_hour, max_hour, vehicle_classes
):
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

    # Create all month numbers between min_date and max_date
    month_numbers = np.arange(
        min_date.month, max_date.month + 1
    ).tolist()

    # Use pyarrow to open the parquet file
    df_traffic = pq.ParquetDataset(
        "/data/vehicles_count.parquet",
        filters=[
            ("MONTH", "in", month_numbers),
            ("CLASS", "in", vehicle_classes),
        ]
    ).read_pandas().to_pandas()

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
    # LATITUDE and LONGITUDE TO FLOAT
    df_traffic["LATITUDE"] = df_traffic["LATITUDE"].astype(float)
    df_traffic["LONGITUDE"] = df_traffic["LONGITUDE"].astype(float)

    return df_traffic


def read_map_data(df_traffic):
    # read geojson
    path = './map/mg.json'
    gdf_bh = gpd.read_file(path)

    gdf_bh = gdf_bh.loc[gdf_bh["name"] == "Belo Horizonte"]
    gdf_bh = gdf_bh.to_crs(epsg=3857)

    ax = gdf_bh.plot(
        color="orange",
        edgecolor="black",
        alpha=0.2,
        figsize=(10, 10)
    )
    ax.set_axis_off()
    
    cx.add_basemap(
        ax,
        source=cx.providers.Stamen.TonerLite
    )

    return ax

def plot_count_data(df_traffic, ax):

    gdf_traffic = gpd.GeoDataFrame(
        df_traffic.copy(),
        geometry=gpd.points_from_xy(
            df_traffic.LONGITUDE, df_traffic.LATITUDE
        )
    )

    gdf_traffic.plot(
        column="COUNT",
        legend=True,
        markersize=1,
        figsize=(10, 10),
        ax=ax
    )

    return ax.figure


if __name__ == "__main__":

    st.title("Traffic in Belo Horizonte - MG")

    vehicle_classes = vehicle_class()
    min_date, max_date = dates_range()
    min_hour, max_hour = hour_range()

    df_traffic = read_traffic_count_data(
        min_date, max_date,
        min_hour, max_hour,
        vehicle_classes
    )

    ax = read_map_data(df_traffic)
    fig = plot_count_data(df_traffic, ax)
    st.pyplot(fig)
