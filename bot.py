import discord
from discord.ext import commands
from discord import app_commands
import json
import os
from datetime import datetime, timedelta
import random
import asyncio
import yt_dlp
import time
import re

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.presences = True
intents.voice_states = True

activity = discord.Activity(type=discord.ActivityType.watching, name="over the server | ,help")
bot = commands.Bot(command_prefix=',', intents=intents, help_command=None, activity=activity, status=discord.Status.online)

DATA_FILE = 'bot_data.json'

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r') as f:
            return json.load(f)
    return {'users': {}, 'guilds': {}, 'username_history': [], 'vanity_history': []}

def save_data(data):
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=2)

data = load_data()
# Ensure global history lists exist
if 'username_history' not in data:
    data['username_history'] = []
if 'vanity_history' not in data:
    data['vanity_history'] = []

# Cooldown tracking for snipe and clearsnipes
snipe_cooldowns = {}  # {user_id: timestamp}
reaction_snipes = {}  # {guild_id: [(emoji, user_name, timestamp), ...]}
rs_cooldowns = {}  # {user_id: timestamp}

def get_user_data(user_id):
    uid = str(user_id)
    if uid not in data['users']:
        data['users'][uid] = {
            'balance': 0,
            'bank': 0,
            'xp': 0,
            'level': 1,
            'daily_last': None,
            'work_last': None,
            'inventory': {},
            'vc_time': 0,
            'vc_join_time': None,
            'message_count': 0,
            'afk': False,
            'afk_status': 'AFK',
            'afk_time': None,
            'jail_roles': []
        }
    # Ensure vc_time fields exist for existing users
    if 'vc_time' not in data['users'][uid]:
        data['users'][uid]['vc_time'] = 0
    if 'vc_join_time' not in data['users'][uid]:
        data['users'][uid]['vc_join_time'] = None
    if 'message_count' not in data['users'][uid]:
        data['users'][uid]['message_count'] = 0
    if 'afk' not in data['users'][uid]:
        data['users'][uid]['afk'] = False
    if 'afk_status' not in data['users'][uid]:
        data['users'][uid]['afk_status'] = 'AFK'
    if 'afk_time' not in data['users'][uid]:
        data['users'][uid]['afk_time'] = None
    if 'jail_roles' not in data['users'][uid]:
        data['users'][uid]['jail_roles'] = []
    return data['users'][uid]

def get_guild_data(guild_id):
    gid = str(guild_id)
    if gid not in data['guilds']:
        data['guilds'][gid] = {
            'voicemaster': {
                'enabled': False,
                'setup_complete': False,
                'category_id': None,
                'join_channel_id': None,
                'interface_channel_id': None,
                'temp_category_id': None,
                'temp_channels': {},
                'priv_enabled': False,
                'priv_setup_complete': False,
                'priv_category_id': None,
                'priv_join_channel_id': None,
                'priv_temp_channels': {}
            },
            'snipes': [],
            'autorole': {
                'enabled': False,
                'role_id': None
            },
            'ping_on_join': {
                'enabled': False,
                'channels': []
            },
            'filter': [],
            'spam_filter': {
                'enabled': False,
                'channels': {},
                'threshold': 5,
                'timeframe': 5000
            },
            'logs': {},
            'welcome': {},
            'vanity': {
                'enabled': False,
                'substring': None,
                'award_channel_id': None,
                'log_channel_id': None,
                'award_message': 'Congratulations! You have vanity!',
                'roles': []
            },
            'antinuke': {
                'enabled': False,
                'admins': [],
                'whitelist': [],
                'role_deletion': False,
                'channel_deletion': False,
                'emoji_deletion': False,
                'mass_member_ban': False,
                'mass_member_kick': False,
                'webhook_creation': False,
                'vanity_protection': False,
                'watch_permissions_grant': [],
                'deny_bot_joins': False,
                'invite_links': False
            },
            'username_history': [],
            'vanity_history': [],
            'giveaways': {},
            'reaction_roles': {},
            'jail': {
                'enabled': False,
                'role_id': None,
                'channel_id': None
            },
            'antiraid': {
                'enabled': False,
                'raid_state': False,
                'check_avatar': False,
                'check_new_accounts': False,
                'action': 'kick',
                'new_account_days': 7,
                'whitelist': []
            }
        }
    else:
        if 'jail' not in data['guilds'][gid]:
            data['guilds'][gid]['jail'] = {
                'enabled': False,
                'role_id': None,
                'channel_id': None
            }
        if 'antiraid' not in data['guilds'][gid]:
            data['guilds'][gid]['antiraid'] = {
                'enabled': False,
                'raid_state': False,
                'check_avatar': False,
                'check_new_accounts': False,
                'action': 'kick',
                'new_account_days': 7,
                'whitelist': []
            }
        if 'voicemaster' not in data['guilds'][gid]:
            data['guilds'][gid]['voicemaster'] = {
                'enabled': False,
                'setup_complete': False,
                'category_id': None,
                'join_channel_id': None,
                'interface_channel_id': None,
                'temp_category_id': None,
                'temp_channels': {},
                'priv_enabled': False,
                'priv_setup_complete': False,
                'priv_category_id': None,
                'priv_join_channel_id': None,
                'priv_temp_channels': {}
            }
        if 'setup_complete' not in data['guilds'][gid].get('voicemaster', {}):
            data['guilds'][gid]['voicemaster']['setup_complete'] = False
        if 'temp_category_id' not in data['guilds'][gid].get('voicemaster', {}):
            data['guilds'][gid]['voicemaster']['temp_category_id'] = None
        if 'priv_enabled' not in data['guilds'][gid].get('voicemaster', {}):
            data['guilds'][gid]['voicemaster']['priv_enabled'] = False
        if 'priv_setup_complete' not in data['guilds'][gid].get('voicemaster', {}):
            data['guilds'][gid]['voicemaster']['priv_setup_complete'] = False
        if 'priv_category_id' not in data['guilds'][gid].get('voicemaster', {}):
            data['guilds'][gid]['voicemaster']['priv_category_id'] = None
        if 'priv_join_channel_id' not in data['guilds'][gid].get('voicemaster', {}):
            data['guilds'][gid]['voicemaster']['priv_join_channel_id'] = None
        if 'priv_temp_channels' not in data['guilds'][gid].get('voicemaster', {}):
            data['guilds'][gid]['voicemaster']['priv_temp_channels'] = {}
        if 'snipes' not in data['guilds'][gid]:
            data['guilds'][gid]['snipes'] = []
        if 'autorole' not in data['guilds'][gid]:
            data['guilds'][gid]['autorole'] = {
                'enabled': False,
                'role_id': None
            }
        if 'ping_on_join' not in data['guilds'][gid]:
            data['guilds'][gid]['ping_on_join'] = {
                'enabled': False,
                'channels': []
            }
        if 'filter' not in data['guilds'][gid]:
            data['guilds'][gid]['filter'] = []
        if 'spam_filter' not in data['guilds'][gid]:
            data['guilds'][gid]['spam_filter'] = {
                'enabled': False,
                'channels': {},
                'threshold': 5,
                'timeframe': 5000
            }
        if 'logs' not in data['guilds'][gid]:
            data['guilds'][gid]['logs'] = {}
        if 'welcome' not in data['guilds'][gid]:
            data['guilds'][gid]['welcome'] = {}
        if 'vanity' not in data['guilds'][gid]:
            data['guilds'][gid]['vanity'] = {
                'enabled': False,
                'substring': None,
                'award_channel_id': None,
                'log_channel_id': None,
                'award_message': 'Congratulations! You have vanity!',
                'roles': []
            }
        if 'antinuke' not in data['guilds'][gid]:
            data['guilds'][gid]['antinuke'] = {
                'enabled': False,
                'admins': [],
                'whitelist': [],
                'role_deletion': False,
                'channel_deletion': False,
                'emoji_deletion': False,
                'mass_member_ban': False,
                'mass_member_kick': False,
                'webhook_creation': False,
                'vanity_protection': False,
                'watch_permissions_grant': [],
                'deny_bot_joins': False,
                'invite_links': False
            }
    return data['guilds'][gid]

temp_channel_owners = {}
priv_channel_allowed = {}  # {channel_id: [user_ids]}
spam_tracking = {}  # {user_id: {channel_id: [timestamp, timestamp, ...]}}
raid_tracking = {}  # {guild_id: [timestamp, timestamp, ...]} - tracks member joins

@bot.event
async def on_reaction_remove(reaction, user):
    """Track removed reactions for reaction snipe"""
    if user.bot or reaction.message.guild is None:
        return
    
    guild_id = reaction.message.guild.id
    if guild_id not in reaction_snipes:
        reaction_snipes[guild_id] = []
    
    emoji_str = str(reaction.emoji)
    message_content = reaction.message.content or "*No text content*"
    if len(message_content) > 100:
        message_content = message_content[:97] + "..."
    
    reaction_snipes[guild_id].insert(0, {
        'emoji': emoji_str,
        'user': user.name,
        'user_id': user.id,
        'message_content': message_content,
        'message_author': reaction.message.author.name,
        'message_author_id': reaction.message.author.id,
        'timestamp': datetime.now().isoformat()
    })
    
    if len(reaction_snipes[guild_id]) > 20:
        reaction_snipes[guild_id].pop()

@bot.event
async def on_member_join(member):
    """Handle member joins - anti-raid protection"""
    if not member.guild:
        return
    
    guild_data = get_guild_data(member.guild.id)
    ar_data = guild_data['antiraid']
    
    # Check whitelist first
    if member.id in ar_data['whitelist']:
        ar_data['whitelist'].remove(member.id)
        save_data(data)
        return
    
    # Only check if anti-raid is enabled
    if not ar_data['enabled']:
        return
    
    action_taken = False
    reason = ""
    
    # Check if raid mode is active (mass joins detected)
    if ar_data['raid_state']:
        action_taken = True
        reason = "Mass join detected (raid mode)"
    
    # Check for no avatar
    if ar_data['check_avatar'] and member.avatar is None and not member.bot:
        action_taken = True
        reason = "No profile picture"
    
    # Check for new account
    if ar_data['check_new_accounts'] and not member.bot:
        account_age = datetime.now() - member.created_at
        if account_age.days < ar_data['new_account_days']:
            action_taken = True
            reason = f"Account too new ({account_age.days} days old)"
    
    if action_taken:
        try:
            if ar_data['action'] == 'kick':
                await member.kick(reason=f"Anti-Raid: {reason}")
            elif ar_data['action'] == 'ban':
                await member.ban(reason=f"Anti-Raid: {reason}")
        except:
            pass

@bot.event
async def on_ready():
    print(f'{bot.user} is online!')
    bot.add_view(VoiceMasterView())
    
    for guild_id, guild_data in data.get('guilds', {}).items():
        vm_data = guild_data.get('voicemaster', {})
        if vm_data.get('enabled'):
            for channel_id, owner_id in vm_data.get('temp_channels', {}).items():
                temp_channel_owners[int(channel_id)] = owner_id
    print(f'Restored {len(temp_channel_owners)} VoiceMaster channels')
    
    try:
        synced = await bot.tree.sync()
        print(f'Synced {len(synced)} slash commands')
    except Exception as e:
        print(f'Error syncing commands: {e}')
    
    await bot.change_presence(status=discord.Status.online, activity=discord.Activity(type=discord.ActivityType.watching, name="over the server | !help"))

@bot.event
async def on_message(message):
    if message.author.bot:
        return
    
    # Check for spam
    if message.guild:
        guild_data = get_guild_data(message.guild.id)
        spam_filter = guild_data.get('spam_filter', {})
        
        if spam_filter.get('enabled'):
            user_id = message.author.id
            channel_id = message.channel.id
            current_time = time.time() * 1000
            
            if user_id not in spam_tracking:
                spam_tracking[user_id] = {}
            if channel_id not in spam_tracking[user_id]:
                spam_tracking[user_id][channel_id] = []
            
            threshold = spam_filter.get('threshold', 5)
            timeframe = spam_filter.get('timeframe', 5000)
            
            spam_tracking[user_id][channel_id] = [t for t in spam_tracking[user_id][channel_id] if current_time - t < timeframe]
            spam_tracking[user_id][channel_id].append(current_time)
            
            if len(spam_tracking[user_id][channel_id]) > threshold:
                try:
                    await message.delete()
                    return
                except:
                    pass
    
    # Anti-nuke: Check for Discord invite links
    if message.guild:
        guild_data = get_guild_data(message.guild.id)
        antinuke = guild_data.get('antinuke', {})
        
        if antinuke.get('enabled') and antinuke.get('invite_links'):
            # Check for Discord invite links
            invite_pattern = r'(?:https?://)?(?:www\.)?(?:discord\.gg|discordapp\.com/invite|discord\.com/invite)/[\w-]+'
            if re.search(invite_pattern, message.content):
                try:
                    # Delete the message
                    await message.delete()
                    
                    # Timeout user for 1 minute
                    await message.author.timeout(timedelta(minutes=1), reason="Discord invite link posted")
                    
                    # DM the bot owner
                    try:
                        embed = discord.Embed(
                            title="Anti-Nuke: Invite Link Detected",
                            description=f"{message.author.mention} ({message.author.name}) posted a Discord invite link in {message.channel.mention}",
                            color=0x000000
                        )
                        embed.add_field(name="Message Content", value=message.content[:1024], inline=False)
                        embed.add_field(name="Guild", value=f"{message.guild.name} ({message.guild.id})", inline=False)
                        embed.add_field(name="Action Taken", value="Timeout: 1 minute", inline=False)
                        embed.set_thumbnail(url=message.author.display_avatar.url)
                        
                        owner = bot.get_user(message.guild.owner_id)
                        if owner:
                            await owner.send(embed=embed)
                    except:
                        pass
                    
                    return
                except discord.Forbidden:
                    pass
    
    # Check for blacklisted words
    if message.guild:
        guild_data = get_guild_data(message.guild.id)
        filter_words = guild_data['filter']
        
        if filter_words:
            message_lower = message.content.lower()
            for word in filter_words:
                if word.lower() in message_lower:
                    try:
                        await message.delete()
                        return
                    except:
                        pass
        
        # Check for vanity
        vanity = guild_data.get('vanity', {})
        if vanity.get('enabled') and vanity.get('substring'):
            if vanity['substring'].lower() in message.content.lower():
                user_id = message.author.id
                # Award roles
                for role_id in vanity.get('roles', []):
                    role = message.guild.get_role(role_id)
                    if role:
                        try:
                            await message.author.add_roles(role)
                        except:
                            pass
                
                # Send award message
                award_channel_id = vanity.get('award_channel_id')
                if award_channel_id:
                    channel = message.guild.get_channel(award_channel_id)
                    if channel:
                        try:
                            await channel.send(vanity.get('award_message', 'Congratulations!'))
                        except:
                            pass
                
                # Log to log channel
                log_channel_id = vanity.get('log_channel_id')
                if log_channel_id:
                    channel = message.guild.get_channel(log_channel_id)
                    if channel:
                        try:
                            embed = discord.Embed(
                                title="Vanity Detected",
                                description=f"{message.author.mention} has vanity!",
                                color=0xffd700
                            )
                            await channel.send(embed=embed)
                        except:
                            pass
    
    user_data = get_user_data(message.author.id)
    
    # Check if user is AFK and welcome them back
    if user_data.get('afk'):
        afk_time = user_data.get('afk_time')
        if afk_time:
            try:
                afk_start = datetime.fromisoformat(afk_time)
                now = datetime.now()
                time_away = now - afk_start
                total_seconds = int(time_away.total_seconds())
                
                embed = discord.Embed(
                    description=f"🔥 {message.author.mention}: Welcome back, you went away {total_seconds} seconds ago",
                    color=0x2b2d31
                )
                welcome_msg = await message.channel.send(embed=embed)
                
                # Update message every 3 seconds for 30 seconds
                async def update_afk_message():
                    for i in range(10):
                        await asyncio.sleep(3)
                        new_seconds = total_seconds + (i + 1) * 3
                        new_embed = discord.Embed(
                            description=f"🔥 {message.author.mention}: Welcome back, you went away {new_seconds} seconds ago",
                            color=0x2b2d31
                        )
                        try:
                            await welcome_msg.edit(embed=new_embed)
                        except:
                            pass
                    
                    # Delete after updates stop
                    await asyncio.sleep(2)
                    try:
                        await welcome_msg.delete()
                    except:
                        pass
                
                asyncio.create_task(update_afk_message())
            except:
                pass
        
        user_data['afk'] = False
        user_data['afk_time'] = None
    
    user_data['message_count'] = user_data.get('message_count', 0) + 1
    xp_gain = random.randint(15, 25)
    user_data['xp'] += xp_gain
    
    xp_needed = int((user_data['level'] ** 1.5) * 100)
    if user_data['xp'] >= xp_needed:
        user_data['level'] += 1
        user_data['xp'] = 0
        embed = discord.Embed(
            title="Level Up!",
            description=f"{message.author.mention} reached **Level {user_data['level']}**!",
            color=0xe91e63
        )
        await message.channel.send(embed=embed, delete_after=5)
    
    save_data(data)
    await bot.process_commands(message)

def check_vanity_in_activities(activities, substring):
    """Helper function to check if vanity substring exists in activities"""
    if not activities or not substring:
        return False
    for activity in activities:
        # Check custom status
        if isinstance(activity, discord.CustomActivity):
            if activity.name and substring.lower() in activity.name.lower():
                return True
        # Check game/app status
        elif isinstance(activity, discord.Game):
            if activity.name and substring.lower() in activity.name.lower():
                return True
        # Check streaming/watching/listening
        elif hasattr(activity, 'name') and activity.name:
            if substring.lower() in activity.name.lower():
                return True
    return False

@bot.event
async def on_presence_update(before, after):
    """Check for vanity in user status/activity"""
    if after.bot:
        return
    
    # Get all guilds the user is in
    for guild in bot.guilds:
        member = guild.get_member(after.id)
        if member is None:
            continue
        
        guild_data = get_guild_data(guild.id)
        vanity = guild_data.get('vanity', {})
        
        if not vanity.get('enabled') or not vanity.get('substring'):
            continue
        
        substring = vanity['substring']
        
        # Check if vanity was in before and after states
        had_vanity = check_vanity_in_activities(before.activities, substring)
        has_vanity = check_vanity_in_activities(after.activities, substring)
        
        # If they had vanity but don't anymore, remove roles
        if had_vanity and not has_vanity:
            for role_id in vanity.get('roles', []):
                role = guild.get_role(role_id)
                if role and role in member.roles:
                    try:
                        await member.remove_roles(role)
                    except:
                        pass
            
            # Log removal
            log_channel_id = vanity.get('log_channel_id')
            if log_channel_id:
                channel = guild.get_channel(log_channel_id)
                if channel:
                    try:
                        embed = discord.Embed(
                            title="Vanity Removed",
                            description=f"{member.mention} removed vanity from their status!",
                            color=0xff0000
                        )
                        await channel.send(embed=embed)
                    except:
                        pass
        
        # If they have vanity now, add roles
        elif has_vanity:
            # Award roles
            for role_id in vanity.get('roles', []):
                role = guild.get_role(role_id)
                if role:
                    try:
                        if role not in member.roles:
                            await member.add_roles(role)
                    except:
                        pass
            
            # Only send award message if they didn't have vanity before
            if not had_vanity:
                # Send award message
                award_channel_id = vanity.get('award_channel_id')
                if award_channel_id:
                    channel = guild.get_channel(award_channel_id)
                    if channel:
                        try:
                            await channel.send(vanity.get('award_message', 'Congratulations!'))
                        except:
                            pass
                
                # Log to log channel
                log_channel_id = vanity.get('log_channel_id')
                if log_channel_id:
                    channel = guild.get_channel(log_channel_id)
                    if channel:
                        try:
                            embed = discord.Embed(
                                title="Vanity Detected in Status",
                                description=f"{member.mention} has vanity in their status!",
                                color=0xffd700
                            )
                            await channel.send(embed=embed)
                        except:
                            pass

class VoiceMasterView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    async def get_user_channel(self, interaction):
        if not interaction.user.voice or not interaction.user.voice.channel:
            await interaction.response.send_message("You must be in a voice channel!", ephemeral=True)
            return None
        channel = interaction.user.voice.channel
        if channel.id not in temp_channel_owners:
            await interaction.response.send_message("This is not a VoiceMaster channel!", ephemeral=True)
            return None
        return channel

    async def check_owner(self, interaction, channel):
        owner_id = temp_channel_owners.get(channel.id)
        if owner_id != interaction.user.id:
            await interaction.response.send_message("You don't own this channel!", ephemeral=True)
            return False
        return True

    @discord.ui.button(emoji="<:icon:1445102255715123301>", style=discord.ButtonStyle.secondary, custom_id="vm_lock", row=0)
    async def lock_channel(self, interaction: discord.Interaction, button: discord.ui.Button):
        channel = await self.get_user_channel(interaction)
        if not channel or not interaction.guild or not await self.check_owner(interaction, channel):
            return
        await channel.set_permissions(interaction.guild.default_role, connect=False)
        await channel.set_permissions(interaction.user, connect=True, view_channel=True)
        await interaction.response.send_message(f"Locked {channel.name}", ephemeral=True)

    @discord.ui.button(emoji="<:icon1:1445102254746112143>", style=discord.ButtonStyle.secondary, custom_id="vm_unlock", row=0)
    async def unlock_channel(self, interaction: discord.Interaction, button: discord.ui.Button):
        channel = await self.get_user_channel(interaction)
        if not channel or not interaction.guild or not await self.check_owner(interaction, channel):
            return
        await channel.set_permissions(interaction.guild.default_role, connect=None)
        await interaction.response.send_message(f"Unlocked {channel.name}", ephemeral=True)

    @discord.ui.button(emoji="<:icon2:1445102253840138282>", style=discord.ButtonStyle.secondary, custom_id="vm_hide", row=0)
    async def hide_channel(self, interaction: discord.Interaction, button: discord.ui.Button):
        channel = await self.get_user_channel(interaction)
        if not channel or not interaction.guild or not await self.check_owner(interaction, channel):
            return
        await channel.set_permissions(interaction.guild.default_role, view_channel=False)
        await channel.set_permissions(interaction.user, connect=True, view_channel=True)
        await interaction.response.send_message(f"Hidden {channel.name}", ephemeral=True)

    @discord.ui.button(emoji="<:icon3:1445102252959469629>", style=discord.ButtonStyle.secondary, custom_id="vm_reveal", row=0)
    async def reveal_channel(self, interaction: discord.Interaction, button: discord.ui.Button):
        channel = await self.get_user_channel(interaction)
        if not channel or not interaction.guild or not await self.check_owner(interaction, channel):
            return
        await channel.set_permissions(interaction.guild.default_role, view_channel=None)
        await interaction.response.send_message(f"Revealed {channel.name}", ephemeral=True)

    @discord.ui.button(emoji="<:icon4:1445102252091117700>", style=discord.ButtonStyle.secondary, custom_id="vm_disconnect", row=0)
    async def disconnect_member(self, interaction: discord.Interaction, button: discord.ui.Button):
        channel = await self.get_user_channel(interaction)
        if not channel or not await self.check_owner(interaction, channel):
            return
        members = [m for m in channel.members if m.id != interaction.user.id]
        if not members:
            await interaction.response.send_message("No other members to disconnect!", ephemeral=True)
            return
        options = [discord.SelectOption(label=m.display_name, value=str(m.id)) for m in members[:25]]
        
        class DisconnectSelect(discord.ui.View):
            def __init__(self, channel):
                super().__init__(timeout=60)
                self.channel = channel
            
            @discord.ui.select(placeholder="Select member to disconnect", options=options)
            async def select_callback(self, select_interaction: discord.Interaction, select: discord.ui.Select):
                member_id = int(select.values[0])
                if interaction.guild is None:
                    await select_interaction.response.send_message("Guild not found!", ephemeral=True)
                    return
                member = interaction.guild.get_member(member_id)
                if member and member.voice:
                    await member.move_to(None)
                    await select_interaction.response.send_message(f"Disconnected {member.display_name}", ephemeral=True)
                else:
                    await select_interaction.response.send_message("Member not found or not in voice", ephemeral=True)
        
        await interaction.response.send_message("Select a member:", view=DisconnectSelect(channel), ephemeral=True)

    @discord.ui.button(emoji="<:icon5:1445102250900066438>", style=discord.ButtonStyle.secondary, custom_id="vm_claim", row=1)
    async def claim_channel(self, interaction: discord.Interaction, button: discord.ui.Button):
        channel = await self.get_user_channel(interaction)
        if not channel or not interaction.guild:
            return
        owner_id = temp_channel_owners.get(channel.id)
        owner = interaction.guild.get_member(owner_id) if owner_id else None
        if owner and owner.voice and owner.voice.channel == channel:
            await interaction.response.send_message("The owner is still in the channel!", ephemeral=True)
            return
        if owner:
            try:
                await channel.set_permissions(owner, overwrite=None)
            except:
                pass
        temp_channel_owners[channel.id] = interaction.user.id
        guild_data = get_guild_data(interaction.guild.id)
        guild_data['voicemaster']['temp_channels'][str(channel.id)] = interaction.user.id
        save_data(data)
        await channel.set_permissions(interaction.user, connect=True, view_channel=True)
        await channel.edit(name=f"{interaction.user.display_name}'s channel")
        await interaction.response.send_message(f"You now own {channel.name}!", ephemeral=True)

    @discord.ui.button(emoji="<:icon6:1445102250036035897>", style=discord.ButtonStyle.secondary, custom_id="vm_activity", row=1)
    async def start_activity(self, interaction: discord.Interaction, button: discord.ui.Button):
        channel = await self.get_user_channel(interaction)
        if not channel or not await self.check_owner(interaction, channel):
            return
        try:
            invite = await channel.create_invite(max_age=3600, target_type=discord.InviteTarget.embedded_application, target_application_id=880218394199220334)
            await interaction.response.send_message(f"Start activity: {invite.url}", ephemeral=True)
        except:
            await interaction.response.send_message("Failed to start activity", ephemeral=True)

    @discord.ui.button(emoji="<:icon7:1445102248865566811>", style=discord.ButtonStyle.secondary, custom_id="vm_info", row=1)
    async def channel_info(self, interaction: discord.Interaction, button: discord.ui.Button):
        channel = await self.get_user_channel(interaction)
        if not channel or not interaction.guild:
            return
        owner_id = temp_channel_owners.get(channel.id)
        owner = interaction.guild.get_member(owner_id) if owner_id else None
        embed = discord.Embed(title=f"Channel Info: {channel.name}", color=0x2b2d31)
        embed.add_field(name="Owner", value=owner.mention if owner else "None", inline=True)
        embed.add_field(name="Members", value=len(channel.members), inline=True)
        embed.add_field(name="User Limit", value=channel.user_limit or "Unlimited", inline=True)
        embed.add_field(name="Bitrate", value=f"{channel.bitrate // 1000}kbps", inline=True)
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @discord.ui.button(emoji="<:icon8:1445102248274170017>", style=discord.ButtonStyle.secondary, custom_id="vm_increase", row=1)
    async def increase_limit(self, interaction: discord.Interaction, button: discord.ui.Button):
        channel = await self.get_user_channel(interaction)
        if not channel or not await self.check_owner(interaction, channel):
            return
        new_limit = (channel.user_limit or 0) + 1
        if new_limit > 99:
            new_limit = 99
        await channel.edit(user_limit=new_limit)
        await interaction.response.send_message(f"User limit: {new_limit}", ephemeral=True)

    @discord.ui.button(emoji="<:icon9:1445102246613487779>", style=discord.ButtonStyle.secondary, custom_id="vm_decrease", row=1)
    async def decrease_limit(self, interaction: discord.Interaction, button: discord.ui.Button):
        channel = await self.get_user_channel(interaction)
        if not channel or not await self.check_owner(interaction, channel):
            return
        new_limit = max(0, (channel.user_limit or 0) - 1)
        await channel.edit(user_limit=new_limit if new_limit > 0 else None)
        await interaction.response.send_message(f"User limit: {'Unlimited' if new_limit == 0 else new_limit}", ephemeral=True)

@bot.event
async def on_member_join(member):
    """Automatically assign role and ping on join when new members join the server"""
    guild_data = get_guild_data(member.guild.id)
    autorole_data = guild_data['autorole']
    ping_data = guild_data['ping_on_join']
    
    # AutoRole: Assign role to new members
    if autorole_data['enabled'] and autorole_data['role_id']:
        role = member.guild.get_role(autorole_data['role_id'])
        if role:
            try:
                await member.add_roles(role)
            except discord.Forbidden:
                print(f"Failed to assign role to {member} - missing permissions")
            except discord.HTTPException:
                print(f"Failed to assign role to {member} - HTTP error")
    
    # Ping on Join: Send ping to selected text channels when user joins the server
    if ping_data['enabled']:
        for channel_id in ping_data['channels']:
            channel = member.guild.get_channel(channel_id)
            if channel and isinstance(channel, discord.TextChannel):
                try:
                    msg = await channel.send(f"{member.mention}")
                    await asyncio.sleep(1)
                    await msg.delete()
                except:
                    pass
    
    # Welcome: Send welcome messages
    welcome_data = guild_data['welcome']
    for channel_id, config in welcome_data.items():
        channel = member.guild.get_channel(int(channel_id))
        if channel and isinstance(channel, discord.TextChannel):
            try:
                message_text = config['message']
                message_text = message_text.replace('{user.mention}', member.mention)
                message_text = message_text.replace('{user.name}', member.name)
                message_text = message_text.replace('{user.display_name}', member.display_name)
                message_text = message_text.replace('{guild.name}', member.guild.name)
                message_text = message_text.replace('{guild.member_count}', str(member.guild.member_count))
                
                msg = await channel.send(message_text)
                
                if config.get('self_destruct'):
                    await asyncio.sleep(config['self_destruct'])
                    try:
                        await msg.delete()
                    except:
                        pass
            except:
                pass
    
    # Logging: Log member joins
    account_age = datetime.now() - member.created_at
    days_old = account_age.days
    years_old = days_old // 365
    
    if years_old > 0:
        age_text = f"{years_old} years ago"
    else:
        age_text = f"{days_old} days ago"
    
    embed = discord.Embed(
        title="Member Joined",
        description=f"{member.name} {member.id} joined the server",
        color=0x2d9d3f
    )
    embed.set_thumbnail(url=member.display_avatar.url)
    embed.add_field(name="Account Created", value=f"{age_text}", inline=True)
    embed.add_field(name="Member Count", value=str(member.guild.member_count), inline=True)
    embed.add_field(name="ID", value=f"{member.id}", inline=False)
    embed.set_footer(text=f"Yesterday at {member.joined_at.strftime('%I:%M %p') if member.joined_at else 'Unknown'}")
    
    await log_event(member.guild, embed, 'members')

@bot.event
async def on_message_delete(message):
    """Store deleted messages for snipe command and log them"""
    if message.author.bot or not message.guild:
        return
    
    guild_data = get_guild_data(message.guild.id)
    snipe_data = {
        'author': message.author.name,
        'author_id': message.author.id,
        'author_avatar': str(message.author.display_avatar.url),
        'content': message.content,
        'timestamp': datetime.now().isoformat(),
        'attachments': [att.url for att in message.attachments]
    }
    
    guild_data['snipes'].insert(0, snipe_data)
    if len(guild_data['snipes']) > 20:
        guild_data['snipes'].pop()
    save_data(data)
    
    # Logging: Log deleted messages
    embed = discord.Embed(
        title="Message Deleted",
        description=f"{message.author.name} {message.author.id} deleted a message in {message.channel.name}",
        color=0xf44336
    )
    embed.add_field(name=message.id, value="", inline=False)
    embed.add_field(name="Content", value=message.content[:1024] if message.content else "(No content)", inline=False)
    embed.set_footer(text=f"Today at {datetime.now().strftime('%I:%M %p')}")
    
    await log_event(message.guild, embed, 'messages')

@bot.event
async def on_voice_state_update(member, before, after):
    guild_data = get_guild_data(member.guild.id)
    vm_data = guild_data['voicemaster']
    ping_data = guild_data['ping_on_join']
    user_data = get_user_data(member.id)
    
    # Track VC time
    if before.channel is None and after.channel is not None:
        # User joined VC
        user_data['vc_join_time'] = datetime.now().isoformat()
        user_data['vc_time'] = float(user_data.get('vc_time', 0))
        save_data(data)
        print(f"[VC] {member.name} joined VC")
    elif before.channel is not None and after.channel is None:
        # User left VC completely
        if user_data.get('vc_join_time'):
            try:
                join_time = datetime.fromisoformat(user_data['vc_join_time'])
                leave_time = datetime.now()
                time_spent = (leave_time - join_time).total_seconds()
                user_data['vc_time'] = float(user_data.get('vc_time', 0)) + time_spent
                user_data['vc_join_time'] = None
                save_data(data)
                print(f"[VC] {member.name} left VC - added {time_spent:.0f}s (total: {user_data['vc_time']:.0f}s)")
            except Exception as e:
                print(f"[VC ERROR] Failed to track {member.name}: {e}")
    elif before.channel is not None and after.channel is not None and before.channel != after.channel:
        # User moved between channels - save time but keep tracking
        if user_data.get('vc_join_time'):
            try:
                join_time = datetime.fromisoformat(user_data['vc_join_time'])
                move_time = datetime.now()
                time_spent = (move_time - join_time).total_seconds()
                user_data['vc_time'] = float(user_data.get('vc_time', 0)) + time_spent
                user_data['vc_join_time'] = datetime.now().isoformat()
                save_data(data)
                print(f"[VC] {member.name} moved channels - added {time_spent:.0f}s")
            except Exception as e:
                print(f"[VC ERROR] Failed to track {member.name} move: {e}")
    
    # VoiceMaster: Create channel on join
    if vm_data['enabled']:
        if after.channel and after.channel.id == vm_data['join_channel_id']:
            category_id = vm_data['temp_category_id'] if vm_data['temp_category_id'] else vm_data['category_id']
            category = member.guild.get_channel(category_id)
            if category:
                new_channel = await member.guild.create_voice_channel(
                    name=f"{member.display_name}'s channel",
                    category=category,
                    user_limit=0
                )
                await member.move_to(new_channel)
                temp_channel_owners[new_channel.id] = member.id
                vm_data['temp_channels'][str(new_channel.id)] = member.id
                save_data(data)
                
                # Log VC creation
                now = datetime.now()
                embed = discord.Embed(
                    title="Voice Channel Created",
                    description=f"{member.name} created a voice channel\nIt was sent at {now.strftime('%m/%d/%Y, %I:%M:%S %p')}",
                    color=0x9b59b6
                )
                embed.set_thumbnail(url=member.display_avatar.url)
                embed.add_field(name="Channel", value=f"{new_channel.mention}", inline=False)
                relative_time = discord.utils.format_dt(now, style='R')
                embed.add_field(name="User ID", value=f"{member.id} • {relative_time} • {now.strftime('%A at %I:%M %p')}", inline=False)
                await log_event(member.guild, embed, 'voice')
        
        if before.channel and str(before.channel.id) in vm_data['temp_channels']:
            if len(before.channel.members) == 0:
                try:
                    await before.channel.delete()
                    del vm_data['temp_channels'][str(before.channel.id)]
                    if before.channel.id in temp_channel_owners:
                        del temp_channel_owners[before.channel.id]
                    save_data(data)
                except:
                    pass
    
    # VoiceMaster Private: Create private channel on join
    if vm_data['priv_enabled']:
        if after.channel and after.channel.id == vm_data['priv_join_channel_id']:
            priv_category = member.guild.get_channel(vm_data['priv_category_id'])
            if priv_category:
                new_channel = await member.guild.create_voice_channel(
                    name=f"{member.display_name}'s private",
                    category=priv_category,
                    user_limit=0
                )
                # Set permissions: everyone can view, but only owner can connect
                await new_channel.set_permissions(member.guild.default_role, view_channel=True, connect=False)
                await new_channel.set_permissions(member, view_channel=True, connect=True)
                # Initialize allowed list for this channel
                priv_channel_allowed[new_channel.id] = []
                
                await member.move_to(new_channel)
                temp_channel_owners[new_channel.id] = member.id
                vm_data['priv_temp_channels'][str(new_channel.id)] = member.id
                priv_channel_allowed[new_channel.id] = []
                save_data(data)
                
                # Log private VC creation
                now = datetime.now()
                embed = discord.Embed(
                    title="Private Voice Channel Created",
                    description=f"{member.name} created a private voice channel\nIt was sent at {now.strftime('%m/%d/%Y, %I:%M:%S %p')}",
                    color=0x8e44ad
                )
                embed.set_thumbnail(url=member.display_avatar.url)
                embed.add_field(name="Channel", value=f"{new_channel.mention}", inline=False)
                relative_time = discord.utils.format_dt(now, style='R')
                embed.add_field(name="User ID", value=f"{member.id} • {relative_time} • {now.strftime('%A at %I:%M %p')}", inline=False)
                await log_event(member.guild, embed, 'voice')
        
        if before.channel and str(before.channel.id) in vm_data['priv_temp_channels']:
            if len(before.channel.members) == 0:
                try:
                    await before.channel.delete()
                    del vm_data['priv_temp_channels'][str(before.channel.id)]
                    if before.channel.id in temp_channel_owners:
                        del temp_channel_owners[before.channel.id]
                    if before.channel.id in priv_channel_allowed:
                        del priv_channel_allowed[before.channel.id]
                    save_data(data)
                except:
                    pass
    
    # Logging: Log voice channel changes
    if before.channel is None and after.channel is not None:
        now = datetime.now()
        embed = discord.Embed(
            title="Voice Channel Joined",
            description=f"{member.name} joined a voice channel\nIt was sent at {now.strftime('%m/%d/%Y, %I:%M:%S %p')}",
            color=0x2ecc71
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.add_field(name="Channel", value=f"{after.channel.mention}", inline=False)
        relative_time = discord.utils.format_dt(now, style='R')
        embed.add_field(name="User ID", value=f"{member.id} • {relative_time} • {now.strftime('%A at %I:%M %p')}", inline=False)
        await log_event(member.guild, embed, 'voice')
    elif before.channel is not None and after.channel is None:
        now = datetime.now()
        embed = discord.Embed(
            title="Voice Channel Left",
            description=f"{member.name} left a voice channel\nIt was sent at {now.strftime('%m/%d/%Y, %I:%M:%S %p')}",
            color=0xe74c3c
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.add_field(name="Channel", value=f"{before.channel.mention}", inline=False)
        relative_time = discord.utils.format_dt(now, style='R')
        embed.add_field(name="User ID", value=f"{member.id} • {relative_time} • {now.strftime('%A at %I:%M %p')}", inline=False)
        await log_event(member.guild, embed, 'voice')
    elif before.channel is not None and after.channel is not None and before.channel != after.channel:
        now = datetime.now()
        embed = discord.Embed(
            title="Voice Channel Moved",
            description=f"{member.name} moved to a different voice channel\nIt was sent at {now.strftime('%m/%d/%Y, %I:%M:%S %p')}",
            color=0x3498db
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.add_field(name="From", value=f"{before.channel.mention}", inline=True)
        embed.add_field(name="To", value=f"{after.channel.mention}", inline=True)
        relative_time = discord.utils.format_dt(now, style='R')
        embed.add_field(name="User ID", value=f"{member.id} • {relative_time} • {now.strftime('%A at %I:%M %p')}", inline=False)
        await log_event(member.guild, embed, 'voice')
    
    # Logging: Log mute/unmute
    if before.self_mute != after.self_mute:
        now = datetime.now()
        action = "Muted" if after.self_mute else "Unmuted"
        color = 0xff6b6b if after.self_mute else 0x51cf66
        embed = discord.Embed(
            title=f"Member {action}",
            description=f"{member.name} {action.lower()} their microphone\nIt was sent at {now.strftime('%m/%d/%Y, %I:%M:%S %p')}",
            color=color
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.add_field(name="Channel", value=f"{after.channel.mention if after.channel else 'N/A'}", inline=False)
        relative_time = discord.utils.format_dt(now, style='R')
        embed.add_field(name="User ID", value=f"{member.id} • {relative_time} • {now.strftime('%A at %I:%M %p')}", inline=False)
        await log_event(member.guild, embed, 'voice')
    
    # Logging: Log deafen/undeafen
    if before.self_deaf != after.self_deaf:
        now = datetime.now()
        action = "Deafened" if after.self_deaf else "Undeafened"
        color = 0xff9800 if after.self_deaf else 0x4caf50
        embed = discord.Embed(
            title=f"Member {action}",
            description=f"{member.name} {action.lower()} themselves\nIt was sent at {now.strftime('%m/%d/%Y, %I:%M:%S %p')}",
            color=color
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.add_field(name="Channel", value=f"{after.channel.mention if after.channel else 'N/A'}", inline=False)
        relative_time = discord.utils.format_dt(now, style='R')
        embed.add_field(name="User ID", value=f"{member.id} • {relative_time} • {now.strftime('%A at %I:%M %p')}", inline=False)
        await log_event(member.guild, embed, 'voice')

@bot.command(name='voicemaster', aliases=['vm'])
@commands.has_permissions(administrator=True)
async def voicemaster(ctx, action: str | None = None, *, args: str | None = None):
    """Setup VoiceMaster system"""
    if action is None:
        embed = discord.Embed(
            title="VoiceMaster Commands",
            description="Manage the VoiceMaster system",
            color=0x2b2d31
        )
        embed.add_field(name=",voicemaster setup", value="Setup VoiceMaster in this server", inline=False)
        embed.add_field(name=",voicemaster priv setup", value="Setup private VoiceMaster (join-to-create private VCs)", inline=False)
        embed.add_field(name=",voicemaster disable", value="Disable VoiceMaster", inline=False)
        embed.add_field(name=",voicemaster reset", value="Reset VoiceMaster (allows setup again)", inline=False)
        embed.add_field(name=",voicemaster category <id>", value="Set category for temp voice channels", inline=False)
        embed.add_field(name=",voicemaster interface", value="Send the control interface", inline=False)
        await ctx.send(embed=embed)
        return
    
    guild_data = get_guild_data(ctx.guild.id)
    vm_data = guild_data['voicemaster']
    
    if action.lower() == 'setup':
        if vm_data['setup_complete']:
            await ctx.send("VoiceMaster is already set up! Use `,voicemaster reset` to set it up again.")
            return
        
        category = await ctx.guild.create_category("VoiceMaster")
        join_channel = await ctx.guild.create_voice_channel("Join to Create", category=category)
        interface_channel = await ctx.guild.create_text_channel("interface", category=category)
        
        vm_data['enabled'] = True
        vm_data['setup_complete'] = True
        vm_data['category_id'] = category.id
        vm_data['join_channel_id'] = join_channel.id
        vm_data['interface_channel_id'] = interface_channel.id
        save_data(data)
        
        embed = discord.Embed(
            title="VoiceMaster Interface",
            description="Click the buttons below to control your voice channel",
            color=0x2b2d31
        )
        embed.add_field(
            name="Button Usage",
            value=(
                "<:icon:1445102255715123301> — **Lock** the voice channel\n"
                "<:icon1:1445102254746112143> — **Unlock** the voice channel\n"
                "<:icon2:1445102253840138282> — **Hide** the voice channel\n"
                "<:icon3:1445102252959469629> — **Reveal** the voice channel\n"
                "<:icon4:1445102252091117700> — **Disconnect** a member\n"
                "<:icon5:1445102250900066438> — **Claim** the voice channel\n"
                "<:icon6:1445102250036035897> — **Start** an activity\n"
                "<:icon7:1445102248865566811> — **View** channel info\n"
                "<:icon8:1445102248274170017> — **Increase** the user limit\n"
                "<:icon9:1445102246613487779> — **Decrease** the user limit"
            ),
            inline=False
        )
        
        bot.add_view(VoiceMasterView())
        await interface_channel.send(embed=embed, view=VoiceMasterView())
        await ctx.send(f"VoiceMaster setup complete! Join {join_channel.mention} to create a channel.")
    
    elif action.lower() == 'disable':
        vm_data['enabled'] = False
        save_data(data)
        await ctx.send("VoiceMaster disabled!")
    
    elif action.lower() == 'reset':
        if not vm_data['setup_complete']:
            await ctx.send("VoiceMaster hasn't been set up yet!")
            return
        
        # Delete the category and channels
        if vm_data['category_id']:
            try:
                category = ctx.guild.get_channel(vm_data['category_id'])
                if category:
                    await category.delete()
            except:
                pass
        
        # Reset all VoiceMaster data
        vm_data['enabled'] = False
        vm_data['setup_complete'] = False
        vm_data['category_id'] = None
        vm_data['join_channel_id'] = None
        vm_data['interface_channel_id'] = None
        vm_data['temp_category_id'] = None
        vm_data['temp_channels'] = {}
        save_data(data)
        
        await ctx.send("VoiceMaster has been reset! You can now use `,voicemaster setup` again.")
    
    elif action.lower() == 'category':
        if not args:
            await ctx.send("Syntax: `,voicemaster category <category_id>`")
            return
        
        try:
            category_id = int(args)
            category = ctx.guild.get_channel(category_id)
            if not category or not isinstance(category, discord.CategoryChannel):
                await ctx.send("Category not found or invalid category ID!")
                return
            
            vm_data['temp_category_id'] = category_id
            save_data(data)
            await ctx.send(f"✅ Temporary voice channels will now be created in {category.mention}!")
        except ValueError:
            await ctx.send("Invalid category ID!")
    
    elif action.lower() == 'priv':
        if not args or args.lower() == 'setup':
            if vm_data['priv_setup_complete']:
                await ctx.send("Private VoiceMaster is already set up! Use `,voicemaster priv reset` to set it up again.")
                return
            
            priv_category = await ctx.guild.create_category("Private VoiceMaster")
            priv_join_channel = await ctx.guild.create_voice_channel("Join for Private VC", category=priv_category)
            
            vm_data['priv_enabled'] = True
            vm_data['priv_setup_complete'] = True
            vm_data['priv_category_id'] = priv_category.id
            vm_data['priv_join_channel_id'] = priv_join_channel.id
            save_data(data)
            
            await ctx.message.add_reaction("✅")
            return
        
        if args.lower() == 'reset':
            if not vm_data['priv_setup_complete']:
                await ctx.send("Private VoiceMaster hasn't been set up yet!")
                return
            
            # Delete the category
            if vm_data['priv_category_id']:
                try:
                    category = ctx.guild.get_channel(vm_data['priv_category_id'])
                    if category:
                        await category.delete()
                except:
                    pass
            
            # Reset all private VoiceMaster data
            vm_data['priv_enabled'] = False
            vm_data['priv_setup_complete'] = False
            vm_data['priv_category_id'] = None
            vm_data['priv_join_channel_id'] = None
            vm_data['priv_temp_channels'] = {}
            save_data(data)
            
            await ctx.message.add_reaction("✅")
            return
        
        # Handle custom category for private setup
        try:
            custom_category_id = int(args)
            category = ctx.guild.get_channel(custom_category_id)
            if not category or not isinstance(category, discord.CategoryChannel):
                await ctx.send("Category not found or invalid category ID!")
                return
            
            priv_join_channel = await ctx.guild.create_voice_channel("Join for Private VC", category=category)
            
            vm_data['priv_enabled'] = True
            vm_data['priv_setup_complete'] = True
            vm_data['priv_category_id'] = category.id
            vm_data['priv_join_channel_id'] = priv_join_channel.id
            save_data(data)
            
            await ctx.message.add_reaction("✅")
        except ValueError:
            await ctx.send("Syntax: `,voicemaster priv setup`, `,voicemaster priv reset`, or `,voicemaster priv <category_id>`")
    
    elif action.lower() == 'interface':
        embed = discord.Embed(
            title="VoiceMaster Interface",
            description="Click the buttons below to control your voice channel",
            color=0x2b2d31
        )
        embed.add_field(
            name="Button Usage",
            value=(
                "<:icon:1445102255715123301> — **Lock** the voice channel\n"
                "<:icon1:1445102254746112143> — **Unlock** the voice channel\n"
                "<:icon2:1445102253840138282> — **Hide** the voice channel\n"
                "<:icon3:1445102252959469629> — **Reveal** the voice channel\n"
                "<:icon4:1445102252091117700> — **Disconnect** a member\n"
                "<:icon5:1445102250900066438> — **Claim** the voice channel\n"
                "<:icon6:1445102250036035897> — **Start** an activity\n"
                "<:icon7:1445102248865566811> — **View** channel info\n"
                "<:icon8:1445102248274170017> — **Increase** the user limit\n"
                "<:icon9:1445102246613487779> — **Decrease** the user limit"
            ),
            inline=False
        )
        bot.add_view(VoiceMasterView())
        await ctx.send(embed=embed, view=VoiceMasterView())

@bot.command(name='balance', aliases=['bal'])
async def balance(ctx, member: discord.Member | None = None):
    """Check your or someone else's balance"""
    member = member or ctx.author
    user_data = get_user_data(member.id)
    
    embed = discord.Embed(
        title=f"{member.display_name}'s Balance",
        color=0xe91e63
    )
    embed.add_field(name="Wallet", value=f"${user_data['balance']:,}", inline=True)
    embed.add_field(name="Bank", value=f"${user_data['bank']:,}", inline=True)
    embed.add_field(name="Total", value=f"${user_data['balance'] + user_data['bank']:,}", inline=True)
    embed.set_thumbnail(url=member.display_avatar.url)
    
    await ctx.send(embed=embed)

@bot.command(name='daily')
async def daily(ctx):
    """Claim your daily reward"""
    user_data = get_user_data(ctx.author.id)
    now = datetime.now()
    
    if user_data['daily_last']:
        last = datetime.fromisoformat(user_data['daily_last'])
        if now - last < timedelta(days=1):
            remaining = timedelta(days=1) - (now - last)
            hours = remaining.seconds // 3600
            minutes = (remaining.seconds % 3600) // 60
            await ctx.send(f"You already claimed your daily! Come back in **{hours}h {minutes}m**")
            return
    
    reward = random.randint(500, 1000)
    user_data['balance'] += reward
    user_data['daily_last'] = now.isoformat()
    save_data(data)
    
    embed = discord.Embed(
        title="Daily Reward Claimed!",
        description=f"You received **${reward:,}**!",
        color=0x4caf50
    )
    await ctx.send(embed=embed)

@bot.command(name='work')
async def work(ctx):
    """Work to earn money"""
    user_data = get_user_data(ctx.author.id)
    now = datetime.now()
    
    if user_data['work_last']:
        last = datetime.fromisoformat(user_data['work_last'])
        if now - last < timedelta(hours=1):
            remaining = timedelta(hours=1) - (now - last)
            minutes = remaining.seconds // 60
            await ctx.send(f"You're tired! Rest for **{minutes}m** before working again")
            return
    
    jobs = [
        ("developer", 300, 600),
        ("designer", 250, 500),
        ("streamer", 200, 700),
        ("trader", 150, 800),
        ("gamer", 100, 400)
    ]
    
    job = random.choice(jobs)
    earnings = random.randint(job[1], job[2])
    user_data['balance'] += earnings
    user_data['work_last'] = now.isoformat()
    save_data(data)
    
    embed = discord.Embed(
        title="Work Complete!",
        description=f"You worked as a **{job[0]}** and earned **${earnings:,}**!",
        color=0x2196f3
    )
    await ctx.send(embed=embed)

@bot.command(name='deposit', aliases=['dep'])
async def deposit(ctx, amount: str):
    """Deposit money into your bank"""
    user_data = get_user_data(ctx.author.id)
    
    amount_int: int
    if amount.lower() == 'all':
        amount_int = user_data['balance']
    else:
        try:
            amount_int = int(amount)
        except ValueError:
            await ctx.send("Please provide a valid amount!")
            return
    
    if amount_int <= 0:
        await ctx.send("Amount must be positive!")
        return
    
    if amount_int > user_data['balance']:
        await ctx.send("You don't have that much money!")
        return
    
    user_data['balance'] -= amount_int
    user_data['bank'] += amount_int
    save_data(data)
    
    await ctx.send(f"Deposited **${amount_int:,}** into your bank!")

@bot.command(name='withdraw', aliases=['with'])
async def withdraw(ctx, amount: str):
    """Withdraw money from your bank"""
    user_data = get_user_data(ctx.author.id)
    
    amount_int: int
    if amount.lower() == 'all':
        amount_int = user_data['bank']
    else:
        try:
            amount_int = int(amount)
        except ValueError:
            await ctx.send("Please provide a valid amount!")
            return
    
    if amount_int <= 0:
        await ctx.send("Amount must be positive!")
        return
    
    if amount_int > user_data['bank']:
        await ctx.send("You don't have that much in your bank!")
        return
    
    user_data['bank'] -= amount_int
    user_data['balance'] += amount_int
    save_data(data)
    
    await ctx.send(f"Withdrew **${amount_int:,}** from your bank!")

@bot.command(name='rob')
async def rob(ctx, member: discord.Member):
    """Try to rob another user"""
    if member.bot or member == ctx.author:
        await ctx.send("You can't rob that user!")
        return
    
    user_data = get_user_data(ctx.author.id)
    target_data = get_user_data(member.id)
    
    if target_data['balance'] < 100:
        await ctx.send("That user is too poor to rob!")
        return
    
    if user_data['balance'] < 50:
        await ctx.send("You need at least $50 to attempt a robbery!")
        return
    
    if random.random() < 0.4:
        stolen = random.randint(50, min(500, target_data['balance']))
        target_data['balance'] -= stolen
        user_data['balance'] += stolen
        save_data(data)
        
        embed = discord.Embed(
            title="Robbery Successful!",
            description=f"You stole **${stolen:,}** from {member.mention}!",
            color=0x4caf50
        )
        await ctx.send(embed=embed)
    else:
        fine = random.randint(100, 300)
        user_data['balance'] -= fine
        save_data(data)
        
        embed = discord.Embed(
            title="Robbery Failed!",
            description=f"You got caught and paid **${fine:,}** in fines!",
            color=0xf44336
        )
        await ctx.send(embed=embed)

@bot.command(name='rank')
async def rank(ctx, member: discord.Member | None = None):
    """Check your or someone else's rank"""
    member = member or ctx.author
    user_data = get_user_data(member.id)
    
    xp_needed = user_data['level'] * 100
    
    embed = discord.Embed(
        title=f"{member.display_name}'s Rank",
        color=0xe91e63
    )
    embed.add_field(name="Level", value=user_data['level'], inline=True)
    embed.add_field(name="XP", value=f"{user_data['xp']}/{xp_needed}", inline=True)
    embed.set_thumbnail(url=member.display_avatar.url)
    
    await ctx.send(embed=embed)

@bot.command(name='leaderboard', aliases=['lb'])
async def leaderboard(ctx):
    """View the server leaderboard"""
    sorted_users = sorted(
        data['users'].items(),
        key=lambda x: x[1]['level'] * 1000 + x[1]['xp'],
        reverse=True
    )[:10]
    
    embed = discord.Embed(
        title="Server Leaderboard",
        color=0xffc107
    )
    
    for i, (user_id, user_data) in enumerate(sorted_users, 1):
        user = bot.get_user(int(user_id))
        if user:
            embed.add_field(
                name=f"{i}. {user.display_name}",
                value=f"Level {user_data['level']} - {user_data['xp']} XP",
                inline=False
            )
    
    await ctx.send(embed=embed)

@bot.command(name='vcleaderboard', aliases=['vclb'])
async def vc_leaderboard(ctx):
    """View the VC activity leaderboard - top 10 most active users"""
    # Calculate total VC time including current active sessions
    user_totals = {}
    for user_id, user_data in data['users'].items():
        total_seconds = float(user_data.get('vc_time', 0))
        
        # Add current session time if user is in VC
        if user_data.get('vc_join_time'):
            try:
                join_time = datetime.fromisoformat(user_data['vc_join_time'])
                current_time = datetime.now()
                session_time = (current_time - join_time).total_seconds()
                total_seconds += session_time
            except:
                pass
        
        user_totals[user_id] = int(total_seconds)
    
    sorted_users = sorted(user_totals.items(), key=lambda x: x[1], reverse=True)[:10]
    
    embed = discord.Embed(
        title="Voice Channel Leaderboard",
        description="Top 10 Most Active Users",
        color=0x000000
    )
    
    medals = ["1st", "2nd", "3rd"]
    
    leaderboard_text = ""
    for i, (user_id, total_seconds) in enumerate(sorted_users, 1):
        user = bot.get_user(int(user_id))
        if user:
            hours = total_seconds // 3600
            minutes = (total_seconds % 3600) // 60
            seconds = total_seconds % 60
            
            time_str = f"{hours}h {minutes}m {seconds}s"
            medal = medals[i-1] if i <= 3 else f"#{i}"
            
            leaderboard_text += f"{medal} **{user.display_name}** • `{time_str}`\n"
    
    embed.description = leaderboard_text
    embed.set_footer(text=f"Last updated • {datetime.now().strftime('%I:%M %p')}")
    
    await ctx.send(embed=embed)

@bot.command(name='messageleaderboard', aliases=['mslb'])
async def message_leaderboard(ctx):
    """View the message leaderboard - top 10 most messages typed"""
    sorted_users = sorted(
        data['users'].items(),
        key=lambda x: x[1].get('message_count', 0),
        reverse=True
    )[:10]
    
    embed = discord.Embed(
        title="Message Leaderboard",
        description="Top 10 Most Active Users",
        color=0x000000
    )
    
    medals = ["1st", "2nd", "3rd"]
    
    leaderboard_text = ""
    for i, (user_id, user_data) in enumerate(sorted_users, 1):
        user = bot.get_user(int(user_id))
        if user:
            message_count = user_data.get('message_count', 0)
            medal = medals[i-1] if i <= 3 else f"#{i}"
            leaderboard_text += f"{medal} **{user.display_name}** • `{message_count:,}` messages\n"
    
    embed.description = leaderboard_text
    embed.set_footer(text=f"Last updated • {datetime.now().strftime('%I:%M %p')}")
    
    await ctx.send(embed=embed)

vc_group = app_commands.Group(name='vc', description='Manage your private voice channel')

@vc_group.command(name='allow', description='Allow a user to join your private VC')
async def vc_allow(interaction: discord.Interaction, member: discord.Member):
    """Allow user to join your private VC"""
    await interaction.response.defer(ephemeral=True)
    
    if not interaction.user.voice or not interaction.user.voice.channel:
        await interaction.followup.send('❌ You must be in a voice channel', ephemeral=True)
        return
    
    channel = interaction.user.voice.channel
    channel_id = channel.id
    
    # Check if user owns this channel
    if channel_id not in temp_channel_owners or temp_channel_owners[channel_id] != interaction.user.id:
        await interaction.followup.send('❌ You do not own this channel', ephemeral=True)
        return
    
    if channel_id not in priv_channel_allowed:
        priv_channel_allowed[channel_id] = []
    
    if member.id not in priv_channel_allowed[channel_id]:
        priv_channel_allowed[channel_id].append(member.id)
        try:
            await channel.set_permissions(member, view_channel=True, connect=True)
            await interaction.followup.send(f'✅ {member.mention} can now join your VC', ephemeral=True)
        except Exception as e:
            await interaction.followup.send(f'❌ Failed to set permissions', ephemeral=True)
    else:
        await interaction.followup.send(f'❌ {member.mention} already has access', ephemeral=True)

@vc_group.command(name='deny', description='Deny a user access to your private VC')
async def vc_deny(interaction: discord.Interaction, member: discord.Member):
    """Deny user access to your private VC"""
    await interaction.response.defer(ephemeral=True)
    
    if not interaction.user.voice or not interaction.user.voice.channel:
        await interaction.followup.send('❌ You must be in a voice channel', ephemeral=True)
        return
    
    channel = interaction.user.voice.channel
    channel_id = channel.id
    
    # Check if user owns this channel
    if channel_id not in temp_channel_owners or temp_channel_owners[channel_id] != interaction.user.id:
        await interaction.followup.send('❌ You do not own this channel', ephemeral=True)
        return
    
    if channel_id in priv_channel_allowed and member.id in priv_channel_allowed[channel_id]:
        priv_channel_allowed[channel_id].remove(member.id)
        try:
            await channel.set_permissions(member, overwrite=None)
            await interaction.followup.send(f'✅ {member.mention} has been denied access', ephemeral=True)
        except Exception as e:
            await interaction.followup.send(f'❌ Failed to remove permissions', ephemeral=True)
    else:
        await interaction.followup.send(f'❌ {member.mention} does not have access', ephemeral=True)

bot.tree.add_command(vc_group)

@bot.command(name='su')
async def server_stats(ctx, member: discord.Member | None = None):
    """View detailed server stats for a user"""
    member = member or ctx.author
    user_data = get_user_data(member.id)
    
    # Get message rank
    message_rank = 1
    user_messages = user_data.get('message_count', 0)
    for uid, data_item in data['users'].items():
        if data_item.get('message_count', 0) > user_messages:
            message_rank += 1
    
    # Get voice rank
    voice_rank = 1
    user_vc_time = float(user_data.get('vc_time', 0))
    if user_data.get('vc_join_time'):
        try:
            join_time = datetime.fromisoformat(user_data['vc_join_time'])
            current_time = datetime.now()
            session_time = (current_time - join_time).total_seconds()
            user_vc_time += session_time
        except:
            pass
    
    for uid, data_item in data['users'].items():
        other_vc_time = float(data_item.get('vc_time', 0))
        if data_item.get('vc_join_time'):
            try:
                join_time = datetime.fromisoformat(data_item['vc_join_time'])
                session_time = (datetime.now() - join_time).total_seconds()
                other_vc_time += session_time
            except:
                pass
        if other_vc_time > user_vc_time:
            voice_rank += 1
    
    # Format times
    vc_hours = int(user_vc_time // 3600)
    vc_minutes = int((user_vc_time % 3600) // 60)
    
    created_date = member.created_at.strftime("%B %d, %Y")
    joined_date = member.joined_at.strftime("%B %d, %Y") if member.joined_at else "Unknown"
    
    embed = discord.Embed(
        title=f"{member.display_name}",
        description=f"private party",
        color=0x2f3136
    )
    embed.set_thumbnail(url=member.display_avatar.url)
    
    # Created On and Joined On
    embed.add_field(name="Created On", value=created_date, inline=True)
    embed.add_field(name="Joined On", value=joined_date, inline=True)
    embed.add_field(name="", value="", inline=False)
    
    # Server Ranks
    ranks_text = f"Message     #`{message_rank}`\nVoice         #`{voice_rank}`"
    embed.add_field(name="Server Ranks", value=ranks_text, inline=True)
    
    # Messages breakdown
    messages_text = f"1d   `{user_messages}` messages\n7d   `{user_messages}` messages\n14d  `{user_messages}` messages"
    embed.add_field(name="Messages", value=messages_text, inline=True)
    
    # Voice Activity breakdown
    voice_text = f"1d   `{vc_hours}h {vc_minutes}m`\n7d   `{vc_hours}h {vc_minutes}m`\n14d  `{vc_hours}h {vc_minutes}m`"
    embed.add_field(name="Voice Activity", value=voice_text, inline=True)
    
    embed.set_footer(text=f"Server Lookback: Last 14 days — Timezone: UTC")
    await ctx.send(embed=embed)

@bot.command(name='kick')
@commands.has_permissions(kick_members=True)
async def kick(ctx, member: discord.Member, *, reason="No reason provided"):
    """Kick a member from the server"""
    await member.kick(reason=reason)
    embed = discord.Embed(
        title="Member Kicked",
        description=f"{member.mention} was kicked\n**Reason:** {reason}",
        color=0xff9800
    )
    await ctx.send(embed=embed)

@bot.command(name='ban')
@commands.has_permissions(ban_members=True)
async def ban(ctx, member: discord.Member, *, reason="No reason provided"):
    """Ban a member from the server"""
    await member.ban(reason=reason)
    embed = discord.Embed(
        title="Member Banned",
        description=f"{member.mention} was banned\n**Reason:** {reason}",
        color=0xf44336
    )
    await ctx.send(embed=embed)

@bot.command(name='clear')
@commands.has_permissions(manage_messages=True)
async def clear(ctx, amount: int):
    """Clear messages from the channel"""
    if amount <= 0 or amount > 100:
        await ctx.send("Please provide a number between 1 and 100!")
        return
    
    deleted = await ctx.channel.purge(limit=amount + 1)
    msg = await ctx.send(f"Deleted {len(deleted) - 1} messages!")
    await asyncio.sleep(3)
    await msg.delete()

@bot.command(name='purge')
@commands.has_permissions(manage_messages=True)
async def purge(ctx, amount: int):
    """Purge messages from the channel (1-200)"""
    if amount <= 0 or amount > 200:
        await ctx.send("Please provide a number between 1 and 200!")
        return
    
    deleted = await ctx.channel.purge(limit=amount + 1)

@bot.command(name='timeout')
@commands.has_permissions(moderate_members=True)
async def timeout(ctx, member: discord.Member, duration: str):
    """Timeout a member (1m, 10m, 1h, 10h, 1d, 7d)"""
    duration_map = {
        '1m': timedelta(minutes=1),
        '10m': timedelta(minutes=10),
        '1h': timedelta(hours=1),
        '10h': timedelta(hours=10),
        '1d': timedelta(days=1),
        '7d': timedelta(days=7)
    }
    
    if duration.lower() not in duration_map:
        await ctx.send("Invalid duration! Allowed: 1m, 10m, 1h, 10h, 1d, 7d")
        return
    
    try:
        await member.timeout(duration_map[duration.lower()], reason="Timed out by moderator")
        embed = discord.Embed(
            title="Member Timed Out",
            description=f"{member.mention} has been timed out for **{duration}**",
            color=0xff9800
        )
        await ctx.send(embed=embed)
    except discord.Forbidden:
        await ctx.send("I don't have permission to timeout this member!")
    except Exception as e:
        await ctx.send(f"Error timing out member: {e}")

@bot.command(name='jailsetup')
@commands.has_permissions(administrator=True)
async def jail_setup(ctx):
    """Setup jail system - creates jailed role and jail channel"""
    guild_data = get_guild_data(ctx.guild.id)
    jail_data = guild_data['jail']
    
    try:
        # Create jailed role
        jail_role = await ctx.guild.create_role(
            name="jailed",
            color=discord.Color.dark_red(),
            reason="Jail system setup"
        )
        
        # Create jail channel
        jail_channel = await ctx.guild.create_text_channel(
            name="jail",
            reason="Jail system setup"
        )
        
        # Set permissions for all existing channels - deny jailed role
        for channel in ctx.guild.channels:
            try:
                await channel.set_permissions(jail_role, view_channel=False)
            except:
                pass
        
        # Set permissions for jail channel - allow jailed role to view and type
        await jail_channel.set_permissions(ctx.guild.default_role, view_channel=False)
        await jail_channel.set_permissions(jail_role, view_channel=True, send_messages=True)
        
        jail_data['enabled'] = True
        jail_data['role_id'] = jail_role.id
        jail_data['channel_id'] = jail_channel.id
        save_data(data)
        
        await ctx.message.add_reaction("✅")
    except Exception as e:
        await ctx.send(f"Error setting up jail: {e}")

@bot.command(name='jail')
@commands.has_permissions(moderate_members=True)
async def jail(ctx, member: discord.Member, *, reason="No reason provided"):
    """Jail a member - removes all roles except jailed"""
    guild_data = get_guild_data(ctx.guild.id)
    jail_data = guild_data['jail']
    
    if not jail_data['enabled'] or not jail_data['role_id']:
        await ctx.send("Jail system not setup! Use `,jailsetup` first.")
        return
    
    jail_role = ctx.guild.get_role(jail_data['role_id'])
    if not jail_role:
        await ctx.send("Jail role not found! Use `,jailsetup` again.")
        return
    
    try:
        # Store member's current roles (excluding @everyone)
        old_roles = [r for r in member.roles if r != ctx.guild.default_role]
        
        # Store in user data for restoration on unjail
        user_data = get_user_data(member.id)
        user_data['jail_roles'] = [r.id for r in old_roles]
        
        # Remove all roles except @everyone
        for role in old_roles:
            await member.remove_roles(role, reason=f"Jailed: {reason}")
        
        # Add jailed role
        await member.add_roles(jail_role, reason=f"Jailed: {reason}")
        save_data(data)
        
        embed = discord.Embed(
            title="Member Jailed",
            description=f"{member.mention} has been jailed\n**Reason:** {reason}",
            color=0x8b0000
        )
        await ctx.send(embed=embed)
        
        # Log jail action
        embed = discord.Embed(
            title="Member Jailed",
            description=f"{member.name} {member.id} was jailed",
            color=0x8b0000
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.add_field(name="Reason", value=reason, inline=False)
        embed.add_field(name="Moderator", value=ctx.author.mention, inline=False)
        embed.set_footer(text=f"Today at {datetime.now().strftime('%I:%M %p')}")
        await log_event(ctx.guild, embed, 'members')
    except discord.Forbidden:
        await ctx.send("I don't have permission to jail this member!")
    except Exception as e:
        await ctx.send(f"Error jailing member: {e}")

@bot.command(name='unjail')
@commands.has_permissions(moderate_members=True)
async def unjail(ctx, member: discord.Member, *, reason="No reason provided"):
    """Unjail a member - restores their previous roles"""
    guild_data = get_guild_data(ctx.guild.id)
    jail_data = guild_data['jail']
    
    if not jail_data['enabled'] or not jail_data['role_id']:
        await ctx.send("Jail system not setup!")
        return
    
    jail_role = ctx.guild.get_role(jail_data['role_id'])
    if not jail_role:
        await ctx.send("Jail role not found!")
        return
    
    try:
        # Remove jailed role
        await member.remove_roles(jail_role, reason=f"Unjailed: {reason}")
        
        # Restore previous roles
        user_data = get_user_data(member.id)
        if user_data.get('jail_roles'):
            for role_id in user_data['jail_roles']:
                role = ctx.guild.get_role(role_id)
                if role:
                    try:
                        await member.add_roles(role, reason=f"Unjailed: {reason}")
                    except:
                        pass
            user_data['jail_roles'] = []
            save_data(data)
        
        embed = discord.Embed(
            title="Member Unjailed",
            description=f"{member.mention} has been unjailed\n**Reason:** {reason}",
            color=0x2d9d3f
        )
        await ctx.send(embed=embed)
        
        # Log unjail action
        embed = discord.Embed(
            title="Member Unjailed",
            description=f"{member.name} {member.id} was unjailed",
            color=0x2d9d3f
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.add_field(name="Reason", value=reason, inline=False)
        embed.add_field(name="Moderator", value=ctx.author.mention, inline=False)
        embed.set_footer(text=f"Today at {datetime.now().strftime('%I:%M %p')}")
        await log_event(ctx.guild, embed, 'members')
    except discord.Forbidden:
        await ctx.send("I don't have permission to unjail this member!")
    except Exception as e:
        await ctx.send(f"Error unjailing member: {e}")

@bot.command(name='antiraid')
@commands.has_permissions(manage_guild=True)
async def antiraid(ctx, action: str | None = None, setting: str | None = None):
    """Configure anti-raid protection"""
    guild_data = get_guild_data(ctx.guild.id)
    ar_data = guild_data['antiraid']
    
    if action is None or action.lower() == 'config':
        embed = discord.Embed(
            title="Anti-Raid Configuration",
            color=0xff6b6b
        )
        embed.add_field(name="Status", value="✅ Enabled" if ar_data['enabled'] else "❌ Disabled", inline=True)
        embed.add_field(name="Raid State", value="🚨 Active" if ar_data['raid_state'] else "✅ Normal", inline=True)
        embed.add_field(name="Check Avatar", value="✅ Yes" if ar_data['check_avatar'] else "❌ No", inline=True)
        embed.add_field(name="Check New Accounts", value="✅ Yes" if ar_data['check_new_accounts'] else "❌ No", inline=True)
        embed.add_field(name="Action", value=ar_data['action'].upper(), inline=True)
        embed.add_field(name="New Account Days", value=str(ar_data['new_account_days']), inline=True)
        embed.add_field(name="Whitelisted", value=str(len(ar_data['whitelist'])), inline=True)
        await ctx.send(embed=embed)
        return
    
    action = action.lower()
    
    if action == 'enable':
        ar_data['enabled'] = True
        save_data(data)
        await ctx.message.add_reaction("✅")
    elif action == 'disable':
        ar_data['enabled'] = False
        save_data(data)
        await ctx.message.add_reaction("✅")
    elif action == 'massoin':
        ar_data['raid_state'] = not ar_data['raid_state']
        save_data(data)
        status = "🚨 Raid mode ENABLED" if ar_data['raid_state'] else "✅ Raid mode DISABLED"
        embed = discord.Embed(description=status, color=0xff6b6b)
        await ctx.send(embed=embed)
    elif action == 'state':
        ar_data['raid_state'] = False
        save_data(data)
        embed = discord.Embed(description="✅ Raid state turned off", color=0x2d9d3f)
        await ctx.send(embed=embed)
    elif action == 'avatar':
        ar_data['check_avatar'] = not ar_data['check_avatar']
        save_data(data)
        status = "✅ Enabled" if ar_data['check_avatar'] else "❌ Disabled"
        embed = discord.Embed(description=f"Avatar check {status}", color=0xff6b6b)
        await ctx.send(embed=embed)
    elif action == 'newaccounts':
        if setting and setting.isdigit():
            ar_data['new_account_days'] = int(setting)
        ar_data['check_new_accounts'] = not ar_data['check_new_accounts']
        save_data(data)
        status = "✅ Enabled" if ar_data['check_new_accounts'] else "❌ Disabled"
        embed = discord.Embed(description=f"New account check {status} ({ar_data['new_account_days']} days)", color=0xff6b6b)
        await ctx.send(embed=embed)
    elif action == 'whitelist':
        if setting == 'view':
            if not ar_data['whitelist']:
                embed = discord.Embed(description="No whitelisted users", color=0x2f3136)
            else:
                whitelist_text = "\n".join([f"<@{uid}>" for uid in ar_data['whitelist'][:10]])
                embed = discord.Embed(description=f"**Whitelisted Users:**\n{whitelist_text}", color=0x2d9d3f)
            await ctx.send(embed=embed)
        else:
            # Try to get member from mention
            if ctx.message.mentions:
                member = ctx.message.mentions[0]
                if member.id not in ar_data['whitelist']:
                    ar_data['whitelist'].append(member.id)
                    save_data(data)
                    embed = discord.Embed(description=f"✅ {member.mention} whitelisted", color=0x2d9d3f)
                else:
                    ar_data['whitelist'].remove(member.id)
                    save_data(data)
                    embed = discord.Embed(description=f"❌ {member.mention} removed from whitelist", color=0xff6b6b)
                await ctx.send(embed=embed)

@bot.command(name='hide')
@commands.has_permissions(manage_channels=True)
async def hide(ctx):
    """Hide the current channel from view"""
    try:
        await ctx.channel.set_permissions(ctx.guild.default_role, view_channel=False)
        await ctx.message.add_reaction("✅")
    except discord.Forbidden:
        await ctx.send("I don't have permission to hide this channel!")
    except Exception as e:
        await ctx.send(f"Error hiding channel: {e}")

@bot.command(name='unhide')
@commands.has_permissions(manage_channels=True)
async def unhide(ctx):
    """Unhide the current channel"""
    try:
        await ctx.channel.set_permissions(ctx.guild.default_role, view_channel=True)
        await ctx.message.add_reaction("✅")
    except discord.Forbidden:
        await ctx.send("I don't have permission to unhide this channel!")
    except Exception as e:
        await ctx.send(f"Error unhiding channel: {e}")

@bot.command(name='lock')
@commands.has_permissions(manage_channels=True)
async def lock(ctx):
    """Lock the channel so no one can type"""
    try:
        await ctx.channel.set_permissions(ctx.guild.default_role, send_messages=False)
        await ctx.message.add_reaction("✅")
    except discord.Forbidden:
        await ctx.send("I don't have permission to lock this channel!")
    except Exception as e:
        await ctx.send(f"Error locking channel: {e}")

@bot.command(name='unlock')
@commands.has_permissions(manage_channels=True)
async def unlock(ctx):
    """Unlock the channel"""
    try:
        await ctx.channel.set_permissions(ctx.guild.default_role, send_messages=True)
        await ctx.message.add_reaction("✅")
    except discord.Forbidden:
        await ctx.send("I don't have permission to unlock this channel!")
    except Exception as e:
        await ctx.send(f"Error unlocking channel: {e}")

class NukeConfirmView(discord.ui.View):
    def __init__(self, ctx, channel):
        super().__init__(timeout=30)
        self.ctx = ctx
        self.channel = channel
        self.confirmed = False
    
    @discord.ui.button(label="Yes", style=discord.ButtonStyle.red, emoji="✅")
    async def yes_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.ctx.author:
            await interaction.response.send_message("You didn't invoke this command!", ephemeral=True)
            return
        
        await interaction.response.defer()
        self.confirmed = True
        self.stop()
    
    @discord.ui.button(label="No", style=discord.ButtonStyle.gray, emoji="❌")
    async def no_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.ctx.author:
            await interaction.response.send_message("You didn't invoke this command!", ephemeral=True)
            return
        
        await interaction.response.defer()
        self.confirmed = False
        self.stop()

@bot.command(name='nuke')
@commands.has_permissions(manage_channels=True)
async def nuke(ctx):
    """Nuke the channel (delete and recreate with same settings)"""
    channel = ctx.channel
    category = channel.category
    
    # Confirmation embed
    confirm_embed = discord.Embed(
        title="⚠️ Are you sure?",
        description=f"This will delete {channel.mention} and recreate it with the same name and permissions.",
        color=0xff9800
    )
    
    view = NukeConfirmView(ctx, channel)
    msg = await ctx.send(embed=confirm_embed, view=view)
    
    await view.wait()
    
    if not view.confirmed:
        cancel_embed = discord.Embed(
            title="Nuke Cancelled",
            description="Channel nuke was cancelled.",
            color=0x4caf50
        )
        await msg.edit(embed=cancel_embed, view=None)
        return
    
    try:
        # Copy channel permissions
        overwrites = channel.overwrites
        channel_name = channel.name
        
        # Delete the old channel
        await channel.delete()
        
        # Create new channel with same settings
        new_channel = await category.create_text_channel(
            name=channel_name,
            overwrites=overwrites
        )
        
        # Send nuke confirmation in new channel
        await new_channel.send("first")
    except discord.Forbidden:
        await ctx.send("I don't have permission to nuke this channel!")
    except Exception as e:
        await ctx.send(f"Error nuking channel: {e}")

@bot.command(name='userinfo', aliases=['ui'])
async def userinfo(ctx, member: discord.Member | None = None):
    """Get information about a user"""
    member = member or ctx.author
    
    embed = discord.Embed(
        title=f"User Info - {member}",
        color=member.color
    )
    embed.set_thumbnail(url=member.display_avatar.url)
    embed.add_field(name="ID", value=member.id, inline=True)
    embed.add_field(name="Nickname", value=member.nick or "None", inline=True)
    embed.add_field(name="Status", value=str(member.status).title(), inline=True)
    if member.joined_at:
        embed.add_field(name="Joined Server", value=member.joined_at.strftime("%Y-%m-%d"), inline=True)
    embed.add_field(name="Account Created", value=member.created_at.strftime("%Y-%m-%d"), inline=True)
    embed.add_field(name="Roles", value=len(member.roles) - 1, inline=True)
    
    await ctx.send(embed=embed)

@bot.command(name='serverinfo', aliases=['si'])
async def serverinfo(ctx):
    """Get information about the server"""
    guild = ctx.guild
    
    # Calculate creation date relative time
    created = guild.created_at
    now = datetime.now(created.tzinfo)
    time_diff = now - created
    
    days = time_diff.days
    hours = time_diff.seconds // 3600
    
    if days > 0:
        time_str = f"{days} days ago" if days > 1 else "1 day ago"
    else:
        time_str = f"{hours} hours ago" if hours > 1 else "1 hour ago"
    
    # Count humans vs bots
    humans = sum(1 for m in guild.members if not m.bot)
    bots = sum(1 for m in guild.members if m.bot)
    
    # Count text vs voice channels
    text_channels = sum(1 for c in guild.channels if isinstance(c, discord.TextChannel))
    voice_channels = sum(1 for c in guild.channels if isinstance(c, discord.VoiceChannel))
    
    # Get verification level
    verification = str(guild.verification_level).replace('_', ' ').title()
    
    # Get emoji count
    emoji_count = len(guild.emojis)
    
    # Create main description
    description = f"Server created on {created.strftime('%B %d, %Y')} ({time_str})\n"
    description += f"{guild.name} is on bot shard ID: {guild.shard_id or 0}/2"
    
    embed = discord.Embed(
        title=guild.name,
        description=description,
        color=0xe91e63
    )
    
    if guild.icon:
        embed.set_thumbnail(url=guild.icon.url)
    
    # Owner section
    embed.add_field(
        name="Owner",
        value=guild.owner.mention if guild.owner else "Unknown",
        inline=True
    )
    
    # Members section
    members_text = f"Total: {guild.member_count}\nHumans: {humans}\nBots: {bots}"
    embed.add_field(
        name="Members",
        value=members_text,
        inline=True
    )
    
    # Information section
    info_text = f"Verification: {verification}\nBoosts: {guild.premium_subscription_count} (level {guild.premium_tier})"
    embed.add_field(
        name="Information",
        value=info_text,
        inline=True
    )
    
    # Channels section
    channels_text = f"Text: {text_channels}\nVoice: {voice_channels}"
    embed.add_field(
        name="Channels ({})".format(len(guild.channels)),
        value=channels_text,
        inline=True
    )
    
    # Counts section
    counts_text = f"Roles: {len(guild.roles)}\nEmojis: {emoji_count}/100"
    embed.add_field(
        name="Counts",
        value=counts_text,
        inline=True
    )
    
    # Design section
    design_text = f"Splash: {'Yes' if guild.splash else 'N/A'}\n"
    design_text += f"Banner: {'Yes' if guild.banner else 'N/A'}\n"
    design_text += f"Icon: {'Click here' if guild.icon else 'N/A'}"
    embed.add_field(
        name="Design",
        value=design_text,
        inline=True
    )
    
    # Footer with Guild ID
    embed.set_footer(text=f"Guild ID: {guild.id} • Today at {datetime.now().strftime('%I:%M %p')}")
    
    await ctx.send(embed=embed)

@bot.command(name='avatar', aliases=['av'])
async def avatar(ctx, member: discord.Member | None = None):
    """Get a user's avatar"""
    member = member or ctx.author
    
    embed = discord.Embed(
        description=f"[{member.display_name}'s avatar]({member.display_avatar.url})",
        color=0xe91e63
    )
    embed.set_image(url=member.display_avatar.url)
    embed.set_footer(text=f"User ID: {member.id}")
    
    await ctx.send(embed=embed)

@bot.command(name='banner')
async def banner(ctx, member: discord.Member | None = None):
    """Get a user's banner"""
    member = member or ctx.author
    
    user = await bot.fetch_user(member.id)
    if user.banner is None:
        embed = discord.Embed(
            description="This user has no banner set!",
            color=0xe91e63
        )
        await ctx.send(embed=embed)
        return
    
    embed = discord.Embed(
        description=f"[{member.display_name}'s banner]({user.banner.url})",
        color=0xe91e63
    )
    embed.set_image(url=user.banner.url)
    embed.set_footer(text=f"User ID: {member.id}")
    
    await ctx.send(embed=embed)

@bot.command(name='snipe', aliases=['s'])
async def snipe(ctx, index: int | None = None):
    """Snipe a deleted message (max 20 stored)"""
    # Check cooldown
    user_id = ctx.author.id
    current_time = time.time()
    
    if user_id in snipe_cooldowns:
        cooldown_time = snipe_cooldowns[user_id] + 2
        if current_time < cooldown_time:
            remaining = cooldown_time - current_time
            embed = discord.Embed(
                description=f"❌ {ctx.author.mention} - Command is on a {remaining:.2f}s cooldown",
                color=0x2f3136
            )
            await ctx.send(embed=embed, delete_after=2)
            return
    
    snipe_cooldowns[user_id] = current_time
    
    if index is None:
        index = 1
    
    if index < 1 or index > 20:
        await ctx.send("Index must be between 1 and 20!")
        return
    
    guild_data = get_guild_data(ctx.guild.id)
    snipes = guild_data['snipes']
    
    if not snipes:
        embed = discord.Embed(
            description=f"{ctx.author.mention} No deleted messages found!",
            color=0x2f3136
        )
        await ctx.send(embed=embed)
        return
    
    if index > len(snipes):
        await ctx.send(f"Only {len(snipes)} sniped message(s) available!")
        return
    
    snipe_data = snipes[index - 1]
    deleted_time = datetime.fromisoformat(snipe_data['timestamp'])
    
    def get_time_str(elapsed_seconds):
        if elapsed_seconds < 60:
            return f"{int(elapsed_seconds)} second{'s' if int(elapsed_seconds) != 1 else ''} ago"
        elif elapsed_seconds < 3600:
            minutes = int(elapsed_seconds / 60)
            return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
        else:
            hours = int(elapsed_seconds / 3600)
            return f"{hours} hour{'s' if hours != 1 else ''} ago"
    
    # Get avatar URL - try stored first, then fetch current user avatar for animations
    avatar_url = snipe_data.get('author_avatar')
    if not avatar_url:
        try:
            user = await bot.fetch_user(snipe_data['author_id'])
            avatar_url = str(user.display_avatar.url)
        except:
            avatar_url = f"https://cdn.discordapp.com/embed/avatars/0.png"
    
    # Calculate initial time
    current_time_dt = datetime.now()
    time_diff = current_time_dt - deleted_time
    time_str = get_time_str(time_diff.total_seconds())
    
    embed = discord.Embed(
        description=snipe_data['content'] or "*No content*",
        color=0x2f3136
    )
    embed.set_author(name=snipe_data['author'], icon_url=avatar_url)
    embed.set_thumbnail(url=avatar_url)
    embed.set_footer(text=f"Deleted {time_str} • {index}/{len(snipes)} messages")
    
    if snipe_data['attachments']:
        if snipe_data['attachments'][0].lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.webp')):
            embed.set_image(url=snipe_data['attachments'][0])
        else:
            attachments_text = '\n'.join(snipe_data['attachments'])
            embed.add_field(name="Attachments", value=attachments_text, inline=False)
    
    msg = await ctx.send(embed=embed)
    
    # Update timer every second for 120 seconds
    for _ in range(120):
        await asyncio.sleep(1)
        current_time_dt = datetime.now()
        time_diff = current_time_dt - deleted_time
        time_str = get_time_str(time_diff.total_seconds())
        
        try:
            embed = discord.Embed(
                description=snipe_data['content'] or "*No content*",
                color=0x2f3136
            )
            embed.set_author(name=snipe_data['author'], icon_url=avatar_url)
            embed.set_thumbnail(url=avatar_url)
            embed.set_footer(text=f"Deleted {time_str} • {index}/{len(snipes)} messages")
            
            if snipe_data['attachments']:
                if snipe_data['attachments'][0].lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.webp')):
                    embed.set_image(url=snipe_data['attachments'][0])
                else:
                    attachments_text = '\n'.join(snipe_data['attachments'])
                    embed.add_field(name="Attachments", value=attachments_text, inline=False)
            
            await msg.edit(embed=embed)
        except:
            break

@bot.command(name='clearsnipes', aliases=['cs'])
async def clear_snipes(ctx):
    """Clear all sniped messages"""
    # Check cooldown
    user_id = ctx.author.id
    current_time = time.time()
    
    if user_id in snipe_cooldowns:
        cooldown_time = snipe_cooldowns[user_id] + 2
        if current_time < cooldown_time:
            remaining = cooldown_time - current_time
            embed = discord.Embed(
                description=f"❌ {ctx.author.mention} - Command is on a {remaining:.2f}s cooldown",
                color=0x2f3136
            )
            await ctx.send(embed=embed, delete_after=2)
            return
    
    snipe_cooldowns[user_id] = current_time
    
    guild_data = get_guild_data(ctx.guild.id)
    guild_data['snipes'] = []
    save_data(data)
    await ctx.message.add_reaction("✅")

@bot.command(name='rs')
async def reaction_snipe(ctx, index=None):
    """Snipe a recently removed reaction"""
    try:
        index = int(index) if index else 1
    except:
        index = 1
    
    if index < 1 or index > 20:
        await ctx.send("Index must be between 1 and 20!")
        return
    
    # Check cooldown
    user_id = ctx.author.id
    current_time = time.time()
    
    if user_id in rs_cooldowns:
        cooldown_time = rs_cooldowns[user_id] + 2
        if current_time < cooldown_time:
            remaining = cooldown_time - current_time
            embed = discord.Embed(
                description=f"❌ {ctx.author.mention} - Command is on a {remaining:.2f}s cooldown",
                color=0x2f3136
            )
            await ctx.send(embed=embed, delete_after=2)
            return
    
    rs_cooldowns[user_id] = current_time
    
    guild_id = ctx.guild.id
    if guild_id not in reaction_snipes or not reaction_snipes[guild_id]:
        embed = discord.Embed(
            description=f"{ctx.author.mention} No removed reactions found!",
            color=0x2f3136
        )
        await ctx.send(embed=embed)
        return
    
    if index > len(reaction_snipes[guild_id]):
        await ctx.send(f"Only {len(reaction_snipes[guild_id])} removed reaction(s) available!")
        return
    
    rs_data = reaction_snipes[guild_id][index - 1]
    removed_time = datetime.fromisoformat(rs_data['timestamp'])
    
    def get_time_str(elapsed_seconds):
        if elapsed_seconds < 60:
            return f"{int(elapsed_seconds)} second{'s' if int(elapsed_seconds) != 1 else ''} ago"
        elif elapsed_seconds < 3600:
            minutes = int(elapsed_seconds / 60)
            return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
        else:
            hours = int(elapsed_seconds / 3600)
            return f"{hours} hour{'s' if hours != 1 else ''} ago"
    
    # Send initial message
    current_time_dt = datetime.now()
    time_diff = current_time_dt - removed_time
    time_str = get_time_str(time_diff.total_seconds())
    
    embed = discord.Embed(
        description=f"{rs_data['user']} reacted with {rs_data['emoji']} {time_str}\n\n{rs_data['message_content']}",
        color=0x2f3136
    )
    embed.set_footer(text=f"Message by {rs_data['message_author']} • {index}/{len(reaction_snipes[guild_id])} reactions")
    
    msg = await ctx.send(embed=embed)
    
    # Update timer every second for 120 seconds
    for _ in range(120):
        await asyncio.sleep(1)
        current_time_dt = datetime.now()
        time_diff = current_time_dt - removed_time
        time_str = get_time_str(time_diff.total_seconds())
        
        try:
            embed = discord.Embed(
                description=f"{rs_data['user']} reacted with {rs_data['emoji']} {time_str}\n\n{rs_data['message_content']}",
                color=0x2f3136
            )
            embed.set_footer(text=f"Message by {rs_data['message_author']} • {index}/{len(reaction_snipes[guild_id])} reactions")
            await msg.edit(embed=embed)
        except:
            break

@bot.command(name='autorole')
@commands.has_permissions(administrator=True)
async def autorole(ctx, action: str | None = None, role: discord.Role | None = None):
    """Manage auto role assignment for new members"""
    guild_data = get_guild_data(ctx.guild.id)
    ar_data = guild_data['autorole']
    
    if action is None:
        embed = discord.Embed(
            title="AutoRole Commands",
            description="Manage automatic role assignment",
            color=0xe91e63
        )
        embed.add_field(name=",autorole set @role", value="Set the role to auto-assign", inline=False)
        embed.add_field(name=",autorole enable", value="Enable auto role", inline=False)
        embed.add_field(name=",autorole disable", value="Disable auto role", inline=False)
        embed.add_field(name=",autorole info", value="Show current settings", inline=False)
        await ctx.send(embed=embed)
        return
    
    action = action.lower()
    
    if action == 'set':
        if not role:
            await ctx.send("Please mention a role: `,autorole set @role`")
            return
        ar_data['role_id'] = role.id
        save_data(data)
        await ctx.send(f"Auto role set to {role.mention}")
    
    elif action == 'enable':
        if not ar_data['role_id']:
            await ctx.send("Please set a role first: `,autorole set @role`")
            return
        ar_data['enabled'] = True
        save_data(data)
        await ctx.send("Auto role **enabled**!")
    
    elif action == 'disable':
        ar_data['enabled'] = False
        save_data(data)
        await ctx.send("Auto role **disabled**!")
    
    elif action == 'info':
        role = ctx.guild.get_role(ar_data['role_id']) if ar_data['role_id'] else None
        embed = discord.Embed(
            title="AutoRole Settings",
            color=0xe91e63
        )
        embed.add_field(name="Status", value="✅ Enabled" if ar_data['enabled'] else "❌ Disabled", inline=True)
        embed.add_field(name="Role", value=role.mention if role else "Not set", inline=True)
        await ctx.send(embed=embed)

@bot.command(name='pingonjoin', aliases=['poj'])
@commands.has_permissions(administrator=True)
async def ping_on_join(ctx, action: str | None = None, channel: discord.TextChannel | None = None):
    """Manage ping on join feature"""
    guild_data = get_guild_data(ctx.guild.id)
    poj_data = guild_data['ping_on_join']
    
    if action is None:
        embed = discord.Embed(
            title="Ping on Join Commands",
            description="Ping users in selected text channels when they join voice channels",
            color=0xe91e63
        )
        embed.add_field(name=",pingonjoin toggle", value="Enable/disable ping on join", inline=False)
        embed.add_field(name=",pingonjoin add #channel", value="Add text channel for pings", inline=False)
        embed.add_field(name=",pingonjoin remove #channel", value="Remove text channel from ping list", inline=False)
        embed.add_field(name=",pingonjoin info", value="Show current settings", inline=False)
        await ctx.send(embed=embed)
        return
    
    action = action.lower()
    
    if action == 'toggle':
        poj_data['enabled'] = not poj_data['enabled']
        save_data(data)
        status = "✅ enabled" if poj_data['enabled'] else "❌ disabled"
        await ctx.send(f"Ping on Join {status}!")
    
    elif action == 'add':
        if not channel:
            await ctx.send("Please mention a text channel: `,pingonjoin add #channel`")
            return
        if channel.id not in poj_data['channels']:
            poj_data['channels'].append(channel.id)
            save_data(data)
            await ctx.send(f"Added {channel.mention} to ping on join!")
        else:
            await ctx.send(f"{channel.mention} is already in the list!")
    
    elif action == 'remove':
        if not channel:
            await ctx.send("Please mention a text channel: `,pingonjoin remove #channel`")
            return
        if channel.id in poj_data['channels']:
            poj_data['channels'].remove(channel.id)
            save_data(data)
            await ctx.send(f"Removed {channel.mention} from ping on join!")
        else:
            await ctx.send(f"{channel.mention} is not in the list!")
    
    elif action == 'info':
        channels_list = []
        for ch_id in poj_data['channels']:
            ch = ctx.guild.get_channel(ch_id)
            if ch:
                channels_list.append(ch.mention)
        
        embed = discord.Embed(
            title="Ping on Join Settings",
            color=0xe91e63
        )
        embed.add_field(name="Status", value="✅ Enabled" if poj_data['enabled'] else "❌ Disabled", inline=True)
        embed.add_field(name="Text Channels", value='\n'.join(channels_list) if channels_list else "No channels selected", inline=False)
        await ctx.send(embed=embed)

@bot.command(name='welcome')
@commands.has_permissions(administrator=True)
async def welcome_command(ctx, action: str | None = None, channel: discord.TextChannel | None = None, *, args: str | None = None):
    """Set up welcome messages for new members"""
    guild_data = get_guild_data(ctx.guild.id)
    welcome_data = guild_data['welcome']
    
    if action is None:
        embed = discord.Embed(
            title="Welcome Commands",
            description="Set up welcome messages for new members",
            color=0xe91e63
        )
        embed.add_field(name=",welcome add (channel) (message) --params", value="Add a welcome message to a channel", inline=False)
        embed.add_field(name=",welcome remove (channel)", value="Remove welcome from a channel", inline=False)
        embed.add_field(name=",welcome list", value="View all welcome messages", inline=False)
        embed.add_field(name="Placeholders", value="{user.mention}, {user.name}, {user.display_name}, {guild.name}, {guild.member_count}", inline=False)
        embed.add_field(name="Parameters", value="--self_destruct (seconds)", inline=False)
        embed.add_field(name="Example", value="`,welcome add #welcome Welcome {user.mention}! Member count: {guild.member_count} --self_destruct 10`", inline=False)
        await ctx.send(embed=embed)
        return
    
    action = action.lower()
    
    if action == 'add':
        if not channel or not args:
            await ctx.send("Syntax: `,welcome add (channel) (message) --params`")
            return
        
        self_destruct = None
        if '--self_destruct' in args:
            parts = args.split('--self_destruct')
            message_text = parts[0].strip()
            try:
                self_destruct = int(parts[1].strip().split()[0])
            except:
                await ctx.send("Invalid self_destruct value!")
                return
        else:
            message_text = args
        
        channel_id = str(channel.id)
        welcome_data[channel_id] = {
            'channel_name': channel.name,
            'message': message_text,
            'self_destruct': self_destruct
        }
        save_data(data)
        await ctx.send(f"✅ Welcome message set for {channel.mention}!")
    
    elif action == 'remove':
        if not channel:
            await ctx.send("Syntax: `,welcome remove (channel)`")
            return
        
        channel_id = str(channel.id)
        if channel_id in welcome_data:
            del welcome_data[channel_id]
            save_data(data)
            await ctx.send(f"✅ Removed welcome message from {channel.mention}!")
        else:
            await ctx.send(f"No welcome message found in {channel.mention}!")
    
    elif action == 'list':
        embed = discord.Embed(
            title="Welcome Messages",
            color=0xe91e63
        )
        
        if welcome_data:
            for channel_id, config in welcome_data.items():
                ch = ctx.guild.get_channel(int(channel_id))
                if ch:
                    self_destruct_text = f" (auto-delete in {config['self_destruct']}s)" if config.get('self_destruct') else ""
                    embed.add_field(
                        name=ch.mention,
                        value=f"```{config['message'][:100]}...```{self_destruct_text}",
                        inline=False
                    )
        else:
            embed.description = "No welcome messages configured!"
        
        await ctx.send(embed=embed)

@bot.command(name='filter')
@commands.has_permissions(administrator=True)
async def filter_command(ctx, action: str | None = None, *, word: str | None = None):
    """Manage word filter blacklist and spam filter"""
    guild_data = get_guild_data(ctx.guild.id)
    filter_words = guild_data['filter']
    spam_filter = guild_data.get('spam_filter', {})
    
    if action is None:
        embed = discord.Embed(
            title="Filter Commands",
            description="Manage blacklisted words and spam",
            color=0xe91e63
        )
        embed.add_field(name=",filter add word", value="Add a word to the blacklist", inline=False)
        embed.add_field(name=",filter remove word", value="Remove a word from the blacklist", inline=False)
        embed.add_field(name=",filter spam on --threshold 5 --timeframe 5000", value="Enable spam filter", inline=False)
        embed.add_field(name=",filter spam off", value="Disable spam filter", inline=False)
        embed.add_field(name=",filterlist", value="Show all blacklisted words", inline=False)
        await ctx.send(embed=embed)
        return
    
    action = action.lower()
    
    if action == 'spam':
        state = word.split()[0].lower() if word else None
        if state not in ['on', 'off']:
            await ctx.message.add_reaction('❌')
            return
        
        if state == 'on':
            spam_filter['enabled'] = True
            threshold = 5
            timeframe = 5000
            
            if word:
                if '--threshold' in word:
                    try:
                        threshold = int(word.split('--threshold')[1].split()[0])
                    except:
                        pass
                if '--timeframe' in word:
                    try:
                        timeframe = int(word.split('--timeframe')[1].split()[0])
                    except:
                        pass
            
            spam_filter['threshold'] = threshold
            spam_filter['timeframe'] = timeframe
            save_data(data)
            await ctx.message.add_reaction('✅')
        
        elif state == 'off':
            spam_filter['enabled'] = False
            save_data(data)
            await ctx.message.add_reaction('✅')
    
    elif action == 'add':
        if not word:
            await ctx.send("Please provide a word: `,filter add word`")
            return
        if word.lower() not in [w.lower() for w in filter_words]:
            filter_words.append(word)
            save_data(data)
            await ctx.send(f"✅ Added **{word}** to the blacklist!")
        else:
            await ctx.send(f"**{word}** is already in the blacklist!")
    
    elif action == 'remove':
        if not word:
            await ctx.send("Please provide a word: `,filter remove word`")
            return
        matching_word = next((w for w in filter_words if w.lower() == word.lower()), None)
        if matching_word:
            filter_words.remove(matching_word)
            save_data(data)
            await ctx.send(f"✅ Removed **{matching_word}** from the blacklist!")
        else:
            await ctx.send(f"**{word}** is not in the blacklist!")

@bot.command(name='filterlist')
async def filter_list(ctx):
    """Show all blacklisted words"""
    guild_data = get_guild_data(ctx.guild.id)
    filter_words = guild_data['filter']
    
    embed = discord.Embed(
        title="Blacklisted Words",
        color=0xe91e63
    )
    
    if filter_words:
        words_text = ', '.join([f"**{word}**" for word in filter_words])
        embed.description = words_text
        embed.add_field(name="Total", value=len(filter_words), inline=False)
    else:
        embed.description = "No blacklisted words!"
    
    await ctx.send(embed=embed)

@bot.command(name='log')
@commands.has_permissions(administrator=True)
async def log_command(ctx, action: str | None = None, channel: discord.TextChannel | None = None, *, event: str | None = None):
    """Manage server logging"""
    guild_data = get_guild_data(ctx.guild.id)
    logs_data = guild_data['logs']
    
    valid_events = ['messages', 'members', 'joinandleaves', 'roles', 'channels', 'invites', 'emojis', 'voice', 'all']
    
    if action is None:
        embed = discord.Embed(
            title="Log Commands",
            description="Set up logging in channels",
            color=0xe91e63
        )
        embed.add_field(name=",log add (channel) (event)", value="Set up logging in a channel", inline=False)
        embed.add_field(name=",log remove (channel) (event)", value="Remove logging from a channel", inline=False)
        embed.add_field(name=",log list", value="View all logging configurations", inline=False)
        embed.add_field(name="Available Events", value=', '.join(valid_events), inline=False)
        await ctx.send(embed=embed)
        return
    
    action = action.lower()
    
    if action == 'add':
        if not channel or not event:
            await ctx.send("Syntax: `,log add (channel) (event)`\nExample: `,log add #logs all`")
            return
        
        if event.lower() not in valid_events:
            await ctx.send(f"Invalid event! Available: {', '.join(valid_events)}")
            return
        
        channel_id = str(channel.id)
        if channel_id not in logs_data:
            logs_data[channel_id] = {'channel_name': channel.name, 'events': []}
        
        if event.lower() not in logs_data[channel_id]['events']:
            logs_data[channel_id]['events'].append(event.lower())
            save_data(data)
            await ctx.message.add_reaction("✅")
        else:
            await ctx.send(f"**{event}** is already being logged in {channel.mention}!")
    
    elif action == 'remove':
        if not channel or not event:
            await ctx.send("Syntax: `,log remove (channel) (event)`")
            return
        
        channel_id = str(channel.id)
        if channel_id in logs_data and event.lower() in logs_data[channel_id]['events']:
            logs_data[channel_id]['events'].remove(event.lower())
            if not logs_data[channel_id]['events']:
                del logs_data[channel_id]
            save_data(data)
            await ctx.send(f"✅ Removed **{event}** logging from {channel.mention}!")
        else:
            await ctx.send(f"No **{event}** logging found in {channel.mention}!")
    
    elif action == 'list':
        embed = discord.Embed(
            title="Logging Configuration",
            color=0xe91e63
        )
        
        if logs_data:
            for channel_id, config in logs_data.items():
                ch = ctx.guild.get_channel(int(channel_id))
                if ch:
                    events_str = ', '.join([f"**{e}**" for e in config['events']])
                    embed.add_field(name=ch.mention, value=events_str, inline=False)
        else:
            embed.description = "No logging channels configured!"
        
        await ctx.send(embed=embed)

async def log_event(guild, embed, event_type):
    """Send log event to all configured log channels"""
    guild_data = get_guild_data(guild.id)
    logs_data = guild_data['logs']
    
    for channel_id, config in logs_data.items():
        should_log = False
        
        # Check if event matches
        if event_type in config['events'] or 'all' in config['events']:
            should_log = True
        
        # Special case: 'joinandleaves' logs member events (joins/leaves)
        if event_type == 'members' and 'joinandleaves' in config['events']:
            should_log = True
        
        if should_log:
            ch = guild.get_channel(int(channel_id))
            if ch:
                try:
                    await ch.send(embed=embed)
                except:
                    pass

@bot.event
async def on_member_update(before, after):
    """Log member updates (roles, etc)"""
    # Check if roles were added
    added_roles = [role for role in after.roles if role not in before.roles]
    
    if added_roles:
        embed = discord.Embed(
            title="Member Role Added",
            description=f"Member: {after.name} {after.id}",
            color=0x4caf50
        )
        embed.set_thumbnail(url=after.display_avatar.url)
        
        role_names = ", ".join([role.name for role in added_roles])
        embed.add_field(name="Roles Added", value=role_names, inline=False)
        embed.set_footer(text=f"User ID: {after.id} • {datetime.now().strftime('%m/%d/%Y, %I:%M:%S %p')} • Yesterday at {datetime.now().strftime('%I:%M %p')}")
        
        await log_event(after.guild, embed, 'members')

@bot.event
async def on_member_remove(member):
    """Log member leaves"""
    embed = discord.Embed(
        title="Member Left",
        description=f"{member.name} {member.id} left the server",
        color=0xff9800
    )
    embed.set_thumbnail(url=member.display_avatar.url)
    embed.add_field(name="ID", value=f"{member.id}", inline=False)
    embed.set_footer(text=f"Yesterday at {datetime.now().strftime('%I:%M %p')}")
    
    await log_event(member.guild, embed, 'members')

@bot.event
async def on_guild_role_update(before, after):
    """Log role updates (position, hoisted, etc)"""
    changes = []
    
    if before.position != after.position:
        changes.append(f"Position: {before.position} → {after.position}")
    
    if before.hoist != after.hoist:
        changes.append(f"Hoisted: {'Yes' if before.hoist else 'No'} → {'Yes' if after.hoist else 'No'}")
    
    if not changes:
        return
    
    embed = discord.Embed(
        title="Role Updated",
        description=f"Role: {after.name} {after.id}",
        color=0xffa500
    )
    
    for change in changes:
        embed.add_field(name="", value=change, inline=False)
    
    embed.set_footer(text=f"Role ID: {after.id} • {datetime.now().strftime('%m/%d/%Y, %I:%M:%S %p')} • Yesterday at {datetime.now().strftime('%I:%M %p')}")
    
    await log_event(after.guild, embed, 'roles')

@bot.event
async def on_guild_role_create(role):
    """Log role creation"""
    embed = discord.Embed(
        title="Role Created",
        description=f"Role: {role.name} {role.id}",
        color=0x4caf50
    )
    embed.set_footer(text=f"Role ID: {role.id}")
    
    await log_event(role.guild, embed, 'roles')

@bot.event
async def on_guild_role_delete(role):
    """Log role deletion"""
    embed = discord.Embed(
        title="Role Deleted",
        description=f"Role: {role.name} {role.id}",
        color=0xf44336
    )
    embed.set_footer(text=f"Role ID: {role.id}")
    
    await log_event(role.guild, embed, 'roles')

@bot.event
async def on_guild_channel_create(channel):
    """Log channel creation"""
    embed = discord.Embed(
        title="Channel Created",
        description=f"{channel.mention}",
        color=0x4caf50
    )
    embed.timestamp = datetime.now()
    
    await log_event(channel.guild, embed, 'channels')

@bot.event
async def on_guild_channel_delete(channel):
    """Log channel deletion"""
    embed = discord.Embed(
        title="Channel Deleted",
        description=f"{channel.name}",
        color=0xf44336
    )
    embed.timestamp = datetime.now()
    
    await log_event(channel.guild, embed, 'channels')

@bot.event
async def on_invite_create(invite):
    """Log invite creation"""
    max_uses_text = "Unlimited" if invite.max_uses == 0 else str(invite.max_uses)
    max_age_text = "Unlimited" if invite.max_age is None else f"{invite.max_age}s"
    temp_text = "Yes" if invite.temporary else "No"
    
    embed = discord.Embed(
        title="Invite Created",
        color=0x2d9d3f
    )
    embed.add_field(name="Code", value=invite.code, inline=False)
    embed.add_field(name="Channel", value=f"{invite.channel.name} {invite.channel.id}", inline=False)
    embed.add_field(name="Inviter", value=f"{invite.inviter.name if invite.inviter else 'Unknown'} {invite.inviter.id if invite.inviter else ''}", inline=False)
    embed.add_field(name="Max Uses", value=max_uses_text, inline=False)
    embed.add_field(name="Max Age", value=max_age_text, inline=False)
    embed.add_field(name="Temporary", value=temp_text, inline=False)
    embed.set_footer(text=f"Invite Code: {invite.code} • {datetime.now().strftime('%m/%d/%Y, %I:%M:%S %p')} • Today at {datetime.now().strftime('%I:%M %p')}")
    
    await log_event(invite.guild, embed, 'invites')

@bot.event
async def on_invite_delete(invite):
    """Log invite deletion"""
    embed = discord.Embed(
        title="Invite Deleted",
        color=0xff9800
    )
    embed.add_field(name="Code", value=invite.code, inline=False)
    embed.add_field(name="Channel", value=f"{invite.channel.name} {invite.channel.id}", inline=False)
    embed.set_footer(text=f"Invite Code: {invite.code} • {datetime.now().strftime('%m/%d/%Y, %I:%M:%S %p')}")
    
    await log_event(invite.guild, embed, 'invites')

@bot.event
async def on_guild_emojis_update(guild, before, after):
    """Log emoji changes"""
    if len(before) < len(after):
        new_emoji = [e for e in after if e not in before][0]
        embed = discord.Embed(
            title="Emoji Added",
            description=f"{new_emoji} - **{new_emoji.name}**",
            color=0x4caf50
        )
    else:
        removed_emoji = [e for e in before if e not in after][0]
        embed = discord.Embed(
            title="Emoji Removed",
            description=f"**{removed_emoji.name}**",
            color=0xf44336
        )
    
    embed.timestamp = datetime.now()
    await log_event(guild, embed, 'emojis')

@bot.event
async def on_member_ban(guild, user):
    """Anti-nuke: Prevent mass bans"""
    guild_data = get_guild_data(guild.id)
    antinuke = guild_data.get('antinuke', {})
    if not antinuke.get('enabled') or not antinuke.get('mass_member_ban'):
        return
    if user.id in antinuke.get('whitelist', []):
        return
    try:
        async for entry in guild.audit_logs(action=discord.AuditLogAction.ban, limit=1):
            if entry.user.id not in antinuke.get('admins', []) and not entry.user.guild_permissions.administrator:
                await entry.user.kick(reason="Anti-nuke protection")
                
                # DM the server owner
                owner = guild.owner
                if owner:
                    embed = discord.Embed(
                        title="User Punished",
                        color=0x000000
                    )
                    embed.add_field(name="Server:", value=guild.name, inline=False)
                    embed.add_field(name="User:", value=entry.user.name, inline=False)
                    embed.add_field(name="Action", value="Mass Banning Members", inline=False)
                    embed.add_field(name="Punishment Type", value="Kick", inline=False)
                    embed.set_footer(text=f"Timestamp: {datetime.now().strftime('%m/%d/%Y, %I:%M:%S %p')}")
                    try:
                        await owner.send(embed=embed)
                    except:
                        pass
    except:
        pass

@bot.event
async def on_member_remove(guild, member):
    """Anti-nuke: Prevent mass kicks"""
    guild_data = get_guild_data(guild.id)
    antinuke = guild_data.get('antinuke', {})
    if not antinuke.get('enabled') or not antinuke.get('mass_member_kick'):
        return
    if member.id in antinuke.get('whitelist', []):
        return
    try:
        async for entry in guild.audit_logs(action=discord.AuditLogAction.kick, limit=1):
            if entry.user.id not in antinuke.get('admins', []) and not entry.user.guild_permissions.administrator:
                await entry.user.kick(reason="Anti-nuke protection")
                
                # DM the server owner
                owner = guild.owner
                if owner:
                    embed = discord.Embed(
                        title="User Punished",
                        color=0x000000
                    )
                    embed.add_field(name="Server:", value=guild.name, inline=False)
                    embed.add_field(name="User:", value=entry.user.name, inline=False)
                    embed.add_field(name="Action", value="Mass Kicking Members", inline=False)
                    embed.add_field(name="Punishment Type", value="Kick", inline=False)
                    embed.set_footer(text=f"Timestamp: {datetime.now().strftime('%m/%d/%Y, %I:%M:%S %p')}")
                    try:
                        await owner.send(embed=embed)
                    except:
                        pass
    except:
        pass

@bot.event
async def on_guild_channel_delete(channel):
    """Anti-nuke: Prevent channel deletion"""
    guild = channel.guild
    guild_data = get_guild_data(guild.id)
    antinuke = guild_data.get('antinuke', {})
    if not antinuke.get('enabled') or not antinuke.get('channel_deletion'):
        return
    try:
        async for entry in guild.audit_logs(action=discord.AuditLogAction.channel_delete, limit=1):
            if entry.user.id not in antinuke.get('admins', []) and not entry.user.guild_permissions.administrator:
                await entry.user.kick(reason="Anti-nuke protection")
                
                # DM the server owner
                owner = guild.owner
                if owner:
                    embed = discord.Embed(
                        title="User Punished",
                        color=0x000000
                    )
                    embed.add_field(name="Server:", value=guild.name, inline=False)
                    embed.add_field(name="User:", value=entry.user.name, inline=False)
                    embed.add_field(name="Action", value="Deleting Channels", inline=False)
                    embed.add_field(name="Punishment Type", value="Kick", inline=False)
                    embed.set_footer(text=f"Timestamp: {datetime.now().strftime('%m/%d/%Y, %I:%M:%S %p')}")
                    try:
                        await owner.send(embed=embed)
                    except:
                        pass
    except:
        pass

@bot.event
async def on_guild_role_delete(role):
    """Anti-nuke: Prevent role deletion"""
    guild = role.guild
    guild_data = get_guild_data(guild.id)
    antinuke = guild_data.get('antinuke', {})
    if not antinuke.get('enabled') or not antinuke.get('role_deletion'):
        return
    try:
        async for entry in guild.audit_logs(action=discord.AuditLogAction.role_delete, limit=1):
            if entry.user.id not in antinuke.get('admins', []) and not entry.user.guild_permissions.administrator:
                await entry.user.kick(reason="Anti-nuke protection")
                
                # DM the server owner
                owner = guild.owner
                if owner:
                    embed = discord.Embed(
                        title="User Punished",
                        color=0x000000
                    )
                    embed.add_field(name="Server:", value=guild.name, inline=False)
                    embed.add_field(name="User:", value=entry.user.name, inline=False)
                    embed.add_field(name="Action", value="Deleting Roles", inline=False)
                    embed.add_field(name="Punishment Type", value="Kick", inline=False)
                    embed.set_footer(text=f"Timestamp: {datetime.now().strftime('%m/%d/%Y, %I:%M:%S %p')}")
                    try:
                        await owner.send(embed=embed)
                    except:
                        pass
    except:
        pass

@bot.event
async def on_guild_emojis_update_antinuke(guild, before, after):
    """Anti-nuke: Prevent emoji deletion"""
    guild_data = get_guild_data(guild.id)
    antinuke = guild_data.get('antinuke', {})
    if not antinuke.get('enabled') or not antinuke.get('emoji_deletion'):
        return
    if len(before) > len(after):
        try:
            async for entry in guild.audit_logs(action=discord.AuditLogAction.emoji_delete, limit=1):
                if entry.user.id not in antinuke.get('admins', []) and not entry.user.guild_permissions.administrator:
                    await entry.user.kick(reason="Anti-nuke protection")
                    
                    # DM the server owner
                    owner = guild.owner
                    if owner:
                        embed = discord.Embed(
                            title="User Punished",
                            color=0x000000
                        )
                        embed.add_field(name="Server:", value=guild.name, inline=False)
                        embed.add_field(name="User:", value=entry.user.name, inline=False)
                        embed.add_field(name="Action", value="Deleting Emojis", inline=False)
                        embed.add_field(name="Punishment Type", value="Kick", inline=False)
                        embed.set_footer(text=f"Timestamp: {datetime.now().strftime('%m/%d/%Y, %I:%M:%S %p')}")
                        try:
                            await owner.send(embed=embed)
                        except:
                            pass
        except:
            pass

@bot.event
async def on_webhook_update_antinuke(channel):
    """Anti-nuke: Prevent webhook creation"""
    guild = channel.guild
    guild_data = get_guild_data(guild.id)
    antinuke = guild_data.get('antinuke', {})
    if not antinuke.get('enabled') or not antinuke.get('webhook_creation'):
        return
    try:
        async for entry in guild.audit_logs(action=discord.AuditLogAction.webhook_create, limit=1):
            if entry.user.id not in antinuke.get('admins', []) and not entry.user.guild_permissions.administrator:
                await entry.user.kick(reason="Anti-nuke protection")
                
                # DM the server owner
                owner = guild.owner
                if owner:
                    embed = discord.Embed(
                        title="User Punished",
                        color=0x000000
                    )
                    embed.add_field(name="Server:", value=guild.name, inline=False)
                    embed.add_field(name="User:", value=entry.user.name, inline=False)
                    embed.add_field(name="Action", value="Creating Webhooks", inline=False)
                    embed.add_field(name="Punishment Type", value="Kick", inline=False)
                    embed.set_footer(text=f"Timestamp: {datetime.now().strftime('%m/%d/%Y, %I:%M:%S %p')}")
                    try:
                        await owner.send(embed=embed)
                    except:
                        pass
    except:
        pass

@bot.event
async def on_guild_update(before, after):
    """Track vanity changes and anti-nuke protection"""
    guild = after
    guild_data = get_guild_data(guild.id)
    
    # Check if vanity URL changed
    if before.vanity_url != after.vanity_url:
        # Track vanity history globally
        if before.vanity_url:
            vanity = before.vanity_url.split('discord.gg/')[-1] if before.vanity_url else None
            vanity_history = data.get('vanity_history', [])
            vanity_history.append({
                'vanity': vanity,
                'changed_at': datetime.now().isoformat()
            })
            if len(vanity_history) > 5000:
                vanity_history = vanity_history[-5000:]
            data['vanity_history'] = vanity_history
            save_data(data)
        
        # Anti-nuke protection
        antinuke = guild_data.get('antinuke', {})
        if antinuke.get('enabled') and antinuke.get('vanity_protection'):
            try:
                async for entry in guild.audit_logs(action=discord.AuditLogAction.guild_update, limit=1):
                    if entry.user.id not in antinuke.get('admins', []) and not entry.user.guild_permissions.administrator:
                        await entry.user.kick(reason="Anti-nuke protection")
                        
                        # DM the server owner
                        owner = guild.owner
                        if owner:
                            embed = discord.Embed(
                                title="User Punished",
                                color=0x000000
                            )
                            embed.add_field(name="Server:", value=guild.name, inline=False)
                            embed.add_field(name="User:", value=entry.user.name, inline=False)
                            embed.add_field(name="Action", value="Editing Vanity URL", inline=False)
                            embed.add_field(name="Punishment Type", value="Kick", inline=False)
                            embed.set_footer(text=f"Timestamp: {datetime.now().strftime('%m/%d/%Y, %I:%M:%S %p')}")
                            try:
                                await owner.send(embed=embed)
                            except:
                                pass
            except:
                pass

@bot.event
async def on_guild_channel_create(channel):
    """Auto-deny jailed role from viewing new channels"""
    guild_data = get_guild_data(channel.guild.id)
    jail_data = guild_data['jail']
    
    if jail_data['enabled'] and jail_data['role_id']:
        jail_role = channel.guild.get_role(jail_data['role_id'])
        if jail_role:
            try:
                await channel.set_permissions(jail_role, view_channel=False)
            except:
                pass

@bot.event
async def on_user_update(before, after):
    """Track username changes globally"""
    if before.name != after.name:
        history = data.get('username_history', [])
        history.append({
            'username': before.name,
            'changed_at': datetime.now().isoformat()
        })
        if len(history) > 5000:
            history = history[-5000:]
        data['username_history'] = history
        save_data(data)

@bot.event
async def on_user_join_antinuke(user):
    """Anti-nuke: Prevent bot joins"""
    if user.bot:
        guild_data = get_guild_data(user.guild.id)
        antinuke = guild_data.get('antinuke', {})
        if not antinuke.get('enabled') or not antinuke.get('deny_bot_joins'):
            return
        try:
            await user.kick(reason="Anti-nuke: Unauthorized bot added")
        except:
            pass

class CommandsPaginationView(discord.ui.View):
    def __init__(self, pages, ctx):
        super().__init__(timeout=60)
        self.pages = pages
        self.current_page = 0
        self.ctx = ctx
    
    def update_buttons(self):
        self.prev_button.disabled = self.current_page == 0
        self.next_button.disabled = self.current_page == len(self.pages) - 1
    
    @discord.ui.button(label="◀", style=discord.ButtonStyle.blurple)
    async def prev_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.ctx.author:
            await interaction.response.send_message("You didn't invoke this command!", ephemeral=True)
            return
        
        if self.current_page > 0:
            self.current_page -= 1
            self.update_buttons()
            await interaction.response.edit_message(embed=self.pages[self.current_page], view=self)
    
    @discord.ui.button(label="▶", style=discord.ButtonStyle.blurple)
    async def next_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.ctx.author:
            await interaction.response.send_message("You didn't invoke this command!", ephemeral=True)
            return
        
        if self.current_page < len(self.pages) - 1:
            self.current_page += 1
            self.update_buttons()
            await interaction.response.edit_message(embed=self.pages[self.current_page], view=self)

@bot.command(name='commands', aliases=['cmds'])
async def commands_command(ctx):
    """Display all commands in paginated format"""
    commands_data = {
        "Economy": [
            "`,balance` / `,bal` - Check balance",
            "`,daily` - Claim daily reward",
            "`,work` - Work to earn money",
            "`,deposit` / `,dep` - Deposit to bank",
            "`,withdraw` / `,with` - Withdraw from bank",
            "`,rob @user` - Rob another user"
        ],
        "Leveling": [
            "`,rank` - Check your level",
            "`,leaderboard` / `,lb` - Top 10 by XP",
            "`,vcleaderboard` / `,vclb` - Top 10 VC users",
            "`,messageleaderboard` / `,mslb` - Top 10 most messages"
        ],
        "Moderation": [
            "`,kick @user [reason]` - Kick a member",
            "`,ban @user [reason]` - Ban a member",
            "`,clear [amount]` - Clear messages",
            "`,purge [amount]` - Purge messages",
            "`,timeout @user 1m/10m/1h/10h/1d/7d` - Timeout",
            "`,hide` - Hide channel",
            "`,unhide` - Unhide channel",
            "`,lock` - Lock channel",
            "`,unlock` - Unlock channel",
            "`,nuke` - Delete & recreate channel"
        ],
        "Utility": [
            "`,userinfo` / `,ui` - User info",
            "`,serverinfo` / `,si` - Server info",
            "`,avatar` / `,av` - Get avatar",
            "`,banner` - Get banner",
            "`,su` - Server stats",
            "`,help` - Show this help"
        ],
        "Snipes": [
            "`,snipe` / `,s` - Most recent deleted",
            "`,s 2-5` - Get specific sniped message",
            "`,clearsnipes` / `,cs` - Clear snipes"
        ],
        "AutoRole": [
            "`,autorole set @role` - Set auto role",
            "`,autorole enable` - Enable auto role",
            "`,autorole disable` - Disable auto role",
            "`,autorole info` - Show settings"
        ],
        "Ping on Join": [
            "`,pingonjoin toggle` - Enable/disable",
            "`,pingonjoin add #channel` - Add channel",
            "`,pingonjoin remove #channel` - Remove channel",
            "`,pingonjoin info` - Show settings"
        ],
        "Filter": [
            "`,filter add word` - Blacklist word",
            "`,filter remove word` - Unblacklist",
            "`,filter spam` - Configure spam filter",
            "`,filterlist` - Show blacklist"
        ],
        "Welcome": [
            "`,welcome add #channel message` - Add welcome",
            "`,welcome remove #channel` - Remove welcome",
            "`,welcome list` - Show welcomes"
        ],
        "Logging": [
            "`,log add #channel event` - Add log",
            "`,log remove #channel event` - Remove log",
            "`,log list` - Show logs",
            "**Events**: messages, members, joinandleaves, roles, channels, invites, emojis, voice, all"
        ],
        "VoiceMaster": [
            "`,voicemaster setup` - Setup VoiceMaster",
            "`,voicemaster priv setup` - Setup private VCs",
            "`,voicemaster disable` - Disable",
            "`,voicemaster reset` - Reset VoiceMaster",
            "`,voicemaster category <id>` - Set category",
            "`,voicemaster interface` - Show panel"
        ],
        "Vanity": [
            "`,vanity set <substring>` - Monitor for vanity",
            "`,vanity award channel #channel` - Set award channel",
            "`,vanity log channel #channel` - Set log channel",
            "`,vanity message <msg>` - Set award message",
            "`,vanity role add @role` - Add reward role",
            "`,vanity role remove @role` - Remove reward role",
            "`,vanity role list` - View roles",
            "`,vanity status` - View settings",
            "`,vanity reset` - Reset vanity"
        ],
        "Anti-Nuke": [
            "`,antinuke enable` - Enable anti-nuke",
            "`,antinuke disable` - Disable anti-nuke",
            "`,antinuke role on/off` - Role deletion protection",
            "`,antinuke channel on/off` - Channel deletion protection",
            "`,antinuke emoji on/off` - Emoji deletion protection",
            "`,antinuke massban on/off` - Mass ban protection",
            "`,antinuke masskick on/off` - Mass kick protection",
            "`,antinuke webhook on/off` - Webhook creation protection",
            "`,antinuke vanity on/off` - Vanity URL protection",
            "`,antinuke botadd on/off` - Deny bot joins",
            "`,antinuke superadmin add @user` - Add super admin",
            "`,antinuke whitelist add @user` - Whitelist member",
            "`,antinuke config` - View settings"
        ]
    }
    
    pages = []
    category_list = list(commands_data.items())
    
    # Create pages - 2 categories per page
    for i in range(0, len(category_list), 2):
        embed = discord.Embed(
            title="📖 All Commands",
            color=0x000000
        )
        
        # Add first category
        category, cmds = category_list[i]
        embed.add_field(
            name=f"**{category}**",
            value="\n".join(cmds),
            inline=False
        )
        
        # Add second category if exists
        if i + 1 < len(category_list):
            category, cmds = category_list[i + 1]
            embed.add_field(
                name=f"**{category}**",
                value="\n".join(cmds),
                inline=False
            )
        
        page_num = (i // 2) + 1
        total_pages = (len(category_list) + 1) // 2
        embed.set_footer(text=f"Page {page_num}/{total_pages}")
        pages.append(embed)
    
    view = CommandsPaginationView(pages, ctx)
    view.update_buttons()
    
    await ctx.send(embed=pages[0], view=view)

@bot.command(name='antinuke')
@commands.has_permissions(manage_guild=True)
async def antinuke(ctx, action: str | None = None, *, args: str | None = None):
    """Configure anti-nuke protection for your server"""
    guild_data = get_guild_data(ctx.guild.id)
    antinuke = guild_data['antinuke']
    
    if action is None:
        embed = discord.Embed(
            title="Anti-Nuke Settings",
            color=0x000000
        )
        embed.add_field(name="`,antinuke enable`", value="Enable anti-nuke", inline=False)
        embed.add_field(name="`,antinuke disable`", value="Disable anti-nuke", inline=False)
        embed.add_field(name="`,antinuke role on/off`", value="Role deletion protection", inline=False)
        embed.add_field(name="`,antinuke channel on/off`", value="Channel deletion protection", inline=False)
        embed.add_field(name="`,antinuke emoji on/off`", value="Emoji deletion protection", inline=False)
        embed.add_field(name="`,antinuke massban on/off`", value="Mass ban protection", inline=False)
        embed.add_field(name="`,antinuke masskick on/off`", value="Mass kick protection", inline=False)
        embed.add_field(name="`,antinuke webhook on/off`", value="Webhook creation protection", inline=False)
        embed.add_field(name="`,antinuke vanity on/off`", value="Vanity URL protection", inline=False)
        embed.add_field(name="`,antinuke botadd on/off`", value="Deny bot joins", inline=False)
        embed.add_field(name="`,antinuke invite on/off`", value="Discord invite link protection", inline=False)
        embed.add_field(name="`,antinuke superadmin add @user`", value="Add super admin", inline=False)
        embed.add_field(name="`,antinuke whitelist add @user`", value="Whitelist member", inline=False)
        embed.add_field(name="`,antinuke config`", value="View settings", inline=False)
        await ctx.send(embed=embed)
        return
    
    action = action.lower()
    
    if action == 'enable':
        # Check if enabling a specific module
        if args:
            args_lower = args.lower()
            if 'role' in args_lower:
                antinuke['role_deletion'] = True
                save_data(data)
                await ctx.message.add_reaction('✅')
            elif 'channel' in args_lower:
                antinuke['channel_deletion'] = True
                save_data(data)
                await ctx.message.add_reaction('✅')
            elif 'emoji' in args_lower:
                antinuke['emoji_deletion'] = True
                save_data(data)
                await ctx.message.add_reaction('✅')
            elif 'massban' in args_lower or 'mass ban' in args_lower:
                antinuke['mass_member_ban'] = True
                save_data(data)
                await ctx.message.add_reaction('✅')
            elif 'masskick' in args_lower or 'mass kick' in args_lower:
                antinuke['mass_member_kick'] = True
                save_data(data)
                await ctx.message.add_reaction('✅')
            elif 'webhook' in args_lower:
                antinuke['webhook_creation'] = True
                save_data(data)
                await ctx.message.add_reaction('✅')
            elif 'vanity' in args_lower:
                antinuke['vanity_protection'] = True
                save_data(data)
                await ctx.message.add_reaction('✅')
            elif 'botadd' in args_lower or 'bot add' in args_lower or 'bot joins' in args_lower:
                antinuke['deny_bot_joins'] = True
                save_data(data)
                await ctx.message.add_reaction('✅')
            elif 'invite' in args_lower:
                antinuke['invite_links'] = True
                save_data(data)
                await ctx.message.add_reaction('✅')
            else:
                await ctx.message.add_reaction('❌')
        else:
            antinuke['enabled'] = True
            save_data(data)
            await ctx.message.add_reaction('✅')
    elif action == 'disable':
        # Check if disabling a specific module
        if args:
            args_lower = args.lower()
            if 'role' in args_lower:
                antinuke['role_deletion'] = False
                save_data(data)
                await ctx.message.add_reaction('✅')
            elif 'channel' in args_lower:
                antinuke['channel_deletion'] = False
                save_data(data)
                await ctx.message.add_reaction('✅')
            elif 'emoji' in args_lower:
                antinuke['emoji_deletion'] = False
                save_data(data)
                await ctx.message.add_reaction('✅')
            elif 'massban' in args_lower or 'mass ban' in args_lower:
                antinuke['mass_member_ban'] = False
                save_data(data)
                await ctx.message.add_reaction('✅')
            elif 'masskick' in args_lower or 'mass kick' in args_lower:
                antinuke['mass_member_kick'] = False
                save_data(data)
                await ctx.message.add_reaction('✅')
            elif 'webhook' in args_lower:
                antinuke['webhook_creation'] = False
                save_data(data)
                await ctx.message.add_reaction('✅')
            elif 'vanity' in args_lower:
                antinuke['vanity_protection'] = False
                save_data(data)
                await ctx.message.add_reaction('✅')
            elif 'botadd' in args_lower or 'bot add' in args_lower or 'bot joins' in args_lower:
                antinuke['deny_bot_joins'] = False
                save_data(data)
                await ctx.message.add_reaction('✅')
            elif 'invite' in args_lower:
                antinuke['invite_links'] = False
                save_data(data)
                await ctx.message.add_reaction('✅')
            else:
                await ctx.message.add_reaction('❌')
        else:
            antinuke['enabled'] = False
            save_data(data)
            await ctx.message.add_reaction('✅')
    elif action == 'config':
        status = "enabled" if antinuke.get('enabled') else "disabled"
        embed = discord.Embed(
            title="Settings",
            description=f"Antinuke is {status} in this server",
            color=0x000000
        )
        
        # Modules section
        modules_text = ""
        modules_text += "Role Deletion: " + ("❌" if not antinuke.get('role_deletion') else "✅") + "\n"
        modules_text += "Channel Deletion: " + ("❌" if not antinuke.get('channel_deletion') else "✅") + "\n"
        modules_text += "Emoji Deletion: " + ("❌" if not antinuke.get('emoji_deletion') else "✅") + "\n"
        modules_text += "Mass Member Ban: " + ("❌" if not antinuke.get('mass_member_ban') else "✅") + "\n"
        modules_text += "Mass Member Kick: " + ("❌" if not antinuke.get('mass_member_kick') else "✅") + "\n"
        modules_text += "Webhook Creation: " + ("❌" if not antinuke.get('webhook_creation') else "✅") + "\n"
        modules_text += "Vanity Protection: " + ("❌" if not antinuke.get('vanity_protection') else "✅") + "\n"
        modules_text += "Discord Invites: " + ("❌" if not antinuke.get('invite_links') else "✅")
        
        embed.add_field(name="Modules", value=modules_text, inline=True)
        
        # General section
        modules_enabled = sum([
            antinuke.get('role_deletion', False),
            antinuke.get('channel_deletion', False),
            antinuke.get('emoji_deletion', False),
            antinuke.get('mass_member_ban', False),
            antinuke.get('mass_member_kick', False),
            antinuke.get('webhook_creation', False),
            antinuke.get('vanity_protection', False),
            antinuke.get('invite_links', False)
        ])
        
        general_text = ""
        general_text += f"Super Admins: {len(antinuke.get('admins', []))}\n"
        general_text += f"Whitelisted Members: {len(antinuke.get('whitelist', []))}\n"
        general_text += f"Protection Modules: {modules_enabled} enabled\n"
        general_text += f"Watch Permissions Grant: 0/12 perms\n"
        general_text += f"Deny Bot Joins (botadd): " + ("❌" if not antinuke.get('deny_bot_joins') else "✅")
        
        embed.add_field(name="General", value=general_text, inline=True)
        
        await ctx.send(embed=embed)
    elif action in ['role', 'channel', 'emoji', 'massban', 'masskick', 'webhook', 'vanity', 'botadd', 'invite']:
        state = args.lower() if args else None
        field_map = {
            'role': 'role_deletion',
            'channel': 'channel_deletion',
            'emoji': 'emoji_deletion',
            'massban': 'mass_member_ban',
            'masskick': 'mass_member_kick',
            'webhook': 'webhook_creation',
            'vanity': 'vanity_protection',
            'botadd': 'deny_bot_joins',
            'invite': 'invite_links'
        }
        field = field_map.get(action)
        if state == 'on':
            antinuke[field] = True
            save_data(data)
            await ctx.message.add_reaction('✅')
        elif state == 'off':
            antinuke[field] = False
            save_data(data)
            await ctx.message.add_reaction('✅')
        else:
            await ctx.message.add_reaction('❌')
    elif action == 'superadmin':
        if args and args.lower() == 'add':
            if ctx.message.mentions:
                user = ctx.message.mentions[0]
                if user.id not in antinuke['admins']:
                    antinuke['admins'].append(user.id)
                    save_data(data)
                    await ctx.message.add_reaction('✅')
                else:
                    await ctx.message.add_reaction('❌')
            else:
                await ctx.message.add_reaction('❌')
    elif action == 'whitelist':
        if args and args.lower() == 'add':
            if ctx.message.mentions:
                user = ctx.message.mentions[0]
                if user.id not in antinuke['whitelist']:
                    antinuke['whitelist'].append(user.id)
                    save_data(data)
                    await ctx.message.add_reaction('✅')
                else:
                    await ctx.message.add_reaction('❌')
            else:
                await ctx.message.add_reaction('❌')

@bot.command(name='vanity')
@commands.has_permissions(manage_guild=True)
async def vanity(ctx, action=None, *args):
    """Vanity reputation system"""
    guild_data = get_guild_data(ctx.guild.id)
    vanity = guild_data['vanity']
    
    if action is None or action == 'help':
        embed = discord.Embed(
            title="Vanity Settings",
            description="Set up vanity status rewards for your server",
            color=0x000000
        )
        embed.add_field(
            name="Setup Commands",
            value="",
            inline=False
        )
        embed.add_field(
            name="`,vanity set <substring>`",
            value="Monitor for a specific text or phrase",
            inline=False
        )
        embed.add_field(
            name="`,vanity award channel #channel`",
            value="Set where award messages are sent",
            inline=False
        )
        embed.add_field(
            name="`,vanity log channel #channel`",
            value="Set where vanity detections are logged",
            inline=False
        )
        embed.add_field(
            name="`,vanity message <msg>`",
            value="Set the award message when vanity is found",
            inline=False
        )
        embed.add_field(
            name="Role Management",
            value="",
            inline=False
        )
        embed.add_field(
            name="`,vanity role add @role`",
            value="Add a role to award when vanity is found",
            inline=False
        )
        embed.add_field(
            name="`,vanity role remove @role`",
            value="Remove a role from vanity rewards",
            inline=False
        )
        embed.add_field(
            name="`,vanity role list`",
            value="View all roles being awarded",
            inline=False
        )
        embed.add_field(
            name="Other Commands",
            value="",
            inline=False
        )
        embed.add_field(
            name="`,vanity status`",
            value="View current vanity settings",
            inline=False
        )
        embed.add_field(
            name="`,vanity reset`",
            value="Reset all vanity settings",
            inline=False
        )
        await ctx.send(embed=embed)
        return
    
    if action == 'set':
        if not args:
            await ctx.message.add_reaction('❌')
            return
        vanity['substring'] = ' '.join(args)
        vanity['enabled'] = True
        save_data(data)
        await ctx.message.add_reaction('✅')
    
    elif action == 'award':
        if len(args) < 1 or args[0] != 'channel':
            await ctx.message.add_reaction('❌')
            return
        if not ctx.message.channel_mentions:
            await ctx.message.add_reaction('❌')
            return
        vanity['award_channel_id'] = ctx.message.channel_mentions[0].id
        save_data(data)
        await ctx.message.add_reaction('✅')
    
    elif action == 'log':
        if len(args) < 1 or args[0] != 'channel':
            await ctx.message.add_reaction('❌')
            return
        if not ctx.message.channel_mentions:
            await ctx.message.add_reaction('❌')
            return
        vanity['log_channel_id'] = ctx.message.channel_mentions[0].id
        save_data(data)
        await ctx.message.add_reaction('✅')
    
    elif action == 'message':
        if not args:
            await ctx.message.add_reaction('❌')
            return
        vanity['award_message'] = ' '.join(args)
        save_data(data)
        await ctx.message.add_reaction('✅')
    
    elif action == 'role':
        if len(args) == 0:
            await ctx.message.add_reaction('❌')
            return
        
        subaction = args[0]
        
        if subaction == 'list':
            if not vanity['roles']:
                embed = discord.Embed(
                    title="Vanity Roles",
                    description="No roles assigned yet",
                    color=0x000000
                )
                await ctx.send(embed=embed)
                return
            roles_text = []
            for role_id in vanity['roles']:
                role = ctx.guild.get_role(role_id)
                if role:
                    roles_text.append(f"• {role.mention}")
            embed = discord.Embed(
                title="Vanity Roles",
                description="\n".join(roles_text) if roles_text else "No roles",
                color=0x000000
            )
            await ctx.send(embed=embed)
            return
        
        if subaction not in ['add', 'remove']:
            await ctx.message.add_reaction('❌')
            return
        
        if not ctx.message.role_mentions:
            await ctx.message.add_reaction('❌')
            return
        
        role_id = ctx.message.role_mentions[0].id
        
        if subaction == 'add':
            if role_id not in vanity['roles']:
                vanity['roles'].append(role_id)
                save_data(data)
            await ctx.message.add_reaction('✅')
        elif subaction == 'remove':
            if role_id in vanity['roles']:
                vanity['roles'].remove(role_id)
                save_data(data)
            await ctx.message.add_reaction('✅')
    
    elif action == 'status':
        substring = vanity.get('substring', 'Not set')
        award_channel = vanity.get('award_channel_id')
        log_channel = vanity.get('log_channel_id')
        
        award_ch_text = f"<#{award_channel}>" if award_channel else "Not set"
        log_ch_text = f"<#{log_channel}>" if log_channel else "Not set"
        
        roles_text = "None"
        if vanity.get('roles'):
            roles_list = []
            for role_id in vanity['roles']:
                role = ctx.guild.get_role(role_id)
                if role:
                    roles_list.append(role.mention)
            roles_text = "\n".join(roles_list) if roles_list else "None"
        
        embed = discord.Embed(
            title="Vanity Status",
            color=0x000000
        )
        embed.add_field(name="Status", value="Enabled" if vanity.get('enabled') else "Disabled", inline=False)
        embed.add_field(name="Vanity Set To", value=f"`{substring}`", inline=False)
        embed.add_field(name="Award Channel", value=award_ch_text, inline=False)
        embed.add_field(name="Log Channel", value=log_ch_text, inline=False)
        embed.add_field(name="Award Message", value=f"`{vanity.get('award_message', 'Not set')}`", inline=False)
        embed.add_field(name="Reward Roles", value=roles_text, inline=False)
        await ctx.send(embed=embed)
    
    elif action == 'reset':
        vanity['enabled'] = False
        vanity['substring'] = None
        vanity['award_channel_id'] = None
        vanity['log_channel_id'] = None
        vanity['award_message'] = 'Congratulations! You have vanity!'
        vanity['roles'] = []
        save_data(data)
        await ctx.message.add_reaction('✅')

@bot.command(name='lookup')
async def lookup(ctx, lookup_type: str = "usernames"):
    """Look up available usernames or vanities from the server"""
    if lookup_type.lower() == "vanities":
        history = data.get('vanity_history', [])
    else:
        history = data.get('username_history', [])
    
    if not history:
        await ctx.send("❌")
        return
    
    # Reverse to show newest first
    history = list(reversed(history))
    
    # Create paginated embeds
    items_per_page = 10
    pages = []
    total_pages = (len(history) + items_per_page - 1) // items_per_page
    
    # Determine title
    title = "Available Vanities" if lookup_type.lower() == "vanities" else "Available Usernames"
    description = "Vanities will be available after being dropped." if lookup_type.lower() == "vanities" else "Usernames will be available 14 days after being dropped."
    
    for page_num in range(total_pages):
        start_idx = page_num * items_per_page
        end_idx = start_idx + items_per_page
        page_items = history[start_idx:end_idx]
        
        # Build content string
        content_lines = []
        for idx, item in enumerate(page_items):
            entry_num = start_idx + idx + 1
            name = item['vanity'] if lookup_type.lower() == "vanities" else item['username']
            try:
                changed_at = datetime.fromisoformat(item['changed_at'])
                time_ago = datetime.now() - changed_at
                
                if time_ago.days > 0:
                    time_str = f"{time_ago.days}d ago"
                elif time_ago.seconds > 3600:
                    time_str = f"{time_ago.seconds // 3600}h ago"
                elif time_ago.seconds > 60:
                    time_str = f"{time_ago.seconds // 60}m ago"
                else:
                    time_str = f"{time_ago.seconds}s ago"
            except:
                time_str = "Unknown"
            
            content_lines.append(f"{entry_num:02d} {name} - {time_str}")
        
        content = "\n".join(content_lines)
        
        embed = discord.Embed(
            title=title,
            description=description,
            color=0x000000
        )
        embed.add_field(name="\u200b", value=content, inline=False)
        embed.set_footer(text=f"Page {page_num + 1}/{total_pages}")
        pages.append(embed)
    
    if len(pages) == 1:
        await ctx.send(embed=pages[0])
    else:
        view = CommandsPaginationView(pages, ctx)
        view.update_buttons()
        await ctx.send(embed=pages[0], view=view)

@bot.command(name='afk')
async def set_afk(ctx, *, status: str = 'AFK'):
    """Set your AFK status"""
    user_data = get_user_data(ctx.author.id)
    
    if user_data.get('afk'):
        user_data['afk'] = False
        user_data['afk_time'] = None
        save_data(data)
        await ctx.message.add_reaction('✅')
    else:
        user_data['afk'] = True
        user_data['afk_status'] = status
        user_data['afk_time'] = datetime.now().isoformat()
        save_data(data)
        embed = discord.Embed(
            description=f"✅ {ctx.author.mention}: You're now AFK with the status: {status}",
            color=0x2b2d31
        )
        await ctx.send(embed=embed)

@bot.command(name='help')
async def help_command(ctx):
    """Display all commands with pagination"""
    pages = []
    
    # Page 1: Economy, Leveling, Moderation
    embed1 = discord.Embed(
        title="Bot Commands - Page 1",
        description="Here are all available commands:",
        color=0xe91e63
    )
    embed1.add_field(
        name="Economy",
        value="`,balance`, `,daily`, `,work`, `,deposit`, `,withdraw`, `,rob`",
        inline=False
    )
    embed1.add_field(
        name="Leveling",
        value="`,rank`, `,leaderboard`, `,vcleaderboard`, `,messageleaderboard`",
        inline=False
    )
    embed1.add_field(
        name="Moderation",
        value="`,kick`, `,ban`, `,clear`, `,purge`, `,timeout`, `,hide`, `,unhide`, `,lock`, `,unlock`, `,nuke`",
        inline=False
    )
    pages.append(embed1)
    
    # Page 2: Utility, Snipes, Lookup, AutoRole
    embed2 = discord.Embed(
        title="Bot Commands - Page 2",
        description="Here are all available commands:",
        color=0xe91e63
    )
    embed2.add_field(
        name="Utility",
        value="`,userinfo`, `,serverinfo`, `,avatar`",
        inline=False
    )
    embed2.add_field(
        name="Snipes",
        value="`,snipe` / `,s`, `,s 2-5`, `,clearsnipes` / `,cs`",
        inline=False
    )
    embed2.add_field(
        name="Lookup",
        value="`,lookup`, `,lookup usernames`, `,lookup vanities`",
        inline=False
    )
    embed2.add_field(
        name="AutoRole",
        value="`,autorole set @role`, `,autorole enable`, `,autorole disable`, `,autorole info`",
        inline=False
    )
    pages.append(embed2)
    
    # Page 3: Ping on Join, Filter, Welcome, Logging
    embed3 = discord.Embed(
        title="Bot Commands - Page 3",
        description="Here are all available commands:",
        color=0xe91e63
    )
    embed3.add_field(
        name="Ping on Join",
        value="`,pingonjoin toggle`, `,pingonjoin add #channel`, `,pingonjoin remove #channel`, `,pingonjoin info`",
        inline=False
    )
    embed3.add_field(
        name="Filter",
        value="`,filter add word`, `,filter remove word`, `,filterlist`",
        inline=False
    )
    embed3.add_field(
        name="Welcome",
        value="`,welcome add #channel message`, `,welcome remove #channel`, `,welcome list`",
        inline=False
    )
    embed3.add_field(
        name="Logging",
        value="`,log add #channel event`, `,log remove #channel event`, `,log list`",
        inline=False
    )
    pages.append(embed3)
    
    # Page 4: VoiceMaster, Vanity, Anti-Nuke
    embed4 = discord.Embed(
        title="Bot Commands - Page 4",
        description="Here are all available commands:",
        color=0xe91e63
    )
    embed4.add_field(
        name="VoiceMaster",
        value="`,voicemaster setup`, `,voicemaster disable`, `,voicemaster reset`, `,voicemaster interface`, `,voicemaster category`",
        inline=False
    )
    embed4.add_field(
        name="Vanity",
        value="`,vanity set <substring>`, `,vanity award channel #channel`, `,vanity log channel #channel`, `,vanity roles add @role`",
        inline=False
    )
    embed4.add_field(
        name="Anti-Nuke",
        value="`,antinuke enable`, `,antinuke disable`, `,antinuke role on/off`, `,antinuke channel on/off`, `,antinuke emoji on/off`, `,antinuke massban on/off`, `,antinuke masskick on/off`, `,antinuke webhook on/off`, `,antinuke vanity on/off`, `,antinuke botadd on/off`, `,antinuke invite on/off`, `,antinuke config`",
        inline=False
    )
    pages.append(embed4)
    
    # Send with pagination
    view = CommandsPaginationView(pages, ctx)
    view.update_buttons()
    await ctx.send(embed=pages[0], view=view)

if __name__ == "__main__":
    TOKEN = os.environ.get('DISCORD_BOT_TOKEN')
    if not TOKEN:
        print("Error: DISCORD_BOT_TOKEN environment variable not set!")
        print("Please add your Discord bot token to the Secrets.")
        exit(1)
    bot.run(TOKEN)
