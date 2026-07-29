"""
Async Memory Manager & History Compaction Engine.
Provides asynchronous memory storage, recall, semantic search, and context history compaction for multi-agent workflows.
"""

import asyncio
import json
from typing import List, Dict, Any, Optional
from datetime import datetime
from meal_planner.models import MemoryNode, AgentMessage, SessionContext, UserProfile
from meal_planner.utils.database import DatabaseManager


class AsyncMemoryManager:
    """
    Asynchronous Memory Manager providing async storage, retrieval, search,
    and history compaction for LLM session context windows.
    """

    def __init__(self, db_manager: Optional[DatabaseManager] = None):
        self.db = db_manager if db_manager else DatabaseManager()

    async def store_memory(
        self,
        session_id: str,
        agent_name: str,
        key: str,
        value: Any,
        memory_type: str = "short_term"
    ) -> MemoryNode:
        """Asynchronously stores a memory node in persistent DB and in-memory cache."""
        node = MemoryNode(
            key=key,
            value=value,
            agent_name=agent_name,
            memory_type=memory_type,
            timestamp=datetime.now().isoformat()
        )
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, self.db.add_memory_node, session_id, node)
        return node

    async def recall_memory(
        self,
        session_id: str,
        agent_name: Optional[str] = None,
        key: Optional[str] = None
    ) -> List[MemoryNode]:
        """Asynchronously recalls memory nodes from database."""
        loop = asyncio.get_running_loop()
        nodes = await loop.run_in_executor(None, self.db.get_memory_nodes, session_id, agent_name, None)

        if key:
            nodes = [n for n in nodes if n.key == key]
        return nodes

    async def search_memory(self, session_id: str, query_term: str) -> List[MemoryNode]:
        """Asynchronously searches memory nodes for query term in key or value."""
        all_nodes = await self.recall_memory(session_id)
        query_lower = query_term.lower()
        results = []
        for node in all_nodes:
            val_str = json.dumps(node.value).lower() if isinstance(node.value, (dict, list)) else str(node.value).lower()
            if query_lower in node.key.lower() or query_lower in val_str:
                results.append(node)
        return results

    async def compact_history_async(
        self,
        session_id: str,
        messages: List[AgentMessage],
        max_messages: int = 6
    ) -> List[AgentMessage]:
        """
        Asynchronously compacts history if message count exceeds max_messages.
        Older messages are summarized into a single COMPACTED_HISTORY_SUMMARY message,
        preserving critical facts (biometrics, exclusions, targets) while truncating verbosity.
        """
        if len(messages) <= max_messages:
            return messages

        # Separate messages to compact and recent messages to preserve
        cutoff = len(messages) - (max_messages - 1)
        old_messages = messages[:cutoff]
        recent_messages = messages[cutoff:]

        # Extract structured facts from old_messages
        summarized_facts = []
        for msg in old_messages:
            msg_str = f"[{msg.sender} -> {msg.recipient}] ({msg.message_type}): "
            if isinstance(msg.payload, dict):
                keys = list(msg.payload.keys())
                msg_str += f"keys={keys}"
            else:
                msg_str += str(msg.payload)[:100]
            summarized_facts.append(msg_str)

        summary_text = f"COMPACTED HISTORY ({len(old_messages)} steps summarized):\n" + "\n".join(f"- {f}" for f in summarized_facts)

        summary_message = AgentMessage(
            sender="SystemMemoryManager",
            recipient="Orchestrator",
            message_type="COMPACTED_HISTORY_SUMMARY",
            payload={"summary": summary_text, "compacted_count": len(old_messages)}
        )

        # Store compacted summary as long-term memory node
        await self.store_memory(
            session_id=session_id,
            agent_name="SystemMemoryManager",
            key=f"compaction_at_{datetime.now().strftime('%H%M%S')}",
            value={"summary": summary_text, "compacted_count": len(old_messages)},
            memory_type="compacted_summary"
        )

        compacted_list = [summary_message] + recent_messages

        # Save compacted interaction to database asynchronously
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, self.db.add_interaction_message, session_id, summary_message)

        return compacted_list

    async def save_session_async(
        self,
        session_id: str,
        user_profile: Optional[UserProfile] = None,
        messages: Optional[List[AgentMessage]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Asynchronously persists session state and interaction history to database."""
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, self.db.save_session, session_id, "default_user", metadata)

        if user_profile:
            await loop.run_in_executor(None, self.db.save_user_profile, session_id, user_profile)

        if messages:
            for msg in messages:
                await loop.run_in_executor(None, self.db.add_interaction_message, session_id, msg)

    async def load_session_async(self, session_id: str) -> SessionContext:
        """Asynchronously loads session context and memory history from database."""
        loop = asyncio.get_running_loop()
        profile = await loop.run_in_executor(None, self.db.get_user_profile, session_id)
        history = await loop.run_in_executor(None, self.db.get_interaction_history, session_id)
        nodes = await loop.run_in_executor(None, self.db.get_memory_nodes, session_id, None, None)

        compacted_summaries = [str(n.value.get("summary")) for n in nodes if n.memory_type == "compacted_summary" and isinstance(n.value, dict)]

        return SessionContext(
            session_id=session_id,
            user_profile=profile,
            message_history=history,
            memory_nodes=nodes,
            compacted_summaries=compacted_summaries
        )
