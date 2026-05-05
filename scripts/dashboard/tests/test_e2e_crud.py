"""Playwright smoke test — golden path: create -> edit -> delete a story.

Requires: pip install pytest-playwright && playwright install chromium
"""
import subprocess
import sys
import time
from pathlib import Path

import pytest
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))


@pytest.fixture(scope="module")
def dashboard_server(tmp_path_factory):
    """Start the dashboard server on a random port for e2e testing."""
    import tempfile
    import os

    tmp = tmp_path_factory.mktemp("e2e")

    # Create a minimal project
    project = tmp / "e2e-project"
    project.mkdir()
    (project / "mb-stage.yaml").write_text("stage: mvp\nsince: 2026-05-05\n")
    (project / "memory").mkdir()
    (project / "_bmad-output").mkdir()
    (project / "_bmad-output" / "implementation-artifacts" / "stories").mkdir(parents=True)

    # Register the project
    home = tmp / "home"
    home.mkdir()
    mb_dir = home / ".mb"
    mb_dir.mkdir()
    (mb_dir / "projects.yaml").write_text(yaml.safe_dump({
        "version": 1,
        "projects": [{"name": "e2e", "path": str(project), "stage": "mvp"}],
    }))

    port = 5199
    repo_root = str(Path(__file__).resolve().parents[3])
    # Preserve real user site-packages since we override HOME
    real_home = os.environ.get("HOME", "")
    user_site = f"{real_home}/Library/Python/3.13/lib/python/site-packages"
    pythonpath = f"{repo_root}:{user_site}"
    env = {**os.environ, "HOME": str(home), "PYTHONPATH": pythonpath}

    # Start uvicorn directly without reload (reload doesn't work well in subprocess)
    proc = subprocess.Popen(
        [sys.executable, "-c",
         f"import uvicorn; uvicorn.run('scripts.dashboard.server:app', host='127.0.0.1', port={port})"],
        env=env,
        cwd=repo_root,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    # Wait for server to start
    import socket
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


@pytest.mark.skipif(
    not Path("/Users/yanickmingala/Library/Caches/ms-playwright").exists(),
    reason="Playwright browsers not installed",
)
class TestCrudE2E:
    def test_golden_path_create_edit_delete(self, dashboard_server, page):
        """Full flow: create a story, edit it, delete it."""
        url = dashboard_server["url"]

        # Navigate to board
        page.goto(f"{url}/projects/e2e/board")
        page.wait_for_load_state("networkidle")

        # Click "New Story" button
        page.click("text=New Story")
        page.wait_for_selector(".modal-overlay")

        # Fill the form
        page.fill('input[name="title"]', "E2E Test Story")
        page.fill('textarea[name="description"]', "Created by Playwright")
        page.select_option('select[name="priority"]', "high")
        page.click('button:has-text("Create Story")')

        # Wait for modal to close and board to refresh
        page.wait_for_selector(".modal-overlay", state="detached", timeout=3000)
        time.sleep(1)  # board refresh

        # Reload board to see the new story
        page.goto(f"{url}/projects/e2e/board")
        page.wait_for_load_state("networkidle")

        # Verify story appears on board
        assert page.locator("text=E2E Test Story").count() > 0

        # Click the story card to open modal
        page.click("text=E2E Test Story")
        page.wait_for_selector(".modal-overlay")

        # Click Edit button
        page.click('button:has-text("Edit")')
        page.wait_for_selector('input[name="title"]')

        # Change the title
        page.fill('input[name="title"]', "E2E Edited Story")
        page.click('button:has-text("Save Changes")')

        # Wait for modal close
        page.wait_for_selector(".modal-overlay", state="detached", timeout=3000)
        time.sleep(1)

        # Reload and verify edit
        page.goto(f"{url}/projects/e2e/board")
        page.wait_for_load_state("networkidle")
        assert page.locator("text=E2E Edited Story").count() > 0

        # Open story and delete it
        page.click("text=E2E Edited Story")
        page.wait_for_selector(".modal-overlay")

        # Handle confirm dialog
        page.on("dialog", lambda dialog: dialog.accept())
        page.click('button:has-text("Delete")')

        # Wait and verify gone
        page.wait_for_selector(".modal-overlay", state="detached", timeout=3000)
        time.sleep(1)
        page.goto(f"{url}/projects/e2e/board")
        page.wait_for_load_state("networkidle")
        assert page.locator("text=E2E Edited Story").count() == 0
