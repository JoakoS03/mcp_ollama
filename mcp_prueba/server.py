import argparse
from mcp.server.fastmcp import FastMCP
import psycopg

server = FastMCP("Saludo", port=21000, host="0.0.0.0")


@server.tool()
def greet(name: str) -> str:
    """
    Saluda a la persona con el nombre dado.

    Ejemplo:
        >>> greet("Juan")
        'Hola, Juan!'
    """
    return f"Hola, {name}!"

@server.tool()
def un_poema_de_amor() -> str:
    """
    Devuelve un poema de amor corto.

    Ejemplo:
        >>> un_poema_de_amor()
        'Eres la luz en mi oscuridad,
         el latido de mi corazón,
         mi amor por ti es infinito,
         mi dulce inspiración.'
    """
    return (
        "Eres la luz en mi oscuridad,\n"
        "el latido de mi corazón,\n"
        "mi amor por ti es infinito,\n"
        "mi dulce inspiración."
    )

def get_connection():
    conn = psycopg.connect(
        host="db",
        port=5432,
        dbname="mcp_database",
        user="admin",
        password="admin123"
    )
    return conn

@server.tool()
def execute_query(query: str) -> str:
    """
    Ejecuta una consulta SQL de tipo (INSERT | DELETE | UPDATE) en la base de datos y devuelve los resultados.

    Ejemplo:
        >>> execute_query("INSERT INTO users (username, password_hash) VALUES ('Juan', 'clave1234');")
        
    """
    try :
        conn = get_connection() #Funcion que crea la conexion a la base de datos
        cursor = conn.cursor() #Crea el cursor
        cursor.execute(query) #Ejecuta la consulta
        
        conn.commit()
        affected = cursor.rowcount

        cursor.close() #Cierra el cursor
        conn.close() #Cierra la conexion
        return f"filas afectadas: {affected}"
    except Exception as e:
        return f"Error al ejecutar la consulta: {e}"


@server.tool()
def get_users(query : str = "SELECT * FROM users;") -> str:
    """
    Realiza una consulta SQL de tipo (SELECT) a la base de datos.

    Ejemplo:
        >>> get_users("SELECT * FROM users WHERE age > 30;")
        
    """
    try :
        conn = get_connection() #Funcion que crea la conexion a la base de datos
        cursor = conn.cursor() #Crea el cursor
        cursor.execute(query) #Ejecuta la consulta
        results = cursor.fetchall() #Obtiene los resultados
        cursor.close() #Cierra el cursor
        conn.close() #Cierra la conexion
        return str(results)
    except Exception as e:
        return f"Error al ejecutar la consulta: {e}"

if __name__ == "__main__":
    # Start the server
    print("🚀Starting server... ")

    # Debug Mode
    #  uv run mcp dev server.py

    # Production Mode
    # uv run server.py --server_type=sse

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--server_type", type=str, default="sse", choices=["sse", "stdio"]
    )

    args = parser.parse_args()
    server.run(args.server_type)