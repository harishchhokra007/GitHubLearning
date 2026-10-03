"""Base agent class and agent communication framework."""

import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime

from config.settings import AgentRole, MessageType
from core.types import AgentMessage

logger = logging.getLogger(__name__)


@dataclass
class AgentState:
    """Represents the state of an agent."""
    agent_id: str
    agent_role: AgentRole
    status: str  # "idle", "processing", "done", "error"
    current_task: Optional[str] = None
    messages: List[AgentMessage] = None
    results: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.messages is None:
            self.messages = []
        if self.results is None:
            self.results = {}


class BaseAgent(ABC):
    """Abstract base class for all agents."""
    
    def __init__(self, agent_id: str, role: AgentRole):
        """
        Initialize a base agent.
        
        Args:
            agent_id: Unique identifier for the agent
            role: Role of the agent in the system
        """
        self.agent_id = agent_id
        self.role = role
        self.state = AgentState(
            agent_id=agent_id,
            agent_role=role,
            status="idle"
        )
        self.message_queue: List[AgentMessage] = []
        self.execution_trace: List[Dict[str, Any]] = []
        
    @abstractmethod
    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process input and return output.
        
        Args:
            input_data: Input data for processing
            
        Returns:
            Dictionary with processing results
        """
        pass
    
    def add_message(self, message: AgentMessage) -> None:
        """Add a message to the agent's queue."""
        self.message_queue.append(message)
        self.state.messages.append(message)
        logger.debug(f"Agent {self.agent_id} received message: {message.message_type}")
    
    def send_message(self, target_agent_id: str, message_type: MessageType, 
                    content: str, metadata: Dict[str, Any] = None) -> AgentMessage:
        """
        Create and return a message to send to another agent.
        
        Args:
            target_agent_id: ID of the target agent
            message_type: Type of message
            content: Message content
            metadata: Additional metadata
            
        Returns:
            AgentMessage object
        """
        msg = AgentMessage(
            agent_id=self.agent_id,
            agent_role=self.role.value,
            message_type=message_type.value,
            content=content,
            metadata=metadata or {}
        )
        return msg
    
    def log_execution_step(self, step_name: str, details: Dict[str, Any] = None) -> None:
        """Log an execution step for tracing."""
        step = {
            'step_name': step_name,
            'agent_id': self.agent_id,
            'timestamp': datetime.now().isoformat(),
            'details': details or {}
        }
        self.execution_trace.append(step)
        logger.info(f"[{self.agent_id}] {step_name}")
    
    def get_execution_trace(self) -> List[Dict[str, Any]]:
        """Get the execution trace for this agent."""
        return self.execution_trace
    
    def update_status(self, status: str, current_task: Optional[str] = None) -> None:
        """Update agent status."""
        self.state.status = status
        if current_task:
            self.state.current_task = current_task
        logger.debug(f"Agent {self.agent_id} status: {status}")


class AgentRegistry:
    """Registry for all agents in the system."""
    
    def __init__(self):
        """Initialize agent registry."""
        self.agents: Dict[str, BaseAgent] = {}
    
    def register(self, agent: BaseAgent) -> None:
        """Register an agent."""
        self.agents[agent.agent_id] = agent
        logger.info(f"Registered agent: {agent.agent_id} ({agent.role.value})")
    
    def get_agent(self, agent_id: str) -> Optional[BaseAgent]:
        """Get an agent by ID."""
        return self.agents.get(agent_id)
    
    def get_agents_by_role(self, role: AgentRole) -> List[BaseAgent]:
        """Get all agents with a specific role."""
        return [agent for agent in self.agents.values() if agent.role == role]
    
    def list_agents(self) -> Dict[str, str]:
        """List all registered agents."""
        return {agent_id: agent.role.value for agent_id, agent in self.agents.items()}
