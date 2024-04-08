from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func, extract, text
from datetime import datetime

"""
CONFIG
"""
app = Flask(__name__)

# config SQL
app.config['SQLALCHEMY_DATABASE_URI'] = "mssql+pyodbc://sqlserver:5'zfx~HU`;jD\"RY}@34.82.132.197/poolpoolgo?driver=ODBC+Driver+17+for+SQL+Server"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

@app.route('/')
def hello_world():
    return 'Hello, World!'

@app.route('/test_db_connection')
def test_db_connection():
    try:
        result = db.session.execute(text('SELECT 1'))
        return 'Database connection established successfully.'
    except Exception as e:
        return f'Failed to establish database connection: {e}'


"""
MODELOS
"""
class Empleado(db.Model):
    id_empleado = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100))
    correo = db.Column(db.String(100))
    rol_id = db.Column(db.Integer, db.ForeignKey('rol.id_rol'))

class Reporte(db.Model):
    id_reporte = db.Column(db.Integer, primary_key=True)
    puntos = db.Column(db.Integer)
    fecha_generacion = db.Column(db.DateTime)
    id_empleado_genera = db.Column(db.Integer, db.ForeignKey('empleado.id_empleado'))



"""
EMPIEZAN ENDPOINTS
"""
### Endpoint que recibe un correo y devuelve la info del empleado
@app.route('/get_user_info', methods=['GET'])
def get_user_info():
    correo = request.args.get('correo')
    
    if correo:
        empleado = Empleado.query.filter_by(correo=correo).first()
        if not empleado:
            return jsonify({'message': 'Employee not found'}), 404

        current_month = datetime.now().month
        current_year = datetime.now().year

        # query que obtiene la suma de puntos y el conteo de reportes del empleado en el mes actual
        report_data = db.session.query(
            func.sum(Reporte.puntos),
            func.count(Reporte.id_reporte)
        ).filter(
            extract('month', Reporte.fecha_generacion) == current_month,
            extract('year', Reporte.fecha_generacion) == current_year,
            Reporte.id_empleado_genera == empleado.id_empleado
        ).first()

        # si no se encontraron reportes son 0
        sum_points, count_reports = report_data if report_data else (0, 0)

        # hacer response
        user_info = {
            'id_empleado': empleado.id_empleado,
            'nombre': empleado.nombre,
            'correo': empleado.correo,
            'rol_id': empleado.rol_id,
            'sum_points': sum_points or 0,
            'count_reports': count_reports or 0
        }

        return jsonify(user_info)
    else:
        return jsonify({'message': 'Email parameter is missing'}), 400


if __name__ == '__main__':
    app.run(debug=True, port=5001, host='0.0.0.0')