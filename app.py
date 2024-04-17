from flask import Flask, jsonify, request, send_file
from flask_sqlalchemy import SQLAlchemy
from flask_uploads import UploadSet, configure_uploads, IMAGES
from sqlalchemy import func, extract, text
from datetime import datetime
from werkzeug.utils import secure_filename
from flask_cors import CORS
import os
import magic

"""
CONFIG
"""
app = Flask(__name__)
CORS(app)

# config SQL
app.config['SQLALCHEMY_DATABASE_URI'] = "mssql+pyodbc://sqlserver:5'zfx~HU`;jD\"RY}@34.82.132.197/poolpoolgo?driver=ODBC+Driver+17+for+SQL+Server"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOADED_PHOTOS_DEST'] = './../imagenes'
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
            {'id_ubicacion': loc.id_ubicacion, 'nombre': loc.nombre, 'latitud': loc.latitud, 'longitud': loc.longitud, 'descripcion': loc.descripcion, 'imageName': loc.imageName}
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
    

## endpoint que regresa todos los usuarios
@app.route('/users', methods=['GET'])
def get_users():
    # Subconsulta para obtener puntos y conteo de reportes por empleado
    subquery = db.session.query(
        Reporte.id_empleado_genera.label("id_empleado"),
        func.coalesce(func.sum(Reporte.puntos), 0).label("points"),
        func.count(Reporte.id_reporte).label("reports")
    ).group_by(Reporte.id_empleado_genera).subquery()

    # Consulta principal que une la subconsulta con los empleados para obtener toda la información necesaria
    users_info = db.session.query(
        Empleado.id_empleado.label("uid"),
        Empleado.nombre.label("fullName"),
        Empleado.correo.label("email"),
        Empleado.rol_id,
        subquery.c.points,
        subquery.c.reports
    ).outerjoin(subquery, Empleado.id_empleado == subquery.c.id_empleado).all()

    # Crear la lista de usuarios en el formato deseado
    users_list = [{
        "uid": user.uid,
        "firstName": user.fullName.split(' ', 1)[0],
        "lastName": user.fullName.split(' ', 1)[1] if len(user.fullName.split(' ', 1)) > 1 else "",
        "email": user.email,
        "rol_id": user.rol_id,
        "points": user.points if user.points is not None else 0,
        "reports": user.reports if user.reports is not None else 0
    } for user in users_info]

    return jsonify(users_list)


## endpoint que regresa todos los reportes pendientes (solo regresa nombre de empleado, nombre ubicacion, descripcion y fecha generacion)
@app.route('/reportes', methods=['GET'])
def get_reportes():
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
        subquery_empleados.c.nombre_empleado,
        subquery_ubicaciones.c.nombre_ubicacion
    ).join(subquery_empleados, Reporte.id_empleado_genera == subquery_empleados.c.id_empleado).join(subquery_ubicaciones, Reporte.id_ubicacion == subquery_ubicaciones.c.id_ubicacion).filter(Reporte.solucionado == False).all()

    # Crear la lista de reportes en el formato deseado
    reportes_list = [{
        "id_reporte": reporte.id_reporte,
        "descripcion": reporte.descripcion,
        "fecha_generacion": reporte.fecha_generacion.strftime("%Y-%m-%d %H:%M:%S"),
        "nombre_empleado": reporte.nombre_empleado,
        "nombre_ubicacion": reporte.nombre_ubicacion
    } for reporte in reportes_info]

    return jsonify(reportes_list)


## Endpoint que recibe un reporte y lo agrega a la base de datos
@app.route('/reporte', methods=['POST'])
def agregar_reporte():
    descripcion = request.form['descripcion']
    id_empleado_genera = request.form['id_empleado_genera']
    id_ubicacion = request.form.get('id_ubicacion', None)
    
    print("info reporte:")
    print(descripcion, id_empleado_genera, id_ubicacion)

    if 'foto' in request.files:
        print("foto encontrada")
        foto = request.files['foto']
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        _, ext = os.path.splitext(foto.filename)
        # Asegúrate de que la extensión extraída comienza con un punto, si no, agregarlo
        if not ext.startswith('.'):
            ext = f'.{ext}'
            
        print("ext: ", ext)
        
        filename = f"{id_empleado_genera}_{timestamp}{ext}"
        foto_path = os.path.join(app.config['UPLOADED_PHOTOS_DEST'], filename)
        foto.save(foto_path)
        ruta_imagen = foto_path
        
        print("ruta imagen: ")
        print(ruta_imagen)
    else:
        ruta_imagen = None

    nuevo_reporte = Reporte(
        descripcion=descripcion,
        ruta_imagen=ruta_imagen,
        id_empleado_genera=id_empleado_genera,
        id_ubicacion=id_ubicacion,
        fecha_generacion=datetime.now(),
    )

    db.session.add(nuevo_reporte)
    db.session.commit()

    return jsonify({'mensaje': 'Reporte agregado exitosamente'}), 201


## endpoints para detalles de reporte
@app.route('/reporteDetalles/<int:reporte_id>', methods=['GET'])
def get_reporte(reporte_id):
    # Buscar el reporte en la base de datos usando el ID proporcionado
    reporte = Reporte.query.get(reporte_id)
    if not reporte:
        return jsonify({'mensaje': 'Reporte no encontrado'}), 404
    
    # Crear la respuesta con los detalles del reporte
    reporte_detalle = {
        'id_reporte': reporte.id_reporte,
        'descripcion': reporte.descripcion,
        'fecha_generacion': reporte.fecha_generacion.strftime("%Y-%m-%d %H:%M:%S"),
        'solucionado': reporte.solucionado,
        'puntos': reporte.puntos,
        'ruta_imagen': request.host_url + 'imagen/' + str(reporte.id_reporte)
    }
    return jsonify(reporte_detalle)


## endpoint que regresa la imagen de un reporte
@app.route('/imagen/<int:reporte_id>')
def get_imagen_reporte(reporte_id):
    reporte = Reporte.query.get(reporte_id)
    if not reporte or not reporte.ruta_imagen:
        return jsonify({'mensaje': 'Imagen no encontrada'}), 404
    
    mime = magic.Magic(mime=True)
    content_type = mime.from_file(reporte.ruta_imagen)

    return send_file(reporte.ruta_imagen, mimetype=content_type)


## endpoint que regresa un arreglo de objetos con nombre completo y puntos ordenados de los usuarios con rolId = 1
@app.route('/tablero', methods=['GET'])
def get_tablero():
    # Subconsulta para obtener información de los empleados
    subquery_empleados = db.session.query(
        Empleado.id_empleado.label("id_empleado"),
        Empleado.nombre.label("nombre_empleado")
    ).filter(Empleado.rol_id == 1).subquery()

    # Subconsulta para obtener la suma de puntos por empleado
    subquery_puntos = db.session.query(
        Reporte.id_empleado_genera.label("id_empleado"),
        func.coalesce(func.sum(Reporte.puntos), 0).label("points")
    ).group_by(Reporte.id_empleado_genera).subquery()

    # Consulta principal que une las subconsultas con los empleados para obtener toda la información necesaria
    tablero_info = db.session.query(
        subquery_empleados.c.nombre_empleado,
        func.coalesce(subquery_puntos.c.points, 0).label('points')  # Asegurarse de asignar el alias 'points'
    ).outerjoin(subquery_puntos, subquery_empleados.c.id_empleado == subquery_puntos.c.id_empleado).all()

    # Crear la lista de usuarios en el formato deseado
    tablero_list = [{
        "nombre_empleado": empleado.nombre_empleado,
        "points": empleado.points
    } for empleado in tablero_info]
    
    return jsonify(tablero_list)
    
    
## endpoint que regresa toda la informacion de todos los reportes (incluido nombre de empleado, nombre ubicacion)
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


# endpoint que marca un reporte como solucionado, pone el id del empleado que lo soluciona y asigna los puntos
@app.route('/reporteSolucionado', methods=['POST'])
def reporte_solucionado():
    data = request.get_json()
    reporte_id = data['reporte_id']
    id_empleado_soluciona = data['id_empleado_soluciona']
    puntos = data['puntos']
    
    request.headers.get
    
    reporte = Reporte.query.get(reporte_id)
    if not reporte:
        return jsonify({'mensaje': 'Reporte no encontrado'}), 404

    reporte.solucionado = True
    reporte.fecha_resolucion = datetime.now()
    reporte.id_empleado_soluciona = id_empleado_soluciona
    reporte.puntos = puntos

    db.session.commit()

    return jsonify({'mensaje': 'Reporte marcado como solucionado'}), 200
    



if __name__ == '__main__':
    app.run(debug=True, port=5001, host='0.0.0.0')