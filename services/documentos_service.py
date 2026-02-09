import os
import re
import os
import httpx
from PySide6.QtWidgets import QFileDialog
from services.supabase_client import supabase


def normalizar_nombre(nombre):
    nombre = nombre.lower()
    nombre = re.sub(r"\s+", "_", nombre)
    nombre = re.sub(r"[^a-z0-9._-]", "", nombre)
    return nombre


def get_file_name(file_path):
    return os.path.basename(file_path)


def get_file_extension(file_path):
    return os.path.splitext(file_path)[1].replace(".", "").lower()


class DocumentosService:

    BUCKET = "documentos"

    # ---------------- LISTAR ----------------
    def listar_documentos(self, nombre="", modulo="", rol=""):
        query = supabase.table("documentos").select("*")

        if nombre:
            query = query.ilike("nombre", f"%{nombre}%")

        if modulo:
            query = query.eq("modulo", modulo)

        if rol == "usuario":
            query = query.eq("modulo", "ventas")

        res = query.order("creado_en", desc=True).execute()
        return res.data or []

    # ---------------- SUBIR ----------------
    def subir_documento(self, file_path, modulo):
        # Nombre original (para mostrar)
        nombre_original = get_file_name(file_path)

        # Nombre seguro (para storage)
        nombre_storage = normalizar_nombre(nombre_original)

        tipo = get_file_extension(file_path)

        # Ruta en el bucket
        ruta = f"{modulo}/{nombre_storage}"

        # Subir archivo al bucket
        with open(file_path, "rb") as f:
            supabase.storage.from_(self.BUCKET).upload(
                ruta,
                f,
                file_options={
                    "content-type": "application/octet-stream"
                }
            )

        # Usuario autenticado
        session = supabase.auth.get_session()
        user_id = session.user.id if session else None

        # Guardar metadata en la tabla
        supabase.table("documentos").insert({
            "nombre": nombre_original,   # nombre legible
            "ruta": ruta,                # ruta real en storage
            "tipo": tipo,
            "modulo": modulo,
            "creado_por": user_id
        }).execute()


    # ---------------- DESCARGAR ----------------
    def descargar_documento(self, ruta, nombre):
        # 1️⃣ Pedir URL firmada
        res = supabase.storage.from_(self.BUCKET).create_signed_url(
            ruta,
            3600
        )

        url = res["signedUrl"]

        # 2️⃣ Elegir dónde guardar
        carpeta = QFileDialog.getExistingDirectory(
            None,
            "Seleccionar carpeta de destino"
        )

        if not carpeta:
            return

        ruta_local = os.path.join(carpeta, nombre)

        # 3️⃣ Descargar sin navegador
        with httpx.stream("GET", url) as response:
            response.raise_for_status()
            with open(ruta_local, "wb") as f:
                for chunk in response.iter_bytes():
                    f.write(chunk)

        # 4️⃣ Abrir archivo (opcional)
        os.startfile(ruta_local)


    def eliminar_documento(self, doc, rol):
        if rol not in ("admin", "superusuario"):
            raise Exception("No tienes permisos para eliminar documentos")

        ruta = doc["ruta"]
        doc_id = doc["id"]

        # 1️⃣ borrar archivo del storage
        supabase.storage.from_(self.BUCKET).remove([ruta])

        # 2️⃣ borrar registro DB
        supabase.table("documentos").delete().eq("id", doc_id).execute()


