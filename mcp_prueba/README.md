# 📦 Componente mcp_prueba

Esta carpeta contiene el código fuente del **Servidor MCP** (`server.py`) y del **Cliente Agente** (`ollama_client.py`).

Para la documentación completa, diagramas de arquitectura y guías paso a paso detalladas, por favor consulta el **[README principal del proyecto en la raíz del repositorio](../README.md)**.

---

## 🛠️ Comandos Rápidos

### Desarrollo Local (con uv)

1. **Crear y activar entorno virtual**:
   ```bash
   uv venv
   # Activar (Windows)
   .venv\Scripts\activate
   # Activar (Linux/macOS)
   source .venv/bin/activate
   ```

2. **Instalar dependencias**:
   ```bash
   uv sync
   ```

3. **Iniciar el servidor MCP (SSE)**:
   ```bash
   uv run server.py --server_type=sse
   ```

4. **Ejecutar el cliente agente**:
   ```bash
   uv run ollama_client.py
   ```

---

### Con Docker

1. **Construir la imagen de Docker**:
   ```bash
   docker build -t mcp_prueba .
   ```

2. **Levantar servidor y cliente con compose**:
   ```bash
   # Servidor en background
   docker compose up -d mcp_server

   # Cliente interactivo
   docker compose run --rm mcp_client
   ```
