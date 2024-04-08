from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text

app = Flask(__name__)

# config SQL
app.config['SQLALCHEMY_DATABASE_URI'] = "mssql+pyodbc://sqlserver:5'zfx~HU`;jD\"RY}@34.82.132.197/poolpoolgo?driver=ODBC+Driver+17+for+SQL+Server"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)



@app.route('/test_db_connection')
def test_db_connection():
    try:
        result = db.session.execute(text('SELECT 1'))
        
        return 'Database connection established successfully.'
    
    except Exception as e:
        return f'Failed to establish database connection: {e}'



@app.route('/')
def hello_world():
    return 'Hello, World!'

@app.route('/prueba')
def prueba():
    return 'Prueba'

if __name__ == '__main__':
    app.run(debug=True, port=5001, host='0.0.0.0')