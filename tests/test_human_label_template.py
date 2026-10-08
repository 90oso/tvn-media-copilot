import importlib.util
from pathlib import Path

import pandas as pd


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "create_human_labels_template.py"
spec = importlib.util.spec_from_file_location("human_labels", SCRIPT)
module = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(module)


def test_disagreement_sample_respects_limit():
    df = pd.DataFrame(
        [
            {"id_noticia": f"N{i}", "titulo": f"Título {i}",
             "cluster_baseline": f"B{i//2}", "cluster_semantic": f"S{i//3}"}
            for i in range(30)
        ]
    )
    sample = module._balanced_sample(df, limit=12, seed=1)
    assert len(sample) == 12
    assert sample["id_noticia"].nunique() == 12


def test_zero_limit_means_all_is_handled_by_main_contract():
    df = pd.DataFrame(
        [{"id_noticia": "N1", "titulo": "A", "cluster_semantic": "S1"}]
    )
    assert len(df) == 1
