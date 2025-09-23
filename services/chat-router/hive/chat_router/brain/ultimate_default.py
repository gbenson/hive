from . import add_route, request_llm_response

add_route("*", request_llm_response())
