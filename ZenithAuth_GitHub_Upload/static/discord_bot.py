# c:\Users\USER\Downloads\ZSAUTH\discord_bot.py
"""
Zenith Auth — Official Discord Bot Integration
Enables Sellers to generate keys, reset HWIDs, manage bans, and query live stats
directly from Discord servers via Zenith Seller API.
"""

import discord
from discord.ext import commands
import requests
import json

# ================= CONFIGURATION =================
# Replace with your Zenith Auth Seller API Endpoint & Private Seller Key
ZENITH_API_URL = "http://localhost:5000/api/seller"
SELLER_KEY = "799b1605a63e8131b94f1d50590e3d18"  # Copy from your Zenith Dashboard -> Seller API tab
BOT_TOKEN = "YOUR_DISCORD_BOT_TOKEN_HERE"
# =================================================

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"[+] Zenith Auth Discord Bot is ONLINE as {bot.user.name} ({bot.user.id})")
    print(f"[*] Connected to Seller API: {ZENITH_API_URL}")
    try:
        synced = await bot.tree.sync()
        print(f"[+] Synced {len(synced)} application slash commands.")
    except Exception as e:
        print(f"[-] Command sync notice: {e}")

# 1. Command: Generate License Key
@bot.tree.command(name="generate", description="Generate a new Zenith Auth license key")
async def generate_key(interaction: discord.Interaction, days: int = 30, level: int = 1, mask: str = "Standard (6x5)", note: str = "Discord Bot"):
    await interaction.response.defer(ephemeral=True)

    try:
        params = {
            "sellerkey": SELLER_KEY,
            "type": "add",
            "amount": 1,
            "expiry": days,
            "level": level,
            "mask": mask,
            "note": note
        }
        res = requests.get(ZENITH_API_URL, params=params, timeout=5).json()

        if res.get("status") == "success":
            key = res.get("key")
            embed = discord.Embed(
                title="🛡️ Zenith Auth — License Created",
                description=f"**License Key:** `{key}`",
                color=0x10b981
            )
            embed.add_field(name="Duration", value=f"{days} Days", inline=True)
            embed.add_field(name="Access Level", value=f"Level {level}", inline=True)
            embed.add_field(name="Mask Format", value=mask, inline=True)
            embed.set_footer(text="Zenith Cloud Sentinel Engine")
            await interaction.followup.send(embed=embed, ephemeral=True)
        else:
            await interaction.followup.send(f"❌ Failed to generate key: {res.get('message')}", ephemeral=True)
    except Exception as e:
        await interaction.followup.send(f"❌ Network error calling Seller API: {e}", ephemeral=True)

# 2. Command: Reset HWID
@bot.tree.command(name="resethwid", description="Reset Hardware ID (HWID) lock for an application user")
async def reset_hwid(interaction: discord.Interaction, username: str):
    await interaction.response.defer(ephemeral=True)

    try:
        params = {
            "sellerkey": SELLER_KEY,
            "type": "resethwid",
            "user": username
        }
        res = requests.get(ZENITH_API_URL, params=params, timeout=5).json()

        if res.get("status") == "success":
            embed = discord.Embed(
                title="🔓 HWID Reset Successful",
                description=f"Hardware lock for **{username}** has been cleared. The user may now login from their new PC.",
                color=0x3b82f6
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
        else:
            await interaction.followup.send(f"❌ Error: {res.get('message')}", ephemeral=True)
    except Exception as e:
        await interaction.followup.send(f"❌ Error: {e}", ephemeral=True)

# 3. Command: Ban User
@bot.tree.command(name="ban", description="Suspend an application user account")
async def ban_user(interaction: discord.Interaction, username: str, reason: str = "Banned via Discord moderation"):
    await interaction.response.defer(ephemeral=True)

    try:
        params = {
            "sellerkey": SELLER_KEY,
            "type": "ban",
            "user": username,
            "reason": reason
        }
        res = requests.get(ZENITH_API_URL, params=params, timeout=5).json()

        if res.get("status") == "success":
            embed = discord.Embed(
                title="⛔ User Suspended",
                description=f"User **{username}** has been banned.\n**Reason:** {reason}",
                color=0xef4444
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
        else:
            await interaction.followup.send(f"❌ Error: {res.get('message')}", ephemeral=True)
    except Exception as e:
        await interaction.followup.send(f"❌ Error: {e}", ephemeral=True)

# 4. Command: App Stats
@bot.tree.command(name="stats", description="View real-time application telemetry and counts")
async def app_stats(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)

    try:
        params = {
            "sellerkey": SELLER_KEY,
            "type": "stats"
        }
        res = requests.get(ZENITH_API_URL, params=params, timeout=5).json()

        if res.get("status") == "success":
            embed = discord.Embed(
                title=f"📊 Zenith Auth Telemetry — {res.get('app_name')}",
                color=0x8b5cf6
            )
            embed.add_field(name="Total Licenses", value=str(res.get("total_licenses")), inline=True)
            embed.add_field(name="Registered Users", value=str(res.get("total_users")), inline=True)
            embed.add_field(name="Active Sessions", value=str(res.get("active_sessions")), inline=True)
            embed.add_field(name="Banned Clients", value=str(res.get("banned_users")), inline=True)
            embed.set_footer(text="Zenith Cloud Sentinel Engine")
            await interaction.followup.send(embed=embed, ephemeral=True)
        else:
            await interaction.followup.send(f"❌ Error: {res.get('message')}", ephemeral=True)
    except Exception as e:
        await interaction.followup.send(f"❌ Error: {e}", ephemeral=True)

if __name__ == "__main__":
    if BOT_TOKEN == "YOUR_DISCORD_BOT_TOKEN_HERE":
        print("=" * 60)
        print("[!] Please set your BOT_TOKEN inside discord_bot.py to run the Discord Bot.")
        print(f"[*] Seller API Endpoint is active at: {ZENITH_API_URL}?sellerkey={SELLER_KEY}")
        print("=" * 60)
    else:
        bot.run(BOT_TOKEN)
