"""Model wrapper for Proposal Generator (RAG + LoRA LLM) — inference time."""

from __future__ import annotations

import json
import logging
from pathlib import Path

import torch
from transformers import AutoTokenizer, AutoModelForCausalLM

logger = logging.getLogger(__name__)

DEFAULT_MODEL_DIR = Path(__file__).parent.parent.parent / "models" / "proposal_lora"

PROMPT_TEMPLATE = """### Instruction
Based on the following research context, generate a structured research proposal.

### Context
{context}

### Research Gap
{gap}

### Proposal
"""


class ProposalGeneratorModel:
    """Wrapper for the trained proposal generator LLM."""

    def __init__(self, model_dir: str | Path | None = None):
        self.model_dir = Path(model_dir) if model_dir else DEFAULT_MODEL_DIR
        self._model = None
        self._tokenizer = None
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    def load(self) -> None:
        """Load the trained model and tokenizer."""
        try:
            from peft import PeftModel, PeftConfig
            config = PeftConfig.from_pretrained(str(self.model_dir))
            base_model = AutoModelForCausalLM.from_pretrained(config.base_model_name_or_path)
            self._model = PeftModel.from_pretrained(base_model, str(self.model_dir))
            self._tokenizer = AutoTokenizer.from_pretrained(str(self.model_dir))
            logger.info("Loaded LoRA proposal model from %s", self.model_dir)
        except Exception as e:
            logger.warning("Could not load LoRA model: %s. Using base GPT-2 for testing.", e)
            self._model = AutoModelForCausalLM.from_pretrained("gpt2")
            self._tokenizer = AutoTokenizer.from_pretrained("gpt2")

        if self._tokenizer.pad_token is None:
            self._tokenizer.pad_token = self._tokenizer.eos_token
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

    def generate_proposal(
        self,
        context: str,
        gap: str,
        max_new_tokens: int = 512,
        temperature: float = 0.7,
    ) -> dict:
        """Generate a structured research proposal."""
        prompt = PROMPT_TEMPLATE.format(context=context, gap=gap)
        inputs = self.tokenizer(prompt, return_tensors="pt", truncation=True, max_length=1536)
        inputs = {k: v.to(self.device) for k, v in inputs.items()}

        with torch.no_grad():
            output_ids = self.model.generate(
                **inputs,
                max_new_tokens=max_new_tokens,
                temperature=temperature,
                do_sample=True,
                top_p=0.9,
                pad_token_id=self.tokenizer.pad_token_id,
            )

        generated = self.tokenizer.decode(output_ids[0][inputs["input_ids"].shape[1]:], skip_special_tokens=True)

        # Try to parse as JSON
        try:
            proposal = json.loads(generated)
        except json.JSONDecodeError:
            proposal = {
                "problem_statement": generated.strip(),
                "objectives": [],
                "methodology": "",
                "expected_outcomes": "",
            }
        return proposal
