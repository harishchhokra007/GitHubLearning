"""Memory agent for context management and conversation tracking."""

import logging
from typing import Any, Dict, List
from collections import deque

from agents.base_agent import BaseAgent
from config.settings import AgentRole
from core.types import AgentMessage, SystemResponse

logger = logging.getLogger(__name__)


class MemoryAgent(BaseAgent):
    """
    Memory agent responsible for:
    - Conversation history management
    - Context preservation
    - State persistence
    - Execution trace tracking
    - Session management
    """
    
    def __init__(self, max_history: int = 100, agent_id: str = "memory_1"):
        """
        Initialize memory agent.
        
        Args:
            max_history: Maximum number of messages to keep in memory
            agent_id: Unique agent identifier
        """
        super().__init__(agent_id, AgentRole.MEMORY)
        self.max_history = max_history
        self.conversation_history: deque = deque(maxlen=max_history)
        self.session_state: Dict[str, Any] = {}
        self.execution_traces: Dict[str, List[Dict[str, Any]]] = {}
        
    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process memory operations.
        
        Args:
            input_data: Can contain various operations
            
        Returns:
            Dictionary with memory state
        """
        self.update_status("processing", "managing_memory")
        
        operation = input_data.get('operation', 'store')
        
        if operation == 'store_response':
            await self._store_response(input_data.get('response'))
        elif operation == 'store_trace':
            await self._store_trace(input_data.get('trace'))
        elif operation == 'get_history':
            return await self._get_history(input_data.get('limit'))
        elif operation == 'update_state':
            await self._update_state(input_data.get('state_update'))
        
        self.update_status("done")
        
        return {
            'status': 'success',
            'memory_size': len(self.conversation_history)
        }
    
    async def _store_response(self, response: Any) -> None:
        """
        Store a system response in memory.
        
        Args:
            response: SystemResponse to store
        """
        if response:
            self.conversation_history.append({
                'type': 'response',
                'data': response,
                'timestamp': response.execution_time_ms if hasattr(response, 'execution_time_ms') else 0
            })
            self.log_execution_step("Response stored", {
                'response_id': response.response_id if hasattr(response, 'response_id') else 'unknown'
            })
    
    async def _store_trace(self, trace: Dict[str, Any]) -> None:
        """
        Store execution trace.
        
        Args:
            trace: Execution trace to store
        """
        if trace:
            trace_id = trace.get('trace_id', f"trace_{len(self.execution_traces)}")
            self.execution_traces[trace_id] = trace.get('steps', [])
            self.log_execution_step("Trace stored", {'trace_id': trace_id})
    
    async def _get_history(self, limit: int = 10) -> Dict[str, Any]:
        """
        Get conversation history.
        
        Args:
            limit: Maximum number of entries to return
            
        Returns:
            Dictionary with history
        """
        history = list(self.conversation_history)[-limit:] if limit else list(self.conversation_history)
        self.log_execution_step("History retrieved", {'size': len(history)})
        return {
            'history': history,
            'total_size': len(self.conversation_history)
        }
    
    async def _update_state(self, state_update: Dict[str, Any]) -> None:
        """
        Update session state.
        
        Args:
            state_update: Dictionary with state updates
        """
        if state_update:
            self.session_state.update(state_update)
            self.log_execution_step("State updated", {'keys_updated': len(state_update)})
    
    def add_to_history(self, message: AgentMessage) -> None:
        """
        Add a message to conversation history.
        
        Args:
            message: Message to add
        """
        self.conversation_history.append({
            'type': 'message',
            'agent_id': message.agent_id,
            'content': message.content,
            'timestamp': message.timestamp.isoformat()
        })
    
    def get_conversation_history(self) -> List[Dict[str, Any]]:
        """Get full conversation history."""
        return list(self.conversation_history)
    
    def get_session_state(self) -> Dict[str, Any]:
        """Get current session state."""
        return self.session_state.copy()
    
    def get_execution_traces(self) -> Dict[str, List[Dict[str, Any]]]:
        """Get all stored execution traces."""
        return self.execution_traces.copy()
    
    def clear_history(self) -> None:
        """Clear conversation history."""
        self.conversation_history.clear()
        self.log_execution_step("History cleared")
    
    def get_memory_summary(self) -> Dict[str, Any]:
        """Get a summary of memory usage."""
        return {
            'history_size': len(self.conversation_history),
            'max_history': self.max_history,
            'num_traces': len(self.execution_traces),
            'state_keys': len(self.session_state),
            'memory_id': self.agent_id
        }
