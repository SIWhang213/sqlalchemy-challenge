# Import the dependencies.
from matplotlib import style
style.use('fivethirtyeight')
import matplotlib.pyplot as plt

import numpy as np
import pandas as pd
import datetime as dt

# Python SQL toolkit and Object Relational Mapper
import sqlalchemy
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, func

from flask import Flask, jsonify

#################################################
# Database Setup
#################################################
engine = create_engine("sqlite:///Resources/hawaii.sqlite")

# reflect an existing database into a new model
Base = automap_base()
# reflect the tables
Base.prepare(autoload_with=engine)

# Save references to each table
Measurement = Base.classes.measurement
Station = Base.classes.station

# Create our session (link) from Python to the DB
session = Session(engine)

#################################################
# Flask Setup
#################################################
app = Flask(__name__)


#################################################
# Flask Routes
#################################################
@app.route("/")
def home():
    """List all available api routes."""
    return (
        "Welcome to the Climate API!<br/><br/>"
        "Available Routes:<br/>"
        "/api/v1.0/precipitation<br/>"
        "/api/v1.0/stations<br/>"
        "/api/v1.0/tobs<br/>"
        "/api/v1.0/<start><br/>"
        "/api/v1.0/<start>/<end><br/>"
    ) 

@app.route("/api/v1.0/precipitation")
def precipitation():
    # Convert the query results from your precipitation analysis (i.e. retrieve only the last 12 months of data)
    #  to a dictionary using date as the key and prcp as the value.
    most_recent_date = session.query(Measurement.date).order_by(Measurement.date.desc()).first()
    most_recent_time = dt.datetime.strptime(most_recent_date[0], '%Y-%m-%d')
    one_year_ago = most_recent_time - dt.timedelta(days=366)

    # Perform a query to retrieve the last 12 months of precipitation data
    precipitation_data = session.query(Measurement.date, Measurement.prcp).\
        filter(Measurement.date >= one_year_ago).\
        filter(Measurement.prcp.isnot(None)).\
        order_by(Measurement.date).all()

    # Create a dictionary with date as the key and prcp as the value
    precipitation_dict = {}
    for date, prcp in precipitation_data:
        precipitation_dict[date] = prcp
     
    # Close Session
    session.close()
    
    #Return the JSON representation of your dictionary.
    return jsonify(precipitation_dict)
    
@app.route("/api/v1.0/stations")
def stations():
    # Query the database to retrieve the list of stations
    stations_data = session.query(Station.station, Station.name).all()

    # Create a list of dictionaries with station information
    station_list = []
    for station, name in stations_data:
        station_dict = {
            "station": station,
            "name": name
        }
        station_list.append(station_dict)
    # Close Session
    session.close()

    # Return the list of stations as JSON
    return jsonify(station_list)


@app.route("/api/v1.0/tobs")
def temperature():
    # Find the most recent date in the data set.
    most_recent_date = session.query(Measurement.date).order_by(Measurement.date.desc()).first()
    most_recent_time = dt.datetime.strptime(most_recent_date[0], '%Y-%m-%d')
    one_year_ago = most_recent_time - dt.timedelta(days=366)

    
    active_stations = session.query(Measurement.station, func.count(Measurement.station)).\
        group_by(Measurement.station).\
        order_by(func.count(Measurement.station).desc()).all()
    
    most_active_station_id = active_stations[0][0]

    # Query the dates and temperature observations of the most-active station for the previous year of data.
    temperature_data = session.query(Measurement.date, Measurement.tobs).\
        filter(Measurement.station == most_active_station_id).\
        filter(Measurement.date >= one_year_ago).all()
    
    # Create a list of temperature observations as JSON objects
    temperature_list = [{"date": date, "temperature": tobs} for date, tobs in temperature_data]

     # Close Session
    session.close()
    
    #Return a JSON list of temperature observations for the previous year.
    return jsonify(temperature_list)

@app.route("/api/v1.0/<start>")
@app.route("/api/v1.0/<start>/<end>")
def temperature_by_date_range(start, end=None):
    # Convert the start date parameter to a datetime object
    start_date = dt.datetime.strptime(start, "%Y-%m-%d")

    if end is None:
        # Handle the case where only the start date is provided
        # Query TMIN, TAVG, and TMAX for all dates greater than or equal to the start date
        temperature_data = session.query(
            func.min(Measurement.tobs).label("TMIN"),
            func.avg(Measurement.tobs).label("TAVG"),
            func.max(Measurement.tobs).label("TMAX")
        ).filter(Measurement.date >= start_date).all()
    else:
        # Convert the end date parameter to a datetime object
        end_date = dt.datetime.strptime(end, "%Y-%m-%d")

        # Handle the case where both start and end dates are provided
        # Query TMIN, TAVG, and TMAX for dates within the specified range (inclusive)
        temperature_data = session.query(
            func.min(Measurement.tobs).label("TMIN"),
            func.avg(Measurement.tobs).label("TAVG"),
            func.max(Measurement.tobs).label("TMAX")
        ).filter(Measurement.date >= start_date, Measurement.date <= end_date).all()

    # Create a JSON response
    temperature_list = [{
        "TMIN": result.TMIN,
        "TAVG": result.TAVG,
        "TMAX": result.TMAX
    } for result in temperature_data]

    # Close Session
    session.close()

    return jsonify(temperature_list)


if __name__ == '__main__':
    app.run(debug=True)