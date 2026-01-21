--------------------No usar-----------------------
### Crear entorno virtual
 - uv .venv
 - Activar
    - .venv\Scripts\activate 

### Sincronizar dependencias
 - uv sync

### Uso:
 - uv run uv run server.py --server_type=sse
 - uv run uv run .\ollama_client.py
------------------------------------------
### Crear la imagen
 - docker build -t mcp_prueba .

### Levantar el contenedor
 #- docker compose run mcp_client (No usar)
 - docker compose up -d mcp_client

docker logs -f $(docker ps | grep "21003" | awk '{print $1}')


j_sueyro@server1:~/Joako/mcp_uv$ curl -X POST http://192.168.30.30:21003/api/agent --json '{"message": "Hola Soy joaquin"}'
{"response":"¡Hola, Joaquin! 😊 ¿En qué puedo ayudarte hoy?"}
j_sueyro@server1:~/Joako/mcp_uv$ curl -X POST http://192.168.30.30:21003/api/agent --json '{"message": "Que me podes decir de Manuel Belgrano"}'
{"response":"Manuel Belgrano (1770-1820) fue un destacado abogado, economista y político argentino, clave en la independencia de América del Sur. Nació en Buenos Aires y jugó un papel fundamental en:\n\n- **Las invasiones inglesas (1806-1807)**: Defendió la ciudad frente a los ataques británicos.\n- **La Revolución de Mayo (1810)**: Como uno de sus principales impulsadores, ayudó a derrocar al virrey español Baltasar Hidalgo de Cisneros.\n- **La bandera argentina**: Diseñó y promovió el uso de la bandera tricolor que hoy es símbolo nacional.\n- **La independencia americana**: Participó en campañas militares en Argentina, Bolivia y Paraguay, y trabajó en pro de la emancipación de Hispanoamérica.\n\nSu legado trasciende fronteras, recordado por su dedicación a los ideales republicanos y su contribución a la formación de las naciones suramericanas. 🇦🇷"}
j_sueyro@server1:~/Joako/mcp_uv$ curl -X POST http://192.168.30.30:21003/api/agent --json '{"message": "Me decis los usuarios ?"}'
{"response":"Aquí tienes los usuarios de la base de datos:\n\n1. **alice** (ID: 1)\n2. **bob** (ID: 2)\n3. **charlie** (ID: 3)\n4. **joaquin** (ID: 9)\n5. **pepe** (ID: 12)\n\nTodos los usuarios están almacenados con sus respectivos IDs y fechas de creación, pero para mantenerte segur@, no se muestran las contraseñas (solo se guardan en formato hasheado en la base de datos). 😊 ¿Necesitas algo más sobre estos usuarios?"}j_sueyro@server1:~/Joako/mcp_uv$ 