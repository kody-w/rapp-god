from __future__ import annotations

import argparse
import contextlib
import re
import sys
from collections.abc import Sequence

from . import __version__
from .client import BrainstemClient
from .commands import (
    Context,
    agent_export,
    agent_import,
    agent_info,
    agent_install,
    agent_list,
    agent_remove,
    agent_search,
    auth_login,
    auth_poll,
    auth_retry,
    auth_status,
    auth_switch,
    brainstem_health,
    brainstem_locate,
    brainstem_run,
    brainstem_version,
    capabilities,
    chat,
    config_path,
    config_show,
    doctor,
    invoke,
    model_list,
    model_set,
    ring_list,
    ring_status,
    status,
    twin_hatch,
    twin_list,
    twin_show,
    unavailable_capability,
)
from .config import Config
from .errors import ConfirmationRequired, InternalFailure, RappError, UsageError
from .output import Output
from .twin_hatch import HATCH_CONFIRMATION_MESSAGE


class _ArgumentParser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        cleaned = re.sub(
            r"the following arguments are required: [a-z_]+_command",
            "a subcommand is required",
            message,
        )
        raise UsageError(cleaned)


def _parser() -> argparse.ArgumentParser:
    parser = _ArgumentParser(
        prog="rapp",
        description="Headless command-line control surface for the RAPP platform.",
    )
    parser.add_argument("--version", action="store_true", help="show the CLI version")
    output_group = parser.add_mutually_exclusive_group()
    output_group.add_argument("--json", action="store_true", help="emit one JSON result")
    output_group.add_argument(
        "--jsonl",
        action="store_true",
        help="emit JSON Lines events for a streaming command",
    )
    parser.add_argument("--quiet", action="store_true", help="suppress successful human output")
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="show tracebacks for unexpected internal failures",
    )
    parser.add_argument("--config", help="path to config.json")
    parser.add_argument("--url", help="Brainstem base URL")
    parser.add_argument("--timeout", type=float, help="request timeout in seconds")
    parser.add_argument(
        "--allow-insecure-http",
        action="store_true",
        help="allow plaintext HTTP to a non-loopback Brainstem",
    )
    parser.add_argument(
        "--secret-file",
        help="path containing the Brainstem LAN secret; prefer this over command-line secrets",
    )

    subcommands = parser.add_subparsers(dest="command", required=True)

    status_parser = subcommands.add_parser(
        "status",
        help="shallow Brainstem reachability probe",
    )
    status_parser.set_defaults(handler=status)

    doctor_parser = subcommands.add_parser("doctor", help="diagnose the local RAPP environment")
    doctor_mode = doctor_parser.add_mutually_exclusive_group()
    doctor_mode.add_argument("--offline", action="store_true", help="skip network probes")
    doctor_mode.add_argument(
        "--deep",
        action="store_true",
        help="load agents through /health; may execute installed cartridge imports",
    )
    doctor_parser.set_defaults(handler=doctor)

    capabilities_parser = subcommands.add_parser(
        "capabilities",
        help="show implemented, read-only, and unavailable surfaces",
    )
    capabilities_parser.set_defaults(handler=capabilities)

    config_parser = subcommands.add_parser("config", help="inspect resolved CLI configuration")
    config_commands = config_parser.add_subparsers(dest="config_command", required=True)
    config_path_parser = config_commands.add_parser("path", help="show the config file path")
    config_path_parser.set_defaults(handler=config_path)
    config_show_parser = config_commands.add_parser("show", help="show resolved non-secret config")
    config_show_parser.set_defaults(handler=config_show)

    brainstem_parser = subcommands.add_parser("brainstem", help="operate the Brainstem runtime")
    brainstem_commands = brainstem_parser.add_subparsers(dest="brainstem_command", required=True)
    health_parser = brainstem_commands.add_parser("health", help="show Brainstem health")
    health_parser.set_defaults(handler=brainstem_health)
    version_parser = brainstem_commands.add_parser("version", help="show Brainstem version")
    version_parser.set_defaults(handler=brainstem_version)
    locate_parser = brainstem_commands.add_parser(
        "locate", help="locate a compatible Brainstem layout"
    )
    locate_parser.add_argument("--home", help="override the Brainstem installation root")
    locate_parser.set_defaults(handler=brainstem_locate)
    run_parser = brainstem_commands.add_parser(
        "run", help="run the installed Brainstem in the foreground"
    )
    run_parser.add_argument("--home", help="override the Brainstem installation root")
    run_parser.set_defaults(handler=brainstem_run)

    launch_parser = subcommands.add_parser(
        "launch",
        help="run a compatible Brainstem layout in the foreground",
    )
    launch_parser.add_argument("--home", help="override the Brainstem installation root")
    launch_parser.set_defaults(handler=brainstem_run)

    chat_parser = subcommands.add_parser("chat", help="send a message through the /chat contract")
    chat_parser.add_argument(
        "message",
        nargs="*",
        help="message text; omit to read stdin or start a REPL",
    )
    chat_parser.add_argument("--history", help="JSON file containing prior conversation turns")
    chat_parser.add_argument("--session-id", help="optional correlation identifier")
    chat_parser.add_argument("--stream", action="store_true", help="use POST /chat/stream")
    chat_parser.add_argument(
        "--show-agent-logs",
        action="store_true",
        help="include potentially sensitive Brainstem agent logs",
    )
    chat_parser.set_defaults(handler=chat)

    model_parser = subcommands.add_parser("model", help="inspect or select the Brainstem model")
    model_commands = model_parser.add_subparsers(dest="model_command", required=True)
    model_list_parser = model_commands.add_parser("list", help="list available models")
    model_list_parser.set_defaults(handler=model_list)
    model_set_parser = model_commands.add_parser("set", help="select a model")
    model_set_parser.add_argument("model", help="model identifier or auto")
    model_set_parser.set_defaults(handler=model_set)

    auth_parser = subcommands.add_parser("auth", help="operate GitHub/Copilot authentication")
    auth_commands = auth_parser.add_subparsers(dest="auth_command", required=True)
    auth_status_parser = auth_commands.add_parser("status", help="show pending login state")
    auth_status_parser.set_defaults(handler=auth_status)
    auth_login_parser = auth_commands.add_parser("login", help="start GitHub device-code login")
    auth_login_parser.add_argument("--wait", action="store_true", help="wait for login completion")
    auth_login_parser.add_argument(
        "--deadline",
        type=float,
        default=600,
        help="maximum wait in seconds",
    )
    auth_login_parser.set_defaults(handler=auth_login)
    auth_poll_parser = auth_commands.add_parser("poll", help="poll a pending login once")
    auth_poll_parser.set_defaults(handler=auth_poll)
    auth_retry_parser = auth_commands.add_parser(
        "retry", help="retry Copilot entitlement with the existing GitHub login"
    )
    auth_retry_parser.set_defaults(handler=auth_retry)
    auth_switch_parser = auth_commands.add_parser(
        "switch", help="clear cached credentials and start a new account login"
    )
    auth_switch_parser.add_argument("--yes", action="store_true", help="confirm credential reset")
    auth_switch_parser.set_defaults(handler=auth_switch)

    agent_parser = subcommands.add_parser("agent", help="manage Brainstem agent cartridges")
    agent_commands = agent_parser.add_subparsers(dest="agent_command", required=True)
    agent_list_parser = agent_commands.add_parser("list", help="list installed agent files")
    agent_list_parser.set_defaults(handler=agent_list)
    agent_import_parser = agent_commands.add_parser("import", help="import a local agent cartridge")
    agent_import_parser.add_argument("file", help="path to a *_agent.py file")
    agent_import_parser.add_argument("--sha256", help="expected catalog SHA-256")
    agent_import_parser.add_argument(
        "--yes",
        action="store_true",
        help="confirm execution of the supplied agent source",
    )
    agent_import_parser.set_defaults(handler=agent_import)
    agent_export_parser = agent_commands.add_parser("export", help="export an installed agent")
    agent_export_parser.add_argument("filename", help="installed *_agent.py filename")
    agent_export_parser.add_argument("-o", "--output", help="destination path")
    agent_export_parser.add_argument("--force", action="store_true", help="replace the destination")
    agent_export_parser.set_defaults(handler=agent_export)
    agent_remove_parser = agent_commands.add_parser("remove", help="remove an installed agent")
    agent_remove_parser.add_argument("filename", help="installed *_agent.py filename")
    agent_remove_parser.add_argument("--yes", action="store_true", help="confirm removal")
    agent_remove_parser.set_defaults(handler=agent_remove)
    agent_search_parser = agent_commands.add_parser("search", help="search pinned RAR agents")
    agent_search_parser.add_argument("query", help="all search terms must match")
    agent_search_parser.set_defaults(handler=agent_search)
    agent_info_parser = agent_commands.add_parser("info", help="show one pinned RAR agent")
    agent_info_parser.add_argument("name", help="fully qualified @publisher/name")
    agent_info_parser.set_defaults(handler=agent_info)
    agent_install_parser = agent_commands.add_parser(
        "install", help="verify and import one agent from the installer-pinned RAR revision"
    )
    agent_install_parser.add_argument("name", help="fully qualified @publisher/name")
    agent_install_parser.add_argument(
        "--yes",
        action="store_true",
        help="confirm execution of verified agent source",
    )
    agent_install_parser.set_defaults(handler=agent_install)

    ring_parser = subcommands.add_parser("ring", help="inspect the RAPP release train")
    ring_commands = ring_parser.add_subparsers(dest="ring_command", required=True)
    ring_list_parser = ring_commands.add_parser("list", help="list release rings")
    ring_list_parser.add_argument("--source", help="override the release-train base URL")
    ring_list_parser.set_defaults(handler=ring_list)
    ring_status_parser = ring_commands.add_parser("status", help="show release-train status")
    ring_status_parser.add_argument("ring", nargs="?", help="optional ring name")
    ring_status_parser.add_argument("--source", help="override the release-train base URL")
    ring_status_parser.set_defaults(handler=ring_status)
    ring_fly_parser = ring_commands.add_parser(
        "fly", help="not available until a sandbox contract is published"
    )
    ring_fly_parser.add_argument("ring", choices=["canary", "nightly", "alpha", "beta"])
    ring_fly_parser.set_defaults(handler=unavailable_capability)
    twin_parser = subcommands.add_parser("twin", help="hatch and inspect local Twins")
    twin_commands = twin_parser.add_subparsers(dest="twin_command", required=True)
    twin_hatch_parser = twin_commands.add_parser(
        "hatch",
        help="materialize a prepared local Twin and register its agents",
    )
    twin_hatch_parser.add_argument(
        "folder",
        metavar="FOLDER",
        help="prepared local Twin folder",
    )
    twin_hatch_parser.add_argument(
        "--yes",
        action="store_true",
        help="confirm copying and registering executable agent Python",
    )
    twin_hatch_parser.add_argument("--home", help="override ~/.rapp/twins")
    twin_hatch_parser.set_defaults(
        handler=twin_hatch,
        confirmation_before_context=HATCH_CONFIRMATION_MESSAGE,
    )
    twin_list_alias_parser = twin_commands.add_parser(
        "list",
        help="list local Twin workspaces",
    )
    twin_list_alias_parser.add_argument("--home", help="override ~/.rapp/twins")
    twin_list_alias_parser.add_argument(
        "--all",
        action="store_true",
        help="include archived and purged twins",
    )
    twin_list_alias_parser.set_defaults(handler=twin_list)
    twin_show_alias_parser = twin_commands.add_parser(
        "show",
        help="show one local Twin workspace",
    )
    twin_show_alias_parser.add_argument("twin", help="directory id or rappid")
    twin_show_alias_parser.add_argument("--home", help="override ~/.rapp/twins")
    twin_show_alias_parser.add_argument(
        "--all",
        action="store_true",
        help="include archived and purged twins",
    )
    twin_show_alias_parser.set_defaults(handler=twin_show)
    twin_list_parser = twin_commands.add_parser(
        "legacy-list",
        help="inspect historical ~/.rapp/twins workspaces without claiming canonical status",
    )
    twin_list_parser.add_argument("--home", help="override ~/.rapp/twins")
    twin_list_parser.add_argument(
        "--all",
        action="store_true",
        help="include archived and purged twins",
    )
    twin_list_parser.set_defaults(handler=twin_list)
    twin_show_parser = twin_commands.add_parser(
        "legacy-show",
        help="show one historical ~/.rapp/twins workspace",
    )
    twin_show_parser.add_argument("twin", help="directory id or rappid")
    twin_show_parser.add_argument("--home", help="override ~/.rapp/twins")
    twin_show_parser.add_argument(
        "--all",
        action="store_true",
        help="include archived and purged twins",
    )
    twin_show_parser.set_defaults(handler=twin_show)
    twin_drive_parser = twin_commands.add_parser(
        "drive", help="not available until a canonical Twin runtime contract is published"
    )
    twin_drive_parser.add_argument("twin", nargs="?")
    twin_drive_parser.set_defaults(handler=unavailable_capability, capability="twin.drive")

    return parser


def _command_name(args: argparse.Namespace) -> str:
    parts = [args.command]
    for attribute in (
        "brainstem_command",
        "config_command",
        "model_command",
        "agent_command",
        "auth_command",
        "ring_command",
        "twin_command",
    ):
        value = getattr(args, attribute, None)
        if value:
            parts.append(value)
    return ".".join(parts)


def _broken_pipe() -> int:
    with contextlib.suppress(OSError):
        sys.stdout.close()
    return 141


def _emit_error(output: Output, error: RappError) -> int:
    try:
        output.error(error)
    except BrokenPipeError:
        return _broken_pipe()
    return error.exit_code


def main(argv: Sequence[str] | None = None) -> int:
    parser = _parser()
    arguments = list(argv) if argv is not None else sys.argv[1:]
    if not arguments:
        parser.print_help()
        return 0
    if "--version" in arguments:
        allowed = {"--version", "--json", "--quiet"}
        unexpected = [argument for argument in arguments if argument not in allowed]
        output = Output(
            json_mode="--json" in arguments,
            command="version",
        )
        if "--jsonl" in arguments or unexpected:
            return _emit_error(
                output,
                UsageError("--version may only be combined with --json or --quiet"),
            )
        output.success({"version": __version__}, message=f"rapp {__version__}")
        return 0
    json_mode = "--json" in arguments or "--jsonl" in arguments
    jsonl_mode = "--jsonl" in arguments
    try:
        args = parser.parse_args(arguments)
    except UsageError as exc:
        output = Output(
            json_mode=json_mode,
            jsonl_mode=jsonl_mode,
        )
        return _emit_error(output, exc)
    output = Output(
        json_mode=args.json or args.jsonl,
        jsonl_mode=args.jsonl,
        quiet=args.quiet,
        command=_command_name(args),
    )
    try:
        is_stream = bool(getattr(args, "stream", False))
        if args.json and is_stream:
            raise UsageError("streaming JSON requires --jsonl instead of --json")
        if args.jsonl and not is_stream:
            raise UsageError("--jsonl is only valid for a streaming command")
        confirmation = getattr(args, "confirmation_before_context", None)
        if isinstance(confirmation, str) and not getattr(args, "yes", False):
            raise ConfirmationRequired(confirmation)
        config = Config.load(
            config_path=args.config,
            brainstem_url=args.url,
            timeout=args.timeout,
            secret_file=args.secret_file,
            allow_insecure_http=args.allow_insecure_http,
        )
        context = Context(
            config=config,
            client=BrainstemClient(config),
            output=output,
        )
        return invoke(args.handler, context, args)
    except RappError as exc:
        return _emit_error(output, exc)
    except KeyboardInterrupt:
        error = RappError("interrupted", code="INTERRUPTED", exit_code=130)
        return _emit_error(output, error)
    except BrokenPipeError:
        return _broken_pipe()
    except Exception:
        if args.verbose:
            raise
        error = InternalFailure()
        return _emit_error(output, error)
