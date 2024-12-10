#!/usr/bin/env python3
"""Network configuration management tool with diff checking and deployment capabilities."""

import argparse

from fnmatch import fnmatch
from nornir import InitNornir
from nornir_utils.plugins.functions import print_result
from nornir_napalm.plugins.tasks import napalm_configure, napalm_get
from tools import nornir_set_creds


def deploy_network(task, configure=False):
    """Execute network device configuration tasks with diff checking and optional deployment."""
    if "linux" in task.host.name:
        pass
    else:
        if configure:
            task.run(
                name=f"Configuring (replace) {task.host.name}!",
                task=napalm_configure,
                filename=f"device_configs/{task.host.name}.cfg",
                replace=True,
            )
        else:
            task.run(
                name=f"Checking diff for {task.host.name}",
                task=napalm_configure,
                filename=f"device_configs/{task.host.name}.cfg",
                replace=True,
                dry_run=True,
            )


def get_device_info(task):
    """Get device facts and configuration."""
    if "linux" in task.host.name:
        pass
    else:
        task.run(
            name=f"Getting info from {task.host.name}",
            task=napalm_get,
            getters=["facts", "interfaces"],
        )


def main():
    """Parse CLI arguments and execute network configuration tasks."""
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # Deploy command
    deploy_parser = subparsers.add_parser("deploy", help="Deploy configuration")
    deploy_parser.add_argument(
        "-c", "--configure", action="store_true", help="Apply configuration changes"
    )
    deploy_parser.add_argument(
        "--limit", help="Limit execution to specific devices (e.g., ceos-01 or ceos*)"
    )

    # Info command
    info_parser = subparsers.add_parser("info", help="Get device information")
    info_parser.add_argument(
        "-g", "--getters", nargs="+",
        default=["facts", "interfaces"],
        help="NAPALM getters to use"
    )
    info_parser.add_argument(
        "--limit", help="Limit execution to specific devices (e.g., ceos-01 or ceos*)"
    )

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    norn = InitNornir(config_file="scripts/nornir_config.yml")
    nornir_set_creds(norn)
    if args.limit:
        filtered_norn = norn.filter(
            filter_func=lambda h: fnmatch(h.name, args.limit)
        )
    else:
        filtered_norn = norn

    if args.command == "deploy":
        result = filtered_norn.run(task=deploy_network, configure=args.configure)
    elif args.command == "info":
        result = filtered_norn.run(task=get_device_info)
    else:
        result = filtered_norn.run(task=deploy_network, configure=False)

    print_result(result)


if __name__ == "__main__":
    main()
