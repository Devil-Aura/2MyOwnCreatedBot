# database.py

from pymongo import MongoClient
from datetime import datetime
import config

class Database:
    def __init__(self):
        self.client = MongoClient(config.MONGO_URI)
        self.db = self.client[config.DATABASE_NAME]
        self.bots = self.db["bots"]
        self.users = self.db["users"]
        self.admins = self.db["admins"]
        self.messages = self.db["messages"]  # New collection for message mappings
        self.filters = self.db["filters"]  # New collection for filters

        # Create indexes for faster queries
        self.bots.create_index("bot_token")
        self.users.create_index([("bot_token", 1), ("user_id", 1)])
        self.admins.create_index([("bot_token", 1), ("admin_id", 1)])
        self.messages.create_index("forwarded_message_id")
        self.filters.create_index([("bot_token", 1), ("trigger", 1)])

    def add_bot(self, bot_token, owner_id):
        """Add a bot to the list of connected bots."""
        self.bots.insert_one({"bot_token": bot_token, "owner_id": owner_id})

    def get_connected_bots(self, owner_id=None):
        """Get all connected bots (optionally filtered by owner)."""
        query = {"owner_id": owner_id} if owner_id else {}
        return [bot["bot_token"] for bot in self.bots.find(query)]

    def add_user(self, bot_token, user_id, name=None, username=None):
        """Add a user to a specific bot's user list."""
        self.users.update_one(
            {"bot_token": bot_token, "user_id": user_id},
            {"$set": {"name": name, "username": username, "last_active": datetime.now()}},
            upsert=True
        )

    def get_users(self, bot_token):
        """Get all users of a specific bot."""
        return [user["user_id"] for user in self.users.find({"bot_token": bot_token})]

    def get_user_count(self, bot_token):
        """Get the number of users for a specific bot."""
        return self.users.count_documents({"bot_token": bot_token})

    def add_admin(self, bot_token, admin_id):
        """Add an admin for a specific bot."""
        self.admins.update_one(
            {"bot_token": bot_token, "admin_id": admin_id},
            {"$set": {"added_at": datetime.now()}},
            upsert=True
        )

    def get_admins(self, bot_token):
        """Get all admins for a specific bot."""
        return [admin["admin_id"] for admin in self.admins.find({"bot_token": bot_token})]

    def remove_admin(self, bot_token, admin_id):
        """Remove an admin for a specific bot."""
        self.admins.delete_one({"bot_token": bot_token, "admin_id": admin_id})

    def add_message_mapping(self, original_user_id, forwarded_message_id, bot_token):
        """Store a mapping between the original user ID and the forwarded message ID."""
        self.messages.insert_one({
            "original_user_id": original_user_id,
            "forwarded_message_id": forwarded_message_id,
            "bot_token": bot_token
        })

    def get_original_user_id(self, forwarded_message_id):
        """Get the original user ID for a forwarded message."""
        message_data = self.messages.find_one({"forwarded_message_id": forwarded_message_id})
        return message_data["original_user_id"] if message_data else None

    def add_filter(self, bot_token, trigger, response):
        """Add a filter for a specific bot."""
        self.filters.insert_one({
            "bot_token": bot_token,
            "trigger": trigger,
            "response": response
        })

    def get_filters(self, bot_token):
        """Get all filters for a specific bot."""
        return list(self.filters.find({"bot_token": bot_token}))

    def delete_filter(self, bot_token, trigger):
        """Delete a filter for a specific bot."""
        self.filters.delete_one({"bot_token": bot_token, "trigger": trigger})

# Initialize database
db = Database()
