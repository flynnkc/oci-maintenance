#!/bin/python3.10

import logging
import argparse

from oci.config import from_file

from modules.inventory import Inventory, _set_log_level as inventory_log
from modules.utils import _set_log_level as utilities_log

log = None

search_types = [
    "instance",
    "volume",
    "vcn",
    "analyticsinstance",
    "apigateway",
    "bastion",
    "bootvolume",
    "certificateauthority",
    "instancepool",
    "clusterscluster",
    "clustersvirtualnode",
    "containerinstance",
    "datacatalog",
    "application",
    "disworkspace",
    "datascienceproject",
    "autonomousdatabase",
    "cloudexadatainfrastructure",
    "dbsystem",
    "devopsproject",
    "filesystem",
    "functionsfunction",
    "integrationinstance",
    "loadbalancer",
    "drg",
    "networkfirewall",
    "bucket",
    "stream",
    "vault",
    "vbsinstance"
    ]

def main():
    parser = argparse.ArgumentParser()

    parser.add_argument('-c', '--compartment', help='Compartment to perform \
                        operations on')
    parser.add_argument('-d', '--debug', action='store_true', help='Enable debug mode')
    parser.add_argument('-a', '--auth', choices=['instance_principal', 'delegation_token'],
                        help='Authentication method if not config file')
    parser.add_argument('-p', '--profile', help='Profile to use from config file \
                        -- Defaults to DEFAULT', default='DEFAULT')
    parser.add_argument('--config', help='Config file location',
                        default='~/.oci/config')

    args = parser.parse_args()

    _set_config(args)

    log.debug(f'Arguments: {args}')

    config = from_file()
    inventory = Inventory(config)
    #inventory.set_resources(["instance"], "us-ashburn-1", query_kwargs={"compartment": "ocid1.compartment.oc1..aaaaaaaavegzwsigdvyjtsq5ryqujwckz5jm5lwkphhdp2a6dqcurxnmkqaa",
    #                                                     "life_cycle_state": "RUNNING",
    #                                                     "defined_tags": {"A-Team": ("Creator", "oke")}})

    inventory.set_resources(["instance"], "us-ashburn-1")
    #inventory.print_resources()
    print(inventory.filter_on_tags("A-Team"))


def make_config(args: argparse.Namespace) -> dict | None:
    if args.auth == None:
        config = from_file(profile_name=args.profile, file_location=args.config)
        if args.debug:
            log.debug(f'Config: {config}')
        return config
    

# Set dependencies on modules
def _set_config(args: argparse.Namespace):
    global log
    # Debug mode
    if args.debug:
        logging.basicConfig(level=logging.DEBUG)
        inventory_log(logging.DEBUG)
        utilities_log(logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)
        inventory_log(logging.INFO)
        utilities_log(logging.INFO)
    log = logging.getLogger(__name__)


if __name__ == '__main__':
    main()