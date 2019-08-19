import docker

import config


def clean_before():
    cli = docker.from_env()
    all_running = cli.containers.list()
    if config.CONTAINER_NAME in [x.name for x in all_running]:
        cli.api.stop(config.CONTAINER_NAME)
        cli.api.remove_container(config.CONTAINER_NAME)
        cli.images.remove(config.CONTAINER_NAME)
