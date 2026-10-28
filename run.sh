#!/bin/sh
# Builds the graph, runs all queries and draws the figure. Needs uv (https://docs.astral.sh/uv/).
set -e
cd "$(dirname "$0")"
deps="--python 3.12 --with rdflib --with networkx --with matplotlib"
uv run $deps python src/build_graph.py
uv run $deps python src/run_queries.py > /dev/null && echo "build/results.md"
uv run $deps python src/plot_graph.py
uv run $deps python src/real_kbl.py > /dev/null && echo "build/oldbeetle.ttl, build/results_oldbeetle.md"
uv run $deps python src/export_viewer.py
mkdir -p docs && cp build/viewer.html docs/index.html && echo "docs/index.html (GitHub Pages)"
