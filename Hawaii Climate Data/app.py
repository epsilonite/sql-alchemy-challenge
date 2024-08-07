# Import the dependencies.
import datetime as dt
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
msr = Base.classes.measurement
stn = Base.classes.station
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
        f"<h3>/api/v1.0/precipitation</br>"
        f"/api/v1.0/stations</br>"
        f"/api/v1.0/temperatures</br>"
        f"/api/v1.0/temperatures/USC00519281</br>"
        f"/api/v1.0/2010-01-01</br>"
        f"/api/v1.0/2010-01-01/2017-08-23</h3>"
        f"Available Date Range: 2010-01-01 to 2017-08-23</br>"
        f"Dates must be in ISO format YYYY-MM-DD</br>"
        f"Available Stations: check  /api/v1/stations"
    )

@app.route("/api/v1.0/precipitation")
def precipitation():
    """Returns json with the date as the key and the value as the precipitation"""
    """Only returns the jsonified precipitation data for the last year in the database"""
    # Create our session (link) from Python to the DB
    session = Session(engine)
    # Result returns maximum recorded rainfall for each day from 2016-08-23 to 2017-08-23
    # (derived from data exploration modeled in jupyter notebook)
    result = session.query(msr.date,msr.prcp).order_by(msr.date).filter(msr.date>"2016-08-22").all()
    session.close()
    # Create a dictionary from the row data
    dict = {}
    for date, prcp in result:
        dict[date]=prcp
    return jsonify(dict)

@app.route("/api/v1.0/stations")
def stations():
    """Returns jsonified data of all of the stations in the database"""
    # Create our session (link) from Python to the DB
    session = Session(engine)
    result = session.query(stn.station,stn.name,stn.latitude,stn.longitude,stn.elevation).all()
    session.close()
    # Create a dictionary from the row data
    dict = {}
    for station, name, latitude, longitude, elevation in result:
        dict[station]={'name':name, 'latitude':latitude, 'longitude':longitude, 'elevation':elevation}
    return jsonify(dict)

@app.route("/api/v1.0/temperatures")
def temperatures():
    """Returns jsonified data for the most active station (USC00519281)"""
    """Only returns the jsonified data for the last year of data"""
    # Create our session (link) from Python to the DB
    session = Session(engine)
    # Result returns temperature data for USC00519281 for each day from 2016-08-23 to 2017-08-23
    result = session.query(msr.date,msr.tobs).order_by(msr.date).filter(msr.date>"2016-08-22").filter(msr.station=='USC00519281').all()
    session.close()
    # Create a dictionary from the row data
    dict = {}
    for date, tobs in result:
        dict[date]=tobs
    return jsonify(dict)

@app.route("/api/v1.0/temperatures/<station>")
def temperatures_stn(station):
    """Returns jsonified data for given station"""
    """Only returns the jsonified data for the last year of data"""
    # Create our session (link) from Python to the DB
    session = Session(engine)
    if station in [session.query(msr.station).distinct().all()[i][0] for i in range(0,session.query(msr.station).distinct().count())]:
        # Result returns temperature data for given station for each day from 2016-08-23 to 2017-08-23
        result = session.query(msr.date,msr.tobs).order_by(msr.date).filter(msr.date>"2016-08-22").filter(msr.station==station).all()
        session.close()
        # Create a dictionary from the row data
        dict = {}
        for date, tobs in result:
            dict[date]=tobs
        return jsonify(dict)
    # Error message
    session.close()
    return jsonify({"error": f"Station: {station} is not found",
                    'stations': 'USC00519281, USC00519397, USC00513117, USC00519523, USC00516128, USC00514830, USC00511918, USC00517948, USC00518838'}), 404

@app.route("/api/v1.0/<start_date>")
def temperatures1(start_date):
    """Accepts the start date as a parameter from the URL"""
    """Returns the min, max, and average temperatures calculated from the given start date to the end of the dataset"""
    try:
        start = dt.date.fromisoformat(start_date)-dt.timedelta(days=1)
        if start>dt.date(2009,12,30) and start<dt.date(2017,8,23):
            # Create our session (link) from Python to the DB
            session = Session(engine)
            # Result returns min,max,avg of temperatures from start date to 2017-08-23
            result = session.query(func.min(msr.tobs),func.max(msr.tobs),func.avg(msr.tobs)).filter(msr.date>start).one()
            session.close()
            # Create a dictionary from result
            return jsonify({'Min':result[0],'Max':result[1],'Average':round(result[2],1)})
        # Error message for date out of range
        return jsonify({"error": f"Date input: {start_date} is not in the available date range 2010-01-01 to 2017-08-23"}), 404
    # Error message for invalid date format
    except ValueError:
        return jsonify({"error": f"Date input: {start_date} is not a valid date in isoformat YYYY-MM-DD"}), 404

@app.route("/api/v1.0/<start_date>/<end_date>")
def temperatures2(start_date,end_date):
    try:
        # Test start date for ISO format
        start = dt.date.fromisoformat(start_date)-dt.timedelta(days=1)
        # Error message for start date out of range
        if start<dt.date(2009,12,31) or start>dt.date(2017,8,22):
            return jsonify({"error": f"Date input: start date: {start_date} is before the available date range 2010-01-01 to 2017-08-23"}), 404
        try:
            #Test end date for ISO format
            end = dt.date.fromisoformat(end_date)+dt.timedelta(days=1)
            if end<start+dt.timedelta(days=2):
                # Error message for end date before start date
                return jsonify({"error": f"Date input: end date: {end_date} is before start date: {start_date}"}), 404
            if end>dt.date(2017,8,24):
                # Error message for end date out of range
                return jsonify({"error": f"Date input: end date: {end_date} is after the available date range 2010-01-01 to 2017-08-23"}), 404
            # Create our session (link) from Python to the DB
            session = Session(engine)
            # Result returns min,max,avg of temperatures from start date to end date
            result = session.query(func.min(msr.tobs),func.max(msr.tobs),func.avg(msr.tobs)).filter(msr.date>start).filter(msr.date<end).one()
            session.close()
            # Create a dictionary from result
            return jsonify({'Min':result[0],'Max':result[1],'Average':round(result[2],1)})
        # Error message for invalid end date format
        except ValueError:
            return jsonify({"error": f"Date input: end date: {end_date} is not a valid date in isoformat YYYY-MM-DD"}), 404
    # Error message for invalid start date format
    except ValueError:
        return jsonify({"error": f"Date input: start date: {start_date} is not a valid date in isoformat YYYY-MM-DD"}), 404

if __name__ == '__main__':
    app.run(debug=True)