import click

# TODO clean this up

STATUS_MESSAGES = {
    404: ("Not found", 4),
    409: ("State conflict", 3),
}

def handle_http_errors(resp):
    "Handles printing and exiting cleanly on HTTP errors."
    if resp.is_success:
        return resp
    default_msg, code = STATUS_MESSAGES.get(resp.status_code, ("Request failed", 1))
    try:
        msg = resp.json().get("detail", default_msg)
    except ValueError:
        msg = default_msg
    err = click.ClickException(msg)
    err.exit_code = code
    raise err
