#!/bin/python3.10

import datetime
import json
import logging

from .utils import Utilities

from oci.config import validate_config
from oci.identity import IdentityClient
from oci.resource_search import ResourceSearchClient
from oci.resource_search.models import StructuredSearchDetails, ResourceSummaryCollection
from oci.response import Response

log = None

class Inventory:
    config = {}
    signer = None
    regions = {}
    resources = {}

    def __init__(self, config: dict, signer=None):
        self.log = logging.getLogger(f'{__name__}.Inventory')
        self.log.info(f"Initializing Inventory object {self}")
        validate_config(config, signer=signer)
        self.log.debug('Configuration validated')
        self.config = config
        self.signer = signer #InstancePrincipalsSecurityTokenSigner if required
        self.log.debug(f'Inventory object initialized with the follwing properties:\nConfig: {self.config}\nSigner: {self.signer}')
        self.set_subscribed_regions()

    def print_resources(self):
        s = {"count": 0}
        count = 0

        for key in self.resources.keys():
            # Use the ResourceSummary __repr__ to get a string representation of a
            # flat dict which we load back into an iterable, parsable dict
            # ;_;
            s[key] = json.loads(self.resources[key].items.__repr__())
            count += len(self.resources[key].items)

        s["count"] = count
        print(json.dumps(s, indent=4))

    '''
    Getters and Setters
    '''

    def set_subscribed_regions(self):
        self.log.info('Getting subscribed regions')
        client = Utilities.make_client(IdentityClient, self.config, self.signer)
        response = client.list_region_subscriptions(self.config['tenancy'])
        self.log.debug(Utilities.print_response_metadata(response))
        for region in response.data:
            self.regions[region.region_name] = region

        self.log.debug(f'Inventory.regions: {self.regions}')

    # Required because OCI configuration has defined region that needs to be changed
    def set_region(self, region:str):
        self.log.debug(f'Setting region to {region}')
        self.config["region"] = region

    # Convenience method for getting everything
    def set_all_resources_all_regions(self, **kwargs):
        self.set_resources_all_regions(["all"], **kwargs)

    def set_resources_all_regions(self, resources: list[str], **kwargs):
        for region in self.regions.keys():
            self.set_resources(resources, region, **kwargs)

    def set_resources(self, resources: list[str], region: str, **kwargs):
        self.set_region(region)
        self.resources[region] = self._get_resources(resources, **kwargs)

    '''
    Filters
    '''

    def filter_on_tags(self, tag_namespace: str, tag_title: str | None=None, tag_value: str | None=None) -> dict:
        result = {"results": []}
        # Filter on tag namespace
        for k in self.resources.keys():
            for item in self.resources[k].items:
                if tag_namespace in item.defined_tags:
                    result["results"].append(item)

        if tag_title is not None:
            pass

        if tag_value is not None:
            pass

        return result

    '''
    Static Methods and Helpers
    '''

    def _get_resources(self, resource_types: list[str], query_kwargs={}, search_kwargs={}) -> ResourceSummaryCollection:
        client = Utilities.make_client(ResourceSearchClient, self.config)
        details = StructuredSearchDetails(query=Inventory._make_query(", ".join(resource_types), **query_kwargs))
        responses = Utilities.paginate(client.search_resources, details, **search_kwargs)
        return Inventory._unpack_search_responses(responses)

    @staticmethod
    def _make_query(resources: str, **kwargs) -> str:
        # Note the flipped order of single/double quotes to support query where clause
        query = f'query {resources} resources'
        keys = kwargs.keys()
        if len(keys) > 0:
            query += " where "
            clauses = []
            if "compartment" in keys:
                clauses.append(f"compartmentId = '{kwargs['compartment']}'")
            if "life_cycle_state" in keys:
                clauses.append(f"lifeCycleState = '{kwargs['life_cycle_state']}'")
            # defined_tags needs to be a dict due to needing the namespace as well as value
            # {"namespace": ("key", "value")}
            if "defined_tags" in keys:
                for k, v in kwargs["defined_tags"].items():
                    defined_tags = (
                        f"definedTags.namespace = '{k}' && definedTags.key = '{v[0]}'" if v[1] is None
                        else f"definedTags.namespace = '{k}' && definedTags.key = '{v[0]}' && definedTags.value ='{v[1]}'"
                    )
                    clauses.append(defined_tags)
            query += " && ".join(clauses)

        log.debug(f'make_query: {query}')
        return(query)
    
    @staticmethod
    def _unpack_search_responses(responses: list[ResourceSummaryCollection]) -> ResourceSummaryCollection:
        log.info("Unpacking Responses...")
        items = []

        for response in responses:
            items.extend(response.data.items)

        collection = ResourceSummaryCollection(items=items)
        log.info(f'Unpacked {len(responses)} Responses!')
        
        return collection
    

def _set_log_level(level):
    logging.basicConfig(level=level)
    global log
    log = logging.getLogger(__name__)