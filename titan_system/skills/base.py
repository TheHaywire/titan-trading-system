"""
Titan Intelligence Skill Base
============================
The foundation for modular, pluggable intelligence components.
"""

from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional
import logging

logger = logging.getLogger("Titan.Skills")

class IntelligenceSkill(ABC):
    """Base class for all intelligence skills"""
    
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
        self.active = True
        self.last_run: Optional[datetime] = None
        self.metadata: Dict[str, Any] = {}

    @abstractmethod
    async def evaluate(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Evaluate market context and return an intelligent insight/constraint.
        
        Args:
            context: Current market/account data
            
        Returns:
            Dict containing:
                - 'status': 'PASS', 'WARN', 'BLOCK'
                - 'adjustment': Score adjustment (-100 to +100)
                - 'reason': Human readable explanation
                - 'metadata': Additional metrics
        """
        pass

    def toggle(self, state: bool):
        """Enable or disable the skill"""
        self.active = state
        logger.info(f"Skill {self.name} changed state to: {'ACTIVE' if state else 'INACTIVE'}")

    def log_result(self, result: Dict[str, Any]):
        """Standardized logging for skill results"""
        status = result.get('status', 'UNKNOWN')
        reason = result.get('reason', 'No reason provided')
        if status == 'BLOCK':
            logger.warning(f"[SKILL:{self.name}] BLOCK: {reason}")
        elif status == 'WARN':
            logger.info(f"[SKILL:{self.name}] WARN: {reason}")
