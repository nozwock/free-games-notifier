from free_games_notifier.crawlers.utils import add_query_params, get_url_schema


def set_server_list_defaults(servers: list[str]) -> list[str]:
    for i, server in enumerate(servers):
        match get_url_schema(server):
            case "ntfy":
                servers[i] = add_query_params(server, {"image": "False"})
            case _:
                # todo:
                pass

    return servers


# Need to do modify the webhook URL directly since apprise doesn't expose
# some python API to add a click action to a notification.
def set_server_list_notify_params(
    servers: list[str], click_action: str, image_url: str | None = None
) -> list[str]:
    for i, server in enumerate(servers):
        match get_url_schema(server):
            case "ntfy":
                servers[i] = add_query_params(
                    server, {"click": click_action, "attach": image_url}
                )
            case _:
                # todo:
                pass

    return servers
