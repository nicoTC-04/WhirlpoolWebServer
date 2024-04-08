from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from flask_uploads import UploadSet, configure_uploads, IMAGES
from sqlalchemy import func, extract, text
from datetime import datetime
from werkzeug.utils import secure_filename

"""
CONFIG
"""
app = Flask(__name__)

# config SQL
app.config['SQLALCHEMY_DATABASE_URI'] = "mssql+pyodbc://sqlserver:5'zfx~HU`;jD\"RY}@34.82.132.197/poolpoolgo?driver=ODBC+Driver+17+for+SQL+Server"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOADED_PHOTOS_DEST'] = './imagenes'
photos = UploadSet('photos', IMAGES)
configure_uploads(app, photos)

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
    descripcion = db.Column(db.Text, nullable=False)
    ruta_imagen = db.Column(db.Text)
    puntos = db.Column(db.Integer)
    fecha_generacion = db.Column(db.DateTime)
    id_empleado_genera = db.Column(db.Integer, db.ForeignKey('empleado.id_empleado'))
    solucionado = db.Column(db.Boolean, default=False)
    id_ubicacion = db.Column(db.Integer, db.ForeignKey('ubicacion.id_ubicacion'))
    
class Ubicacion(db.Model):
    id_ubicacion = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100))
    latitud = db.Column(db.Float)
    longitud = db.Column(db.Float)
    descripcion = db.Column(db.String(100))



"""
EMPIEZAN ENDPOINTS
"""
### Endpoint que recibe un correo y devuelve la info del empleado
@app.route('/get_user_info', methods=['GET'])
def get_user_info():
    correo = request.headers.get('correo')
    
    if correo:
        empleado = Empleado.query.filter_by(correo=correo).first()
        if not empleado:
            return jsonify({'message': 'No se encontro el empleado'}), 404

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
        
        locations = Ubicacion.query.all()
        all_locations = [
            {'id_ubicacion': loc.id_ubicacion, 'nombre': loc.nombre, 'latitud': loc.latitud, 'longitud': loc.longitud, 'descripcion': loc.descripcion}
            for loc in locations
        ]

        # hacer response
        user_info = {
            'id_empleado': empleado.id_empleado,
            'nombre': empleado.nombre,
            'correo': empleado.correo,
            'rol_id': empleado.rol_id,
            'sum_points': sum_points or 0,
            'count_reports': count_reports or 0,
            'ubicaciones': all_locations
        }

        return jsonify(user_info)
    else:
        return jsonify({'message': 'Email parameter is missing'}), 400
    

### Endpoint que recibe un reporte y lo agrega a la base de datos
@app.route('/reporte', methods=['POST'])
def agregar_reporte():
    descripcion = request.form['descripcion']
    id_empleado_genera = request.form['id_empleado_genera']
    # Suponiendo que el cliente envía la ID de ubicación y producto, si es aplicable
    id_ubicacion = request.form.get('id_ubicacion', None)

    if 'foto' in request.files:
        foto = request.files['foto']
        filename = secure_filename(foto.filename)
        foto.save(os.path.join(app.config['UPLOADED_PHOTOS_DEST'], filename))
        ruta_imagen = os.path.join(app.config['UPLOADED_PHOTOS_DEST'], filename)
    else:
        ruta_imagen = None

    nuevo_reporte = Reporte(
        descripcion=descripcion,
        ruta_imagen=ruta_imagen,
        id_empleado_genera=id_empleado_genera,
        id_ubicacion=id_ubicacion,
    )

    db.session.add(nuevo_reporte)
    db.session.commit()

    return jsonify({'mensaje': 'Reporte agregado exitosamente'}), 201



if __name__ == '__main__':
    app.run(debug=True, port=5001, host='0.0.0.0')