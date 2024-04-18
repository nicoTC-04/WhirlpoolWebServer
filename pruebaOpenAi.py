from flask import Flask, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text
from flask_cors import CORS
from openai import OpenAI


"""
CONFIG
"""
app = Flask(__name__)
CORS(app)

# config SQL
app.config['SQLALCHEMY_DATABASE_URI'] = "mssql+pyodbc://sqlserver:5'zfx~HU`;jD\"RY}@34.82.132.197/poolpoolgo?driver=ODBC+Driver+17+for+SQL+Server"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# config OpenAi
client = OpenAI(api_key="sk-proj-b0Csaf8jzxqYdSlkq1i6T3BlbkFJOTZQrE49FWVdPF0UpkEO")

# config endpoints
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
    descripcion = db.Column(db.Text, nullable=False)
    ruta_imagen = db.Column(db.Text)
    puntos = db.Column(db.Integer)
    fecha_generacion = db.Column(db.DateTime)
    id_empleado_genera = db.Column(db.Integer, db.ForeignKey('empleado.id_empleado'))
    fecha_resolucion = db.Column(db.DateTime)
    id_empleado_soluciona = db.Column(db.Integer, db.ForeignKey('empleado.id_empleado'))
    solucionado = db.Column(db.Boolean, default=False)
    id_ubicacion = db.Column(db.Integer, db.ForeignKey('ubicacion.id_ubicacion'))
    
class Ubicacion(db.Model):
    id_ubicacion = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100))
    latitud = db.Column(db.Float)
    longitud = db.Column(db.Float)
    descripcion = db.Column(db.String(100))
    imageName = db.Column(db.String(100))
    
    
    
    
    
@app.route('/reportesAll', methods=['GET'])
def get_reportes_all():
    # Subconsulta para obtener información de los empleados y ubicaciones
    subquery_empleados = db.session.query(
        Empleado.id_empleado.label("id_empleado"),
        Empleado.nombre.label("nombre_empleado")
    ).subquery()

    subquery_ubicaciones = db.session.query(
        Ubicacion.id_ubicacion.label("id_ubicacion"),
        Ubicacion.nombre.label("nombre_ubicacion")
    ).subquery()

    # Consulta principal que une la subconsulta con los reportes para obtener toda la información necesaria
    reportes_info = db.session.query(
        Reporte.id_reporte.label("id_reporte"),
        Reporte.descripcion,
        Reporte.fecha_generacion,
        Reporte.solucionado,
        subquery_empleados.c.nombre_empleado,
        subquery_ubicaciones.c.nombre_ubicacion
    ).join(subquery_empleados, Reporte.id_empleado_genera == subquery_empleados.c.id_empleado).join(subquery_ubicaciones, Reporte.id_ubicacion == subquery_ubicaciones.c.id_ubicacion).all()

    # Crear la lista de reportes en el formato deseado
    reportes_list = [{
        "id_reporte": reporte.id_reporte,
        "descripcion": reporte.descripcion,
        "fecha_generacion": reporte.fecha_generacion.strftime("%Y-%m-%d %H:%M:%S"),
        "solucionado": reporte.solucionado,
        "nombre_empleado": reporte.nombre_empleado,
        "nombre_ubicacion": reporte.nombre_ubicacion
    } for reporte in reportes_info]

    return jsonify(reportes_list)

@app.route('/resumenAi', methods=['GET'])
def generar_resumen():
    # Obtener toda la información de todos los reportes, incluyendo ubicaciones y usuarios
    reportes_info = get_reportes_all().json

    # Crear un texto que incluya descripciones de reportes, nombres de empleados, nombres de ubicaciones, etc.
    texto_reportes = ""
    for reporte in reportes_info:
        texto_reportes += f"Reporte ID: {reporte['id_reporte']}\n"
        texto_reportes += f"Descripción: {reporte['descripcion']}\n"
        texto_reportes += f"Fecha de generación: {reporte['fecha_generacion']}\n"
        texto_reportes += f"Solucionado: {reporte['solucionado']}\n"
        texto_reportes += f"Nombre de empleado: {reporte['nombre_empleado']}\n"
        texto_reportes += f"Nombre de ubicación: {reporte['nombre_ubicacion']}\n\n"

    # Enviar el texto al API de OpenAI para generar un resumen
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "Vas a hacer un resumen de los reportes que se generan de productos whirlpool en las tiendas dadas que no sea mayor a un parrafo. Quiero que me des informacion acumulada de las tiendas y me digas la severidad que tu le das a los reportes. No quiero que simplementes me dictes los problemas"},
                {"role": "user", "content": texto_reportes}
            ]
        )

        resumen = response.choices[0].message.content
        return jsonify({'resumen': resumen}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
    


if __name__ == '__main__':
    app.run(debug=True, port=5001, host='0.0.0.0')