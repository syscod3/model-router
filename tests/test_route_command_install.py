from __future__ import annotations

from pathlib import Path

import install


def test_installer_adds_route_command_and_dispatch_to_hermes_sources(tmp_path):
    commands_path = tmp_path / "commands.py"
    commands_path.write_text(
        """COMMANDS = [
    CommandDef("t1", "legacy", "Configuration", cli_only=True),
    CommandDef("auto", "legacy", "Configuration", cli_only=True),
]
""",
        encoding="utf-8",
    )
    cli_path = tmp_path / "cli.py"
    cli_path.write_text(
        """class CLI:
    def setup(self):
        if not self._ensure_runtime_credentials():
            return False

    def process_command(self, canonical, cmd_original):
        if canonical == "help":
            return True
        elif canonical in ("t1", "t2", "t3", "t4", "t5"):
            self._handle_tier_pin(canonical)
        elif canonical == "auto":
            self._handle_auto_routing()
        elif canonical == "model":
            self._handle_model_switch(cmd_original)

    def _should_handle_model_command_inline(self):
        return False

    def run(self, text, has_images):
        if text or has_images:
            pass
""",
        encoding="utf-8",
    )

    assert install.repair_commands_py(commands_path)
    assert install.repair_cli_py(cli_path)

    patched_commands = commands_path.read_text(encoding="utf-8")
    assert 'CommandDef("route"' in patched_commands
    assert patched_commands.count('CommandDef("t1"') == 1
    patched_cli = cli_path.read_text(encoding="utf-8")
    assert "def _handle_route(self, cmd_original: str)" in patched_cli
    assert 'elif canonical == "route":' in patched_cli
    assert "self._handle_route(cmd_original)" in patched_cli
    assert patched_cli.count('elif canonical in ("t1", "t2", "t3", "t4", "t5"):') == 1
