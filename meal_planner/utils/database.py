"""
Persistent SQLite Database Connection Manager for Meal Planner.
Manages persistent session state, user profiles, interaction histories, and memory nodes using parameterized queries.
"""

import sqlite3
import json
import dataclasses
from typing import Dict, Any, List, Optional
from datetime import datetime
from meal_planner.models import UserProfile, AgentMessage, MemoryNode


def default_json_serializer(obj):
    """Custom JSON serializer that handles dataclasses and objects with to_dict."""
    if dataclasses.is_dataclass(obj):
        return dataclasses.asdict(obj)
    if hasattr(obj, "to_dict"):
        return obj.to_dict()
    if hasattr(obj, "__dict__"):
        return obj.__dict__
    return str(obj)


class DatabaseManager:
    """
    Manages persistent SQLite database connections and schemas.
    All SQL operations strictly use parameterized queries to prevent SQL injection.
    """

    def __init__(self, db_path: str = "meal_planner.db"):
        self.db_path = db_path
        self.conn: Optional[sqlite3.Connection] = None
        self.connect()
        self.init_db()

    def connect(self):
        """Establishes SQLite connection with check_same_thread=False for async/multithread safety."""
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row

    def init_db(self):
        """Initializes relational table schemas for session, profile, history, and memory storage."""
        with self.conn:
            cursor = self.conn.cursor()

            # Sessions table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    session_id TEXT PRIMARY KEY,
                    user_id TEXT DEFAULT 'default_user',
                    created_at TEXT,
                    updated_at TEXT,
                    metadata_json TEXT
                )
            """)

            # User profiles table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS user_profiles (
                    session_id TEXT PRIMARY KEY,
                    height_cm REAL,
                    weight_kg REAL,
                    age INTEGER,
                    sex TEXT,
                    activity_level TEXT,
                    raw_goal TEXT,
                    parsed_goal_type TEXT,
                    caloric_target_offset REAL,
                    diet_preferences_json TEXT,
                    dietary_exclusions_json TEXT,
                    created_at TEXT,
                    FOREIGN KEY(session_id) REFERENCES sessions(session_id)
                )
            """)

            # Inter-agent & session interaction message history
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS interaction_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT,
                    sender TEXT,
                    recipient TEXT,
                    message_type TEXT,
                    payload_json TEXT,
                    timestamp TEXT,
                    FOREIGN KEY(session_id) REFERENCES sessions(session_id)
                )
            """)

            # Memory nodes table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS memory_nodes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT,
                    agent_name TEXT,
                    memory_type TEXT,
                    key_name TEXT,
                    value_json TEXT,
                    timestamp TEXT,
                    FOREIGN KEY(session_id) REFERENCES sessions(session_id)
                )
            """)

            # Meal plan artifact results table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS meal_plans (
                    session_id TEXT PRIMARY KEY,
                    plan_json TEXT,
                    audit_json TEXT,
                    grocery_json TEXT,
                    created_at TEXT,
                    FOREIGN KEY(session_id) REFERENCES sessions(session_id)
                )
            """)

    def save_session(self, session_id: str, user_id: str = "default_user", metadata: Optional[Dict[str, Any]] = None):
        """Saves or updates session entry."""
        now = datetime.now().isoformat()
        meta_str = json.dumps(metadata if metadata else {}, default=default_json_serializer)
        with self.conn:
            self.conn.execute("""
                INSERT INTO sessions (session_id, user_id, created_at, updated_at, metadata_json)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(session_id) DO UPDATE SET
                    updated_at = excluded.updated_at,
                    metadata_json = excluded.metadata_json
            """, (session_id, user_id, now, now, meta_str))

    def save_user_profile(self, session_id: str, profile: UserProfile):
        """Saves or updates user profile in database."""
        now = datetime.now().isoformat()
        prefs_json = json.dumps(profile.diet_preferences, default=default_json_serializer)
        excls_json = json.dumps(profile.dietary_exclusions, default=default_json_serializer)
        with self.conn:
            self.conn.execute("""
                INSERT INTO user_profiles (
                    session_id, height_cm, weight_kg, age, sex, activity_level,
                    raw_goal, parsed_goal_type, caloric_target_offset,
                    diet_preferences_json, dietary_exclusions_json, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(session_id) DO UPDATE SET
                    height_cm = excluded.height_cm,
                    weight_kg = excluded.weight_kg,
                    age = excluded.age,
                    sex = excluded.sex,
                    activity_level = excluded.activity_level,
                    raw_goal = excluded.raw_goal,
                    parsed_goal_type = excluded.parsed_goal_type,
                    caloric_target_offset = excluded.caloric_target_offset,
                    diet_preferences_json = excluded.diet_preferences_json,
                    dietary_exclusions_json = excluded.dietary_exclusions_json
            """, (
                session_id, profile.height_cm, profile.weight_kg, profile.age,
                profile.sex, profile.activity_level, profile.raw_goal,
                profile.parsed_goal_type, profile.caloric_target_offset,
                prefs_json, excls_json, now
            ))

    def get_user_profile(self, session_id: str) -> Optional[UserProfile]:
        """Retrieves user profile for given session_id."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM user_profiles WHERE session_id = ?", (session_id,))
        row = cursor.fetchone()
        if not row:
            return None

        return UserProfile(
            height_cm=row["height_cm"],
            weight_kg=row["weight_kg"],
            age=row["age"],
            sex=row["sex"],
            activity_level=row["activity_level"],
            raw_goal=row["raw_goal"],
            parsed_goal_type=row["parsed_goal_type"],
            caloric_target_offset=row["caloric_target_offset"],
            diet_preferences=json.loads(row["diet_preferences_json"]),
            dietary_exclusions=json.loads(row["dietary_exclusions_json"])
        )

    def add_interaction_message(self, session_id: str, message: AgentMessage):
        """Appends an interaction message to persistent log."""
        payload_str = json.dumps(message.payload, default=default_json_serializer)
        with self.conn:
            self.conn.execute("""
                INSERT INTO interaction_history (session_id, sender, recipient, message_type, payload_json, timestamp)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (session_id, message.sender, message.recipient, message.message_type, payload_str, message.timestamp))

    def get_interaction_history(self, session_id: str) -> List[AgentMessage]:
        """Loads interaction message history for a session."""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT sender, recipient, message_type, payload_json, timestamp
            FROM interaction_history
            WHERE session_id = ?
            ORDER BY id ASC
        """, (session_id,))
        rows = cursor.fetchall()
        messages = []
        for r in rows:
            try:
                payload = json.loads(r["payload_json"])
            except Exception:
                payload = {}
            messages.append(AgentMessage(
                sender=r["sender"],
                recipient=r["recipient"],
                message_type=r["message_type"],
                payload=payload,
                timestamp=r["timestamp"]
            ))
        return messages

    def add_memory_node(self, session_id: str, node: MemoryNode):
        """Persists a memory node."""
        val_str = json.dumps(node.value, default=default_json_serializer)
        with self.conn:
            self.conn.execute("""
                INSERT INTO memory_nodes (session_id, agent_name, memory_type, key_name, value_json, timestamp)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (session_id, node.agent_name, node.memory_type, node.key, val_str, node.timestamp))

    def get_memory_nodes(self, session_id: str, agent_name: Optional[str] = None, memory_type: Optional[str] = None) -> List[MemoryNode]:
        """Retrieves memory nodes for a session with optional filters."""
        query = "SELECT agent_name, memory_type, key_name, value_json, timestamp FROM memory_nodes WHERE session_id = ?"
        params = [session_id]

        if agent_name:
            query += " AND agent_name = ?"
            params.append(agent_name)
        if memory_type:
            query += " AND memory_type = ?"
            params.append(memory_type)

        query += " ORDER BY id ASC"

        cursor = self.conn.cursor()
        cursor.execute(query, params)
        rows = cursor.fetchall()

        nodes = []
        for r in rows:
            try:
                val = json.loads(r["value_json"])
            except Exception:
                val = r["value_json"]
            nodes.append(MemoryNode(
                key=r["key_name"],
                value=val,
                agent_name=r["agent_name"],
                memory_type=r["memory_type"],
                timestamp=r["timestamp"]
            ))
        return nodes

    def close(self):
        """Closes database connection safely."""
        if self.conn:
            self.conn.close()
            self.conn = None
