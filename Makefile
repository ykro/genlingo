# Genlingo — David (fine-tuned Gemma on a Cloud Run GPU) vs. Goliath (Gemini). See README.md.
-include .env
export

UV      := uv run --project duel
TAG     ?= genlingo-$(shell date +%Y-%m)

.PHONY: help deploy check screenshots capacity projections test eval eval-dev niches counterparts train train-data \
        test-set real-pairs ambiguous-terms pairs datasheet data

help:
	@grep -hE '^[a-z-]+:.*## ' Makefile | awk -F':.*## ' '{printf "  make %-16s %s\n", $$1, $$2}'

deploy: ## Deploy David (Cloud Run GPU, europe-west4) and the comparison page (public Cloud Run URL)
	bash infra/04-david.sh
	bash infra/05-page.sh

check: ## Check the live page end to end: wakes David, translates every example on both sides
	$(UV) python scripts/check_page.py

screenshots: ## Screenshots of the live page for docs/demo/ (real browser, light theme)
	uv run --project duel --with playwright python scripts/screenshots.py

projections: ## Rewrite the README's "time and cost in the cloud" section (es + en) from docs/data/capacity.json
	python3 scripts/projections.py

capacity: ## Measure David's throughput (1/4/8/16 at a time) and both sides' time and cost per translation -> docs/data/capacity.json (README projections; open the page first so David is awake)
	cd duel && uv run python ../scripts/bench_capacity.py

test: ## Run all tests (no network: MOCK_AI in tests)
	cd duel && MOCK_AI=1 uv run pytest -q

# A Cloud Run GPU job runs at most 1 h and loading each model from the bucket takes minutes, so `make eval` runs
# these groups as separate jobs, one after another (one L4 of quota), and merges them.
EVAL_GROUPS ?= genlingo-2026-10d-e2b,genlingo-2026-10d-e2b-f16,genlingo-2026-10c-e2b-nomulti,genlingo-2026-10c-e2b-nomulti-f16 \
               genlingo-2026-10b-e2b,genlingo-2026-10b-e2b-f16,genlingo-2026-10-e2b-q5_k_m \
               genlingo-2026-10-e2b,genlingo-2026-10-e2b-f16,genlingo-2026-09,genlingo-2026-09-f16 \
               base,goliath,goliath_glossary
eval: ## Test set through base models, every David and Goliath -> evals/report.md (once per data round): one Cloud Run GPU job per group in EVAL_GROUPS, merged
	@\
	for g in $(EVAL_GROUPS); do bash infra/06-eval-job.sh --models $$g || exit 1; done; \
	$(UV) python evals/merge_results.py $$(ls -t evals/results/2*.json | grep -v merged | head -$(words $(EVAL_GROUPS)))

eval-dev: ## Dev set (data decisions, ablations), same job -> evals/report_dev.md: make eval-dev [EVAL_ARGS="--nbest 4"]
	bash infra/06-eval-job.sh --split dev $(EVAL_ARGS)

eval-probe: ## Held-out pan-Hispanic Gen Z probe (real web sentences, LATAM and GT) -> evals/report_probe.md: make eval-probe [EVAL_ARGS="--models <tag>"]
	bash infra/06-eval-job.sh --split probe $(EVAL_ARGS)
	$(UV) python evals/probe_report.py $$(ls -t evals/results/probe-*.json | head -1)

niches: ## Pre-registered niches (evals/niche.md) from the latest test eval -> evals/niche_report.md
	$(UV) python evals/niche_report.py

data-pull: ## Download the quoted text of sources that can't be redistributed (private bucket -> data/.private/); needs project access
	$(UV) python scripts/private_data.py pull

data-push: ## Upload data/.private/ to the private bucket (after a data round)
	$(UV) python scripts/private_data.py push

test-set: ## Build test pairs from real web usage examples and validate them against the term bank
	$(UV) python scripts/build_test_set.py
	$(UV) python scripts/validate_test_set.py

STT_CORPUS := data/.cache/stt_all.json
ambiguous-terms: ## Flag term-bank entries that are also ordinary words (general-speech corpus, CC BY 4.0)
	@[ -f $(STT_CORPUS) ] || curl -sL https://huggingface.co/datasets/shraavb/spanish-slang-stt-data/resolve/main/splits/all.json -o $(STT_CORPUS)
	$(UV) python scripts/flag_ambiguous_terms.py $(STT_CORPUS)

real-pairs: ## Training pairs anchored in real web sentences (both directions), validated against the term bank; 20 % to dev
	$(UV) python scripts/build_real_pairs.py

counterparts: ## Term -> counterpart table validated by meaning (mutual nearest + Gemini top-5 check) -> data/counterparts.jsonl
	$(UV) python scripts/build_counterparts.py

pairs: ## Generate synthetic training pairs with GEMINI_MODEL from validated counterparts (paid, ~1,500)
	$(UV) python scripts/generate_pairs.py

datasheet: ## Recount data/DATASHEET.md
	$(UV) python scripts/datasheet.py

data: test-set real-pairs pairs datasheet ## Rebuild all data (test set, real-anchored pairs, synthetic pairs, datasheet)

# Stage recipe (genlingo-2026-10c-e2b-nomulti): no multi-term pairs, no ORPO stage. Both were tried
# and left out (no gain on the dev set); MULTI=1 / ORPO=1 bring them back for an ablation.
TRAIN_EXCLUDE := $(if $(filter 1,$(MULTI)),,--exclude synthetic_multi)

train-data: ## Render training pairs into chat JSONL with the lexicon glossary (stage recipe) [MULTI=1] [ORPO=1]
	$(UV) python scripts/build_train_set.py $(TRAIN_EXCLUDE)
	$(if $(filter 1,$(ORPO)),$(UV) python scripts/build_pref_set.py)

train: train-data ## Fine-tune in the cloud (L4 job trains, CPU job merges + GGUF): make train [TAG=genlingo-YYYY-MM, default today] [QUANT=Q5_K_M] [TRAIN_ARGS=…]
	$(UV) python train/submit_job.py --app genlingo --tag $(TAG) --data data/train/chat.jsonl \
	  $(if $(filter 1,$(ORPO)),--pref data/train/pref.jsonl) -- $(TRAIN_ARGS)
