import psycopg2
import time
import hashlib
import os

# IP de la base de datos
ip = "192.168.100.149"

# Configuración de conexión a bases de datos
DB_CONFIG = {
    'clientes': {
        'dbname': 'clientes',
        'user': 'cliente',
        'password': 'cliente',
        'host': ip,
        'port': 5436
    },
    'ventas': {
        'dbname': 'ventas',
        'user': 'venta',
        'password': 'venta',
        'host': ip,
        'port': 5435
    },
    'warehouse': {
        'dbname': 'warehouse',
        'user': 'dw',
        'password': 'dw',
        'host': ip,
        'port': 5437
    }
}


# Función para conectar a una base de datos PostgreSQL
def connect_db(db_config):
    conn = psycopg2.connect(
        dbname=db_config['dbname'],
        user=db_config['user'],
        password=db_config['password'],
        host=db_config['host'],
        port=db_config['port']
    )
    return conn


# Función para calcular el hash de un archivo
def calculate_file_hash(file_path):
    hasher = hashlib.md5()
    with open(file_path, 'rb') as f:
        buffer = f.read()
        hasher.update(buffer)
    return hasher.hexdigest()


# Función para extraer datos de una tabla
def extract_data(db_name, table_name):
    query = f'SELECT * FROM {table_name}'
    conn = connect_db(DB_CONFIG[db_name])
    cursor = conn.cursor()
    cursor.execute(query)
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return rows


# Función para guardar datos en un archivo CSV
def save_to_csv(data, file_path):
    with open(file_path, 'w') as f:
        for row in data:
            f.write(','.join(map(str, row)) + '\n')


# Función para cargar datos en el data warehouse
def load_data(file_path, table_name):
    conn = connect_db(DB_CONFIG['warehouse'])
    cursor = conn.cursor()

    # Definir los nombres de las columnas según la tabla
    column_definitions = {
        'clientes': ['id', 'nombre', 'email', 'telefono', 'updated_at'],
        'productos': ['id', 'nombre', 'precio', 'updated_at'],
        'ventas': ['id', 'producto_id', 'cantidad', 'fecha', 'cliente_id']
    }

    columns = column_definitions.get(table_name)

    if not columns:
        print(f"No se encontraron definiciones de columnas para la tabla {table_name}")
        return

    placeholders = ','.join(['%s'] * len(columns))
    update_set = ', '.join([f"{col} = EXCLUDED.{col}" for col in columns if col != 'id'])
    insert_query = f'''
        INSERT INTO {table_name} ({', '.join(columns)})
        VALUES ({placeholders})
        ON CONFLICT (id) DO UPDATE
        SET {update_set}
    '''

    with open(file_path, 'r') as f:
        for line in f:
            values = line.strip().split(',')
            try:
                if table_name == 'ventas':
                    values = [
                        int(values[0]),  # id
                        int(values[1]),  # producto_id
                        int(values[2]),  # cantidad
                        values[3],  # fecha
                        int(values[4])  # cliente_id
                    ]
                elif table_name == 'productos':
                    values = [
                        int(values[0]),  # id
                        values[1],  # nombre
                        float(values[2]),  # precio
                        values[3]  # updated_at
                    ]
                elif table_name == 'clientes':
                    values = [
                        int(values[0]),  # id
                        values[1],  # nombre
                        values[2],  # email
                        values[3],  # telefono
                        values[4]  # updated_at
                    ]
                else:
                    print(f"Tabla no reconocida: {table_name}")
                    continue

                cursor.execute(insert_query, values)
            except ValueError as e:
                print(f"Error de conversión en la línea: {line}. Error: {e}")
                continue
            except Exception as e:
                print(f"Error en la consulta SQL: {e}")

    conn.commit()
    cursor.close()
    conn.close()



# Función principal del proceso ETL
def etl_process():
    # Extrae datos de las bases de datos
    clientes_data = extract_data('clientes', 'clientes')
    productos_data = extract_data('ventas', 'productos')
    transacciones_data = extract_data('ventas', 'transacciones')

    # Guarda los datos en archivos CSV
    save_to_csv(clientes_data, 'clientes_data.csv')
    save_to_csv(productos_data, 'productos_data.csv')
    save_to_csv(transacciones_data, 'transacciones_data.csv')

    # Carga los datos en el data warehouse
    load_data('clientes_data.csv', 'clientes')
    load_data('productos_data.csv', 'productos')

    # Procesa transacciones y carga en ventas del data warehouse
    conn = connect_db(DB_CONFIG['warehouse'])
    cursor = conn.cursor()
    with open('transacciones_data.csv', 'r') as f:
        for line in f:
            values = line.strip().split(',')
            if len(values) == 5:  # Asegúrate de que haya 5 valores
                try:
                    values = [
                        int(values[0]),  # id
                        int(values[1]),  # cliente_id
                        int(values[2]),  # producto_id
                        int(values[3]),  # cantidad
                        values[4]  # fecha
                    ]
                except ValueError as e:
                    print(f"Error de conversión en la línea: {line}. Error: {e}")
                    continue

                insert_query = '''
                    INSERT INTO ventas (id, cliente_id, producto_id, cantidad, fecha)
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (id) DO UPDATE
                    SET cliente_id = EXCLUDED.cliente_id,
                        producto_id = EXCLUDED.producto_id,
                        cantidad = EXCLUDED.cantidad,
                        fecha = EXCLUDED.fecha
                '''
                cursor.execute(insert_query, values)
                conn.commit()
    cursor.close()
    conn.close()


# Programa principal para ejecutar ETL cada 10 segundos y eliminar archivos después de 10 segundos
if __name__ == '__main__':
    while True:
        etl_process()
        time.sleep(10)
        tables = ['clientes', 'productos', 'transacciones']
        for table_name in tables:
            file_path = f'{table_name}_data.csv'
            if os.path.exists(file_path):
                os.remove(file_path)
