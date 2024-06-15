import streamlit as st
import pandas as pd
import folium
from streamlit_folium import folium_static
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
from pymongo import MongoClient
import plotly.graph_objects as go

# Connect to MongoDB
client = MongoClient("mongodb+srv://Mani94:mani@cluster0.xbcyanf.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")
db = client.sample_airbnb
collection = db.listingsAndReviews

# Load data from MongoDB
#After Data Cleaning Process
#Save the CSV file
# For now, we'll use the CSV file
data = pd.read_csv(r"C:\Users\manik\Desktop\Air bnb Analysis\cleaned_airbnb_listings.csv")

# Streamlit app
st.title("Airbnb Data Visualization")

# Sidebar for filters
st.sidebar.header("Filters")

# Add "All" option to country filter
countries = ["All"] + list(data["country"].unique())
country_filter = st.sidebar.selectbox("Select Country", countries)

# Filter cities based on selected country and add "All" option
if country_filter == "All":
    cities = ["All"] + list(data["suburb"].unique())
else:
    cities = ["All"] + list(data[data["country"] == country_filter]["suburb"].unique())
city_filter = st.sidebar.selectbox("Select City", cities)

# Property type filter
property_type_filter = st.sidebar.multiselect("Select Property Type", data["property_type"].unique())

# Price range filter
price_range = st.sidebar.slider("Price Range", float(data["price"].min()), float(data["price"].max()), (100.0, 500.0))

# Rating range filter
rating_range = st.sidebar.slider("Rating Range", float(data["review_scores_rating"].min()), float(data["review_scores_rating"].max()), (80.0, 100.0))

# Room type filter
room_type_filter = st.sidebar.selectbox("Room Type", data['room_type'].unique())

# Filter data based on sidebar selections
filtered_data = data[
    (data["price"].between(price_range[0], price_range[1])) &
    (data["review_scores_rating"].between(rating_range[0], rating_range[1])) &
    (data["room_type"] == room_type_filter)
]

if country_filter != "All":
    filtered_data = filtered_data[filtered_data["country"] == country_filter]

if city_filter != "All":
    filtered_data = filtered_data[filtered_data["suburb"] == city_filter]

if property_type_filter:
    filtered_data = filtered_data[filtered_data["property_type"].isin(property_type_filter)]

# Remove rows with NaN values in latitude or longitude
filtered_data = filtered_data.dropna(subset=['latitude', 'longitude'])

# Display filtered data
if not filtered_data.empty:
    st.write(f"### Listings of type '{property_type_filter}' and room type '{room_type_filter}'")
    st.write(filtered_data)

    # Geospatial visualization
    st.subheader("Geospatial visualization")
    m = folium.Map(location=[filtered_data["latitude"].mean(), filtered_data["longitude"].mean()], zoom_start=13)

    for idx, row in filtered_data.iterrows():
        folium.Marker(
            [row["latitude"], row["longitude"]],
            tooltip=f"Price: ${row['price']} \nRating: {row['review_scores_rating']}"
        ).add_to(m)

    folium_static(m)
    st.write(f"This map shows the geographical distribution of listings filtered by:")
    st.write(f"- **Country**: {country_filter if country_filter != 'All' else 'All Countries'}")
    st.write(f"- **City**: {city_filter if city_filter != 'All' else 'All Cities'}")
    st.write(f"- **Property Type**: {property_type_filter if property_type_filter else 'All Types'}")
    st.write(f"- **Price Range**: {price_range[0]} to {price_range[1]}")
    st.write(f"- **Rating Range**: {rating_range[0]} to {rating_range[1]}")
    st.write(f"- **Room Type**: {room_type_filter}")

    # Price visualization
    st.subheader("Price Distribution")
    fig, ax = plt.subplots()
    sns.histplot(data=filtered_data, x="price", bins=20, ax=ax)
    plt.title("Price Distribution")
    st.pyplot(fig)
    st.write(f"**Price Distribution Details**:")
    st.write(f"- **Mean Price**: ${filtered_data['price'].mean():.2f}")
    st.write(f"- **Median Price**: ${filtered_data['price'].median():.2f}")
    st.write(f"- **Min Price**: ${filtered_data['price'].min():.2f}")
    st.write(f"- **Max Price**: ${filtered_data['price'].max():.2f}")

    # Rating visualization
    st.subheader("Rating Distribution")
    fig = px.histogram(filtered_data, x="review_scores_rating", nbins=20)
    fig.update_layout(title="Rating Distribution")
    st.plotly_chart(fig)
    st.write(f"**Rating Distribution Details**:")
    st.write(f"- **Mean Rating**: {filtered_data['review_scores_rating'].mean():.2f}")
    st.write(f"- **Median Rating**: {filtered_data['review_scores_rating'].median():.2f}")
    st.write(f"- **Min Rating**: {filtered_data['review_scores_rating'].min():.2f}")
    st.write(f"- **Max Rating**: {filtered_data['review_scores_rating'].max():.2f}")

    # Availability visualization
    st.subheader("Availability by Month")
    availability_data = filtered_data[['availability_30', 'availability_60', 'availability_90', 'availability_365']]
    availability_data = availability_data.melt(var_name='Availability Period', value_name='Days Available')
    fig2 = px.box(availability_data, x='Availability Period', y='Days Available')
    fig2.update_layout(title="Availability by Period")
    st.plotly_chart(fig2)
    st.write(f"**Availability Details**:")
    for period in ['availability_30', 'availability_60', 'availability_90', 'availability_365']:
        st.write(f"- **{period.replace('_', ' ')}**:")
        st.write(f"  - Mean: {filtered_data[period].mean():.2f} days")
        st.write(f"  - Median: {filtered_data[period].median():.2f} days")
        st.write(f"  - Min: {filtered_data[period].min()} days")
        st.write(f"  - Max: {filtered_data[period].max()} days")

    # Location-based insights
    st.subheader("Location-Based Insights")
    location_stats = filtered_data.groupby("suburb")[["latitude", "longitude", "price", "review_scores_rating", "availability_365"]].mean().reset_index()

    # Interactive map
    fig = go.Figure(go.Scattermapbox(
        lat=location_stats["latitude"],
        lon=location_stats["longitude"],
        mode="markers",
        marker=dict(
            size=location_stats["availability_365"] / 10,
            color=location_stats["review_scores_rating"],
            colorscale="Viridis",
            showscale=True,
            colorbar=dict(title="Rating"),
            opacity=0.8
        ),
        text=location_stats["suburb"],
        hoverinfo="lat+lon+text"
    ))

    fig.update_layout(
        mapbox_style="open-street-map",
        mapbox_center_lon=location_stats["longitude"].mean(),
        mapbox_center_lat=location_stats["latitude"].mean(),
        mapbox_zoom=10,
        title="Average Ratings and Availability by Location",
        margin=dict(l=0, r=0, t=30, b=0)
    )

    st.plotly_chart(fig, use_container_width=True)
    st.write(f"This interactive map visualizes the average ratings and availability by location. Larger markers indicate higher availability. The color gradient represents the average rating, with darker colors indicating higher ratings.")

    # Interactive visualizations
    st.subheader("Interactive Visualizations")

    # Price distribution by property type
    fig = px.box(filtered_data, x="property_type", y="price", color="property_type")
    fig.update_layout(title="Price Distribution by Property Type")
    st.plotly_chart(fig, use_container_width=True)
    st.write("**Price Distribution by Property Type**:")
    for property_type in filtered_data["property_type"].unique():
        subset = filtered_data[filtered_data["property_type"] == property_type]
        st.write(f"- **{property_type}**:")
        st.write(f"  - Mean Price: ${subset['price'].mean():.2f}")
        st.write(f"  - Median Price: ${subset['price'].median():.2f}")
        st.write(f"  - Min Price: ${subset['price'].min():.2f}")
        st.write(f"  - Max Price: ${subset['price'].max():.2f}")

    # Rating distribution by location
    fig = px.violin(filtered_data, x="suburb", y="review_scores_rating", color="suburb")
    fig.update_layout(title="Rating Distribution by Location")
    st.plotly_chart(fig, use_container_width=True)
    st.write("**Rating Distribution by Location**:")
    for suburb in filtered_data["suburb"].unique():
        subset = filtered_data[filtered_data["suburb"] == suburb]
        st.write(f"- **{suburb}**:")
        st.write(f"  - Mean Rating: {subset['review_scores_rating'].mean():.2f}")
        st.write(f"  - Median Rating: {subset['review_scores_rating'].median():.2f}")
        st.write(f"  - Min Rating: {subset['review_scores_rating'].min():.2f}")
        st.write(f"  - Max Rating: {subset['review_scores_rating'].max():.2f}")

else:
    st.write("No data available for the selected filters.")
