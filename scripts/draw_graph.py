import sys, pathlib
ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from claim_pilot.graph import build_graph

mermaid = build_graph().get_graph().draw_mermaid()
out = ROOT / "docs" / "graph.md"
out.parent.mkdir(exist_ok=True)
out.write_text(f"```mermaid\n{mermaid}\n```\n", encoding="utf-8")
print(f"Wrote {out}")