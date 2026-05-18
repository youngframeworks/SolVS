import subprocess


def test_validate_agents_runs():
    cp = subprocess.run(["python3", "scripts/validate_agents.py"])
    assert cp.returncode == 0
