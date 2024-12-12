from flask import Flask, render_template, request
import pandas as pd
from sqlalchemy import create_engine
import folium
from folium.plugins import HeatMap
import plotly.express as px
import plotly.graph_objects as go
import config

app = Flask(__name__)

def get_connection():
    db_url = f"mysql+pymysql://{config.DB_USER}:{config.DB_PASSWORD}@{config.DB_HOST}/{config.DB_NAME}"
    return create_engine(db_url)

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/accident_heatmap')
def accident_heatmap():
    
    start_date = request.args.get('start_date', '2014-01-01')
    end_date = request.args.get('end_date', '2015-01-01')
    engine = get_connection()
    
    query = f"""
        SELECT Latitude, Longitude, Date, Weather_Conditions, Light_Conditions, Accident_Severity
        FROM Accidents
        WHERE Latitude != 0 
        AND Longitude != 0
        AND Date BETWEEN '{start_date}' AND '{end_date}'

    """
    data = pd.read_sql(query, con=engine)
    engine.dispose()

    accident_map = folium.Map(location=config.MAP_DEFAULT_LOCATION, zoom_start=config.MAP_DEFAULT_ZOOM_START)

    
    
    heat_data = [
        [row['Latitude'], row['Longitude'], 4 - row['Accident_Severity']]
        for _, row in data.iterrows()
    ]
    HeatMap(heat_data, radius=10, blur=15, max_zoom=10).add_to(accident_map)

    accident_map.save('templates/accident_heatmap.html')
    return render_template('accident_heatmap.html', start_date=start_date, end_date=end_date)

@app.route('/casualties_map')
def casualties_map():
    
    start_date = request.args.get('start_date', '2014-01-01')
    end_date = request.args.get('end_date', '2015-01-01')

    engine = get_connection()
    query = f"""
        SELECT Latitude, Longitude, Number_of_Casualties, Date, Accident_Severity
        FROM Accidents
        WHERE Latitude != 0 
        AND Longitude != 0
        AND Date BETWEEN '{start_date}' AND '{end_date}'

    """
    data = pd.read_sql(query, con=engine)
    engine.dispose()

    casualties_map = folium.Map(location=[54.5260, -2.6189], zoom_start=3)

    
    
    
    heat_data = [
        [row['Latitude'], row['Longitude'], row['Number_of_Casualties']]
        for _, row in data.iterrows()
    ]
    HeatMap(heat_data, radius=10, blur=15, max_zoom=10).add_to(casualties_map)

    casualties_map.save('templates/casualties_map.html')
    return render_template('casualties_map.html', start_date=start_date, end_date=end_date)

@app.route('/casualties_chart')
def casualties_chart():
    
    
    engine = get_connection()
    data = pd.read_sql("""
        SELECT Accident_Severity, SUM(Number_of_Casualties) as total_casualties
        FROM Accidents
        GROUP BY Accident_Severity
    """, con=engine)
    engine.dispose()

    data['Severity_Desc'] = data['Accident_Severity'].map({1: 'Fatal', 2: 'Serious', 3: 'Slight'})

    fig = px.bar(
        data,
        x='Severity_Desc',
        y='total_casualties',
        title='Total Casualties by Accident Severity',
        labels={'Severity_Desc':'Severity', 'total_casualties':'Total Casualties'},
        color='Severity_Desc'
    )
    fig.update_layout(template=config.PLOTLY_TEMPLATE)
    graph_html = fig.to_html(full_html=False)

    return render_template('casualties_chart.html', graph_html=graph_html)

@app.route('/weather_chart')
def weather_chart():
    
    engine = get_connection()
    data = pd.read_sql("""
        SELECT Weather_Conditions, COUNT(*) as Count_Accidents
        FROM Accidents
        WHERE Weather_Conditions != ''
        GROUP BY Weather_Conditions
        ORDER BY Count_Accidents DESC
    """, con=engine)
    engine.dispose()

    fig = px.bar(
        data, 
        x='Weather_Conditions', 
        y='Count_Accidents',
        title='Accidents by Weather Condition',
        labels={'Weather_Conditions':'Weather', 'Count_Accidents':'Count'},
        color='Count_Accidents'
    )
    fig.update_layout(template='plotly_dark', xaxis_tickangle=45)
    graph_html = fig.to_html(full_html=False)

    return render_template('weather_chart.html', graph_html=graph_html)

@app.route('/accidents_by_weather')
def accidents_by_weather():
    engine = get_connection()
    data = pd.read_sql("SELECT * FROM v_accidents_by_weather", con=engine)
    engine.dispose()
    
    fig = px.bar(
        data,
        x='Weather_Conditions',
        y='Count_Accidents',
        title='Accidents by Weather Condition',
        labels={'Weather_Conditions':'Weather', 'Count_Accidents':'Accidents'},
        color='Count_Accidents'
    )
    fig.update_layout(template='plotly_dark', xaxis_tickangle=45)
    graph_html = fig.to_html(full_html=False)
    
    return render_template('chart.html', graph_html=graph_html, title="Accidents by Weather")

@app.route('/casualties_by_sex')
def casualties_by_sex():
    engine = get_connection()
    data = pd.read_sql("SELECT * FROM v_casualties_by_sex", con=engine)
    engine.dispose()
    
    fig = px.pie(
        data,
        names='Sex_of_Casualty',
        values='Count_Casualties',
        title='Casualties by Sex',
        color='Sex_of_Casualty'
    )
    fig.update_layout(template='plotly_dark')
    graph_html = fig.to_html(full_html=False)
    
    return render_template('chart.html', graph_html=graph_html, title="Casualties by Sex")

@app.route('/vehicle_types')
def vehicle_types():
    engine = get_connection()
    data = pd.read_sql("SELECT * FROM v_vehicle_types", con=engine)
    engine.dispose()
    
    fig = px.bar(
        data,
        x='Vehicle_Type',
        y='Count_Vehicles',
        title='Count of Vehicles by Type Involved in Accidents',
        labels={'Vehicle_Type':'Vehicle Type', 'Count_Vehicles':'Count'},
        color='Count_Vehicles'
    )
    fig.update_layout(template='plotly_dark', xaxis_tickangle=45)
    graph_html = fig.to_html(full_html=False)
    
    return render_template('chart.html', graph_html=graph_html, title="Vehicle Types Involved")

@app.route('/accident_severity_by_month')
def accident_severity_by_month():
    engine = get_connection()
    data = pd.read_sql("SELECT * FROM v_accident_severity_by_month", con=engine)
    engine.dispose()
    
    
    severity_map = {1:'Fatal', 2:'Serious', 3:'Slight'}
    data['Severity_Desc'] = data['Accident_Severity'].map(severity_map)
    
    fig = px.bar(
        data,
        x='Accident_Month',
        y='Count_Accidents',
        color='Severity_Desc',
        barmode='group',
        title='Accident Severity by Month',
        labels={'Accident_Month':'Month', 'Count_Accidents':'Accidents'}
    )
    fig.update_layout(template='plotly_dark')
    graph_html = fig.to_html(full_html=False)
    
    return render_template('chart.html', graph_html=graph_html, title="Accident Severity by Month")

@app.route('/avg_casualties')
def avg_casualties():
    engine = get_connection()
    data = pd.read_sql("SELECT * FROM v_avg_casualties_per_accident", con=engine)
    engine.dispose()

    avg_value = data['Avg_Casualties'].iloc[0]

    
    fig = go.Figure(go.Indicator(
        mode="number",
        value=avg_value,
        title={'text': "Average Casualties per Accident"}
    ))

    fig.update_layout(template='plotly_dark')

    graph_html = fig.to_html(full_html=False)
    return render_template('chart.html', graph_html=graph_html, title="Average Casualties per Accident")


if __name__ == '__main__':
    app.run(debug=True)
