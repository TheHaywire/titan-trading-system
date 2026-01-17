"""
Skill Registry
==============
Central hub for Titan Intelligence Skills.
Evaluates all active skills and provides a unified intelligence score.
"""

from typing import Dict, List, Any, Optional
import logging
import asyncio
from .base import IntelligenceSkill
from .news_guardian import NewsGuardianSkill
from .correlation_guard import CorrelationGuardSkill

logger = logging.getLogger("Titan.SkillRegistry")

class SkillRegistry:
    def __init__(self):
        self.skills: Dict[str, IntelligenceSkill] = {}
        self._load_default_skills()

    def _load_default_skills(self):
        """Pre-load the standard intelligent skills"""
        self.register(NewsGuardianSkill())
        self.register(CorrelationGuardSkill())
        logger.info(f"Loaded {len(self.skills)} intelligent skills.")

    def register(self, skill: IntelligenceSkill):
        self.skills[skill.name] = skill

    async def evaluate_all(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run all active skills and aggregate results.
        
        Returns:
            Dict with final status, adjustment, and aggregated reasoning.
        """
        results = []
        
        # Run skills concurrently
        tasks = [skill.evaluate(context) for skill in self.skills.values() if skill.active]
        results = await asyncio.gather(*tasks)
        
        final_adjustment = 0
        final_status = 'PASS'
        reasons = []
        
        for result in results:
            final_adjustment += result.get('adjustment', 0)
            
            status = result.get('status')
            if status == 'BLOCK':
                final_status = 'BLOCK'
            elif status == 'WARN' and final_status != 'BLOCK':
                final_status = 'WARN'
                
            reason = result.get('reason')
            if reason and status != 'PASS':
                reasons.append(reason)
                
        return {
            'status': final_status,
            'adjustment': final_adjustment,
            'reasons': reasons,
            'skill_count': len(results)
        }

    def get_skill(self, name: str) -> Optional[IntelligenceSkill]:
        return self.skills.get(name)
