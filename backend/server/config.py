from dataclasses import dataclass

@dataclass
class Routes:
    healthcheck: str = "/healthcheck"
