import discord 
from discord.ext import commands 
import requests 
import mySecrets 
import json 
import os 
from datetime import datetime

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix='$', intents=intents)

GASTOS_FILE = 'gastos.json'

# --- NUEVO: Diccionario de categorías ---
CATEGORIAS_MAP = {
    "Comida": ["restaurante", "tacos", "comida", "snack", "bebida", "cafetería", "almuerzo", "cena", "desayuno"],
    "Entretenimiento": ["cine", "netflix", "spotify", "juego", "bar", "concierto", "fiesta"],
    "Transporte": ["gasolina", "uber", "camión", "metro", "estacionamiento", "taxi", "pasaje"],
    "Compras": ["ropa", "super", "amazon", "mercado", "zapatos", "maquillaje", "tienda"],
    "Salud": ["farmacia", "doctor", "gimnasio", "dentista", "medicina", "hospital"],
    "Educación": ["curso", "libro", "universidad", "escuela", "clase"],
    "Otros": []
}

def clasificar_categoria(nombre_categoria: str) -> str:
    """Detecta la categoría general según las palabras clave."""
    nombre_categoria = nombre_categoria.lower()
    for categoria_general, palabras in CATEGORIAS_MAP.items():
        for palabra in palabras:
            if palabra in nombre_categoria:
                return categoria_general
    return "Otros"

def cargar_gastos():
    if os.path.exists(GASTOS_FILE):
        with open(GASTOS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def guardar_gastos(gastos):
    with open(GASTOS_FILE, 'w', encoding='utf-8') as f:
        json.dump(gastos, f, indent=4, ensure_ascii=False)

# --- REGISTRAR GASTO ---
@bot.command()
async def gasto(ctx, monto: float, *, categoria: str):
    user_id = str(ctx.author.id)
    gastos = cargar_gastos()

    if user_id not in gastos:
        gastos[user_id] = {
            'nombre': ctx.author.name,
            'gastos': []
        }

    categoria = categoria.replace('en ', '').strip()
    categoria_general = clasificar_categoria(categoria)

    nuevo_gasto = {
        'monto': monto,
        'categoria': categoria.title(),
        'categoria_general': categoria_general,
        'fecha': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }

    gastos[user_id]['gastos'].append(nuevo_gasto)
    guardar_gastos(gastos)

    embed = discord.Embed(
        title="Gasto Registrado",
        description=f"Gasto guardado en **{categoria_general}**",
        color=discord.Color.green()
    )
    embed.add_field(name="Monto", value=f"${monto:.2f}", inline=True)
    embed.add_field(name="Detalle", value=categoria.title(), inline=True)
    embed.add_field(name="Categoría General", value=categoria_general, inline=True)
    embed.add_field(name="Fecha", value=datetime.now().strftime('%d/%m/%Y'), inline=True)
    embed.set_footer(text=f"Registrado por {ctx.author.name}")

    await ctx.send(embed=embed)

# --- RESUMEN ---
@bot.command()
async def resumen(ctx):
    user_id = str(ctx.author.id)
    gastos = cargar_gastos()

    if user_id not in gastos or not gastos[user_id]['gastos']:
        await ctx.send("No tienes gastos registrados aún. Usa `$gasto <monto> en <categoría>`")
        return

    categorias = {}
    total_general = 0

    for gasto in gastos[user_id]['gastos']:
        cat = gasto.get('categoria_general', 'Otros')
        monto = gasto['monto']
        categorias[cat] = categorias.get(cat, 0) + monto
        total_general += monto

    embed = discord.Embed(
        title="Resumen de Gastos por Categoría",
        description="Tus gastos agrupados:",
        color=discord.Color.blue()
    )

    for categoria, monto in sorted(categorias.items(), key=lambda x: x[1], reverse=True):
        porcentaje = (monto / total_general) * 100
        embed.add_field(
            name=f"🏷 {categoria}",
            value=f"${monto:.2f} ({porcentaje:.1f}%)",
            inline=False
        )

    embed.add_field(name= "Total General", value=f"**${total_general:.2f}**", inline=False)
    embed.set_footer(text=f"Total de gastos: {len(gastos[user_id]['gastos'])}")

    await ctx.send(embed=embed)

# --- HISTORIAL --- #asdasdad
@bot.command()
async def historial(ctx, limite: int = 10):
    user_id = str(ctx.author.id)
    gastos = cargar_gastos()

    if user_id not in gastos or not gastos[user_id]['gastos']:
        await ctx.send("No tienes gastos registrados aún.")
        return

    ultimos_gastos = gastos[user_id]['gastos'][-limite:][::-1]

    embed = discord.Embed(
        title="Historial de Gastos",
        description=f"Últimos {len(ultimos_gastos)} gastos:",
        color=discord.Color.purple()
    )

    for i, gasto in enumerate(ultimos_gastos, 1):
        fecha = datetime.strptime(gasto['fecha'], '%Y-%m-%d %H:%M:%S')
        embed.add_field(
            name=f"{i}. {gasto['categoria']} - ${gasto['monto']:.2f} ({gasto['categoria_general']})",
            value=f"   {fecha.strftime('%d/%m/%Y %H:%M')}",
            inline=False
        )

    await ctx.send(embed=embed)

# --- LIMPIAR GASTOS ---
@bot.command()
async def limpiar_gastos(ctx):
    user_id = str(ctx.author.id)
    gastos = cargar_gastos()

    if user_id in gastos:
        cantidad = len(gastos[user_id]['gastos'])
        del gastos[user_id]
        guardar_gastos(gastos)
        await ctx.send(f"Se eliminaron {cantidad} gastos registrados.")
    else:
        await ctx.send("No tienes gastos para eliminar.")

# --- AYUDA PERSONALIZADA ---
@bot.command()
async def ayuda_gastos(ctx):
    embed = discord.Embed(
        title=" -- Sistema de Gestión de Gastos --",
        description="Comandos disponibles:",
        color=discord.Color.gold()
    )

    embed.add_field(
        name="$gasto <monto> en <categoría>",
        value="Registra un nuevo gasto\nEjemplo: `$gasto 150 en Restaurante`",
        inline=False
    )
    embed.add_field(
        name="$resumen",
        value="Muestra un resumen de tus gastos agrupados por categoría general",
        inline=False
    )
    embed.add_field(
        name="$historial [cantidad]",
        value="Muestra los últimos gastos \nEjemplo: `$historial 20`",
        inline=False
    )
    embed.add_field(
        name="$limpiar_gastos",
        value="Elimina todos tus gastos registrados",
        inline=False
    )

    await ctx.send(embed=embed)

# --- TEST ---
@bot.command()
async def test(ctx, *args):
    respuesta = ' '.join(args)
    await ctx.send(respuesta)

# --- READY EVENT ---
@bot.event
async def on_ready():
    print(f'Bot conectado como {bot.user}')
    print('Sistema de gastos activado')

bot.run(mySecrets.TOKEN)
