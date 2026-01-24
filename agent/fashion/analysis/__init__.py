"""
Analysis Module for Fashion Design

Модуль для анализа паттернов, оптимизации и обработки правил.
Независимый модуль без внешних платных API.
"""

import logging
logger = logging.getLogger(__name__)

# Ленивые импорты для предотвращения UnicodeEncodeError
def _lazy_import_constraints():
    try:
        from . import constraints
        return constraints
    except ImportError as e:
        logger.warning(f"Could not import constraints module: {e}")
        return None

def _lazy_import_reward():
    try:
        from . import reward
        return reward
    except ImportError as e:
        logger.warning(f"Could not import reward module: {e}")
        return None

def _lazy_import_optimizer():
    try:
        from . import optimizer
        return optimizer
    except ImportError as e:
        logger.warning(f"Could not import optimizer module: {e}")
        return None

def _lazy_import_rule_diff():
    try:
        from . import rule_diff
        return rule_diff
    except ImportError as e:
        logger.warning(f"Could not import rule_diff module: {e}")
        return None

def _lazy_import_rule_proposal():
    try:
        from . import rule_proposal
        return rule_proposal
    except ImportError as e:
        logger.warning(f"Could not import rule_proposal module: {e}")
        return None

def _lazy_import_apply_proposal():
    try:
        from . import apply_proposal
        return apply_proposal
    except ImportError as e:
        logger.warning(f"Could not import apply_proposal module: {e}")
        return None

def _lazy_import_targets():
    try:
        from . import targets
        return targets
    except ImportError as e:
        logger.warning(f"Could not import targets module: {e}")
        return None

__all__ = [
    # Constraints
    'ConstraintEngine',
    'ConstraintValidator', 
    'ConstraintType',
    'ConstraintResult',
    # Reward
    'RewardEngine',
    'RewardCalculator',
    'RewardType',
    # Optimizer
    'BaseOptimizer',
    'OptimizationResult',
    'OptimizationCandidate',
    'CandidateGenerator',
    'CandidateEvaluator',
    'OptimizationLoop',
    'OptimizationReportBuilder',
    # Rule processing
    'RuleDiff',
    'RuleProposalEngine',
    'ApplyProposal',
    # Targets
    'TargetSpec',
    'TargetLibrary',
    'TARGET_PATH_MAPPINGS'
]
