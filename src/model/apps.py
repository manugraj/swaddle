from typing import List, Optional

from pydantic import BaseModel, Field

from src.model import InfraCharacteristic, Grouped, GitRepo
from src.model.server import Cluster


class App(Grouped):
    name: str
    git: Optional[GitRepo]
    docker_file: Optional[str] = Field(default="docker-compose.yml", description="Name of docker-compose "
                                                                                 "configuration in repository")
    docker_compose: Optional[dict] = Field(description="Docker compose definition")
    availability: Optional[int] = Field(default=3)
    qualities: InfraCharacteristic
    active: bool = Field(default=True, description="Status")


class AppsRequest(BaseModel):
    apps: List[App]


class AppStack(BaseModel):
    deployed_in: Optional[List[Cluster]]
    stack_name: str


class AppLog(App):
    deployments: Optional[List[AppStack]]
