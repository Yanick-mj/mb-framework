"""Playwright smoke test — golden path: create -> edit -> delete a story.

Requires: pip install pytest-playwright && playwright install chromium
"""
import os
import site
import socket
import subprocess
import sys
import time
from pathlib import Path

import pytest
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

REPO_ROOT = str(Path(__file__).resolve().parents[3])


def _playwright_available() -> bool:
    try:
        from playwright.sync_api import sync_playwright
        return True
    except ImportError:
        return False


@pytest.fixture(scope="module")
def dashboard_server(tmp_path_factory):
    """Start the dashboard server for e2e testing."""
    tmp = tmp_path_factory.mktemp("e2e")

    project = tmp / "e2e-project"
    project.mkdir()
    (project / "mb-stage.yaml").write_text("stage: mvp\nsince: 2026-05-05\n")
    (project / "memory").mkdir()
    (project / "_mb-output" / "implementation-artifacts" / "stories").mkdir(parents=True)

    home = tmp / "home"
    home.mkdir()
    mb_dir = home / ".mb"
    mb_dir.mkdir()
    (mb_dir / "projects.yaml").write_text(yaml.safe_dump({
        "version": 1,
        "projects": [{"name": "e2e", "path": str(project), "stage": "mvp"}],
    }))

    port = 5199
    # Preserve user site-packages since we override HOME
    user_sites = site.getusersitepackages()
    pythonpath = os.pathsep.join(filter(None, [REPO_ROOT, user_sites]))
    env = {**os.environ, "HOME": str(home), "PYTHONPATH": pythonpath}

    proc = subprocess.Popen(
        [sys.executable, "-c",
         f"import uvicorn; uvicorn.run('scripts.dashboard.server:app', host='127.0.0.1', port={port})"],
        env=env, cwd=REPO_ROOT, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    )

    for _ in range(30):
        time.sleep(0.3)
        try:
            with socket.create_connection(("127.0.0.1", port), timeout=0.5):
                break
        except (ConnectionRefusedError, OSError):
            continue
    else:
        proc.terminate()
        raise RuntimeError(f"Server failed to start: {proc.stderr.read().decode()}")

    yield {"url": f"http://localhost:{port}", "project_path": project}

    proc.terminate()
    proc.wait(timeout=5)


@pytest.mark.skipif(not _playwright_available(), reason="Playwright not installed")
class TestCrudE2E:
    def test_golden_path_create_edit_delete(self, dashboard_server, page):
        """Full flow: create a story, edit it, delete it."""
        url = dashboard_server["url"]

        page.goto(f"{url}/projects/e2e/board")
        page.wait_for_load_state("networkidle")

        page.click("text=New Story")
        page.wait_for_selector(".modal-overlay")

        page.fill('input[name="title"]', "E2E Test Story")
        page.fill('textarea[name="description"]', "Created by Playwright")
        page.select_option('select[name="priority"]', "high")
        page.click('button:has-text("Create Story")')

        page.wait_for_selector(".modal-overlay", state="detached", timeout=3000)
        time.sleep(1)

        page.goto(f"{url}/projects/e2e/board")
        page.wait_for_load_state("networkidle")
        assert page.locator("text=E2E Test Story").count() > 0

        page.click("text=E2E Test Story")
        page.wait_for_selector(".modal-overlay")

        page.click('button:has-text("Edit")')
        page.wait_for_selector('input[name="title"]')

        page.fill('input[name="title"]', "E2E Edited Story")
        page.click('button:has-text("Save Changes")')

        page.wait_for_selector(".modal-overlay", state="detached", timeout=3000)
        time.sleep(1)

        page.goto(f"{url}/projects/e2e/board")
        page.wait_for_load_state("networkidle")
        assert page.locator("text=E2E Edited Story").count() > 0

        page.click("text=E2E Edited Story")
        page.wait_for_selector(".modal-overlay")

        page.on("dialog", lambda dialog: dialog.accept())
        page.click('button:has-text("Delete")')

        page.wait_for_selector(".modal-overlay", state="detached", timeout=3000)
        time.sleep(1)
        page.goto(f"{url}/projects/e2e/board")
        page.wait_for_load_state("networkidle")
        assert page.locator("text=E2E Edited Story").count() == 0
