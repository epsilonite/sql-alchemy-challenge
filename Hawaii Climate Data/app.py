# Import the dependencies.
import numpy as np
import datetime as dt
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
meas = Base.classes.measurement
stns = Base.classes.station
# Create our session (link) from Python to the DB
# session = Session(engine)

#################################################
# Flask Setup
#################################################
app = Flask(__name__)

#################################################
# Flask Routes
#################################################
@app.route("/")
def welcome():
    """List all available api routes."""
    return (
        f"<h1>Hawaii Climate Data Portal</h1>"
        f"<h2>Available Routes:</h2>"
        f"<h3>/api/v1/precipitation</br>"
        f"/api/v1/stations</br>"
        f"/api/v1/temperatures</br>"
        f"/api/v1/temperatures/2010-01-01</br>"
        f"/api/v1/temperatures/2010-01-01/2017-08-23</br>"
        f"/api/v1/temperatures/station/USC00519281</h3>"
        f"Available Date Range: 2010-01-01 to 2017-08-23</br>"
        f"Dates must be in ISO format YYYY-MM-DD</br>"
        f"Available Stations: check  /api/v1/stations"
    )

@app.route("/api/v1/precipitation")
def precipitation():
    """Returns json with the date as the key and the value as the precipitation"""
    """Only returns the jsonified precipitation data for the last year in the database"""
    # Create our session (link) from Python to the DB
    session = Session(engine)
    results = session.query(meas.date,func.max(meas.prcp)).group_by(meas.date).order_by(meas.date).filter(meas.date>"2016-08-22").all()
    session.close()
    # Create a dictionary from the row data
    year_prcp = {}
    for date, prcp in results:
        year_prcp[date]=prcp
    return jsonify(year_prcp)

@app.route("/api/v1/stations")
def stations():
    """Returns jsonified data of all of the stations in the database"""
    # Create our session (link) from Python to the DB
    session = Session(engine)
    results = session.query(stns.station,stns.name).all()
    session.close()
    # Create a dictionary from the row data
    all_stns = {}
    for station, name in results:
        all_stns[station]=name
    return jsonify(all_stns)

@app.route("/api/v1/temperatures")
def temperatures():
    """Returns jsonified data for the most active station (USC00519281)"""
    """Only returns the jsonified data for the last year of data"""
    # Create our session (link) from Python to the DB
    session = Session(engine)
    results = session.query(meas.date,meas.tobs).order_by(meas.date).filter(meas.date>"2016-08-22").filter(meas.station=='USC00519281').all()
    session.close()
    # Create a dictionary from the row data
    year_temp = {}
    for date, tobs in results:
        year_temp[date]=tobs
    return jsonify(year_temp)

@app.route("/api/v1/temperatures/station/<station>")
def temperatures_stn(station):
    """Returns jsonified data for given station"""
    """Only returns the jsonified data for the last year of data"""
    # Create our session (link) from Python to the DB
    session = Session(engine)
    if station in [session.query(meas.station).distinct().all()[i][0] for i in range(0,session.query(meas.station).distinct().count())]:
        results = session.query(meas.date,meas.tobs).order_by(meas.date).filter(meas.date>"2016-08-22").filter(meas.station==station).all()
        session.close()
    else:
        return jsonify({"error": f"Station: {station} is not found",
                        'stations': 'USC00519281, USC00519397, USC00513117, USC00519523, USC00516128, USC00514830, USC00511918, USC00517948, USC00518838'}), 404
    # Create a dictionary from the row data
    year_temp = {}
    for date, tobs in results:
        year_temp[date]=tobs
    return jsonify(year_temp)

@app.route("/api/v1/temperatures/<start_date>")
def temperatures1(start_date):
    """Accepts the start date as a parameter from the URL"""
    """Returns the min, max, and average temperatures calculated from the given start date to the end of the dataset"""
    try:
        start = dt.date.fromisoformat(start_date)-dt.timedelta(days=1)
        if start>=dt.date(2009,12,31) and start<dt.date(2017,8,23):
            # Create our session (link) from Python to the DB
            session = Session(engine)
            results = session.query(func.min(meas.tobs),func.max(meas.tobs),func.avg(meas.tobs)).filter(meas.date>start).one()
            session.close()
            # Create a dictionary from results
            return jsonify({'Min':results[0],'Max':results[1],'Average':round(results[2],1)})
        return jsonify({"error": f"Date input: {start_date} is not in the available date range 2010-01-01 to 2017-08-23"}), 404
    except ValueError:
        return jsonify({"error": f"Date input: {start_date} is not a valid date in isoformat YYYY-MM-DD"}), 404

@app.route("/api/v1/temperatures/<start_date>/<end_date>")
def temperatures2(start_date,end_date):
    try:
        start = dt.date.fromisoformat(start_date)-dt.timedelta(days=1)
        if start<dt.date(2009,12,31) or start>=dt.date(2017,8,23):
            return jsonify({"error": f"Date input: {start_date} is not in the available date range 2010-01-01 to 2017-08-23"}), 404
        try:
            end = dt.date.fromisoformat(end_date)+dt.timedelta(days=1)
            if end<=start: 
                return jsonify({"error": f"Date input: {end_date} is before start date"}), 404
            if end>dt.date(2017,8,24): 
                return jsonify({"error": f"Date input: {end_date} is not in the available date range 2010-01-01 to 2017-08-23"}), 404
            # Create our session (link) from Python to the DB
            session = Session(engine)
            results = session.query(func.min(meas.tobs),func.max(meas.tobs),func.avg(meas.tobs)).filter(meas.date>start).filter(meas.date<end).one()
            session.close()
            # Create a dictionary from results
            return jsonify({'Min':results[0],'Max':results[1],'Average':round(results[2],1)})
        except ValueError:
            return jsonify({"error": f"Date input: {end_date} is not a valid date in isoformat YYYY-MM-DD"}), 404
    except ValueError:
        return jsonify({"error": f"Date input: {start_date} is not a valid date in isoformat YYYY-MM-DD"}), 404

if __name__ == '__main__':
    app.run(debug=True)