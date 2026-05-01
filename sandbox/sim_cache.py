from dataclasses import dataclass, field
from typing import List, Any

@dataclass
class SimState:
    """Contenedor de estado que agrupa todas las entidades relevantes de la simulación."""
    ball: Any = None
    robots: List[Any] = field(default_factory=list)
    goals: List[Any] = field(default_factory=list)
    pitch: Any = None
