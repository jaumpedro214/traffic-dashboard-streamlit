import streamlit as st

import geopandas as gpd
import contextily as cx

import numpy as np
import pandas as pd
import pyarrow.parquet as pq

import matplotlib.pyplot as plt
import matplotlib.patheffects as pe
import matplotlib.patches as mpatches

MIN_DATE = pd.to_datetime("2022-01-01")
MAX_DATE = pd.to_datetime("2022-02-28")

VEHICLE_CLASSES_TRANSLATE = {
    "BUS/TRUCK": "CAMINHAO_ONIBUS",
    "CAR": "AUTOMOVEL",
    "MOTORCYCLE": "MOTO",
    "UNDEFINED": "INDEFINIDO"
}

## Widgets ##
## ======= ##


def widget_dates_range():
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


def widget_vehicle_class():
    vehicle_type = st.sidebar.multiselect(
        "Vehicle Class",
        ["BUS/TRUCK", "CAR", "MOTORCYCLE", "UNDEFINED"],
        ["BUS/TRUCK", "CAR", "MOTORCYCLE", "UNDEFINED"]
    )

    return vehicle_type


def widget_hour_range():

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


def text_sidebar_about():
    st.sidebar.markdown(
        """
        ## About

        This app is a demo of a streamlit app that uses geopandas to plot data on a map.

        The data used is from the [Brazilian Government Open Data Portal](https://dados.gov.br/dados/conjuntos-dados/contagens-volumetricas-de-radares), made availabye by the Belo Horizonte City Hall.
        It contains the readings of the traffic radars in the city of Belo Horizonte, in the state of Minas Gerais.

        _Author: [João Pedro](https://github.com/jaumpedro214)_
        """
    )

    st.sidebar.markdown(
        """
        ## Caveats

        1. As the data is collected from traffic radars, the data is not 100% accurate and is biased towards the main roads.
        2. Because of 1, the numbers are probably way under the real numbers.
        """
    )


## Data ##
## ==== ##


@st.cache
def read_traffic_count_data(
    min_date, max_date, min_hour, max_hour, vehicle_classes
):
    # translate the vehicle classes

    vehicle_classes = [
        VEHICLE_CLASSES_TRANSLATE[vehicle_class]
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

    return df_traffic


@st.cache
def group_traffic_count_data(df_traffic):

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


@st.cache
def group_traffic_count_data_by_class(df_traffic):

    # group by CLASS
    df_traffic = (
        df_traffic
        .groupby(["CLASS"])
        .agg({
            "COUNT": "sum"
        })
        .reset_index()
    )

    # Calculate percentage
    df_traffic["PERCENTAGE"] = (
        df_traffic["COUNT"] / df_traffic["COUNT"].sum()
    )

    return df_traffic

## Plot ##
## ==== ##


def load_map_data():
    # read geojson
    path = './map/mg.json'
    gdf_bh = gpd.read_file(path)

    gdf_bh = gdf_bh.loc[gdf_bh["name"] == "Belo Horizonte"]
    gdf_bh = gdf_bh.to_crs(epsg=3857)

    return gdf_bh


def read_map_data(df_traffic):
    gdf_bh = load_map_data()

    ax = gdf_bh.plot(
        color="black",
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
    gdf_traffic = gdf_traffic.set_crs(epsg=4326).to_crs(epsg=3857)

    gdf_traffic["MARKER_SIZE"] = gdf_traffic["COUNT"] / (1e4)

    ax = gdf_traffic.plot(
        column="COUNT",
        legend=True,
        markersize="MARKER_SIZE",
        figsize=(10, 10),
        zorder=2,
        color="#fc4c4c",
        alpha=0.8,
        ax=ax
    )

    # add the count to each point
    gdf_traffic_head = gdf_traffic.sort_values(
        "COUNT", ascending=False).head(5)

    # if x < 1e4 -> 8
    # if x > 1e4 and x <= 1e6 -> 10
    # if x >= 1e6 -> 12
    def fontsize_func(x): return 10 if x < 1e3 else 12 if x <= 1e6 else 14
    # Use K and M to represent the number

    def text_number_represent(
        x): return f"{x/1e3:.1f}K" if x < 1e6 else f"{x/1e6:.1f}M"

    for x, y, label in zip(
        gdf_traffic_head.geometry.x,
        gdf_traffic_head.geometry.y,
        gdf_traffic_head["COUNT"]
    ):
        ax.annotate(
            text_number_represent(label),
            xy=(x, y),
            xytext=(0, 2),
            textcoords="offset points",
            fontsize=fontsize_func(label),
            color="white",
            ha="center",
            va="bottom",
            # add outline to the text
            path_effects=[
                pe.withStroke(linewidth=0.5, foreground="black")
            ]
        )

    return ax


def plot_class_counts_data(df_traffic_classgrouped, vehicle_classes):

    emojis = {
        "MOTO": ":motor_scooter:",
        "AUTOMOVEL": ":red_car:",
        "CAMINHAO_ONIBUS": ":truck:",
        "INDEFINIDO": ":question:"
    }

    # Remove Undefined class
    if 'UNDEFINED' in vehicle_classes:
        vehicle_classes.remove("UNDEFINED")

    if len(vehicle_classes) == 0:
        return

    # Plot class grouped data
    class_columns = st.columns(len(vehicle_classes))

    for i, vehicle_class in enumerate(vehicle_classes):

        vehicle_class_pt = VEHICLE_CLASSES_TRANSLATE[vehicle_class]

        count = df_traffic_classgrouped.query(
            f"CLASS == '{vehicle_class_pt}'"
        )["COUNT"].values[0]
        percentage = df_traffic_classgrouped.query(
            f"CLASS == '{vehicle_class_pt}'"
        )["PERCENTAGE"].values[0]

        count_text = f"{count:,}".replace(",", " ")

        class_columns[i].subheader(
            f"{emojis[vehicle_class_pt]} {vehicle_class}")
        class_columns[i].markdown(
            f"""
            #### {count_text} ({percentage:.1%}) 
            """
        )


if __name__ == "__main__":

    # App header
    TITLE = "How, when and where people move in  the roads of Belo Horizonte?"
    SUBTITLE = "Georeferenced and temporal analysis of traffic in the capital of Minas Gerais"

    st.title(TITLE)
    st.sidebar.markdown("## "+SUBTITLE)
    st.markdown("")

    # Adding widgets
    # on the sidebar

    vehicle_classes = widget_vehicle_class()
    min_date, max_date = widget_dates_range()
    min_hour, max_hour = widget_hour_range()
    text_sidebar_about()

    if len(vehicle_classes) == 0:
        st.stop()

    # Main app
    # Read data
    df_traffic = read_traffic_count_data(
        min_date, max_date,
        min_hour, max_hour,
        vehicle_classes
    ).copy()
    df_traffic_geogrouped = group_traffic_count_data(df_traffic).copy()
    df_traffic_classgrouped = group_traffic_count_data_by_class(
        df_traffic).copy()

    total_count = df_traffic_classgrouped["COUNT"].sum()

    # Title with total count
    st.header(
        f"{total_count:,} ".replace(',', ' ')
        + "vehicles detected"
    )

    # Plot georeferenced data
    ax = read_map_data(df_traffic_geogrouped)
    ax = plot_count_data(df_traffic_geogrouped, ax)
    st.pyplot(ax.figure)

    # Plot class grouped data
    plot_class_counts_data(df_traffic_classgrouped, vehicle_classes)
