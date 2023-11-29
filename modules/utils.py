#!/bin/python3.10

import logging

from oci.response import Response

log = None

"""Utilities contains static methods that can be leveraged by other classes
    for the purposes of code comprehension elsewhere
"""
class Utilities:

    @staticmethod
    def print_response_metadata(response: Response) -> str:
        return (f'Response metadata:\n'
                f'\thas_next_page: {response.has_next_page}\n'
                f'\theaders: {response.headers}\n'
                f'\tnext_page: {response.next_page}\n'
                f'\trequest id: {response.request_id}\n'
                f'\trequest: \n\t\t{response.status} {response.request.method} {response.request.url}\n'
                f'\t\tHeader {response.request.header_params}\n'
                f'\t\tParameters {response.request.query_params}\n'
                f'\t\tType {response.request.response_type}\n'
                f'\t\tEnforce Content Headers {response.request.enforce_content_headers}\n'
                f'\t\tBody {response.request.body}')

    @staticmethod
    def make_client(client_type: object, config: dict, signer=None, **kwargs) -> object:
        log.debug(f'Making client with parameters:\n\tclient_type: {client_type}'
                  f'\n\tConfig: {config}\n\tSigner: {signer}')
        client = None
        if signer is None:
            client = client_type(config, **kwargs)
        else:
            client = client_type({}, signer=signer, **kwargs)

        return client
    
    # Will will return a list of responses with unknown data fields and let the caller
    # sort out the data
    @staticmethod
    def paginate(client_method: callable, *args, **kwargs) -> list[Response]:
        responses = [client_method(*args, **kwargs)]
        log.debug(Utilities.print_response_metadata(responses[-1]))
        if responses[-1].status != 200:
            log.error(f'Response status {responses[-1].status} during {client_method}\n{responses[-1].data}')

        # Keep looping while there are more pages
        while responses[-1].has_next_page:
            response = client_method(*args, page=responses[-1].next_page, **kwargs)
            responses.append(response)
            log.debug(Utilities.print_response_metadata(response))
            if response.status != 200:
                log.error(f'Response status {response.status} during {client_method}\n{response.data}')

        log.info(f'Returned {len(responses)} Response objects')
        return responses
    

def _set_log_level(level):
    logging.basicConfig(level=level)
    global log
    log = logging.getLogger(__name__)