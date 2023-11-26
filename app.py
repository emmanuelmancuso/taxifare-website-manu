import streamlit as st
import requests
from datetime import datetime, time
import pandas as pd
import numpy as np
from streamlit.components.v1 import declare_component
import pydeck as pdk
import googlemaps
import folium
from folium import plugins
from streamlit_folium import folium_static

#==================================================================
# Default values
#==================================================================
default_pickup_address = "Harlem"
default_dropoff_address = "Brooklyn"
default_pickup_datetime = datetime.strptime("2012-10-06 12:10:20", "%Y-%m-%d %H:%M:%S")
default_pickup_address = "New York, USA"
default_dropoff_address = "Brooklyn, USA"
default_passenger_count = 1

prediction = None
button_pressed = False

total_duration_minutes=None
route_coordinates=[]

pickup_location = None
dropoff_location = None

pickup_longitude = None
pickup_latitude = None
dropoff_longitude = None
dropoff_latitude = None

pickup_date = datetime(2012, 10, 6)
pickup_time = time(12, 10)
pickup_latitude_float=40.7127753
dropoff_latitude_float=40.6781784
pickup_longitude_float=-74.0059728
dropoff_longitude_float=-73.9441579

pickup_icon = "images/start.png"
dropoff_icon = "images/end.png"

data = []
data.append({"position": [pickup_longitude_float, pickup_latitude_float], "color": [0, 128, 0], "radius": 100,"icon": pickup_icon})
data.append({"position": [dropoff_longitude_float, dropoff_latitude_float], "color": [255, 0, 0], "radius": 100, "icon": dropoff_icon})

params = {
        "pickup_datetime": f"{pickup_date} {pickup_time}",
        "pickup_longitude": pickup_longitude,
        "pickup_latitude": pickup_latitude,
        "dropoff_longitude": dropoff_longitude,
        "dropoff_latitude": dropoff_latitude,
        "passenger_count": default_passenger_count,
        "width": 700,
        "height": 500,
    }
#==================================================================
# Récupérer la clé Google Maps à partir des secrets de Streamlit
google_maps_api_key = st.secrets["GOOGLE_MAPS_API_KEY"]
gmaps = googlemaps.Client(key=google_maps_api_key)

#==================================================================
#  The page and the title
#==================================================================
st.set_page_config(page_title="🚕 Taxi Fare Model by ManU 🚕", layout="wide")
st.markdown(f"<div style='text-align:center; font-size:36px; color:navy;'><b>🚕 Taxi Fare Model by ManU 🚕<br><br></b></div>", unsafe_allow_html=True)

#==================================================================
# Columns definition and size
#==================================================================
col1, col2= st.columns([1, 2], gap="small")
#==================================================================
# First column
#==================================================================
with col1:
    st.markdown(f"<div style='text-align:center; font-size:18px; margin:0px;'><b>Date and hour : </b></div>", unsafe_allow_html=True)
    # Divide the 1st column into 2 subcolumns
    sub_col1, sub_col2 = st.columns([1, 1])
    with sub_col1:
        pickup_date = st.date_input("", value=default_pickup_datetime.date())
    with sub_col2:
        pickup_time = st.time_input("", value=default_pickup_datetime.time())
    #==================================================================
    # Pickup adress user entry
    #==================================================================
    def reload_selectbox_addr_start():
        st.session_state.addr_start = st.session_state.select_start
    def reload_text_input_addr_start():
        if st.session_state.addr_start:
            autocomplete_results_start = gmaps.places_autocomplete(st.session_state.addr_start)
            st.session_state.addr_start = [address['description'] for address in autocomplete_results_start][0]
    st.markdown(f"<div style='text-align:center; font-size:18px; margin:0px;'><b>Departure address : </b></div>", unsafe_allow_html=True)
    sub_col1, sub_col2 = st.columns([1, 1])
    with sub_col1:
        pickup_address = st.text_input("",
                            key="addr_start",
                            value=default_pickup_address,
                            on_change=reload_text_input_addr_start)
        if st.session_state.addr_start:
            autocomplete_results_start = gmaps.places_autocomplete(st.session_state.addr_start)
            options_start = [address['description'] for address in autocomplete_results_start]
        else:
            options_start=["Addresses available"]
    with sub_col2:
        st.selectbox(" ",
                    options=options_start,
                    key="select_start",
                    on_change=reload_selectbox_addr_start)
    #==================================================================
    # Dropoff adress user entry
    #==================================================================
    def reload_selectbox_addr_end():
        st.session_state.addr_end = st.session_state.select_end
    def reload_text_input_addr_end():
        if st.session_state.addr_end:
            autocomplete_results_end = gmaps.places_autocomplete(st.session_state.addr_end)
            st.session_state.addr_end = [address['description'] for address in autocomplete_results_end][0]
    st.markdown(f"<div style='text-align:center; font-size:18px; margin:0px;'><b>Arrival address : </b></div>", unsafe_allow_html=True)
    sub_col1, sub_col2 = st.columns([1, 1])
    with sub_col1:
        dropoff_address = st.text_input("",
                            key="addr_end",
                            value=default_dropoff_address,
                            on_change=reload_text_input_addr_end)
        if st.session_state.addr_end:
            autocomplete_results_end = gmaps.places_autocomplete(st.session_state.addr_end)
            options_end = [address['description'] for address in autocomplete_results_end]
        else:
            options_end=["Addresses available"]
    with sub_col2:
        st.selectbox(" ",
                    options=options_end,
                    key="select_end",
                    on_change=reload_selectbox_addr_end)
    #==================================================================
    # Passenger count
    #==================================================================
    st.markdown(f"<div style='text-align:center; font-size:18px; margin:0px;'><b>Number of passengers : </b></div>", unsafe_allow_html=True)
    passenger_count = st.slider("",
                            min_value=1,
                            max_value=10,
                            step=1,
                            value=default_passenger_count)
#==================================================================
# Obtains the coordinates (lat and lon) for the pickup and dropoff adresses
#==================================================================
if pickup_address and dropoff_address:
    pickup_location = gmaps.geocode(pickup_address)
    dropoff_location = gmaps.geocode(dropoff_address)
if pickup_location and dropoff_location:
    # Extract the coordinates lat and lon
    pickup_latitude, pickup_longitude = pickup_location[0]['geometry']['location']['lat'], pickup_location[0]['geometry']['location']['lng']
    dropoff_latitude, dropoff_longitude = dropoff_location[0]['geometry']['location']['lat'], dropoff_location[0]['geometry']['location']['lng']
    # Parameters for the API query to obtain the predict price
    params = {
        "pickup_datetime": f"{pickup_date} {pickup_time}",
        "pickup_longitude": pickup_longitude,
        "pickup_latitude": pickup_latitude,
        "dropoff_longitude": dropoff_longitude,
        "dropoff_latitude": dropoff_latitude,
        "passenger_count": passenger_count,
        "width": 700,
        "height": 500,
    }
#==================================================================
# Convert numeric values into float type
#==================================================================
if pickup_longitude and pickup_latitude and dropoff_longitude and dropoff_latitude:
    pickup_longitude_float = float(pickup_longitude)
    pickup_latitude_float = float(pickup_latitude)
    dropoff_longitude_float = float(dropoff_longitude)
    dropoff_latitude_float = float(dropoff_latitude)
    # Assign default value for data used in the map section
    data = [{"position": [pickup_longitude_float, pickup_latitude_float], "color": [0, 128, 0], "radius": 100,"icon": pickup_icon},
            {"position": [dropoff_longitude_float, dropoff_latitude_float], "color": [255, 0, 0], "radius": 100,"icon": dropoff_icon}]

#==================================================================
# Calcul of the directions between pickup and dropoff points
#==================================================================
    directions_result = gmaps.directions(
        f"{pickup_latitude_float}, {pickup_longitude_float}",
        f"{dropoff_latitude_float}, {dropoff_longitude_float}",
        mode="driving"
    )
    # Store the points of the route in 'route_coordinates list
    if len(directions_result) != 0:
        route_coordinates = []
        for step in directions_result[0]['legs'][0]['steps']:
            route_coordinates.append(step['polyline']['points'])
        # Convert coordonninates from polyline into a list of latitudes eand longitudes
        decoded_coordinates = [googlemaps.convert.decode_polyline(point) for point in route_coordinates]
        # Flatten the list of lists into a single list of coordinates
        route_coordinates = [coord for sublist in decoded_coordinates for coord in sublist]
        # Total duration of the route
        total_duration = sum(step['duration']['value'] for step in directions_result[0]['legs'][0]['steps'])
        # Convert the duration in minutes unit
        total_duration_minutes = total_duration // 60
#==================================================================
# Prediction button
#==================================================================
with col1:
    sub_col1, sub_col2, sub_col3 = st.columns([1, 1, 1])
    with sub_col2:
        if st.button("Predict taxi fare"):
            button_pressed = True
            # Check all parameters are filled
            if not(pickup_date and pickup_time and pickup_longitude_float and pickup_latitude_float and dropoff_longitude_float and dropoff_latitude_float and passenger_count):
                st.write("Please fill in all mandatory fields.")
            else:
                # API REQUEST
                response = requests.get('https://taxifare.lewagon.ai/predict', params=params)
                # Check the response
                if response.status_code == 200:
                    try:
                        # Result extraction -> Taxi Fare
                        prediction = response.json()['fare']
                        # Display the results (fare amount and duration)
                        with col2:
                            if prediction and len(route_coordinates)!=0:
                                st.markdown(f"<div style='text-align:center; font-size:20px;'>Trip price prediction : <span style='color:darkgreen;'><b>{round(prediction, 2)} $</b></span></div>", unsafe_allow_html=True)
                            else:
                                st.markdown(f"<div style='text-align:center; font-size:20px;'><span style='color:darkgreen;'><b>Route calculation impossible.<br>Enter another address.</b></span></div>", unsafe_allow_html=True)
                            if total_duration_minutes:
                                st.markdown(f"<div style='text-align:center; font-size:20px;'>Travel time : <span style='color:darkgreen;'><b>{total_duration_minutes} min</b></span></div>", unsafe_allow_html=True)
                    except KeyError:
                        # Error of API response displayed
                        with col2:
                            st.write("The 'prediction' key is missing from the API response.")
                else:
                    # Error of API response displayed
                    with col2:
                        st.write(f"Error during prediction. Please complete all fields.")
            # Update the data list for the data display on the map
            data = []
            for coord in route_coordinates:
                data.append({"position": [coord['lng'], coord['lat']], "color": [0, 0, 0], "radius": 30})
            # Interpolation of the route points to obtains a continus route plot
            interpolated_points = []
            for i in range(len(route_coordinates) - 1):
                start_coord = route_coordinates[i]
                end_coord = route_coordinates[i + 1]
                # nb of points to interpolate
                num_interpolated_points = 10
                # Interpolation
                for j in range(num_interpolated_points + 1):
                    alpha = j / num_interpolated_points
                    interpolated_lng = start_coord['lng'] * (1 - alpha) + end_coord['lng'] * alpha
                    interpolated_lat = start_coord['lat'] * (1 - alpha) + end_coord['lat'] * alpha
                    interpolated_points.append({"position": [interpolated_lng, interpolated_lat], "color": [0, 0, 0], "radius": 30})
            # Add interpolated points
            data.extend(interpolated_points)
            # Add the Pickup and Dropoff points
            data.append({"position": [pickup_longitude_float, pickup_latitude_float], "color": [0, 128, 0], "radius": 100,"icon": pickup_icon})
            data.append({"position": [dropoff_longitude_float, dropoff_latitude_float], "color": [255, 0, 0], "radius": 100,"icon": dropoff_icon})
#==================================================================
# Map section in the second columns
#==================================================================
with col2:
#    view_state = {"latitude": (pickup_latitude_float + dropoff_latitude_float) / 2,
#                  "longitude": (pickup_longitude_float + dropoff_longitude_float) / 2,
#                  "zoom": 10,
#                  "pitch": 0}

#    scatterplot_layer = pdk.Layer("ScatterplotLayer",
#                                           data=data,
#                                           get_position="position",
#                                           get_radius="radius",
#                                           get_fill_color="color",
#                                           pickable=True,
#                                           auto_highlight=True)

#    icon_layer = pdk.Layer(type="IconLayer",
#                                           data=data,
#                                           get_position="position",
#                                           get_icon="icon",
#                                           get_size=4,
#                                           size_scale=15,
#                                           pickable=True)

     # Create the Pydeck deck with both ScatterplotLayer and IconLayer
#    deck = pdk.Deck(
#        map_style="mapbox://styles/mapbox/streets-v12",
#        initial_view_state=view_state,
#        layers=[scatterplot_layer, icon_layer]
#    )

    # Display the Pydeck deck using Streamlit
#    st.pydeck_chart(deck)

    #==================================================================
    # Map section with Folium
    #==================================================================
    mymap = folium.Map(location=[(pickup_latitude_float + dropoff_latitude_float) / 2,
                                (pickup_longitude_float + dropoff_longitude_float) / 2],
                    zoom_start=11,
                    tiles="OpenStreetMap")

    # Ajouter des marqueurs pour la prise en charge et le dépose
    folium.Marker(location=[pickup_latitude_float, pickup_longitude_float], popup=pickup_address,
                icon=folium.Icon(color='green')).add_to(mymap)

    folium.Marker(location=[dropoff_latitude_float, dropoff_longitude_float], popup=dropoff_address,
                icon=folium.Icon(color='red')).add_to(mymap)

    # Ajouter la ligne reliant les points intermédiaires
    if len(route_coordinates)!=0 and button_pressed:
        folium.PolyLine(locations=[[coord['lat'], coord['lng']] for coord in route_coordinates], color='blue').add_to(mymap)

    # Afficher la carte Folium dans Streamlit
    folium_static(mymap)

# Ajouter une sidebar
st.sidebar.markdown("[Created by ManU](https://www.linkedin.com/in/emmanuel-mancuso-89103225/) :link:")
st.sidebar.markdown("""
                    Welcome to the TaxiFare project team at WagonCab 🚕
In this module, you will impersonate a ML Engineer at WagonCab, a new taxi-app startup opening in New York!

WagonCab is willing to launch a new ML-product in production called TaxiFare. It’s goal is to integrate into its app the prediction of the price of conventional taxi rides in new york, in order to show its user how much money they would gain by comparison!

Your company has at its disposal the huge public [NYC Trip Record Dataset](https://www.nyc.gov/site/tlc/about/tlc-trip-record-data.page) which weights around 170 Go, and looks as follow

A team of Data Scientists has been staffed to create and fine-tune a machine learning model to predict the price of a ride.
They have been working in a isolated notebook context, hand-crafting & fine-tuning the best possible model, trained on a small, manageable subset of this dataset.""")
