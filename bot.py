import csv
import datetime
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

TOKEN = "8061146251:AAGoiu1mx1rWsxUb_Ljyy2-qF4jiiQvkUQU"
ARCHIVO_TAREAS = "tareas.csv"

# Prioridades válidas
PRIORIDADES = ["baja", "media", "alta"]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    mensaje = (
        "👋 Hola, este bot te ayudará a gestionar tus tareas.\n\n"
        "📌 Comandos disponibles:\n"
        "/agregar TAREA | PRIORIDAD | YYYY-MM-DD | ETIQUETA,CATEGORIA - Agrega una tarea\n"
        "/listar - Lista todas las tareas\n"
        "/eliminar ID - Elimina una tarea por su ID\n"
        "/actualizar ID | campo | nuevo_valor - Actualiza un campo (tarea, prioridad, fecha, etiquetas)\n"
        "/ayuda - Muestra este mensaje\n\n"
        "Ejemplo para agregar:\n"
        "/agregar Comprar libro | alta | 2025-06-15 | lectura,personal"
    )
    await update.message.reply_text(mensaje)

async def ayuda(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await start(update, context)

def cargar_tareas():
    tareas = []
    try:
        with open(ARCHIVO_TAREAS, "r", newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            tareas = list(reader)
    except FileNotFoundError:
        pass
    return tareas

def guardar_tareas(tareas):
    with open(ARCHIVO_TAREAS, "w", newline="", encoding="utf-8") as f:
        fieldnames = ["id", "tarea", "prioridad", "fecha", "etiquetas"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(tareas)

def generar_id(tareas):
    if not tareas:
        return "1"
    ids = [int(t["id"]) for t in tareas]
    return str(max(ids) + 1)

async def agregar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    texto = update.message.text.partition(" ")[2].strip()
    partes = [p.strip() for p in texto.split("|")]
    if len(partes) != 4:
        await update.message.reply_text("⚠ Usa el formato:\n/agregar TAREA | PRIORIDAD | YYYY-MM-DD | ETIQUETA,CATEGORIA")
        return

    tarea, prioridad, fecha_str, etiquetas = partes

    if prioridad.lower() not in PRIORIDADES:
        await update.message.reply_text(f"⚠ Prioridad inválida. Usa: {', '.join(PRIORIDADES)}")
        return

    try:
        fecha = datetime.datetime.strptime(fecha_str, "%Y-%m-%d").date()
    except ValueError:
        await update.message.reply_text("⚠ La fecha debe estar en formato YYYY-MM-DD")
        return

    etiquetas = etiquetas.replace(" ", "")
    etiquetas_lista = etiquetas.split(",") if etiquetas else []

    tareas = cargar_tareas()
    nueva_tarea = {
        "id": generar_id(tareas),
        "tarea": tarea,
        "prioridad": prioridad.lower(),
        "fecha": fecha_str,
        "etiquetas": ",".join(etiquetas_lista),
    }
    tareas.append(nueva_tarea)
    guardar_tareas(tareas)

    await update.message.reply_text(f"✅ Tarea agregada con ID {nueva_tarea['id']}.")

async def listar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tareas = cargar_tareas()
    if not tareas:
        await update.message.reply_text("⚠ No tienes tareas registradas.")
        return

    mensaje = "📋 Lista de tareas:\n"
    for t in tareas:
        mensaje += (
            f"ID: {t['id']} | {t['tarea']} | Prioridad: {t['prioridad']} | "
            f"Fecha límite: {t['fecha']} | Etiquetas: {t['etiquetas']}\n"
        )
    await update.message.reply_text(mensaje)

async def eliminar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("⚠ Usa el formato: /eliminar ID")
        return
    id_eliminar = context.args[0]
    tareas = cargar_tareas()
    nuevas_tareas = [t for t in tareas if t["id"] != id_eliminar]
    if len(nuevas_tareas) == len(tareas):
        await update.message.reply_text(f"⚠ No se encontró tarea con ID {id_eliminar}.")
        return
    guardar_tareas(nuevas_tareas)
    await update.message.reply_text(f"🗑 Tarea con ID {id_eliminar} eliminada.")

async def actualizar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    texto = update.message.text.partition(" ")[2].strip()
    partes = [p.strip() for p in texto.split("|")]
    if len(partes) != 3:
        await update.message.reply_text(
            "⚠ Usa el formato: /actualizar ID | campo | nuevo_valor\n"
            "Campos válidos: tarea, prioridad, fecha, etiquetas"
        )
        return

    id_tarea, campo, nuevo_valor = partes
    campo = campo.lower()
    if campo not in ["tarea", "prioridad", "fecha", "etiquetas"]:
        await update.message.reply_text("⚠ Campo inválido. Usa: tarea, prioridad, fecha, etiquetas")
        return

    tareas = cargar_tareas()
    tarea_encontrada = False

    for t in tareas:
        if t["id"] == id_tarea:
            tarea_encontrada = True
            if campo == "prioridad":
                if nuevo_valor.lower() not in PRIORIDADES:
                    await update.message.reply_text(f"⚠ Prioridad inválida. Usa: {', '.join(PRIORIDADES)}")
                    return
                t["prioridad"] = nuevo_valor.lower()
            elif campo == "fecha":
                try:
                    datetime.datetime.strptime(nuevo_valor, "%Y-%m-%d")
                    t["fecha"] = nuevo_valor
                except ValueError:
                    await update.message.reply_text("⚠ La fecha debe estar en formato YYYY-MM-DD")
                    return
            elif campo == "etiquetas":
                nuevo_valor = nuevo_valor.replace(" ", "")
                t["etiquetas"] = nuevo_valor
            else:
                t["tarea"] = nuevo_valor
            break

    if not tarea_encontrada:
        await update.message.reply_text(f"⚠ No se encontró tarea con ID {id_tarea}.")
        return

    guardar_tareas(tareas)
    await update.message.reply_text(f"✅ Tarea con ID {id_tarea} actualizada.")

import asyncio

async def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("ayuda", ayuda))
    app.add_handler(CommandHandler("agregar", agregar))
    app.add_handler(CommandHandler("clientes", clientes))
    app.add_handler(CommandHandler("eliminar", eliminar))
    app.add_handler(CommandHandler("actualizar", actualizar))
    app.add_handler(CommandHandler("exportar", exportar))

    # Programar la tarea diaria
    schedule.every().day.at("16:10").do(lambda: asyncio.create_task(revisar_cobros(app)))

    # Lanzar scheduler y bot al mismo tiempo
    asyncio.create_task(scheduler(app))
    print("✅ Bot funcionando. Esperando mensajes y tareas programadas...")
    await app.run_polling()

if __name__ == "__main__":
    asyncio.run(main())

