from dataclasses import dataclass, field


@dataclass
class AgentMemory:
    goal: str
    observations: list[str] = field(default_factory=list)
    actions: list[str] = field(default_factory=list)

    def remember_observation(self, value: str) -> None:
        self.observations.append(value)

    def remember_action(self, value: str) -> None:
        self.actions.append(value)
