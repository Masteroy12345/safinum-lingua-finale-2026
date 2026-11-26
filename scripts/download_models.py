"""Télécharge et vérifie les modèles IA locaux (traduction, correction de phrases, TTS) dans models/."""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from huggingface_hub import snapshot_download

ROOT = Path(__file__).resolve().parents[1]
MODELS_DIR = ROOT / "models"

CAMEROON_INT8_PAIRS = [
    "francais-ewondo",
    "ewondo-francais",
    "francais-fufulde",
    "fufulde-francais",
    "francais-ghomala",
    "ghomala-francais",
    "francais-medumba",
    "medumba-francais",
    "francais-english",
    "english-francais",
]

IGNORE_DUPLICATES = [
    "pytorch_model.bin",
    "*.h5",
    "*.ot",
    "*.msgpack",
    "*.onnx",
    "*.onnx_data",
]

HF_MODELS: list[dict[str, Any]] = [
    {
        "name": "opus-mt-fr-bnt",
        "repo_id": "Helsinki-NLP/opus-mt-tc-bible-big-deu_eng_fra_por_spa-bnt",
        "role": "translation_bantu",
        "languages": ["dua", "bas", "ewo"],
        "license": "CC-BY-4.0",
        "ignore_patterns": IGNORE_DUPLICATES,
    },
    {
        "name": "opus-mt-fr-mul",
        "repo_id": "Helsinki-NLP/opus-mt-tc-bible-big-deu_eng_fra_por_spa-mul",
        "role": "translation_multilingual",
        "languages": ["wes", "pcm", "bas", "ful"],
        "license": "CC-BY-4.0",
        "ignore_patterns": IGNORE_DUPLICATES,
    },
    {
        "name": "opus-mt-bnt-fr",
        "repo_id": "Helsinki-NLP/opus-mt-tc-bible-big-bnt-deu_eng_fra_por_spa",
        "role": "translation_bantu_reverse",
        "languages": ["dua", "bas", "ewo", "fr", "en"],
        "license": "CC-BY-4.0",
        "ignore_patterns": IGNORE_DUPLICATES,
    },
    {
        "name": "t5-spell-fr",
        "repo_id": "fdemelo/t5-base-spell-correction-fr",
        "role": "sentence_correction_fr",
        "languages": ["fr"],
        "license": "Apache-2.0",
        "ignore_patterns": IGNORE_DUPLICATES,
    },
    {
        "name": "t5-grammar-en",
        "repo_id": "vennify/t5-base-grammar-correction",
        "role": "sentence_correction_en",
        "languages": ["en"],
        "license": "Apache-2.0",
        "ignore_patterns": ["*.h5", "*.ot", "*.msgpack"],  # only pytorch_model.bin exists
    },
    {
        "name": "mms-tts-ewo",
        "repo_id": "OlameMend/mms-tts-ewo",
        "role": "tts_audio",
        "languages": ["ewo"],
        "license": "CC-BY-NC-4.0",
        "ignore_patterns": ["*.h5", "*.ot", "*.msgpack"],
    },
    {
        "name": "mms-tts-ful",
        "repo_id": "facebook/mms-tts-ful",
        "role": "tts_audio",
        "languages": ["fub", "ful"],
        "license": "CC-BY-NC-4.0",
        "ignore_patterns": IGNORE_DUPLICATES,
    },
    {
        "name": "mms-tts-pcm",
        "repo_id": "facebook/mms-tts-pcm",
        "role": "tts_audio",
        "languages": ["wes", "pcm"],
        "license": "CC-BY-NC-4.0",
        "ignore_patterns": IGNORE_DUPLICATES,
    },
    {
        "name": "mms-tts-fra",
        "repo_id": "facebook/mms-tts-fra",
        "role": "tts_audio",
        "languages": ["fr"],
        "license": "CC-BY-NC-4.0",
        "ignore_patterns": IGNORE_DUPLICATES,
    },
    {
        "name": "ewondo-french-yemen2016",
        "repo_id": "yemen2016/ewondo-french-model",
        "role": "translation_ewondo_fr_experimental",
        "languages": ["ewo", "fr"],
        "license": "unknown",
        "ignore_patterns": ["runs/*", "*.h5"],
    },
    {
        "name": "ewondo-tts-speecht5",
        "repo_id": "exyms/ewondo-tts-speecht5",
        "role": "tts_ewondo_speecht5",
        "languages": ["ewo"],
        "license": "unknown",
        "ignore_patterns": ["runs/*", "*.h5"],
    },
]

HF_DATASETS: list[dict[str, Any]] = [
    {
        "name": "soreva",
        "repo_id": "OlameMend/soreva",
        "allow_patterns": ["README.md", "data/*_cm/*.tsv", "data/*_cm/*.csv"],
        "description": "Corpus parallèle audio/transcription 31 langues camerounaises (ewo, bbj, bas, dua, fub, wes, byv...)",
    },
    {
        "name": "french-fulfulde-adamaoua",
        "repo_id": "FredMike23/french-FULFULDE-ADAMAOUA",
        "allow_patterns": None,
        "description": "Lexique bilingue Français <-> Fulfulde Adamaoua (42 768 entrées)",
    },
    {
        "name": "fulfulde-agri",
        "repo_id": "BATBAINA/fulfulde-dataset-asr-agri",
        "allow_patterns": ["README.md", "*.csv"],
        "description": "Métadonnées ASR Fulfulde avec gloses françaises",
    },
    {
        "name": "cameroon-pidgin-pairs",
        "repo_id": "michsethowusu/english-cameroon-pidgin_sentence-pairs_mt560",
        "allow_patterns": None,
        "description": "Corpus parallèle Anglais <-> Cameroonian Pidgin (28 159 paires)",
    },
]


def convert_to_ct2_int8(src_dir: Path, dst_dir: Path) -> bool:
    """Convertit un modèle Marian/T5 HuggingFace en CTranslate2 int8 pour inférence CPU rapide."""
    if (dst_dir / "model.bin").exists():
        return True
    try:
        import ctranslate2

        converter = ctranslate2.converters.TransformersConverter(str(src_dir))
        converter.convert(str(dst_dir), quantization="int8", force=True)
        # Copier les fichiers tokenizer dans le dossier converti pour chargement autonome
        for fname in ("source.spm", "target.spm", "vocab.json", "tokenizer_config.json", "special_tokens_map.json", "tokenizer.json", "spiece.model"):
            f = src_dir / fname
            if f.exists():
                (dst_dir / fname).write_bytes(f.read_bytes())
        return True
    except Exception as exc:
        print(f"  [warn] Conversion CT2 ignoree pour {src_dir.name}: {exc}")
        return False


def main() -> None:
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    os.environ.setdefault("HF_HUB_DISABLE_TELEMETRY", "1")
    manifest: dict[str, Any] = {"models": {}}

    # 1. Telecharger cameroon-int8 (10 directions FR <-> ewo/fub/bbj/byv/en)
    ct2_root = MODELS_DIR / "cameroon-int8"
    print(f"[1/2] Telechargement flagship-ai/cameroon-int8 ({len(CAMEROON_INT8_PAIRS)} paires)...")
    patterns = [f"{pair}/*" for pair in CAMEROON_INT8_PAIRS]
    snapshot_download(
        repo_id="flagship-ai/cameroon-int8",
        local_dir=str(ct2_root),
        allow_patterns=patterns + ["README.md"],
    )
    manifest["models"]["cameroon-int8"] = {
        "repo_id": "flagship-ai/cameroon-int8",
        "role": "translation_cameroon_ct2_int8",
        "pairs": CAMEROON_INT8_PAIRS,
        "local_dir": str(ct2_root.relative_to(ROOT)),
        "license": "CC-BY-NC-4.0",
    }

    # 2. Telecharger les modeles HuggingFace (OPUS-MT Bantu/Mul, T5 correction, MMS-TTS)
    total = len(HF_MODELS)
    for idx, spec in enumerate(HF_MODELS, start=1):
        name = spec["name"]
        dst = MODELS_DIR / name
        print(f"[2/2] ({idx}/{total}) Telechargement {spec['repo_id']} -> {dst.name}...")
        snapshot_download(
            repo_id=spec["repo_id"],
            local_dir=str(dst),
            ignore_patterns=spec.get("ignore_patterns"),
        )
        entry = {
            "repo_id": spec["repo_id"],
            "role": spec["role"],
            "languages": spec["languages"],
            "local_dir": str(dst.relative_to(ROOT)),
            "license": spec["license"],
        }
        if name.startswith("opus-mt-"):
            ct2_dst = MODELS_DIR / f"{name}-ct2-int8"
            if convert_to_ct2_int8(dst, ct2_dst):
                entry["ct2_int8_dir"] = str(ct2_dst.relative_to(ROOT))
        manifest["models"][name] = entry

    # 3. Telecharger les datasets de reference (Soreva, Fulfulde, Pidgin) dans datasets/
    datasets_dir = ROOT / "datasets"
    datasets_dir.mkdir(parents=True, exist_ok=True)
    manifest["datasets"] = {}
    for dspec in HF_DATASETS:
        d_dst = datasets_dir / dspec["name"]
        print(f"[3/3] Telechargement dataset {dspec['repo_id']} -> datasets/{dspec['name']}...")
        kwargs: dict[str, Any] = {"repo_id": dspec["repo_id"], "repo_type": "dataset", "local_dir": str(d_dst)}
        if dspec.get("allow_patterns"):
            kwargs["allow_patterns"] = dspec["allow_patterns"]
        snapshot_download(**kwargs)
        manifest["datasets"][dspec["name"]] = {
            "repo_id": dspec["repo_id"],
            "description": dspec["description"],
            "local_dir": str(d_dst.relative_to(ROOT)),
        }

    manifest_path = MODELS_DIR / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Manifest genere : {manifest_path}")


if __name__ == "__main__":
    main()
