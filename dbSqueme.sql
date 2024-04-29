CREATE DATABASE poolpoolgo;
commit;

USE poolpoolgo;

CREATE TABLE Rol (
    id_rol INT PRIMARY KEY NOT NULL,
    nombre VARCHAR(100) NOT NULL,
    descripcion NVARCHAR(255)
);

CREATE TABLE Empleado (
    id_empleado INT PRIMARY KEY IDENTITY(1,1),
    nombre VARCHAR(100),
    correo VARCHAR(100),
    rol_id INT NOT NULL,
    CONSTRAINT fk_rol FOREIGN KEY (rol_id) REFERENCES Rol(id_rol)
);

CREATE TABLE Ubicacion (
    id_ubicacion INT PRIMARY KEY IDENTITY(1,1),
    nombre VARCHAR(100),
    latitud FLOAT,
    longitud FLOAT
);

ALTER TABLE Ubicacion ADD descripcion VARCHAR(100);

CREATE TABLE Reporte (
    id_reporte INT PRIMARY KEY IDENTITY(1,1),
    descripcion VARCHAR(MAX) NOT NULL,
    ruta_imagen VARCHAR(MAX),
    fecha_resolucion DATETIME,
    puntos INT,
    solucionado BIT,
    id_ubicacion INT,
    id_empleado_genera INT,
    id_empleado_soluciona INT,
    fecha_generacion DATETIME DEFAULT GETDATE(),
	CONSTRAINT fk_ubicacion FOREIGN KEY (id_ubicacion) REFERENCES Ubicacion(id_ubicacion),
    CONSTRAINT fk_empleado_genera FOREIGN KEY (id_empleado_genera) REFERENCES Empleado(id_empleado),
    CONSTRAINT fk_empleado_soluciona FOREIGN KEY (id_empleado_soluciona) REFERENCES Empleado(id_empleado)
);

CREATE TABLE Premio (
    id_premio INT PRIMARY KEY IDENTITY(1,1),
    nombre VARCHAR(100) NOT NULL,
    descripcion VARCHAR(255)
);

CREATE TABLE EmpleadoPremio (
    id_empleado INT NOT NULL,
    id_premio INT NOT NULL,
    CONSTRAINT pk_empleadopremio PRIMARY KEY (id_empleado, id_premio),
    CONSTRAINT fk_empleado FOREIGN KEY (id_empleado) REFERENCES Empleado(id_empleado),
    CONSTRAINT fk_premio FOREIGN KEY (id_premio) REFERENCES Premio(id_premio)
);


INSERT INTO Rol (id_rol, nombre, descripcion) VALUES (1, 'Operativo', 'Rol encargado de generar reportes');
INSERT INTO Rol (id_rol, nombre, descripcion) VALUES (2, 'Administrativo', 'Rol encargado de solucionar reportes');

INSERT INTO Empleado (nombre, correo, rol_id) VALUES ('Nicolás Treviño', 'nicolas@whirlpool.com', 1);
INSERT INTO Empleado (nombre, correo, rol_id) VALUES ('Ramiro Garza', 'ramiro@whirlpool.com', 1);
INSERT INTO Empleado (nombre, correo, rol_id) VALUES ('Pedro Sanchez', 'pedro@whirlpool.com', 2);

INSERT INTO Ubicacion (nombre, descripcion, latitud, longitud) VALUES ('Liverpool Valle Oriente', 'San Pedro Garza García', 25.755845, -100.271838);


INSERT INTO Reporte (
    descripcion,
    ruta_imagen,
    puntos,
    solucionado,
    id_ubicacion,
    id_empleado_genera,
    id_empleado_soluciona
) VALUES (
    'Lavadora se encuentra dañada',
    '/reporte1.jpg',
    0,
    0,
    1,
    1,
    NULL
);

INSERT INTO Reporte (
    descripcion,
    ruta_imagen,
    fecha_resolucion,
    puntos,
    solucionado,
    id_ubicacion,
    id_empleado_genera,
    id_empleado_soluciona,
    fecha_generacion
) VALUES (
    'Reporte de problema resuelto',
    '/reporte2.jpg',
    GETDATE(),
    200,
    1,
    1,
    1,
    3,
	GETDATE()
);


SELECT * FROM Reporte;


SELECT * FROM Ubicacion;
