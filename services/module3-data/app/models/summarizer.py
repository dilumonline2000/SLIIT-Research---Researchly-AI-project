"""Model wrapper for Research Summarizer (BART+LoRA) — inference time."""

from __future__ import annotations

import logging
from pathlib import Path

import torch
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM

logger = logging.getLogger(__name__)

DEFAULT_MODEL_DIR = Path(__file__).parent.parent.parent / "models" / "summarizer"


class SummarizerModel:
    """Wrapper for the trained BART summarization model."""

    def __init__(self, model_dir: str | Path | None = None):
        self.model_dir = Path(model_dir) if model_dir else DEFAULT_MODEL_DIR
        self._model = None
        self._tokenizer = None
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    def load(self) -> None:
        base_model = "facebook/bart-large-cnn"
        try:
            from peft import PeftModel, PeftConfig
            config = PeftConfig.from_pretrained(str(self.model_dir))
            base = AutoModelForSeq2SeqLM.from_pretrained(config.base_model_name_or_path)
            self._model = PeftModel.from_pretrained(base, str(self.model_dir))
            self._tokenizer = AutoTokenizer.from_pretrained(str(self.model_dir))
            logger.info("Loaded LoRA summarizer from %s", self.model_dir)
        except Exception:
            weights_path = self.model_dir / "model.pt"
            if weights_path.exists():
                self._model = AutoModelForSeq2SeqLM.from_pretrained(base_model)
                self._model.load_state_dict(torch.load(weights_path, map_location=self.device, weights_only=True))
                self._tokenizer = AutoTokenizer.from_pretrained(str(self.model_dir) if (self.model_dir / "tokenizer_config.json").exists() else base_model)
                logger.info("Loaded full summarizer from %s", self.model_dir)
            else:
                self._model = AutoModelForSeq2SeqLM.from_pretrained(base_model)
                self._tokenizer = AutoTokenizer.from_pretrained(base_model)
                logger.warning("Using base BART model (no fine-tuned weights found)")

        self._model = self._model.to(self.device).eval()

    @property
    def model(self):
        if self._model is None:
            self.load()
        return self._model

    @property
    def tokenizer(self):
        if self._tokenizer is None:
            self.load()
        return self._tokenizer

    def summarize(self, text: str, max_length: int = 256, min_length: int = 50, num_beams: int = 4) -> str:
        """Summarize a research paper text."""
        inputs = self.tokenizer(text, max_length=1024, truncation=True, return_tensors="pt")
        inputs = {k: v.to(self.device) for k, v in inputs.items()}

        with torch.no_grad():
            output_ids = self.model.generate(
                **inputs,
                max_length=max_length,
                min_length=min_length,
                num_beams=num_beams,
                early_stopping=True,
                no_repeat_ngram_size=3,
            )
        return self.tokenizer.decode(output_ids[0], skip_special_tokens=True)
