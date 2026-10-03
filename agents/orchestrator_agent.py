"""Orchestrator agent for query planning and task routing."""

import logging
from typing import Any, Dict, List
import json

from agents.base_agent import BaseAgent
from config.settings import AgentRole, MessageType
from core.types import QueryPlan, Subtask

logger = logging.getLogger(__name__)


class OrchestratorAgent(BaseAgent):
    """
    Orchestrator agent responsible for:
    - Decomposing user queries into subtasks
    - Planning execution strategy
    - Routing tasks to appropriate agents
    - Managing workflow state
    """
    
    def __init__(self, agent_id: str = "orchestrator_1"):
        """Initialize orchestrator agent."""
        super().__init__(agent_id, AgentRole.ORCHESTRATOR)
        self.llm = None  # Will be set during initialization
        
    def set_llm(self, llm):
        """Set the LLM to use for planning."""
        self.llm = llm
    
    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a query and create an execution plan.
        
        Args:
            input_data: Must contain 'query' key with user query
            
        Returns:
            Dictionary with plan and routing information
        """
        self.update_status("processing", "decomposing_query")
        
        query = input_data.get('query', '')
        if not query:
            raise ValueError("Query is required")
        
        self.log_execution_step("Query received", {'query': query})
        
        # Decompose query into subtasks
        subtasks = await self._decompose_query(query)
        self.log_execution_step("Query decomposed", {'num_subtasks': len(subtasks)})
        
        # Create execution plan
        plan = QueryPlan(
            original_query=query,
            plan_id=f"plan_{len(self.execution_trace)}",
            subtasks=subtasks,
            reasoning="Multi-step reasoning required",
            execution_order=[s.subtask_id for s in subtasks]
        )
        
        self.state.results['plan'] = plan
        self.update_status("done")
        
        return {
            'plan': plan,
            'subtasks': subtasks,
            'status': 'success'
        }
    
    async def _decompose_query(self, query: str) -> List[Subtask]:
        """
        Decompose a query into subtasks.
        
        Args:
            query: User query
            
        Returns:
            List of subtasks
        """
        subtasks = []
        
        # Task 1: Retrieval
        subtask_1 = Subtask(
            subtask_id="retrieval_1",
            agent_role=AgentRole.RETRIEVER.value,
            description=f"Retrieve relevant documents for: {query}",
            dependencies=[],
            priority=1
        )
        subtasks.append(subtask_1)
        
        # Task 2: Analysis (depends on retrieval)
        subtask_2 = Subtask(
            subtask_id="analysis_1",
            agent_role=AgentRole.ANALYZER.value,
            description=f"Analyze retrieved documents and synthesize answer for: {query}",
            dependencies=["retrieval_1"],
            priority=2
        )
        subtasks.append(subtask_2)
        
        # Task 3: Verification (depends on analysis)
        subtask_3 = Subtask(
            subtask_id="verification_1",
            agent_role=AgentRole.VERIFIER.value,
            description="Verify grounding and validate response",
            dependencies=["analysis_1"],
            priority=3
        )
        subtasks.append(subtask_3)
        
        return subtasks
    
    def get_execution_plan_summary(self) -> Dict[str, Any]:
        """Get a summary of the execution plan."""
        if 'plan' not in self.state.results:
            return {}
        
        plan = self.state.results['plan']
        return {
            'plan_id': plan.plan_id,
            'original_query': plan.original_query,
            'num_subtasks': len(plan.subtasks),
            'execution_order': plan.execution_order,
            'subtasks': [
                {
                    'id': s.subtask_id,
                    'role': s.agent_role,
                    'description': s.description
                }
                for s in plan.subtasks
            ]
        }
