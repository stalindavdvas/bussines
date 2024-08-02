1.- acceder con el comando cd bases
2.- Iniciar los contenedores de bases de datos con el comando docker-compose up --build
3.- Una vez iniciados, utilizar un admnistrador de base de datos para postgres como PGadmin o HeidiSQL y conectarse a las bases de datos en los puerto proporcionados.
    5435 para la base de datos ventas: user: venta, pass:venta, dbname: ventas
    5436 para la base de datos clientes: user: cliente, pass:cliente, dbname: clientes
    5437 para la base de datos datawarehouse: user: dw, pass:dw, dbname: warehouse
4.- Ejecutar los scripts proporcionados en el archivo tablas_bases.txt
5.- regresar con el comando cd ..
6.- Ingresar con cd metabase
7.- Ejecutar docker-compose up --build para levantar el contenedor de metabase
8.- ingresar el comando cd ..
9.- Ejecutar el comando pip install requirements.txt -r
10.- Cuando ya esten levantados los contenedores, ejecutar el archivo etl.py
11.- Realizar la conexion de la base de datos con metabase a través de la interfaz de metabase en http://localhost:3000 hacia la base de datos warehouse en el puerto 5437
12.- Crear los dashboard con los KPI's que necesiten en la interfaz de metabase eligiendo en nuevo consulta sql.

1.- Total Ingresos
    SELECT SUM(cantidad * p.precio) AS total_ingresos
    FROM ventas v
    JOIN productos p ON v.producto_id = p.id;

2.- Clientes Potenciales
        SELECT
        c.id AS cliente_id,
        c.nombre AS cliente_nombre,
        COUNT(t.id) AS total_transacciones,
        SUM(t.cantidad) AS total_cantidad_comprada
        FROM
            ventas t
        JOIN
            clientes c ON t.cliente_id = c.id
        GROUP BY
            c.id, c.nombre
        ORDER BY
            total_cantidad_comprada DESC
        LIMIT 10; -- Limita el resultado a los 10 clientes que más han comprado

3.- Productos más vendidos
        SELECT p.nombre AS producto, SUM(v.cantidad) AS total_vendido
        FROM ventas v
        JOIN productos p ON v.producto_id = p.id
        GROUP BY p.nombre
        ORDER BY total_vendido DESC
        LIMIT 5;


