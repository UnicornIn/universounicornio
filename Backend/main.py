from fastapi import FastAPI, HTTPException, Depends, status, Form, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer
from fastapi.responses import JSONResponse
from passlib.context import CryptContext
from pydantic import BaseModel
from jose import JWTError
from schemas import (
    TokenResponse, UserCreate, UserProfile, ClientData, 
    PreferenceRequest, ProductItem, PedidoMongo, 
    ClientCreate, Order, ApprovedOrderResponse,
    Bussiness, BussinessLogin, Distribuidor, DistribuidorCreate,
    DistribuidorResponse, DistribuidorUpdate, EmbajadorUpdate
)
from datetime import datetime, timedelta
import mercadopago
import jwt, requests
from typing import List, Optional
import os
from dotenv import load_dotenv
import urllib.parse
from bson import ObjectId
# Importaciones de las colecciones desde database.py
from database import (
    collection, collection_client, collection_transaction, 
    collection_pedidos, collection_wallet, collection_bussiness,
    collection_grandistribuidor, collection_distribuidor,
    verify_password, create_access_token, SECRET_KEY, ALGORITHM
)

# Configuración de FastAPI
app = FastAPI()

load_dotenv()


MERCADO_PAGO_API_URL = "https://api.mercadopago.com/v1/payments"
BUSINESS_CREDENTIALS = {
    "67b4ec6810a08e4b0f7c6dd8": {  # Green Energy Ltda.
        "access_token": os.getenv("GREEN_ENERGY_ACCESS_TOKEN", "").strip(),
        "public_key": os.getenv("GREEN_ENERGY_PUBLIC_KEY", "").strip(),
        "domain": "https://rizosfelicesmx.unicornio.tech/"
    },
    "67cb61058d171ae47134abe5": {  # Rizos Felices México
        "access_token": os.getenv("RIZOS_FELICES_MEXICO_ACCESS_TOKEN", "").strip(),
        "public_key": os.getenv("RIZOS_FELICES_MEXICO_PUBLIC_KEY", "").strip(),
        "domain": "https://rizosfelicesmx.unicornio.tech/"
    },
    "67cb603a8d171ae47134abe4": {  # Rizos Felices Pachuca
        "access_token": os.getenv("RIZOS_FELICES_PACHUCA_ACCESS_TOKEN", "").strip(),
        "public_key": os.getenv("RIZOS_FELICES_PACHUCA_PUBLIC_KEY", "").strip(),
        "domain": "https://rizosfelicesmx.unicornio.tech/"
    }
}
import os

for business_id, credentials in BUSINESS_CREDENTIALS.items():
    if not credentials["access_token"]:
        print(f"❌ ERROR: ACCESS_TOKEN de {business_id} no está definido en el .env")
        raise ValueError(f"ACCESS_TOKEN de {business_id} no está definido en el .env")
    else:
        print(f"✅ ACCESS_TOKEN encontrado para negocio {business_id}")

    # Crear instancia del SDK de Mercado Pago
    credentials["sdk"] = mercadopago.SDK(credentials["access_token"])

# Inicializar FastAPI
app = FastAPI()


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/token")
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Configuración de CORS
origins = [
    "https://rizosfelicesco.unicornio.tech",
    "https://rizosfelicesmx.unicornio.tech",
    "http://localhost:3000"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No se pudieron validar las credenciales",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        rol: str = payload.get("rol")
        
        print("📢 Usuario autenticado:", {"email": email, "rol": rol})  # <-- Agregar print
        
        if not email or not rol:
            raise credentials_exception
        return {"email": email, "rol": rol}
    except jwt.PyJWTError:
        raise credentials_exception


@app.get("/")
async def read_root():
    return {"message": "Bienvenido a la API de Embajadores"}

@app.get("/api/pais")
async def obtener_pais(ref: str = Query(..., description="Correo del embajador")):
    # Decodificar el valor de ref para manejar caracteres como %40
    ref_decoded = urllib.parse.unquote(ref).lower()  # Convertir a minúsculas

    # Buscar embajador por email
    embajador = await collection.find_one({"email": ref_decoded})
    print("Conexión a Mongo válida:", collection.count_documents({}))

    if not embajador:
        raise HTTPException(status_code=404, detail="Embajador no encontrado")
    
    pais = embajador.get("pais", "País no definido")  # Manejo seguro
    return {"id": str(embajador["_id"]), "email": embajador["email"], "pais": pais}

# ENDPOINT PARA INICIAR SESIÓN POR ROLES (INCLUYENDO EMBAJADORES)
@app.post("/token", response_model=TokenResponse)
async def login(
    username: str = Form(...),  # Correo electrónico
    password: str = Form(...)   # Contraseña
):
    user = None  # Inicializamos la variable user

    # Buscar el usuario en la colección de embajadores
    user = await collection.find_one({"email": username})
    if user:
        email_field = "email"  # Para embajadores, el correo está en "email"
        nombre = user.get("full_name")
        rol = user.get("rol", "Embajador")  # Si no tiene rol explícito, asumir "Embajador"
    else:
        # Buscar en la colección de negocios
        user = await collection_bussiness.find_one({"correo_electronico": username})
        if user:
            email_field = "correo_electronico"
            nombre = user.get("nombre")
            rol = user.get("rol")
        else:
            # Buscar en la colección de grandistribuidores
            user = await collection_grandistribuidor.find_one({"correo_electronico": username})
            if user:
                email_field = "correo_electronico"
                nombre = user.get("nombre")
                rol = user.get("rol")
            else:
                # Buscar en la colección de distribuidores
                user = await collection_distribuidor.find_one({"correo_electronico": username})
                if user:
                    email_field = "correo_electronico"
                    nombre = user.get("nombre")
                    rol = user.get("rol")
                else:
                    raise HTTPException(status_code=400, detail="Usuario no encontrado.")

    # Verificar la contraseña
    if not verify_password(password, user.get("hashed_password")):
        raise HTTPException(status_code=401, detail="Contraseña incorrecta.")

    # Obtener país del usuario
    pais = user.get("pais")

    # Si el usuario es un distribuidor y no tiene rol, asignarle "Distribuidor"
    if not rol and user.get("negocio_id"):
        rol = "Distribuidor"

    # Asegurar que el rol sea válido
    if rol not in ["Negocio", "Grandistribuidor", "Distribuidor", "Embajador"]:
        raise HTTPException(status_code=403, detail="Rol no válido.")

    # Crear el token de acceso
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user[email_field], "rol": rol, "nombre": nombre, "pais": pais},
        expires_delta=access_token_expires
    )

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        rol=rol,
        nombre=nombre,
        pais=pais
    )

# ENDPOINT PARA CREAR UN NUEVO EMBAJADOR
@app.post("/crear-embajador/", status_code=status.HTTP_201_CREATED)
async def crear_embajador(
    embajador: UserCreate, 
    current_user: dict = Depends(get_current_user)
):
    # Verificar que el usuario autenticado sea un Distribuidor
    if current_user["rol"] != "Distribuidor":
        raise HTTPException(status_code=403, detail="No autorizado para crear embajadores")

    # Buscar el distribuidor autenticado en la base de datos
    distribuidor = await collection_distribuidor.find_one({"correo_electronico": current_user["email"]})
    if not distribuidor:
        raise HTTPException(status_code=404, detail="Distribuidor no encontrado")
    
    distribuidor_id = distribuidor["_id"]  # ObjectId del distribuidor
    negocio_id = distribuidor.get("negocio_id")  # Obtener el negocio_id del distribuidor

    if not negocio_id:
        raise HTTPException(status_code=400, detail="El distribuidor no tiene un negocio asociado")

    # Verificar si el embajador ya existe por correo electrónico
    existing_user = await collection.find_one({"email": embajador.email})
    if existing_user:
        raise HTTPException(status_code=400, detail="El embajador ya existe.")

    # Encriptar la contraseña antes de guardarla
    hashed_password = pwd_context.hash(embajador.password)

    # Crear el nuevo embajador con el negocio_id y distribuidor_id
    new_embajador = {
        "email": embajador.email,
        "hashed_password": hashed_password,
        "full_name": embajador.full_name,
        "whatsapp_number": embajador.whatsapp_number,
        "pais": embajador.pais,
        "rol": "Embajador",  # Rol asignado automáticamente
        "distribuidor_id": distribuidor_id,  # Guardar el ObjectId del distribuidor
        "negocio_id": negocio_id  # Asignar automáticamente el negocio_id del distribuidor
    }

    # Insertar el embajador en la base de datos
    result = await collection.insert_one(new_embajador)

    # Devolver el ID del nuevo embajador creado
    return {
        "mensaje": "Embajador creado exitosamente",
        "id": str(result.inserted_id),
        "distribuidor_id": str(distribuidor_id),
        "negocio_id": str(negocio_id)  # Devolver el negocio_id asignado
    }
    
# ENDPOINT PARA LOS DATOS DEL EMBAJADOR AUTENTICADO
@app.get("/ambassadors", response_model=UserProfile)
async def get_user_profile(current_user: dict = Depends(get_current_user)):
    # Obtener el usuario de la base de datos
    user = await collection.find_one({"email": current_user["email"]})

    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    # Verificar si el usuario tiene el rol de "Embajador"
    if user.get("rol") != "Embajador":
        raise HTTPException(status_code=403, detail="Acceso denegado: no tienes el rol de embajador")

    # Construir el perfil del embajador
    profile_data = {
        "full_name": user.get("full_name"),
        "whatsapp_number": user.get("whatsapp_number"),
        "email": user.get("email"),
        "address": user.get("address", "Sin dirección proporcionada"),
        "rol": user.get("rol"),
    }

    return profile_data

# ENDPOINT PARA OBTENER LOS CLIENTES ASOCIADOS A UN EMBAJADOR
@app.get("/clients", response_model=List[ClientData])
async def get_clients(current_user: dict = Depends(get_current_user)):
    """
    Obtiene los clientes asociados al embajador autenticado.
    """
    # Obtener el email del embajador autenticado
    email = current_user.get("email")
    if not email:
        raise HTTPException(status_code=401, detail="Usuario no autenticado")
    
    # Verificar si el embajador existe
    ambassador = await collection.find_one({"email": email})
    if not ambassador:
        raise HTTPException(status_code=404, detail="Embajador no encontrado")

    # Obtener todos los clientes asociados al email del embajador
    clients_cursor = collection_client.find({"ref": email})
    clients = await clients_cursor.to_list(length=100)

    if not clients:
        raise HTTPException(status_code=404, detail="No hay clientes disponibles")

    # Convertir los resultados en una lista de objetos ClientData
    client_list = []
    for client in clients:
        client_data = ClientData(
            name=client.get("nombre"),
            email=client.get("correo_electronico"),
            whatsapp_phone=client.get("telefono"),
        )
        client_list.append(client_data)

    return client_list


# ENDPOINT PARA CREAR UN CLIENTE ASOSIADO A UN EMBAJADOR
@app.post("/clients", response_model=ClientCreate)
async def create_client(client_data: ClientCreate, current_user: str = Depends(get_current_user)):
    """
    Guarda un nuevo cliente asociado al embajador autenticado.
    """
    # Verificar si el embajador existe
    ambassador = await collection.find_one({"email": current_user})
    if not ambassador:
        raise HTTPException(status_code=404, detail="Embajador no encontrado")

    # Verificar si el cliente ya existe (por correo electrónico)
    existing_client = await collection_client.find_one({"email": client_data.email})
    if existing_client:
        raise HTTPException(status_code=400, detail="El cliente ya existe")

    # Crear el documento del cliente
    client_document = {
        "nombre": client_data.name,
        "correo_electronico": client_data.email,
        "telefono": client_data.whatsapp_phone,
        "instagram": client_data.instagram,
        "ref": client_data.ref,  # Asociar el cliente al embajador
    }

    # Insertar el cliente en la colección
    result = await collection_client.insert_one(client_document)
    if not result.inserted_id:
        raise HTTPException(status_code=500, detail="Error al guardar el cliente")

    # Devolver los datos del cliente guardado
    return {**client_data.dict(), "id": str(result.inserted_id)}


# ENDPOINT PARA CREAR UN PEDIDO Y LA PREFERENCIA CON MERCADO PAGO
@app.post("/create-preference")
async def create_preference(request: PreferenceRequest):
    try:
        print("📥 Datos recibidos:", request.dict())

        # 1. Buscar al embajador en la base de datos por su correo (ref)
        embajador = await collection.find_one({"email": request.ref})
        if not embajador:
            print("❌ Embajador no encontrado")
            raise HTTPException(status_code=400, detail="Embajador no encontrado")
        print("✅ Embajador encontrado:", embajador)

        # 2. Obtener el negocio_id del embajador
        negocio_id = embajador.get("negocio_id")
        if not negocio_id:
            print("❌ Embajador no tiene un negocio asociado")
            raise HTTPException(status_code=400, detail="Embajador no tiene un negocio asociado")
        print("✅ Negocio ID del embajador:", negocio_id)

        # 3. Buscar el negocio en collection_bussiness
        negocio = await collection_bussiness.find_one({"_id": ObjectId(negocio_id)})
        if not negocio:
            print("❌ Negocio no encontrado")
            raise HTTPException(status_code=400, detail="Negocio no encontrado")
        print("✅ Negocio encontrado:", negocio)

        # 4. Verificar si el negocio está en BUSINESS_CREDENTIALS
        negocio_id_str = str(negocio["_id"])  # Convertir a string para buscar en BUSINESS_CREDENTIALS
        if negocio_id_str not in BUSINESS_CREDENTIALS:
            print("❌ Negocio no registrado en BUSINESS_CREDENTIALS")
            raise HTTPException(status_code=400, detail="Negocio no registrado en BUSINESS_CREDENTIALS")
        print("✅ Negocio registrado en BUSINESS_CREDENTIALS")

        # 5. Obtener credenciales del negocio
        credenciales = BUSINESS_CREDENTIALS[negocio_id_str]
        sdk = mercadopago.SDK(credenciales["access_token"])
        print("✅ Credenciales del negocio obtenidas")

        # 6. Calcular el total del pedido
        total = sum(item.unit_price * item.quantity for item in request.items)
        print("✅ Total del pedido calculado:", total)

        # 7. Guardar el pedido en MongoDB
        pedido_data = PedidoMongo(
            cedula=request.cedula,
            nombre=request.nombre,
            apellidos=request.apellidos,
            pais_region=request.pais_region,
            direccion_calle=request.direccion_calle,
            numero_casa=request.numero_casa,
            estado_municipio=request.estado_municipio,
            localidad_ciudad=request.localidad_ciudad,
            telefono=request.telefono,
            correo_electronico=request.correo_electronico,
            ref=request.ref,
            productos=request.items,
            total=total,
        )

        result = await collection_pedidos.insert_one(pedido_data.dict())
        pedido_id = str(result.inserted_id)
        print("✅ Pedido guardado en MongoDB con ID:", pedido_id)

        # 8. Crear la preferencia de pago en Mercado Pago
        preference_data = {
            "items": [{"title": item.title, "quantity": item.quantity, "unit_price": item.unit_price} for item in request.items],
            "external_reference": pedido_id,  # ID del pedido en MongoDB
            "back_urls": {
                "success": f"{credenciales['domain']}?ref={request.ref}",
                "failure": f"{credenciales['domain']}?ref={request.ref}",
                "pending": f"{credenciales['domain']}?ref={request.ref}"
            },
            "auto_return": "approved",
            "notification_url": "https://api.unicornio.tech/webhook",
        }

        preference_response = sdk.preference().create(preference_data)
        print("✅ Preferencia de pago creada en Mercado Pago")

        # 9. Verificar la respuesta de Mercado Pago
        if "response" in preference_response and "init_point" in preference_response["response"]:
            print("✅ Preferencia creada exitosamente:", preference_response["response"]["init_point"])
            return {"init_point": preference_response["response"]["init_point"]}
        else:
            print("❌ Error al crear la preferencia en Mercado Pago")
            raise HTTPException(status_code=500, detail="Error al crear la preferencia en Mercado Pago")

    except Exception as e:
        print("❌ Error:", str(e))
        raise HTTPException(status_code=422, detail=str(e))
 
# ENDPOINT PARA TRAER TODOS LOS PAGOS HECHOS POR MEDIO DE MERCADO PAGO
@app.get("/payments")
async def get_all_payments(negocio_id: str, begin_date: str, end_date: str, limit: int = 50, offset: int = 0):
    """
    Endpoint para obtener todas las compras realizadas en Mercado Pago de un negocio específico.
    
    Parámetros:
    - negocio_id: ID del negocio cuyos pagos quieres ver.
    - begin_date: Fecha de inicio en formato ISO 8601 (e.g., "2025-01-01T00:00:00Z").
    - end_date: Fecha de fin en formato ISO 8601 (e.g., "2025-01-09T23:59:59Z").
    - limit: Número máximo de resultados por página.
    - offset: Offset para la paginación.
    """

    # Verificar si el negocio existe en las credenciales
    if negocio_id not in BUSINESS_CREDENTIALS:
        raise HTTPException(status_code=400, detail="Negocio no registrado en Mercado Pago")

    # Obtener el SDK correcto
    sdk = BUSINESS_CREDENTIALS[negocio_id]["sdk"]

    filters = {
        "range": "date_created",
        "begin_date": begin_date,
        "end_date": end_date,
        "limit": limit,
        "offset": offset
    }

    try:
        # Realizar la búsqueda en Mercado Pago
        response = sdk.payment().search(filters)

        # Validar la respuesta
        if response["status"] != 200:
            raise HTTPException(status_code=response["status"], detail=response.get("message", "Error en Mercado Pago"))

        # Extraer los resultados de pagos
        payments = response["response"]["results"]

        return {"payments": payments}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ENDPOINT PARA TRAER LOS PEDIDOS DE LOS CLIENTES POR EMBAJADOR
@app.get("/orders-by-ambassador", response_model=List[Order])
async def get_orders_by_ambassador(current_user: dict = Depends(get_current_user)):
    email = current_user.get("email")
    if not email:
        raise HTTPException(status_code=401, detail="Usuario no autenticado")
    
    ambassador = await collection.find_one({"email": email})
    if not ambassador:
        raise HTTPException(status_code=404, detail="Embajador no encontrado")
    
    orders_cursor = collection_pedidos.find({"ref": email})
    orders = await orders_cursor.to_list(length=100)
    
    if not orders:
        raise HTTPException(status_code=404, detail="No se encontraron pedidos para este embajador")
    
    order_list = []
    for order in orders:
        order_id = order.get('_id')
        transaction = await collection_transaction.find_one({"external_reference": str(order_id)})
        
        status = transaction.get('status') if transaction else None
        date_created = transaction.get('date_created') if transaction else None
        transaction_id = str(transaction.get('id')) if transaction else None
        
        updated_order = {**order, "status": status, "date_created": date_created, "transaction_id": transaction_id}
        await collection_pedidos.update_one({"_id": order_id}, {"$set": updated_order})
        
        existing_client = await collection_client.find_one(
            {"$or": [
                {"correo_electronico": order.get('correo_electronico')},
                {"telefono": order.get('telefono')}
            ]}
        )
        
        full_name = " ".join(filter(None, [order.get('nombre', '').strip(), order.get('apellidos', '').strip()]))
        cliente_data = {
            "nombre": full_name,
            "correo_electronico": order.get('correo_electronico'),
            "telefono": order.get('telefono'),
            "ref": order.get('ref')
        }
        
        if existing_client:
            differences = {key: value for key, value in cliente_data.items() if existing_client.get(key) != value}
            if differences:
                await collection_client.update_one({"_id": existing_client["_id"]}, {"$set": differences})
        else:
            await collection_client.insert_one(cliente_data)
        
        order_list.append(Order(
            cedula=order.get('cedula'),
            nombre=order.get('nombre'),
            apellidos=order.get('apellidos'),
            pais_region=order.get('pais_region'),
            direccion_calle=order.get('direccion_calle'),
            numero_casa=order.get('numero_casa'),
            estado_municipio=order.get('estado_municipio'),
            localidad_ciudad=order.get('localidad_ciudad'),
            telefono=order.get('telefono'),
            correo_electronico=order.get('correo_electronico'),
            ref=order.get('ref'),
            productos=[ProductItem(**item) for item in order.get('productos', [])],
            total=order.get('total'),
            status=status,
            date_created=date_created,
            transaction_id=transaction_id
        ))
    
    return order_list

# ENDPOINT PARA RECIBIR LAS RESPUESTAS DE LOS PEDIDOS QUE HAN REALIZADO POR MERCADO PAGO
@app.post("/webhook")
async def webhook(request: Request):
    """
    Webhook para recibir notificaciones de Mercado Pago, consultar detalles del pago y guardarlos en MongoDB.
    """
    try:
        # Leer los datos enviados por Mercado Pago
        payment = await request.json()
        print("Notificación recibida:", payment)

        # Obtener el payment_id desde los datos recibidos
        payment_id = payment.get("data", {}).get("id") or payment.get("id")  
        if not payment_id:
            raise HTTPException(status_code=400, detail="No se recibió un payment_id válido")

        # Consultar el pago en Mercado Pago (pero primero obtener el negocio correcto)
        pedido = await collection_pedidos.find_one({"_id": ObjectId(payment.get("external_reference"))})
        if not pedido:
            raise HTTPException(status_code=404, detail="Pedido no encontrado en la base de datos")

        # Buscar al embajador asociado con el pedido
        embajador = await collection.find_one({"email": pedido["ref"]})
        if not embajador:
            raise HTTPException(status_code=404, detail="Embajador no encontrado")

        # Obtener el negocio asociado al embajador
        negocio_id = embajador.get("negocio_id")
        if not negocio_id or negocio_id not in BUSINESS_CREDENTIALS:
            raise HTTPException(status_code=400, detail="El embajador no tiene un negocio válido con credenciales")

        access_token = BUSINESS_CREDENTIALS[negocio_id]["access_token"]

        # Consultar los detalles del pago usando la API de Mercado Pago
        url = f"https://api.mercadopago.com/v1/payments/{payment_id}"
        headers = {"Authorization": f"Bearer {access_token}"}
        response = requests.get(url, headers=headers)

        # Manejo de la respuesta de la API de Mercado Pago
        if response.status_code == 200:
            payment_data = response.json()

            # Extraer solo los campos necesarios
            filtered_data = {
                "id": payment_data.get("id"),
                "status": payment_data.get("status"),
                "date_created": payment_data.get("date_created"),
                "date_approved": payment_data.get("date_approved"),
                "external_reference": payment_data.get("external_reference"),
                "timestamp": datetime.utcnow()  # Agregar un timestamp para saber cuándo se guardó
            }

            print("Detalles del pago filtrados:", filtered_data)

            # Guardar los datos en MongoDB (usando motor)
            result = await collection_transaction.insert_one(filtered_data)
            if result.inserted_id:
                print("Datos guardados en MongoDB con ID:", result.inserted_id)

                # Convertir el ObjectId a una cadena para la respuesta
                filtered_data["_id"] = str(result.inserted_id)

                return {"status": "success", "message": "Datos guardados en MongoDB", "payment_data": filtered_data}
            else:
                print("Error al guardar los datos en MongoDB")
                raise HTTPException(status_code=500, detail="Error al guardar los datos en MongoDB")
        else:
            print(f"Error al consultar el pago: {response.status_code} - {response.text}")
            raise HTTPException(
                status_code=response.status_code,
                detail=f"Error consultando detalles del pago: {response.text}"
            )
    except Exception as e:
        print("Error procesando el webhook:", e)
        raise HTTPException(status_code=500, detail="Error procesando el webhook")

# ENDPOINT PARA CALCULAR LA COMISION DE UN EMBAJADOR
@app.post("/calcular-comision", summary="Calcular comisión para el embajador autenticado")
async def calcular_comision(current_user: str = Depends(get_current_user)):
    """
    Endpoint protegido para calcular la comisión del embajador autenticado.
    Solo se calcula la comisión para pedidos con estado "approved".
    """
    try:
        # Buscar al embajador autenticado en la colección ambassador
        embajador = await collection.find_one({"email": current_user})
        if not embajador:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Embajador no encontrado"
            )

        # Obtener el ObjectId del embajador autenticado
        embajador_id = str(embajador["_id"])

        # Obtener todos los pedidos asociados al embajador con estado "approved"
        pedidos_cursor = collection_pedidos.find({
            "ref": embajador["email"],
            "status": "approved"  # Filtrar solo pedidos con estado "approved"
        })
        pedidos_aprobados = await pedidos_cursor.to_list(length=100)

        # Calcular el total de ventas solo para pedidos aprobados
        total_ventas = sum(pedido["total"] for pedido in pedidos_aprobados)

        # Calcular la comisión (25% del total de ventas)
        comision = total_ventas * 0.25

        # Crear o actualizar la wallet del embajador
        wallet = {
            "embajador_id": embajador_id,
            "total_ventas": total_ventas,
            "comision": comision,
            "fecha_actualizacion": datetime.utcnow()
        }

        # Insertar o actualizar en la colección wallet
        await collection_wallet.update_one(
            {"embajador_id": embajador_id},
            {"$set": wallet},
            upsert=True
        )

        return {
            "message": "Comisión calculada y wallet actualizada",
            "wallet": wallet
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al calcular la comisión"
        ) from e

# ENDPOINT PARA OBTENER EL TOTAL DE CLIENTES Y DE VENTAS POR EMBAJADOR
@app.get("/dashboard/metrics")
async def get_dashboard_metrics(current_user: dict = Depends(get_current_user)):
    try:
        email = current_user.get("email")
        rol = current_user.get("rol")

        if not email or not rol:
            raise HTTPException(status_code=401, detail="Usuario no autenticado")
        
        print(f"📧 Usuario autenticado: {email} - Rol: {rol}")

        total_clientes = 0
        ventas_totales = 0

        if rol == "Embajador":
            # Total de clientes directos del embajador
            total_clientes = await collection_client.count_documents({"ref": email})
            print(f"📊 Total de clientes del embajador: {total_clientes}")

            # Ventas totales de pedidos aprobados del embajador
            ventas_totales_cursor = collection_pedidos.aggregate([
                {"$match": {"ref": email, "status": "approved"}},
                {"$group": {"_id": None, "total": {"$sum": "$total"}}}
            ])
            ventas_totales_result = await ventas_totales_cursor.to_list(length=1)
            ventas_totales = ventas_totales_result[0]["total"] if ventas_totales_result else 0
            print(f"📊 Ventas totales aprobadas del embajador: {ventas_totales}")

        elif rol == "Distribuidor":
            # Buscar embajadores asociados al distribuidor
            distribuidor = await collection_distribuidor.find_one({"correo_electronico": email})
            if distribuidor:
                distribuidor_id = distribuidor["_id"]  # Se mantiene como ObjectId

                embajadores_cursor = collection.find({"distribuidor_id": distribuidor_id})  # Cambio aquí
                embajadores = await embajadores_cursor.to_list(length=None)
                
                embajador_emails = [emb["email"] for emb in embajadores]
                print(f"📊 Embajadores asociados al distribuidor: {embajador_emails}")

                # Total de clientes de los embajadores del distribuidor
                total_clientes = await collection_client.count_documents({"ref": {"$in": embajador_emails}})
                print(f"📊 Total de clientes de los embajadores del distribuidor: {total_clientes}")

                # Ventas totales de pedidos aprobados de los embajadores
                ventas_totales_cursor = collection_pedidos.aggregate([
                    {"$match": {"ref": {"$in": embajador_emails}, "status": "approved"}},
                    {"$group": {"_id": None, "total": {"$sum": "$total"}}}
                ])
                ventas_totales_result = await ventas_totales_cursor.to_list(length=1)
                ventas_totales = ventas_totales_result[0]["total"] if ventas_totales_result else 0
                print(f"📊 Ventas totales aprobadas de los embajadores del distribuidor: {ventas_totales}")

        elif rol == "Negocio":
            # Buscar embajadores asociados directamente al negocio
            negocio = await collection_bussiness.find_one({"correo_electronico": email})
            if negocio:
                embajadores_cursor = collection.find({"negocio_id": str(negocio["_id"])})

                embajadores = await embajadores_cursor.to_list(length=None)

                embajador_emails = [emb["email"] for emb in embajadores]
                print(f"📊 Embajadores asociados al negocio: {embajador_emails}")

                # Total de clientes de los embajadores del negocio
                total_clientes = await collection_client.count_documents({"ref": {"$in": embajador_emails}})
                print(f"📊 Total de clientes de los embajadores del negocio: {total_clientes}")

                # Ventas totales de pedidos aprobados de los embajadores del negocio
                ventas_totales_cursor = collection_pedidos.aggregate([
                    {"$match": {"ref": {"$in": embajador_emails}, "status": "approved"}},
                    {"$group": {"_id": None, "total": {"$sum": "$total"}}}
                ])
                ventas_totales_result = await ventas_totales_cursor.to_list(length=1)
                ventas_totales = ventas_totales_result[0]["total"] if ventas_totales_result else 0
                print(f"📊 Ventas totales aprobadas de los embajadores del negocio: {ventas_totales}")

        return {
            "total_clientes": total_clientes,
            "ventas_totales_approved": ventas_totales
        }

    except Exception as e:
        print(f"❌ Error en el endpoint /dashboard/metrics: {e}")
        raise HTTPException(status_code=500, detail="Error al obtener las métricas del dashboard")

# ENDPOINT PARA OBTENER LA COMISION DE LA CARTERA POR EMBAJADOR
@app.get("/wallet/comision-actualizada", summary="Obtener la comisión de la cartera")
async def obtener_comision_actualizada(current_user: str = Depends(get_current_user)):
    """
    Endpoint protegido para obtener la comisión del embajador autenticado.
    """
    try:
        # Buscar al embajador autenticado
        embajador = await collection.find_one({"email": current_user})
        if not embajador:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Embajador no encontrado"
            )

        # Obtener la wallet asociada al embajador
        wallet = await collection_wallet.find_one({"embajador_id": str(embajador["_id"])})
        if not wallet:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Wallet no encontrada"
            )

        return {
            "comision": wallet.get("comision", 0.0),
            "total_ventas": wallet.get("total_ventas", 0.0),
            "fecha_actualizacion": wallet.get("fecha_actualizacion", "No disponible")
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al obtener la información de la cartera"
        ) from e

    except Exception as e:
        print(f"Error en el endpoint: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al obtener la información de la cartera"
        ) from e
        
# ENDPOINT PARA OBTENER LOS PEDIDOS DE UN CLIENTE ESPECIFICO POR EMBAJADOR
@app.get("/orders-by-client/{client_email}", response_model=List[Order])
async def get_orders_by_client(client_email: str, current_user: str = Depends(get_current_user)):
    """
    Endpoint protegido para obtener los pedidos de un cliente específico.
    Solo devuelve los pedidos con estado 'approved'.
    Valida que el embajador autenticado sea el propietario del cliente.
    """
    try:
        # Verificar si el cliente pertenece al embajador autenticado
        client = await collection_client.find_one({"correo_electronico": client_email, "ref": current_user})
        if not client:
            raise HTTPException(
                status_code=404,
                detail="Cliente no encontrado o no pertenece al embajador autenticado"
            )

        # Recuperar los pedidos del cliente con estado 'approved'
        orders_cursor = collection_pedidos.find({
            "correo_electronico": client_email,
            "status": "approved"  # Filtrar por pedidos con estado 'approved'
        })
        orders = await orders_cursor.to_list(length=100)

        if not orders:
            raise HTTPException(
                status_code=404,
                detail="No se encontraron pedidos aprobados para este cliente"
            )

        # Construir la lista de pedidos
        order_list = []
        for order in orders:
            order_list.append(Order(
                cedula=order.get('cedula'),
                nombre=order.get('nombre'),
                apellidos=order.get('apellidos'),
                pais_region=order.get('pais_region'),
                direccion_calle=order.get('direccion_calle'),
                numero_casa=order.get('numero_casa'),
                estado_municipio=order.get('estado_municipio'),
                localidad_ciudad=order.get('localidad_ciudad'),
                telefono=order.get('telefono'),
                correo_electronico=order.get('correo_electronico'),
                ref=order.get('ref'),
                productos=[ProductItem(**item) for item in order.get('productos', [])],
                total=order.get('total'),
                status=order.get('status'),
                date_created=order.get('date_created'),
                transaction_id=order.get('transaction_id')
            ))

        return order_list

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error interno del servidor: {str(e)}"
        )


# ENDPOINT PARA OBTENER LOS PEDIDOS APROBADOS POR EMBAJADOR PARA LA WALLET
@app.get("/approved-orders", response_model=List[ApprovedOrderResponse])
async def get_approved_orders(current_user: dict = Depends(get_current_user)):
    email = current_user.get("email")
    if not email:
        raise HTTPException(status_code=401, detail="Usuario no autenticado")
    
    ambassador = await collection.find_one({"email": email})
    if not ambassador:
        raise HTTPException(status_code=404, detail="Embajador no encontrado")
    
    orders_cursor = collection_pedidos.find({"ref": email, "status": "approved"})
    orders = await orders_cursor.to_list(length=100)
    
    if not orders:
        raise HTTPException(status_code=404, detail="No se encontraron pedidos aprobados para este embajador")
    
    approved_orders = []
    for order in orders:
        fecha = order.get("date_created")
        
        if isinstance(fecha, datetime):
            fecha_formateada = fecha.strftime("%d/%m/%Y, %I:%M:%S %p")
        elif isinstance(fecha, str):
            try:
                fecha_dt = datetime.fromisoformat(fecha)
                fecha_formateada = fecha_dt.strftime("%d/%m/%Y, %I:%M:%S %p")
            except ValueError:
                fecha_formateada = "No disponible"
        else:
            fecha_formateada = "No disponible"
        
        approved_orders.append({
            "status": order.get("status", "approved"),
            "fecha": fecha_formateada,
            "id_transaccion": order.get("transaction_id", "No disponible"),
            "total": order.get("total", 0.0)
        })
    
    return approved_orders

# Endpoint para registrar un negocio
@app.post("/negocios/registro", status_code=status.HTTP_201_CREATED)
async def registrar_negocio(negocio: Bussiness):
    # Verificar si el negocio ya existe por correo electrónico
    existing_negocio = await collection_bussiness.find_one({"correo_electronico": negocio.correo_electronico})
    if existing_negocio:
        raise HTTPException(status_code=400, detail="El negocio ya está registrado.")

    # Validar que el rol sea uno de los permitidos
    if negocio.rol not in ["Negocio", "Grandistribuidor", "Distribuidor", "Embajador"]:
        raise HTTPException(status_code=400, detail="Rol no válido.")

    # Encriptar la contraseña antes de guardarla
    hashed_password = pwd_context.hash(negocio.password)

    # Crear el nuevo negocio
    nuevo_negocio = {
        "nombre": negocio.nombre,
        "pais": negocio.pais,
        "whatsapp": negocio.whatsapp,
        "correo_electronico": negocio.correo_electronico,
        "hashed_password": hashed_password,
        "rol": negocio.rol,  # Guardar el rol del negocio
    }

    # Insertar el negocio en la colección `negocios`
    result = await collection_bussiness.insert_one(nuevo_negocio)

    if result.inserted_id:
        return {
            "mensaje": "Negocio registrado exitosamente",
            "id": str(result.inserted_id),
            "rol": negocio.rol,  # Incluir el rol en la respuesta
        }
    else:
        raise HTTPException(status_code=500, detail="Error al registrar el negocio.")

# Endpoint para iniciar sesión de un negocio
@app.post("/negocios/login", response_model=TokenResponse)
async def login_negocio(login_data: BussinessLogin):
    # Buscar el negocio por correo electrónico
    negocio = await collection_bussiness.find_one({"correo_electronico": login_data.correo_electronico})
    if not negocio:
        raise HTTPException(status_code=400, detail="Negocio no encontrado.")

    # Verificar la contraseña
    if not verify_password(login_data.password, negocio["hashed_password"]):
        raise HTTPException(status_code=401, detail="Contraseña incorrecta.")

    # Generar el token JWT
    access_token_expires = timedelta(minutes=30)
    access_token = create_access_token(
        data={"sub": negocio["correo_electronico"], "tipo": "negocio"},
        expires_delta=access_token_expires
    )

    return {"access_token": access_token, "token_type": "bearer"}

# ENDPOINT PARA TRAER LOS DATOS DEL NEGOCIO AUTENTICADO
@app.get("/negocios/perfil")
async def obtener_perfil_negocio(current_user: dict = Depends(get_current_user)):
    # Verificar que el usuario tenga el rol "Negocio"
    if current_user["rol"] != "Negocio":
        raise HTTPException(status_code=403, detail="Acceso denegado. Solo para negocios.")

    # Buscar el negocio en la colección de negocios
    negocio = await collection_bussiness.find_one({"correo_electronico": current_user["email"]})
    if not negocio:
        raise HTTPException(status_code=404, detail="Negocio no encontrado.")

    # Devolver los datos del negocio (excluyendo la contraseña)
    return {
        "nombre": negocio.get("nombre"),
        "pais": negocio.get("pais"),
        "whatsapp": negocio.get("whatsapp"),
        "correo_electronico": negocio.get("correo_electronico"),
        "rol": negocio.get("rol"),
    }

# ENDPOINT PARA CREAR DISRTRIBUIDORES
@app.post("/distribuidores/", response_model=Distribuidor)
async def crear_distribuidor(
    distribuidor: DistribuidorCreate,
    current_user: dict = Depends(get_current_user)
):
    # Verificar que el usuario autenticado sea un negocio
    if current_user["rol"] != "Negocio":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo los negocios pueden crear distribuidores"
        )

    # Obtener el ID del negocio autenticado
    negocio = await collection_bussiness.find_one({"correo_electronico": current_user["email"]})
    if not negocio:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="El negocio autenticado no existe en la base de datos"
        )

    # Verificar si el correo ya está registrado como distribuidor
    existing_distribuidor_correo = await collection_distribuidor.find_one(
        {"correo_electronico": distribuidor.correo_electronico}
    )
    if existing_distribuidor_correo:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El correo ya está registrado como distribuidor"
        )

    # Verificar si el número de teléfono ya está registrado como distribuidor
    existing_distribuidor_telefono = await collection_distribuidor.find_one(
        {"phone": distribuidor.phone}
    )
    if existing_distribuidor_telefono:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El número de teléfono ya está registrado como distribuidor"
        )

    # Hashear la contraseña
    hashed_password = pwd_context.hash(distribuidor.password)

    # Crear el documento del distribuidor
    distribuidor_dict = distribuidor.dict()
    distribuidor_dict["nombre"] = distribuidor_dict.pop("name")  # Renombrar 'name' a 'nombre'
    distribuidor_dict["pais"] = distribuidor.pais  # Asignar el país proporcionado en los datos del distribuidor
    distribuidor_dict["telefono"] = distribuidor_dict.pop("phone")  # Renombrar 'phone' a 'telefono'
    distribuidor_dict["correo_electronico"] = distribuidor.correo_electronico
    distribuidor_dict["hashed_password"] = hashed_password
    distribuidor_dict["negocio_id"] = str(negocio["_id"])  # Asociar al negocio autenticado
    distribuidor_dict["rol"] = "Distribuidor"  # Asignar el rol "Distribuidor"
    del distribuidor_dict["password"]  # Eliminar la contraseña en texto plano

    # Guardar el distribuidor en MongoDB
    result = await collection_distribuidor.insert_one(distribuidor_dict)
    if result.inserted_id:
        distribuidor_dict["id"] = str(result.inserted_id)
        return distribuidor_dict
    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="Error al crear el distribuidor"
    )

# ENDPOINT PARA ACTUALIZAR O EDITAR LOS DATOS DE UN DISTRIBUIDOR
@app.put("/distribuidores/{distribuidor_id}", response_model=Distribuidor)
async def editar_distribuidor(
    distribuidor_id: str,
    distribuidor_update: DistribuidorUpdate,
    current_user: dict = Depends(get_current_user)
):
    # Verificar que el usuario autenticado sea un negocio
    if current_user["rol"] != "Negocio":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo los negocios pueden editar distribuidores"
        )

    # Obtener el ID del negocio autenticado
    negocio = await collection_bussiness.find_one({"correo_electronico": current_user["email"]})
    if not negocio:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="El negocio autenticado no existe en la base de datos"
        )

    # Convertir distribuidor_id a ObjectId
    try:
        distribuidor_id_obj = ObjectId(distribuidor_id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El ID del distribuidor no es válido"
        )

    # Buscar el distribuidor en la base de datos
    distribuidor = await collection_distribuidor.find_one(
        {"_id": distribuidor_id_obj, "negocio_id": str(negocio["_id"])}
    )
    if not distribuidor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="El distribuidor no existe o no pertenece a este negocio"
        )

    # Actualizar los campos proporcionados
    update_data = distribuidor_update.dict(exclude_unset=True)
    if "password" in update_data:
        update_data["hashed_password"] = pwd_context.hash(update_data["password"])
        del update_data["password"]

    # Actualizar el distribuidor en MongoDB
    await collection_distribuidor.update_one(
        {"_id": distribuidor_id_obj},
        {"$set": update_data}
    )

    # Obtener el distribuidor actualizado
    distribuidor_actualizado = await collection_distribuidor.find_one({"_id": distribuidor_id_obj})
    distribuidor_actualizado["id"] = str(distribuidor_actualizado["_id"])
    return distribuidor_actualizado

# ENDPOINT PARA ELIMINAR UN DISTRIBUIDOR
@app.delete("/distribuidores/{distribuidor_id}")
async def eliminar_distribuidor(
    distribuidor_id: str,
    current_user: dict = Depends(get_current_user)
):
    # Verificar que el usuario autenticado sea un negocio
    if current_user["rol"] != "Negocio":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo los negocios pueden eliminar distribuidores"
        )

    # Obtener el ID del negocio autenticado
    negocio = await collection_bussiness.find_one({"correo_electronico": current_user["email"]})
    if not negocio:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="El negocio autenticado no existe en la base de datos"
        )

    # Convertir distribuidor_id a ObjectId
    try:
        distribuidor_id_obj = ObjectId(distribuidor_id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El ID del distribuidor no es válido"
        )

    # Buscar el distribuidor en la base de datos
    distribuidor = await collection_distribuidor.find_one(
        {"_id": distribuidor_id_obj, "negocio_id": str(negocio["_id"])}
    )
    if not distribuidor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="El distribuidor no existe o no pertenece a este negocio"
        )

    # Eliminar el distribuidor
    await collection_distribuidor.delete_one({"_id": distribuidor_id_obj})

    return {"message": "Distribuidor eliminado correctamente"}

# ENDPOINT PARA OBTENER LOS DISTRIBUIDORES ASOCIADOS A UN NEGOCIO
@app.get("/distribuidores/negocio/", response_model=List[DistribuidorResponse])
async def obtener_distribuidores_negocio(current_user: dict = Depends(get_current_user)):
    # Verificar que el usuario autenticado sea un negocio
    if current_user["rol"] != "Negocio":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo los negocios pueden ver sus distribuidores"
        )

    # Buscar el negocio en la colección de negocios
    negocio = await collection_bussiness.find_one({"correo_electronico": current_user["email"]})
    if not negocio:
        raise HTTPException(status_code=404, detail="Negocio no encontrado.")

    # Obtener los distribuidores asociados al negocio
    distribuidores_cursor = collection_distribuidor.find({"negocio_id": str(negocio["_id"])})
    distribuidores = await distribuidores_cursor.to_list(length=100)

    # Convertir los resultados en una lista de objetos DistribuidorResponse
    distribuidores_list = []
    for distribuidor in distribuidores:
        distribuidores_list.append(DistribuidorResponse(
            id=str(distribuidor["_id"]),
            nombre=distribuidor.get("nombre", "Nombre no disponible"),  # Valor predeterminado
            correo_electronico=distribuidor.get("correo_electronico", "Correo no disponible"),  # Valor predeterminado
            telefono=distribuidor.get("telefono", "Teléfono no disponible"),  # Valor predeterminado
            pais=distribuidor.get("pais", "País no disponible"),  # Valor predeterminado
            rol=distribuidor.get("rol", "Rol no disponible")  # Valor predeterminado
        ))

    return distribuidores_list

# ENDPOINT PARA TRAER LOS DATOS DEL DISTRIBUIDOR AUTENTICADO
@app.get("/distribuidor/me", response_model=Distribuidor)
async def obtener_distribuidor_autenticado(current_user: dict = Depends(get_current_user)):
    # Verificar si el usuario es un distribuidor
    if current_user["rol"] != "Distribuidor":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo los distribuidores pueden acceder a este recurso",
        )

    # Buscar al distribuidor en la base de datos
    distribuidor = await collection_distribuidor.find_one({"correo_electronico": current_user["email"]})
    if not distribuidor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Distribuidor no encontrado",
        )

    # Devolver los datos del distribuidor
    return Distribuidor(
        nombre=distribuidor["nombre"],
        telefono=distribuidor["telefono"],
        correo_electronico=distribuidor["correo_electronico"],
        pais=distribuidor["pais"],
        id=str(distribuidor["_id"]),  # Convertir ObjectId a string
        negocio_id=distribuidor["negocio_id"],
        rol=distribuidor["rol"],
    )

# ENDPOINT PARA ELIMINAR UN EMBAJADOR POR EL DISTRIBUIDOR
@app.delete("/embajadores/{embajador_id}")
async def eliminar_embajador(
    embajador_id: str,
    current_user: dict = Depends(get_current_user)  # Verifica autenticación
):
    # Verificar que el usuario autenticado sea un distribuidor
    if current_user["rol"] != "Distribuidor":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo los distribuidores pueden eliminar embajadores"
        )

    # Obtener el ID del distribuidor autenticado
    distribuidor = await collection_distribuidor.find_one({"correo_electronico": current_user["email"]})
    if not distribuidor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="El distribuidor autenticado no existe en la base de datos"
        )

    # Convertir `distribuidor["_id"]` a `ObjectId` si no lo es
    distribuidor_id_obj = distribuidor["_id"] if isinstance(distribuidor["_id"], ObjectId) else ObjectId(distribuidor["_id"])

    # Validar y convertir embajador_id a ObjectId
    if not ObjectId.is_valid(embajador_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El ID del embajador no es válido"
        )
    
    embajador_id_obj = ObjectId(embajador_id)

    # Buscar el embajador en la base de datos
    embajador = await collection.find_one(
        {"_id": embajador_id_obj, "distribuidor_id": distribuidor_id_obj}  # <-- Comparar como ObjectId
    )
    if not embajador:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="El embajador no existe o no pertenece a este distribuidor"
        )

    # Eliminar el embajador
    await collection.delete_one({"_id": embajador_id_obj})

    return {"message": "Embajador eliminado correctamente"}

# ENDPOINT PARA PODER ACTUALIZAR UN EMBAJADOR POR EL DISTRIBUIDOR
@app.put("/embajadores/{embajador_id}")
async def editar_embajador(
    embajador_id: str,
    embajador_data: EmbajadorUpdate,
    current_user: dict = Depends(get_current_user)  # Verifica autenticación
):
    # Verificar que el usuario autenticado sea un distribuidor
    if current_user["rol"] != "Distribuidor":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo los distribuidores pueden editar embajadores"
        )

    # Obtener el ID del distribuidor autenticado
    distribuidor = await collection_distribuidor.find_one({"correo_electronico": current_user["email"]})
    if not distribuidor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="El distribuidor autenticado no existe en la base de datos"
        )

    distribuidor_id_obj = distribuidor["_id"] if isinstance(distribuidor["_id"], ObjectId) else ObjectId(distribuidor["_id"])

    # Validar y convertir embajador_id a ObjectId
    if not ObjectId.is_valid(embajador_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El ID del embajador no es válido"
        )
    
    embajador_id_obj = ObjectId(embajador_id)

    # Buscar el embajador en la base de datos
    embajador = await collection.find_one(
        {"_id": embajador_id_obj, "distribuidor_id": distribuidor_id_obj}
    )
    if not embajador:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="El embajador no existe o no pertenece a este distribuidor"
        )

    # Crear el diccionario con los datos a actualizar
    update_data = {key: value for key, value in embajador_data.dict(exclude_unset=True).items()}

    # Si no hay datos a actualizar, devolver error
    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No se proporcionaron datos para actualizar"
        )

    # Actualizar el embajador en la base de datos
    await collection.update_one(
        {"_id": embajador_id_obj},
        {"$set": update_data}
    )

    return {"message": "Embajador actualizado correctamente"}

# ENDPOINT PARA PODER OBTENER LOS EMBAJADORES ASOCIADOS A UN DISTRIBUIDOR
@app.get("/distribuidores/{distribuidor_id}/embajadores", response_model=List[dict])
async def get_embajadores_por_distribuidor(
    distribuidor_id: str, user: dict = Depends(get_current_user)
):
    """Obtiene los embajadores de un distribuidor, asegurando que pertenezca al negocio del usuario autenticado."""

    # Obtener el distribuidor desde la colección correcta
    distribuidor = await collection_distribuidor.find_one({"_id": ObjectId(distribuidor_id)})

    if not distribuidor:
        raise HTTPException(status_code=404, detail="Distribuidor no encontrado")

    # Obtener el negocio del distribuidor
    negocio_id = distribuidor.get("negocio_id")
    negocio = await collection_bussiness.find_one({"_id": ObjectId(negocio_id)})

    if not negocio:
        raise HTTPException(status_code=404, detail="El distribuidor no tiene un negocio asignado")

    # Verificar que el usuario autenticado pertenece a ese negocio
    if user["rol"] != "admin" and user["email"] != negocio.get("correo_electronico"):
        raise HTTPException(status_code=403, detail="No tienes permiso para ver estos embajadores")

    # 🔍 Detectar si distribuidor_id está almacenado como ObjectId o string
    embajadores = await collection.find({"distribuidor_id": distribuidor_id}).to_list(length=100)

    if not embajadores:  # Si no encontró, probar con ObjectId
        embajadores = await collection.find({"distribuidor_id": ObjectId(distribuidor_id)}).to_list(length=100)

    # Convertir ObjectId a string en la respuesta
    for embajador in embajadores:
        embajador["_id"] = str(embajador["_id"])
        embajador["distribuidor_id"] = str(embajador["distribuidor_id"])

    return embajadores

# ENDPOINT PARA PARA MOSTRAR LOS EMBAJADORES POR DISTRIBUIDOR
@app.get("/embajadores", response_model=list)
async def obtener_embajadores(
    current_user: dict = Depends(get_current_user)
):
    # Verificar que el usuario autenticado sea un distribuidor
    if current_user["rol"] != "Distribuidor":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo los distribuidores pueden ver sus embajadores"
        )

    # Buscar el distribuidor en la base de datos
    distribuidor = await collection_distribuidor.find_one({"correo_electronico": current_user["email"]})
    if not distribuidor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="El distribuidor autenticado no existe en la base de datos"
        )

    distribuidor_id_obj = distribuidor["_id"]  # Usar directamente el ObjectId

    # Buscar los embajadores asociados a este distribuidor
    embajadores = await collection.find({"distribuidor_id": distribuidor_id_obj}).to_list(length=None)

    if not embajadores:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No se encontraron embajadores para este distribuidor"
        )

    # Convertir ObjectId a string para evitar errores en la respuesta JSON
    for embajador in embajadores:
        embajador["_id"] = str(embajador["_id"])
        embajador["distribuidor_id"] = str(embajador["distribuidor_id"])

    return embajadores

# ENDPOINT PARA OBTENER LOS CLIENTES Y MOSTRAR EN EL NEGOCIO
@app.get("/negocios/clientes", response_model=List[dict])
async def obtener_clientes(current_user: dict = Depends(get_current_user)):
    print(f"🔑 Usuario autenticado: {current_user}")  # Depuración

    # 🔒 Verificar si el usuario tiene rol de negocio
    if current_user["rol"] != "Negocio":
        raise HTTPException(status_code=403, detail="Acceso denegado")

    try:
        # 🔹 Buscar el negocio usando "correo_electronico"
        negocio = await collection_bussiness.find_one({"correo_electronico": current_user["email"]})
        print(f"🏢 Negocio encontrado: {negocio}")  # Depuración
        if not negocio:
            raise HTTPException(status_code=404, detail="Negocio no encontrado")

        negocio_id = str(negocio["_id"])  # Convertir ObjectId a string

        # 🔹 Obtener distribuidores del negocio
        distribuidores_cursor = collection_distribuidor.find({"negocio_id": negocio_id}, {"_id": 1})
        distribuidores = await distribuidores_cursor.to_list(length=None)
        print(f"📦 Distribuidores encontrados: {distribuidores}")  # Depuración
        if not distribuidores:
            return []

        # Extraer IDs de distribuidores
        distribuidor_ids = [str(d["_id"]) for d in distribuidores]

        # 🔹 Obtener embajadores de los distribuidores (CORREGIDO)
        embajadores_cursor = collection.find(
            {"distribuidor_id": {"$in": [ObjectId(d_id) for d_id in distribuidor_ids]}}, 
            {"_id": 1, "email": 1}
        )
        embajadores = await embajadores_cursor.to_list(length=None)
        print(f"🧑‍💼 Embajadores encontrados: {embajadores}")  # Depuración
        if not embajadores:
            return []

        # Extraer emails de embajadores (los clientes los referencian por email)
        embajador_emails = [e["email"] for e in embajadores]

        # 🔹 Obtener clientes referidos por esos embajadores
        clientes_cursor = collection_client.find({"ref": {"$in": embajador_emails}})
        clientes = await clientes_cursor.to_list(length=None)
        print(f"👥 Clientes encontrados: {clientes}")  # Depuración

        return [
            {
                "id": str(cliente["_id"]),
                "nombre": cliente["nombre"],
                "correo_electronico": cliente["correo_electronico"],
                "telefono": cliente["telefono"],
                "referido_por": cliente["ref"]
            }
            for cliente in clientes
        ]

    except Exception as e:
        print(f"❌ Error: {e}")  # Depuración
        raise HTTPException(status_code=500, detail=str(e))

# ENDPOINT PARA OBTENER PEDIDOS POR NEGOCIO Y DISTRIBUIDOR
@app.get("/pedidos", status_code=status.HTTP_200_OK)
async def obtener_pedidos(current_user: dict = Depends(get_current_user)):
    """
    Obtiene los pedidos asociados a un negocio o distribuidor.
    """
    # Validar que el usuario sea un Negocio o un Distribuidor
    if current_user["rol"] not in ["Negocio", "Distribuidor"]:
        raise HTTPException(status_code=403, detail="No autorizado para ver pedidos")

    print("📢 Email autenticado:", current_user["email"])
    print("📢 Rol autenticado:", current_user["rol"])

    # Buscar el usuario en la base de datos con `correo_electronico`
    if current_user["rol"] == "Negocio":
        user = await collection_bussiness.find_one({"correo_electronico": current_user["email"]})
    else:  # Si es distribuidor
        user = await collection_distribuidor.find_one({"correo_electronico": current_user["email"]})

    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado en la base de datos")

    usuario_id = str(user["_id"])  # Convertir a string
    print("📢 Usuario encontrado en la base de datos:", usuario_id)

    # 🔥 Ajustar la consulta de embajadores para que funcione con ObjectId
    try:
        embajadores_cursor = collection.find(
            {"$or": [
                {"negocio_id": usuario_id}, 
                {"distribuidor_id": ObjectId(usuario_id)}  # <- Asegurar que se compara correctamente
            ]}
        )
        embajadores = await embajadores_cursor.to_list(None)
    except Exception as e:
        print("🚨 Error obteniendo embajadores:", str(e))
        embajadores = []

    # Extraer los correos (ref) de los embajadores asociados
    embajador_refs = [emb["email"] for emb in embajadores]
    print("📢 Embajadores asociados:", embajador_refs)

    # Si no hay embajadores, retornar una lista vacía
    if not embajador_refs:
        print("📢 No hay embajadores asociados.")
        return []

    # Buscar pedidos que tengan un ref que coincida con los embajadores asociados
    pedidos_cursor = collection_pedidos.find({"ref": {"$in": embajador_refs}})
    pedidos = await pedidos_cursor.to_list(None)

    # Convertir `_id` y `transaction_id` a string
    for pedido in pedidos:
        pedido["_id"] = str(pedido["_id"])
        if "transaction_id" in pedido:
            pedido["transaction_id"] = str(pedido["transaction_id"])

    print("📢 Total de pedidos encontrados:", len(pedidos))
    return pedidos

# ENDPOINT PARA OBTENER LOS CLIENTES DE LA RED DEL NEGOCIO
@app.get("/clients-orders")
async def get_clients_orders():
    """
    Obtiene la lista de clientes con sus datos y sus pedidos.
    """
    clients_cursor = collection_client.find({}, {
        "_id": 1,
        "nombre": 1,
        "correo_electronico": 1,
        "telefono": 1,
        "ref": 1
    })
    
    clients = await clients_cursor.to_list(length=None)

    formatted_clients = []
    
    for client in clients:
        client_email = client.get("correo_electronico", "")

        # Contar pedidos y calcular total gastado
        total_orders = await collection_pedidos.count_documents({"correo_electronico": client_email})
        total_spent_pipeline = [
            {"$match": {"correo_electronico": client_email}},
            {"$group": {"_id": None, "total": {"$sum": "$total"}}}
        ]
        total_spent_result = await collection_pedidos.aggregate(total_spent_pipeline).to_list(length=1)
        total_spent = total_spent_result[0]["total"] if total_spent_result else 0

        formatted_clients.append({
            "id": str(client["_id"]),
            "nombre": client.get("nombre", "Desconocido"),
            "correo_electronico": client_email,
            "telefono": client.get("telefono", "Sin número"),
            "ref": client.get("ref", "No asignado"),
            "total_orders": total_orders,
            "total_spent": total_spent
        })

    return {"clients": formatted_clients}

# ENDPOINT PARA OBTENER LOS PEDIDOS CON EL ENDPOINT ANTERIOR O CLIENTS 
@app.get("/orders/{email}", response_model=dict)
async def get_orders(email: str):
    """
    Obtiene los pedidos de un cliente específico usando su correo electrónico.
    """
    try:
        orders_cursor = collection_pedidos.find(
            {"correo_electronico": email}, 
            {"_id": 1, "productos": 1, "total": 1, "status": 1, "date_created": 1, "transaction_id": 1}
        )
        orders = await orders_cursor.to_list(length=None)

        if not orders:
            raise HTTPException(status_code=404, detail="No se encontraron pedidos para este cliente.")

        formatted_orders = [
            {
                "id": str(order["_id"]),  # Convertir ObjectId a string
                "products": order.get("productos", []),
                "total": order.get("total", 0),
                "status": order.get("status", "pending"),  # Valor por defecto si es null
                "date": order.get("date_created") or "Fecha no disponible",  # Manejar null
                "transaction_id": order.get("transaction_id", "N/A"),  # Manejar null
            }
            for order in orders
        ]

        return {"orders": formatted_orders}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener pedidos: {str(e)}")
    
    
    