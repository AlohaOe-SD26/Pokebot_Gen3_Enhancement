"""
Opens the custom web dashboard in the default browser shortly after a
profile is loaded, so nobody has to remember the URL. Only fires when the
bot's HTTP server is enabled (http.yml).

To disable: set AUTO_OPEN to False below (or delete this file).
"""

import threading
import webbrowser
from typing import TYPE_CHECKING

from modules.plugin_interface import BotPlugin

if TYPE_CHECKING:
    from modules.profiles import Profile

# Default OFF: the native dashboard GUI is now the main interface; flip this
# to True if you want the browser dashboard to open automatically as well.
AUTO_OPEN: bool = False

# The HTTP server starts just after the profile loads, so give it a moment
# to bind before pointing a browser at it.
_OPEN_DELAY_SECONDS: float = 2.5


class DashboardAutoOpenPlugin(BotPlugin):
    def on_profile_loaded(self, profile: "Profile") -> None:
        if not AUTO_OPEN:
            return

        from modules.context import context

        server = context.config.http.http_server
        if not server.enable:
            return

        url = f"http://{server.ip}:{server.port}/static/custom-ui/index.html"
        timer = threading.Timer(_OPEN_DELAY_SECONDS, webbrowser.open, args=(url,))
        timer.daemon = True
        timer.start()
