import datetime
import sys
import traceback as _traceback

from modules.console import console
from modules.context import context
from modules.exceptions import PrettyException


def write_crash_log(exc_type, exc_instance, tb) -> "str | None":
    """Write an unhandled exception to `crash-<timestamp>.log` beside the bot.

    ‼ WHY THIS EXISTS. The bot's traceback used to live only on the console, and
    `install_sandbox.py` launches it as a SUBPROCESS OF THE INSTALLER — so on a crash the
    error flashes and the window closes with it (user, 2026-07-26: "it gives me an error
    but quickly closes"). A crash that cannot be read cannot be fixed, and asking someone
    to photograph a window that closes in under a second is not a diagnostic strategy.
    Fully guarded: a failure to write the crash log must never replace the crash itself.
    """
    try:
        from modules.runtime import get_base_path

        path = get_base_path() / f"crash-{datetime.datetime.now():%Y%m%d-%H%M%S}.log"
        text = "".join(_traceback.format_exception(exc_type, exc_instance, tb))
        try:
            profile = getattr(context, "profile", None)
            header = f"profile: {getattr(profile, 'path', None)}\nbot mode: {getattr(context, 'bot_mode', None)}\n\n"
        except Exception:
            header = ""
        path.write_text(header + text, encoding="utf-8")
        return str(path)
    except Exception:
        return None


def exception_hook(exc_type: type[Exception], exc_instance: Exception, traceback) -> None:
    """General handler for exceptions to remove tracebacks and highlight messages if debug is off.

    :param exc_type: Base Exception type, kept for parity with the overridden hook.
    :param exc_instance: Instanced exception object being raised.
    :param traceback: Traceback object, kept for parity with the overridden hook.
    """
    if not isinstance(exc_instance, PrettyException):
        crash_log = write_crash_log(exc_type, exc_instance, traceback)
        if crash_log:
            console.print(f"[bold red]Crash written to:[/] {crash_log}")
        raise exc_instance
    if context.debug:
        raise exc_instance.bare_message()
    message = exc_instance.message_template.format(*exc_instance.args)
    message = f"{exc_instance.message_color}{message}[/]"
    if exc_instance.recommendation:
        recommendation = f"{exc_instance.recommendation_color}{exc_instance.recommendation}[/]"
        message = f"{message}\n{recommendation}"
    console.print(message)
    exit_code = exc_instance.exit_code
    if exit_code is not None:
        sys.exit(exit_code)


def register_exception_hook():
    sys.excepthook = exception_hook
