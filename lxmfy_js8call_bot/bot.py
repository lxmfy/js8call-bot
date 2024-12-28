from lxmfy import LXMFBot
from .storage.sqlite_storage import SQLiteStorage
import os
import time
import logging
from logging.handlers import RotatingFileHandler
import configparser
from socket import socket, AF_INET, SOCK_STREAM
import json
import threading
from collections import defaultdict, Counter
from datetime import datetime, timedelta
import concurrent.futures

class JS8CallBot(LXMFBot):
    def __init__(self, name='LXMFy-JS8Call--Bot'):
        # Load config first
        self.config = configparser.ConfigParser()
        self.config.read('config.ini')
        
        # Initialize LXMFBot with config values
        super().__init__(
            name=name,
            announce=self.config.getint('bot', 'announce_interval', fallback=360),
            announce_immediately=True,
            admins=self.config.get('bot', 'allowed_users', fallback='').strip().split(','),
            hot_reloading=True,
            rate_limit=5,
            cooldown=60,
            max_warnings=3,
            warning_timeout=300,
            command_prefix="/"
        )
        
        # Setup SQLite storage after parent initialization
        self.db = SQLiteStorage(self.config.get('js8call', 'db_file', fallback='js8call.db'))
        
        self.setup_logging()
        self.setup_js8call()
        self.setup_state()

    def setup_logging(self):
        self.logger = logging.getLogger('js8call_lxmf_bot')
        self.logger.setLevel(logging.INFO)
        
        handlers = [
            RotatingFileHandler('js8call_lxmf_bot.log', maxBytes=1000000, backupCount=5),
            logging.StreamHandler()
        ]
        
        for handler in handlers:
            formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)

    def setup_js8call(self):
        self.js8call_server = (
            self.config.get('js8call', 'host', fallback='localhost'),
            self.config.getint('js8call', 'port', fallback=2442)
        )
        self.js8call_socket = None
        self.js8call_connected = False
        
        # JS8Call specific settings
        self.js8groups = self.config.get('js8call', 'js8groups', fallback='').split(',')
        self.js8urgent = self.config.get('js8call', 'js8urgent', fallback='').split(',')
        self.js8groups = [group.strip() for group in self.js8groups]
        self.js8urgent = [group.strip() for group in self.js8urgent]
        
    def setup_state(self):
        """Initialize bot state and load users from storage"""
        # Initialize state
        self.distro_list = set()
        self.user_groups = defaultdict(set)
        self.muted_users = defaultdict(set)
        self.start_time = time.time()
        
        # Load existing state from storage
        self.load_state_from_storage()

    def load_state_from_storage(self):
        """Load users and their settings from storage"""
        try:
            # Load distribution list
            users_data = self.storage.get('users', {})
            if users_data:
                for user_hash, user_data in users_data.items():
                    self.distro_list.add(user_hash)
                    self.user_groups[user_hash] = set(user_data.get('groups', []))
                    self.muted_users[user_hash] = set(user_data.get('muted_groups', []))
            self.logger.info(f"Loaded {len(self.distro_list)} users from storage")
        except Exception as e:
            self.logger.error(f"Error loading state from storage: {e}")

    def save_state_to_storage(self):
        """Save current state to storage"""
        try:
            users_data = {}
            for user in self.distro_list:
                users_data[user] = {
                    'groups': list(self.user_groups[user]),
                    'muted_groups': list(self.muted_users[user])
                }
            self.storage.set('users', users_data)
            self.logger.debug("Saved state to storage")
        except Exception as e:
            self.logger.error(f"Error saving state to storage: {e}")

    def add_to_distro_list(self, user):
        """Add a user to the distribution list"""
        if user not in self.distro_list:
            self.distro_list.add(user)
            # Add default groups if configured
            default_groups = self.config.get('bot', 'default_groups', fallback='').split(',')
            default_groups = [g.strip() for g in default_groups if g.strip()]
            for group in default_groups:
                self.user_groups[user].add(group)
            
            # Save updated state
            self.save_state_to_storage()
            
            # Send welcome message
            welcome_msg = f"You have been added to the JS8Call message group"
            if default_groups:
                welcome_msg += f" and the following default groups: {', '.join(default_groups)}"
            welcome_msg += ". You will receive messages when they are available."
            self.send(user, welcome_msg)
            
            self.logger.info(f"Added {user} to distribution list")
        else:
            self.send(user, "You are already in the JS8Call message group.")

    def remove_from_distro_list(self, user):
        """Remove a user from the distribution list"""
        if user in self.distro_list:
            self.distro_list.remove(user)
            self.user_groups.pop(user, None)
            self.muted_users.pop(user, None)
            
            # Save updated state
            self.save_state_to_storage()
            
            self.send(user, "You have been removed from the JS8Call message group and all groups.")
            self.logger.info(f"Removed {user} from distribution list")
        else:
            self.send(user, "You are not in the JS8Call message group.")

    def add_user_to_groups(self, user, groups):
        """Add a user to specified groups"""
        if user in self.distro_list:
            for group in groups:
                if group in self.js8groups or group in self.js8urgent:
                    self.user_groups[user].add(group)
            
            # Save updated state
            self.save_state_to_storage()
            
            self.send(user, f"You have been added to the following groups: {', '.join(groups)}")
            self.logger.info(f"Added {user} to groups: {', '.join(groups)}")
        else:
            self.send(user, "You need to join the JS8Call message group first. Use /add command.")

    def remove_user_from_group(self, user, group):
        """Remove a user from a specific group"""
        if user in self.distro_list and group in self.user_groups[user]:
            self.user_groups[user].remove(group)
            
            # Save updated state
            self.save_state_to_storage()
            
            self.send(user, f"You have been removed from the group: {group}")
            self.logger.info(f"Removed {user} from group: {group}")
        else:
            self.send(user, f"You are not in the group: {group}")

    def register_commands(self):
        @self.command(description="Add yourself to the JS8Call message group")
        def add(ctx):
            self.add_to_distro_list(ctx.sender)

        @self.command(description="Remove yourself from the JS8Call message group")
        def remove(ctx):
            self.remove_from_distro_list(ctx.sender)

        @self.command(description="Show available groups and your subscriptions")
        def groups(ctx):
            groups_output = self.show_groups(ctx.sender)
            ctx.reply(groups_output)

        @self.command(description="Join one or more groups")
        def join(ctx):
            if ctx.args:
                self.add_user_to_groups(ctx.sender, ctx.args)
            else:
                ctx.reply("Usage: /join <group1> <group2> ...")

        @self.command(description="Leave a specific group")
        def leave(ctx):
            if ctx.args:
                self.remove_user_from_group(ctx.sender, ctx.args[0])
            else:
                ctx.reply("Usage: /leave <group>")

        @self.command(description="Show bot help")
        def help(ctx):
            ctx.reply(self.show_help())

        @self.command(description="Show message log")
        def showlog(ctx):
            try:
                num_messages = int(ctx.args[0]) if ctx.args else 10
                log_output = self.show_log(num_messages)
                ctx.reply(log_output)
            except (IndexError, ValueError):
                ctx.reply("Usage: /showlog <number>")

        @self.command(description="Show bot statistics")
        def stats(ctx):
            period = ctx.args[0] if ctx.args and ctx.args[0] in ['day', 'month'] else None
            stats_output = self.show_stats(period)
            ctx.reply(stats_output)

        @self.command(description="Show bot information")
        def info(ctx):
            info_output = self.show_info()
            ctx.reply(info_output)

    def run(self):
        self.logger.info('JS8Call LXMF Bot starting up...')
        self.register_commands()
        
        # Start JS8Call connection thread
        js8call_thread = threading.Thread(target=self.js8call_loop)
        js8call_thread.daemon = True
        js8call_thread.start()
        
        # Run the main LXMFBot loop
        try:
            super().run()
        except KeyboardInterrupt:
            self.logger.info("Shutting down JS8Call LXMF bot...")
        finally:
            if self.js8call_socket:
                self.js8call_socket.close()
            self.storage.cleanup()

    def js8call_loop(self):
        while True:
            try:
                if not self.js8call_connected:
                    self.connect_js8call()
                if self.js8call_connected:
                    self.process_js8call_messages()
                time.sleep(1)
            except Exception as e:
                self.logger.error(f"JS8Call loop error: {e}")
                time.sleep(5)

    def connect_js8call(self):
        """Connect to JS8Call instance"""
        self.logger.info(f"Connecting to JS8Call on {self.js8call_server}")
        self.js8call_socket = socket(AF_INET, SOCK_STREAM)
        try:
            self.js8call_socket.connect(self.js8call_server)
            self.js8call_connected = True
            self.logger.info("Connected to JS8Call")
        except Exception as e:
            self.logger.error(f"Failed to connect to JS8Call: {e}")
            self.js8call_socket = None
            self.js8call_connected = False

    def process_js8call_messages(self):
        """Process messages from JS8Call"""
        if not self.js8call_connected:
            return

        try:
            # Read data from socket
            data = self.js8call_socket.recv(4096).decode('utf-8')
            if not data:
                self.js8call_connected = False
                self.logger.warning("JS8Call connection lost")
                return

            # Process JSON messages
            messages = data.strip().split('\n')
            for message in messages:
                try:
                    if not message:
                        continue
                    msg_data = json.loads(message)
                    self.handle_js8call_message(msg_data)
                except json.JSONDecodeError as e:
                    self.logger.error(f"Failed to parse JS8Call message: {e}")
                    continue

        except Exception as e:
            self.logger.error(f"Error processing JS8Call messages: {e}")
            self.js8call_connected = False

    def handle_js8call_message(self, data):
        """Handle a single JS8Call message"""
        try:
            if data['type'] == 'RX.DIRECTED':
                # Parse directed message
                parts = data['value'].split(':')
                if len(parts) < 2:
                    self.logger.warning(f"Invalid directed message format: {data['value']}")
                    return

                sender = parts[0].strip()
                content = ':'.join(parts[1:]).strip()

                # Check for blocked words
                if any(word.lower() in content.lower() for word in self.blocked_words):
                    self.logger.info(f"Message from {sender} contains blocked words. Skipping.")
                    return

                # Forward to LXMF users based on message type
                if any(content.startswith(group) for group in self.js8groups):
                    # Group message
                    for group in self.js8groups:
                        if content.startswith(group):
                            message = content[len(group):].strip()
                            self.forward_group_message(sender, group, message)
                            break
                elif any(content.startswith(group) for group in self.js8urgent):
                    # Urgent message
                    for group in self.js8urgent:
                        if content.startswith(group):
                            message = content[len(group):].strip()
                            self.forward_urgent_message(sender, group, message)
                            break
                else:
                    # Direct message
                    self.forward_direct_message(sender, content)

        except Exception as e:
            self.logger.error(f"Error handling JS8Call message: {e}")

    def forward_direct_message(self, sender: str, message: str):
        """Forward a direct message to all LXMF users"""
        formatted_message = f"Direct message from {sender}: {message}"
        self._send_to_users(formatted_message)
        self.db.insert_message(sender, "DIRECT", message)
        self.logger.info(f"Forwarded direct message from {sender}")

    def forward_group_message(self, sender: str, group: str, message: str):
        """Forward a group message to subscribed LXMF users"""
        formatted_message = f"Group message from {sender} to {group}: {message}"
        self._send_to_users(formatted_message, group)
        self.db.insert_message(sender, group, message)
        self.logger.info(f"Forwarded group message from {sender} to {group}")

    def forward_urgent_message(self, sender: str, group: str, message: str):
        """Forward an urgent message to subscribed LXMF users"""
        formatted_message = f"URGENT message from {sender} to {group}: {message}"
        self._send_to_users(formatted_message, group)
        self.db.insert_message(sender, group, message)
        self.logger.info(f"Forwarded urgent message from {sender} to {group}")

    def _send_to_users(self, message: str, group: str = None):
        """Send a message to all users or group subscribers"""
        futures = []
        for user in self.distro_list:
            if group is None or (group in self.user_groups[user] and group not in self.muted_users[user]):
                futures.append(self.thread_pool.submit(self.send, user, message))
        concurrent.futures.wait(futures)

    def show_help(self):
        """Return help message with available commands"""
        return (
            "Available commands:\n"
            "/add - Add yourself to the JS8Call message group\n"
            "/remove - Remove yourself from the JS8Call message group\n"
            "/groups - Show available groups and your subscriptions\n"
            "/join <group1> <group2> ... - Join one or more groups\n"
            "/leave <group> - Leave a specific group\n"
            "/mute <group1> <group2> ... or ALL - Mute one or more groups or all groups\n"
            "/unmute <group1> <group2> ... or ALL - Unmute one or more groups or all groups\n"
            "/help - Show this help message\n"
            "/showlog <number> - Show the last <number> messages (max 50)\n"
            "/stats - Show current stats\n"
            "/stats <day|month> - Show stats for the specified period\n"
            "/info - Show bot information\n"
            "/analytics [day|week] - Show usage statistics"
        )

    def show_groups(self, user):
        """Show available groups and user's subscriptions"""
        available_groups = set(self.js8groups + self.js8urgent)
        user_groups = self.user_groups.get(user, set())
        muted_groups = self.muted_users.get(user, set())
        
        output = "Available groups:\n"
        for group in available_groups:
            status = "[Subscribed]" if group in user_groups else "[Not subscribed]"
            if group in muted_groups:
                status += " [Muted]"
            output += f"{group} {status}\n"
        return output

    def show_info(self):
        """Show bot information"""
        uptime = str(timedelta(seconds=int(time.time() - self.start_time)))
        info = f"Bot uptime: {uptime}\n"
        if self.bot_location:
            info += f"Location: {self.bot_location}\n"
        if self.node_operator:
            info += f"Node operator: {self.node_operator}\n"
        if not self.bot_location and not self.node_operator:
            info += "No additional info available"
        return info

    def show_log(self, num_messages):
        """Show recent messages"""
        num_messages = min(int(num_messages), 50)
        messages = self.execute_db_query('''
            SELECT sender, receiver, message, timestamp
            FROM (
                SELECT sender, receiver, message, timestamp FROM messages
                UNION ALL
                SELECT sender, groupname as receiver, message, timestamp FROM groups
                UNION ALL
                SELECT sender, groupname as receiver, message, timestamp FROM urgent
            )
            ORDER BY timestamp DESC
            LIMIT ?
        ''', (num_messages,))
        
        log_output = f"Last {len(messages)} messages:\n\n"
        for msg in reversed(messages):
            log_output += f"[{msg[3]}] From {msg[0]} to {msg[1]}: {msg[2]}\n\n"
        return log_output

    def show_stats(self, period=None):
        """Show statistics for the specified period"""
        current_users = len(self.distro_list)
        output = f"Current users: {current_users}\n"

        if period == 'day':
            date = datetime.now().strftime('%Y-%m-%d')
            stats = self.execute_db_query("SELECT user_count FROM stats WHERE date = ?", (date,))
            if stats:
                output += f"Users today: {stats[0][0]}\n"
            else:
                output += "No data for today\n"
        elif period == 'month':
            current_month = datetime.now().strftime('%Y-%m')
            stats = self.execute_db_query("SELECT AVG(user_count) FROM stats WHERE date LIKE ?", (f"{current_month}%",))
            if stats and stats[0][0] is not None:
                avg_users = round(stats[0][0], 2)
                output += f"Average users this month: {avg_users}\n"
            else:
                output += "No data for this month\n"

        return output

if __name__ == "__main__":
    bot = JS8CallBot()
    bot.run()