# Genlingo — David (small local Gemma) vs. Goliath (Gemini). See README.md.
-include .env
export

UV      := uv run --project duel
TAG     ?= genlingo-$(shell date +%Y-%m)
DUEL_PORT ?= 8787
DUEL_URL  := http://127.0.0.1:$(DUEL_PORT)
# JDK 21 for the Firestore emulator (rules tests), only inside make: brew install openjdk@21
JAVA21    := $(shell brew --prefix openjdk@21 2>/dev/null)/libexec/openjdk.jdk/Contents/Home

.PHONY: help up reset test eval eval-dev niches counterparts train train-local train-finish train-data quant-sweep pull-model export review-test review-test-apply \
        test-set real-pairs ambiguous-terms pairs datasheet data deploy

help:
	@grep -hE '^[a-z-]+:.*## ' Makefile | awk -F':.*## ' '{printf "  make %-18s %s\n", $$1, $$2}'

up: ## Start Ollama + warm David + duel service + presenter view (works with Wi-Fi off)
	@scripts/up.sh

reset: ## Clear rounds, votes and scoreboard (local + this event's Firestore rounds)
	@$(UV) python scripts/reset.py

test: ## Run all tests (no network: MOCK_AI in tests). SKIP_WEB=1 / SKIP_RULES=1 skip a suite on purpose
	cd duel && MOCK_AI=1 uv run pytest -q
	@if [ -d web/node_modules ]; then cd web && npm test --silent && npx tsc --noEmit && npx eslint . ; \
	elif [ "$(SKIP_WEB)" = 1 ]; then echo "!! SKIP_WEB=1: web tests NOT run"; \
	else echo "!! web tests can't run: (cd web && npm install), or SKIP_WEB=1 to skip them on purpose" >&2; exit 1; fi
	@if [ -x "$(JAVA21)/bin/java" ] && [ -d web/node_modules ]; then \
	  cd web && JAVA_HOME="$(JAVA21)" PATH="$(JAVA21)/bin:$$PATH" npm run --silent test:rules; \
	elif [ "$(SKIP_RULES)" = 1 ] || [ "$(SKIP_WEB)" = 1 ]; then echo "!! Firestore rules tests NOT run"; \
	else echo "!! Firestore rules tests can't run: brew install openjdk@21, or SKIP_RULES=1 to skip them on purpose" >&2; exit 1; fi

eval: ## Test set through base models, David and Goliath -> evals/report.md (once per data round)
	$(UV) python evals/run_eval.py $(EVAL_ARGS)

eval-dev: ## Dev set (data decisions, ablations) -> evals/report_dev.md: make eval-dev [EVAL_ARGS="--nbest 4"]
	$(UV) python evals/run_eval.py --split dev $(EVAL_ARGS)

niches: ## Pre-registered niches (evals/niche.md) from the latest test eval -> evals/niche_report.md
	$(UV) python evals/niche_report.py

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

pairs: ## Generate synthetic training pairs with GEMINI_MODEL from validated counterparts (paid, ~1,500 + 800 multi-term)
	$(UV) python scripts/generate_pairs.py
	$(UV) python scripts/generate_multi_pairs.py

datasheet: ## Recount data/DATASHEET.md
	$(UV) python scripts/datasheet.py

data: test-set real-pairs pairs datasheet ## Rebuild all data (test set, synthetic pairs, datasheet)

review-test: ## (Optional) export the test set to a CSV for a human pass over the automatic validation
	$(UV) python scripts/review_test.py export

review-test-apply: ## Apply the decisions from data/review/test_review.csv
	$(UV) python scripts/review_test.py apply

export: ## Pull presenter-approved audience pairs from Firestore into data/pairs/human.jsonl
	$(UV) python scripts/export_human.py
	$(UV) python scripts/datasheet.py

train-data: ## Render training pairs into chat JSONL (v2+lex glossary) + preference prompts for ORPO
	$(UV) python scripts/build_train_set.py
	$(UV) python scripts/build_pref_set.py

train: train-data ## Fine-tune in the cloud (L4 job trains, CPU job merges + GGUF): make train TAG=genlingo-2027-03 [QUANT=Q5_K_M] [TRAIN_ARGS=…]
	$(UV) python train/submit_job.py --app genlingo --tag $(TAG) --data data/train/chat.jsonl \
	  $(if $(wildcard data/train/pref.jsonl),--pref data/train/pref.jsonl) -- $(TRAIN_ARGS)

train-local: train-data ## Same training on this Mac (MPS), for experiments
	uv run --python 3.12 --with-requirements train/requirements.txt --with torch==2.14.0 \
	  python train/train_local.py $(TAG) data/train/chat.jsonl

train-finish: ## Fallback: merge + GGUF a cloud-trained adapter on this Mac: make train-finish TAG=… [QUANT=…] [KEEP_F16=1]
	uv run --python 3.12 --with-requirements train/requirements.txt --with torch==2.14.0 \
	  python train/finish_local.py $(TAG)

quant-sweep: ## Q5/Q6/Q8 + imatrix-calibrated Q4/Q5 from a David's f16 GGUF, registered in Ollama
	train/setup_llama_cpp.sh >/dev/null && uv run --project duel python train/quant_sweep.py $(TAG)

pull-model: ## Download a trained David into Ollama: make pull-model TAG=... [FP16=1]
	MODELS_BUCKET=$(MODELS_BUCKET) train/pull_model.sh $(TAG)

deploy: ## Deploy the audience web app to Cloud Run (min-instances=1)
	bash infra/04-web-service-account.sh
	bash infra/05-deploy-web.sh
