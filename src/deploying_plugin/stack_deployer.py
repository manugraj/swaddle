import json
from typing import Tuple, Optional

from src.core.deployment_plugin import Deploying
from src.core.group_data import GroupDataManager
from src.core.ssh import SSH
from src.model.apps import App
from src.model.commands import Command
from src.model.deploy import DeploymentStep, DeployingStack
from src.model.message import SimpleStatus, MinStatus
from src.model.server import Server


class StackDeployer(Deploying):

    def __init__(self, group_manager: GroupDataManager):
        self.group_manager = group_manager

    def define_process(self, stack: DeployingStack) -> Tuple[SimpleStatus, DeployingStack]:
        messages = []
        for app_fabric in stack.apps:
            for cluster_fabric in app_fabric.clusters:
                cluster_data = self.group_manager.get_cluster_log(stack.group,
                                                                  cluster_id=cluster_fabric.cluster.cluster_id)
                messages.append(
                    f"Deployed {app_fabric.app.name} using deployment method:{self._deploy(cluster_data.data.managers[0], app_fabric.app, stack.deployment_id)}")
        return SimpleStatus(status=MinStatus.SUCCESS, messages=messages), stack

    def deployment_step(self) -> DeploymentStep:
        return DeploymentStep.DEPLOYMENT_5

    def entry_criteria(self, component: DeployingStack) -> Tuple[bool, Optional[str]]:
        return True, None

    def _deploy(self, server: Server, app: App, deployment_id: str):
        mechanism = None
        node = SSH.connect_server(server)
        node.run(Command(command=f"mkdir {deployment_id}"))
        privileged = server.privileged
        if app.git:
            if len(node.run_all_safe(
                    [
                        Command(command=f"cd {deployment_id}; git clone {app.git.repo}", privileged=privileged),
                        Command(command=f"cd {deployment_id}; docker-compose build", privileged=privileged),
                        Command(command=f"cd {deployment_id}; docker stack -c docker-compose.yml {app.name}",
                                privileged=privileged)])) < 3:
                raise Exception("Failed to deploy application")
            mechanism = "git"
        elif app.docker_compose:
            if len(node.run_all_safe(
                    [
                        Command(command=f"cd {deployment_id};echo {json.dumps(app.docker_compose)} >> {app.name}.json"),
                        Command(command=f"cd {deployment_id};docker-compose -f {app.name}.json build",
                                privileged=privileged),
                        Command(command=f"cd {deployment_id};docker stack -c {app.name}.yml {app.name}",
                                privileged=privileged)
                    ])) < 3:
                raise Exception("Failed to deploy application")
            mechanism = "dc"
        return mechanism
