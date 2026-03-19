"""
D365 Demo Scenario Modules
==========================
Pluggable scenario templates for D365 Customer Service demos.

Each scenario module generates:
- Demo script content (Markdown)
- Talk tracks and voice lines
- Data requirements
- Demo section content for HTML guides

Available Scenarios:
- phone_call: Inbound phone call with screen pop
- chat_conversation: Bot → agent escalation flow
- email_samples: Email-to-case demo emails
- order_management: Order lookup and modification
- shipment_tracking: "Where's my order?" scenario
- rma_return: Return/RMA/Credit processing
- warranty: Warranty lookup and coverage check
- quick_quote: Quote generation flow (if enabled)
"""

from typing import Dict, Any, List, Callable
from pathlib import Path

# Scenario registry - maps scenario key to (filename, generator_function)
SCENARIO_REGISTRY: Dict[str, tuple] = {}


def register_scenario(key: str, filename: str):
    """Decorator to register a scenario generator."""
    def decorator(func: Callable):
        SCENARIO_REGISTRY[key] = (filename, func)
        return func
    return decorator


def get_available_scenarios() -> List[str]:
    """Return list of available scenario keys."""
    return list(SCENARIO_REGISTRY.keys())


def generate_scenario(key: str, config: Dict[str, Any], customer_name: str) -> str:
    """Generate a specific scenario's content."""
    if key not in SCENARIO_REGISTRY:
        raise ValueError(f"Unknown scenario: {key}. Available: {get_available_scenarios()}")
    
    filename, generator = SCENARIO_REGISTRY[key]
    return generator(config, customer_name)


def generate_all_scenarios(config: Dict[str, Any], customer_name: str, 
                           output_dir: Path, scenarios: List[str] = None) -> Dict[str, Path]:
    """Generate multiple scenarios and save to files."""
    results = {}
    target_scenarios = scenarios or get_available_scenarios()
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    for key in target_scenarios:
        if key not in SCENARIO_REGISTRY:
            continue
        filename, generator = SCENARIO_REGISTRY[key]
        content = generator(config, customer_name)
        output_path = output_dir / filename
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(content)
        results[key] = output_path
    
    return results


# Import all scenario modules to register them
from d365.scenarios import phone_call
from d365.scenarios import chat_conversation
from d365.scenarios import email_samples
from d365.scenarios import order_management
from d365.scenarios import shipment_tracking
from d365.scenarios import rma_return
from d365.scenarios import warranty
