from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import asyncpg

app = FastAPI()

# ---------------------------
# CONFIGURACIÓN BASE DE DATOS
# ---------------------------

DATABASE_URL = "postgresql://usuario:contraseña@localhost:5432/tu_basedatos"

# Variable global del pool
pool = None


# ---------------------------
# MODELO PYDANTIC
# ---------------------------

class Usuario(BaseModel):
    nombre: str
    edad: int


# ---------------------------
# EVENTOS DE INICIO Y CIERRE
# ---------------------------

@app.on_event("startup")
async def startup():
    global pool

    pool = await asyncpg.create_pool(
        DATABASE_URL,
        min_size=1,
        max_size=10
    )

    # Crear tabla automáticamente
    async with pool.acquire() as conn:
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS usuarios (
                id SERIAL PRIMARY KEY,
                nombre TEXT NOT NULL,
                edad INTEGER NOT NULL
            )
        """)


@app.on_event("shutdown")
async def shutdown():
    await pool.close()


# ---------------------------
# RUTA PRINCIPAL
# ---------------------------

@app.get("/")
async def inicio():
    return {"mensaje": "API funcionando correctamente"}


# ---------------------------
# CREAR USUARIO
# ---------------------------

@app.post("/usuarios")
async def crear_usuario(usuario: Usuario):

    query = """
        INSERT INTO usuarios(nombre, edad)
        VALUES($1, $2)
        RETURNING id, nombre, edad
    """

    async with pool.acquire() as conn:
        resultado = await conn.fetchrow(
            query,
            usuario.nombre,
            usuario.edad
        )

    return dict(resultado)


# ---------------------------
# OBTENER TODOS LOS USUARIOS
# ---------------------------

@app.get("/usuarios")
async def obtener_usuarios():

    query = "SELECT * FROM usuarios"

    async with pool.acquire() as conn:
        usuarios = await conn.fetch(query)

    return [dict(usuario) for usuario in usuarios]


# ---------------------------
# OBTENER USUARIO POR ID
# ---------------------------

@app.get("/usuarios/{id}")
async def obtener_usuario(id: int):

    query = "SELECT * FROM usuarios WHERE id = $1"

    async with pool.acquire() as conn:
        usuario = await conn.fetchrow(query, id)

    if not usuario:
        raise HTTPException(
            status_code=404,
            detail="Usuario no encontrado"
        )

    return dict(usuario)


# ---------------------------
# ACTUALIZAR USUARIO
# ---------------------------

@app.put("/usuarios/{id}")
async def actualizar_usuario(id: int, usuario: Usuario):

    query = """
        UPDATE usuarios
        SET nombre = $1,
            edad = $2
        WHERE id = $3
        RETURNING id, nombre, edad
    """

    async with pool.acquire() as conn:
        resultado = await conn.fetchrow(
            query,
            usuario.nombre,
            usuario.edad,
            id
        )

    if not resultado:
        raise HTTPException(
            status_code=404,
            detail="Usuario no encontrado"
        )

    return dict(resultado)


# ---------------------------
# ELIMINAR USUARIO
# ---------------------------

@app.delete("/usuarios/{id}")
async def eliminar_usuario(id: int):

    query = """
        DELETE FROM usuarios
        WHERE id = $1
        RETURNING id
    """

    async with pool.acquire() as conn:
        resultado = await conn.fetchrow(query, id)

    if not resultado:
        raise HTTPException(
            status_code=404,
            detail="Usuario no encontrado"
        )

    return {"mensaje": "Usuario eliminado"}