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

def cargar_gastos():
    if os.path.exists(GASTOS_FILE):
        with open(GASTOS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def guardar_gastos(gastos):
    with open(GASTOS_FILE, 'w', encoding='utf-8') as f:
        json.dump(gastos, f, indent=4, ensure_ascii=False)

@bot.command()
async def gasto(ctx, monto: float, *, categoria: str): #!  gastos - Ejemplo: $gasto 150 en Restaurante
  
    user_id = str(ctx.author.id)
    gastos = cargar_gastos()
    
    # Crear entrada del usuario si no existe
    if user_id not in gastos:
        gastos[user_id] = {
            'nombre': ctx.author.name,
            'gastos': []
        }
    
    # Limpiar la palabra "en" si viene en la categoría
    categoria = categoria.replace('en ', '').strip()
    
    # Registrar el gasto
    nuevo_gasto = {
        'monto': monto,
        'categoria': categoria.title(),
        'fecha': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }
    
    gastos[user_id]['gastos'].append(nuevo_gasto)
    guardar_gastos(gastos)
    
    # Respuesta con embed bonito
    embed = discord.Embed(
        title="✅ Gasto Registrado",
        description=f"Se ha registrado tu gasto correctamente",
        color=discord.Color.green()
    )
    embed.add_field(name="💵 Monto", value=f"${monto:.2f}", inline=True)
    embed.add_field(name="📁 Categoría", value=categoria.title(), inline=True)
    embed.add_field(name="📅 Fecha", value=datetime.now().strftime('%d/%m/%Y'), inline=True)
    embed.set_footer(text=f"Registrado por {ctx.author.name}")
    
    await ctx.send(embed=embed)

@bot.command()
async def resumen(ctx): #! Resumen

    user_id = str(ctx.author.id)
    gastos = cargar_gastos()
    
    if user_id not in gastos or not gastos[user_id]['gastos']:
        await ctx.send("No tienes gastos registrados aún. Usa `$gasto <monto> en <categoría>`")
        return
    
    # Calcular totales por categoría
    categorias = {}
    total_general = 0
    
    for gasto in gastos[user_id]['gastos']:
        cat = gasto['categoria']
        monto = gasto['monto']
        
        if cat not in categorias:
            categorias[cat] = 0
        categorias[cat] += monto
        total_general += monto
    
    # Crear embed
    embed = discord.Embed(
        title="📊 Resumen de Gastos",
        description=f"Tus gastos hasta ahora:",
        color=discord.Color.blue()
    )
    
    # Agregar categorías
    for categoria, monto in sorted(categorias.items(), key=lambda x: x[1], reverse=True):
        porcentaje = (monto / total_general) * 100
        embed.add_field(
            name=f"📁 {categoria}", 
            value=f"${monto:.2f} ({porcentaje:.1f}%)", 
            inline=False
        )
    
    embed.add_field(name="$ Total General", value=f"**${total_general:.2f}**", inline=False)
    embed.set_footer(text=f"Total de gastos: {len(gastos[user_id]['gastos'])}")
    
    await ctx.send(embed=embed)

@bot.command()
async def historial(ctx, limite: int = 10): #! Historial - Ejemplo: $historial 20

    user_id = str(ctx.author.id)
    gastos = cargar_gastos()
    
    if user_id not in gastos or not gastos[user_id]['gastos']:
        await ctx.send("No tienes gastos registrados aún.")
        return
    
    ultimos_gastos = gastos[user_id]['gastos'][-limite:][::-1]
    
    embed = discord.Embed(
        title="📜 Historial de Gastos",
        description=f"Últimos {len(ultimos_gastos)} gastos:",
        color=discord.Color.purple()
    )
    
    for i, gasto in enumerate(ultimos_gastos, 1):
        fecha = datetime.strptime(gasto['fecha'], '%Y-%m-%d %H:%M:%S')
        embed.add_field(
            name=f"{i}. {gasto['categoria']} - ${gasto['monto']:.2f}",
            value=f"   {fecha.strftime('%d/%m/%Y %H:%M')}",
            inline=False
        )
    
    await ctx.send(embed=embed)

@bot.command()
async def limpiar_gastos(ctx): #! Limpiar gastos
 
    user_id = str(ctx.author.id)
    gastos = cargar_gastos()
    
    if user_id in gastos:
        cantidad = len(gastos[user_id]['gastos'])
        del gastos[user_id]
        guardar_gastos(gastos)
        
        await ctx.send(f"Se eliminaron {cantidad} gastos registrados.")
    else:
        await ctx.send("No tienes gastos para eliminar.")

# Comando de ayuda personalizado
@bot.command()
async def ayuda_gastos(ctx): #! Ayuda gastos

    embed = discord.Embed(
        title="💰 Sistema de Gestión de Gastos",
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
        value="Muestra un resumen de tus gastos por categoría",
        inline=False
    )
    embed.add_field(
        name="$historial [cantidad]",
        value="Muestra los últimos gastos (por defecto 10)\nEjemplo: `$historial 20`",
        inline=False
    )
    embed.add_field(
        name="$limpiar_gastos",
        value="Elimina todos tus gastos registrados",
        inline=False
    )
    
    await ctx.send(embed=embed)

@bot.command()
async def test(ctx, *args): #! Test
    respuesta = ' '.join(args)
    await ctx.send(respuesta)

@bot.event
async def on_ready():
    print(f'Bot conectado como {bot.user}')
    print(f'Sistema de gastos activado')
    #print()

bot.run(mySecrets.TOKEN)