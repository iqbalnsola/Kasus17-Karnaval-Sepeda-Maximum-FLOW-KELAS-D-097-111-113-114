from pathlib import Path

DIRS = [
    "config", "core", "cases/scenarios", "algorithms/maxflow",
    "data/rute_maps", "tests", "scripts", "output", "docs",
]
FILES = [
    "README.md", "TUTORIAL.md", "GLOSSARY.md", "requirements.txt", ".gitignore",
    "config/settings.py",
    "core/base_algorithm.py", "core/graph_model.py", "core/simulation_runner.py",
    "core/simulation_observers.py", "core/visualizer.py",
    "cases/scenario_loader.py", "cases/scenarios/case_17_karnaval_sepeda.yaml",
    "algorithms/registry.py",
    "algorithms/maxflow/ford_fulkerson.py", "algorithms/maxflow/dinic.py",
    "algorithms/maxflow/push_relabel.py",
    "tests/test_scenario_loader.py", "tests/test_scaffolding.py",
    "tests/test_all_scenarios.py", "tests/test_maxflow.py",
    "scripts/cli_utils.py", "scripts/run_simulation.py",
    "scripts/run_benchmark.py", "scripts/ekstrak_rute.py",
    "output/.gitkeep", "docs/.gitkeep", "data/rute_maps/.gitkeep",
]
# __init__.py hanya di folder kode Python
PACKAGES = ["config", "core", "cases", "algorithms", "algorithms/maxflow", "tests", "scripts"]

for d in DIRS:
    Path(d).mkdir(parents=True, exist_ok=True)
for f in FILES + [f"{p}/__init__.py" for p in PACKAGES]:
    Path(f).touch(exist_ok=True)
print("Kerangka selesai dibuat.")