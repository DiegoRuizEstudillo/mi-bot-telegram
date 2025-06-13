import csv
import datetime
import schedule
import asyncio
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

TOKEN = "8061146251:AAGoiu1mx1rWsxUb_Ljyy2-qF4jiiQvkUQU"
ADMIN_ID = 5844318309
ARCHIVO_CLIENTES = "clientes.csv"
ARCHIVO_EXPORTACION = "clientes_exportados.txt"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    mensaje = (
        "👋 Hola, este bot te ayudará a recordar los cobros mensuales.\n\n"
        "📌 Comandos disponibles:\n"
        "/agregar Nombre completo YYYY-MM-DD - Agrega un cliente con fecha de instalación\n"
        "/clientes - Lista los clientes registrados\n"
        "/eliminar Nombre - Elimina un cliente por nombre\n"
        "/actualizar Nombre YYYY-MM-DD - Actualiza la fecha de un cliente\n"
        "/exportar - Exporta la lista de clientes a un archivo .txt\n"
        "/ayuda - Muestra este mensaje de ayuda\n"
    )
    await update.message.reply_text(mensaje)

async def ayuda(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await start(update, context)  # Reusar el mensaje de start

async def agregar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 2:
        await update.message.reply_text("⚠ Usa el formato: /agregar Nombre completo YYYY-MM-DD")
        return
    fecha = context.args[-1]
    nombre = " ".join(context.args[:-1])
    try:
        datetime.datetime.strptime(fecha, "%Y-%m-%d")
        with open(ARCHIVO_CLIENTES, "a", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([nombre, fecha])
        await update.message.reply_text(f"✅ Cliente '{nombre}' agregado con fecha {fecha}.")
    except ValueError:
        await update.message.reply_text("⚠ La fecha debe estar en formato YYYY-MM-DD")

async def clientes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        with open(ARCHIVO_CLIENTES, "r") as f:
            reader = csv.reader(f)
            mensaje = "📋 Clientes registrados:\n"
            for row in reader:
                mensaje += f"- {row[0]} (instalado el {row[1]})\n"
        await update.message.reply_text(mensaje)
    except FileNotFoundError:
        await update.message.reply_text("⚠ No hay clientes registrados todavía.")

async def eliminar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("⚠ Usa el formato: /eliminar Nombre")
        return
    nombre_a_eliminar = " ".join(context.args)
    try:
        clientes = []
        eliminado = False
        with open(ARCHIVO_CLIENTES, "r") as f:
            reader = csv.reader(f)
            for row in reader:
                if row[0].lower() != nombre_a_eliminar.lower():
                    clientes.append(row)
                else:
                    eliminado = True
        if eliminado:
            with open(ARCHIVO_CLIENTES, "w", newline="") as f:
                writer = csv.writer(f)
                writer.writerows(clientes)
            await update.message.reply_text(f"🗑 Cliente '{nombre_a_eliminar}' eliminado.")
        else:
            await update.message.reply_text(f"⚠ No se encontró cliente con el nombre '{nombre_a_eliminar}'.")
    except FileNotFoundError:
        await update.message.reply_text("⚠ No hay clientes registrados todavía.")

async def actualizar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 2:
        await update.message.reply_text("⚠ Usa el formato: /actualizar Nombre YYYY-MM-DD")
        return
    nueva_fecha = context.args[-1]
    nombre_a_actualizar = " ".join(context.args[:-1])
    try:
        datetime.datetime.strptime(nueva_fecha, "%Y-%m-%d")
    except ValueError:
        await update.message.reply_text("⚠ La fecha debe estar en formato YYYY-MM-DD")
        return

    try:
        clientes = []
        encontrado = False
        with open(ARCHIVO_CLIENTES, "r") as f:
            reader = csv.reader(f)
            for row in reader:
                if row[0].lower() == nombre_a_actualizar.lower():
                    clientes.append([row[0], nueva_fecha])
                    encontrado = True
                else:
                    clientes.append(row)
        if encontrado:
            with open(ARCHIVO_CLIENTES, "w", newline="") as f:
                writer = csv.writer(f)
                writer.writerows(clientes)
            await update.message.reply_text(f"✅ Fecha del cliente '{nombre_a_actualizar}' actualizada a {nueva_fecha}.")
        else:
            await update.message.reply_text(f"⚠ No se encontró cliente con el nombre '{nombre_a_actualizar}'.")
    except FileNotFoundError:
        await update.message.reply_text("⚠ No hay clientes registrados todavía.")

async def exportar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        with open(ARCHIVO_CLIENTES, "r") as f:
            reader = csv.reader(f)
            with open(ARCHIVO_EXPORTACION, "w") as f2:
                f2.write("Lista de clientes:\n")
                for row in reader:
                    f2.write(f"- {row[0]} (instalado el {row[1]})\n")
        await update.message.reply_text("✅ Archivo exportado correctamente.")
        # También podrías enviar el archivo, pero por simplicidad solo aviso.
        # Para enviar el archivo, usar: await update.message.reply_document(document=open(ARCHIVO_EXPORTACION, 'rb'))
    except FileNotFoundError:
        await update.message.reply_text("⚠ No hay clientes registrados todavía.")

async def revisar_cobros(app):
    hoy = datetime.date.today()
    dia_hoy = hoy.day
    try:
        with open(ARCHIVO_CLIENTES, "r") as f:
            reader = csv.reader(f)
            recordatorios = []
            for row in reader:
                nombre, fecha_str = row
                fecha = datetime.datetime.strptime(fecha_str, "%Y-%m-%d").date()
                if fecha.day == dia_hoy:
                    recordatorios.append(f"💰 Cobro a {nombre} (instalado el {fecha_str})")
            
            # 🟢 Mensaje de verificación
            mensaje = f"🔎 Verificación diaria realizada a las {datetime.datetime.now().strftime('%H:%M:%S')}.\n"
            if recordatorios:
                mensaje += "🔔 Cobros encontrados hoy:\n" + "\n".join(recordatorios)
            else:
                mensaje += "✅ No hay cobros programados para hoy."
            
            await app.bot.send_message(chat_id=ADMIN_ID, text=mensaje)

    except FileNotFoundError:
        await app.bot.send_message(chat_id=ADMIN_ID, text="⚠ No hay archivo de clientes para verificar cobros.")


def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("ayuda", ayuda))
    app.add_handler(CommandHandler("agregar", agregar))
    app.add_handler(CommandHandler("clientes", clientes))
    app.add_handler(CommandHandler("eliminar", eliminar))
    app.add_handler(CommandHandler("actualizar", actualizar))
    app.add_handler(CommandHandler("exportar", exportar))

    schedule.every().day.at("09:40").do(lambda: asyncio.create_task(revisar_cobros(app)))

    print("✅ Bot funcionando. Esperando mensajes y tareas programadas...")

    loop = asyncio.get_event_loop()
    try:
        loop.create_task(app.run_polling())
        loop.create_task(scheduler(app))
        loop.run_forever()
    except KeyboardInterrupt:
        print("Bot detenido por usuario")
    finally:
        loop.run_until_complete(app.shutdown())
        loop.close()

if __name__ == "__main__":
    main()

