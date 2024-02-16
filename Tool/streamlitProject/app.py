# Launch the app using the following command (using the terminal):
# python -m streamlit run app.py
import base64

import streamlit as st
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from statsmodels.tsa.seasonal import seasonal_decompose
import pickle

# Function to decompose time series and display sub-time series
def decompose_and_display(data, selected_column):
    # Set 'time' as index for seasonal decomposition
    data.set_index('Discrete_Time', inplace=True)

    # Decompose time series into trend, seasonal, and residual components
    result = seasonal_decompose(data[selected_column], model='additive', period=10)  # Assuming seasonality period is 12

    # Create a new DataFrame with decomposed components
    decomposed_data = pd.DataFrame({
        'Original': data[selected_column],
        'Trend': result.trend,
        'Residual': result.resid
    })

    # Plot each sub-time series
    fig = go.Figure()

    for column in decomposed_data.columns:
        fig.add_trace(go.Scatter(x=decomposed_data.index, y=decomposed_data[column], mode='lines', name=column))

    # Set layout options
    fig.update_layout(showlegend=True)

    st.plotly_chart(fig, use_container_width=True)

# Function to load and visualize time series data with Plotly
def visualize_time_series(data, selected_column):
    # Create a scatter plot for the entire time series
    fig = go.Figure()

    # Add a line trace for the entire time series
    fig.add_trace(go.Scatter(x=data['Discrete_Time'], y=data[selected_column], mode='lines', name='Time Series'))

    # Identify points lower than 0.85 and higher than 1.05
    below_threshold = data[data[selected_column] < 0.83]
    above_threshold = data[data[selected_column] > 1.075]

    # Add scatter traces for points below 0.85 and above 1.05
    fig.add_trace(go.Scatter(x=below_threshold['Discrete_Time'], y=below_threshold[selected_column], mode='markers', marker=dict(color='red'), name='Below 0.83'))
    fig.add_trace(go.Scatter(x=above_threshold['Discrete_Time'], y=above_threshold[selected_column], mode='markers', marker=dict(color='red'), name='Above 1.075'))

    # Set layout options
    fig.update_layout(width=800, showlegend=True)
    
    st.subheader(f"Time Series Visualization for {selected_column}:")
    st.plotly_chart(fig, use_container_width=True)

# Set page configuration to make the interface wider
st.set_page_config(page_title="T-Sentry", page_icon="📈", layout="wide")


LOGO_IMAGE = "images/logo_sentry_transparent.png"
LOGO_TITLE = "T-Sentry"
UNICAM_LOGO = "images/logo_unicam.png"
SCHNELL_LOGO = "images/logo_Schnell.png"

st.markdown(
    """
    <style>
    .headerContainer {
        display: flex;
        justify-content: space-between;
    }
    .logoContainer {
        display: flex;
        align-items: center;
    }
    .companiesContainer {
        display: flex;
        flex-direction: column;
        align-items: center; /* Center items horizontally */
        text-align: center; /* Center text horizontally */
    }
    .title-logo-text {
        font-weight: 700 !important;
        font-size: 70px !important;
        padding-top: 0px;
        margin-bottom: 0px;
    }
    .title-logo-img {
        width: 150px;
        height: 150px;
    }
    .company-logo-img {
        max-height: 100px; 
        width: auto;
        margin-bottom: 10px; 
    }
    .collaboration-text {
        font-size: 25px; 
        margin-bottom: 5px; 
        text-align: center; 
    }
    </style>
    """,
    unsafe_allow_html=True
)

st.markdown(
    f"""
    <div class="headerContainer">
        <div class="logoContainer">
            <img class="title-logo-img" src="data:image/png;base64,{base64.b64encode(open(LOGO_IMAGE, "rb").read()).decode()}">
            <p class="title-logo-text">{LOGO_TITLE}</p>
        </div>
        <div class="companiesContainer">
            <p class="collaboration-text">In collaboration with:</p>
            <div>
                <img class="company-logo-img" src="data:image/png;base64,{base64.b64encode(open(UNICAM_LOGO, "rb").read()).decode()}">
                <img class="company-logo-img" src="data:image/png;base64,{base64.b64encode(open(SCHNELL_LOGO, "rb").read()).decode()}">
            </div>
        </div>
    </div>
    """,
    unsafe_allow_html=True
)

# File upload
uploaded_file = st.file_uploader("Upload a CSV file", type=["csv"])

# Divide the space into two columns
col1, col2 = st.columns(2)

if uploaded_file is not None:
    # Load data
    df = pd.read_csv(uploaded_file, sep=";")
    dff = df.copy()

    # Value columns of the dataframe to be used
    value_columns = ['Board1Acc1', 'Board1Acc2', 'Board1Acc3',
                   'Board2Acc1', 'Board2Acc2', 'Board2Acc3',
                   'Board3Acc1', 'Board3Acc2', 'Board3Acc3']

    # Visualize time series
    with col1:
        st.subheader("Time Series Visualization:")
        # Allow user to choose the column to visualize
        selected_column = st.selectbox("Select a column to visualize", value_columns)

        # Visualize time series
        visualize_time_series(dff, selected_column)

# Classify data
if uploaded_file is not None:
    # On the second column add the classifier and the button to classify the time series
    with col2:
        st.subheader("Classify Time Series:")
        # Load the model
        with open('../../saved_models/pruned_classifier_model.pkl', 'rb') as model_file:
            model = pickle.load(model_file)
            print("Model loaded successfully!")
        
        # Add a button to classify time series as anomaly or not
        if st.button("Classify Time Series"):
            # Load and apply PCA to the time series
            with open('../../saved_models/pca_transformer.pkl', 'rb') as pca_file:
                pca = pickle.load(pca_file)
                print("PCA loaded successfully!")
                principalComponents = pca.fit_transform(dff[['Acquisition_Number','Discrete_Time'] + value_columns])
                principalDf = pd.DataFrame(data = principalComponents, columns = ['principal_component_1', 'principal_component_2'])
            
            st.subheader("Time Series Classification:")

            # Predict anomalies using principal components 1 and 2
            predictions = model.predict(principalDf)
            
            # Calculate the percentage of anomalies
            percentage_anomalies = (predictions == "guasto").sum() / len(predictions) * 100

            # Display pie chart
            fig_pie = go.Figure(data=[go.Pie(labels=['Anomalies', 'Normal'],
                                             values=[percentage_anomalies, 100 - percentage_anomalies],
                                             hole=0.3,
                                             marker_colors=['#FF6347', '#4CAF50'])])

            fig_pie.update_layout(width=300, height=300)

            st.plotly_chart(fig_pie)
        

        # Displayed statistics below the "prediction section"
        st.subheader("Time Series Statistics:")
        st.markdown(f"**Selected Column:** {selected_column}")
        st.markdown(f"**Mean:** {dff[selected_column].mean()}")
        st.markdown(f"**Variance:** {dff[selected_column].var()}")
        st.markdown(f"**Minimum:** {dff[selected_column].min()}")
        st.markdown(f"**Maximum:** {dff[selected_column].max()}")
        # Add more statistics as needed

# Decompose time series into trend and residual components
if uploaded_file is not None:
    st.subheader(f"Decomposed Time Series for {selected_column}:")
    decompose_and_display(dff, selected_column)


# TODO
# 1. Load the model correctly
# 2. Adjust the thresholds for the points classified as anomalies
# 3. Display statistics on the main page in a styled container
