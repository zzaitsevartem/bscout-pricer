import sys
from pathlib import Path

import pydantic_settings.sources

pydantic_settings.sources.DotEnvSettingsSource._read_env_files = lambda self: {}
sys.path.insert(0, str(Path.cwd()))
import pytest


class NoSkippedTests:
    skipped = 0

    def pytest_runtest_logreport(self, report):
        if report.skipped:
            self.skipped += 1


plugin = NoSkippedTests()
result = pytest.main(sys.argv[1:], plugins=[plugin])
if result == 0 and plugin.skipped == 0:
    print("BACKEND_VERIFIED_NO_SKIPS")
    raise SystemExit(0)
raise SystemExit(result or 1)
