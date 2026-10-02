# Genlingo — David (small local Gemma) vs. Goliath (Gemini). See README.md.
-include .env
export

UV      := uv run --project duel
TAG     ?= genlingo-$(shell date +%Y-%m)
DUEL_PORT ?= 8787
DUEL_URL  := http://127.0.0.1:$(DUEL_PORT)
# JDK 21 for the Firestore emulator (rules tests), only inside make: brew install openjdk@21
JAVA21    := $(shell brew --prefix openjdk@21 2>/dev/null)/libexec/openjdk.jdk/Contents/Home

.PHONY: help up reset test eval train train-local train-finish train-data quant-sweep pull-model export review-test review-test-apply \
        test-set real-pairs ambiguous-terms pairs datasheet data deploy

help:
	@grep -hE '^[a-z-]+:.*## ' Makefile | awk -F':.*## ' '{printf "  make %-18s %s\n", $$1, $$2}'

up: ## Start Ollama + warm David + duel service + presenter view (works with Wi-Fi off)
	@scripts/up.sh

reset: ## Clear rounds, votes and scoreboard (local + this event's Firestore rounds)
	@$(UV) python scripts/reset.py

test: ## Run all tests (no network: MOCK_AI in tests)
	cd duel && MOCK_AI=1 uv run pytest -q
	@if [ -d web/node_modules ]; then cd web && npm test --silent && npx tsc --noEmit && npx eslint . ; else echo "(web: npm install first to run its tests)"; fi
	@if [ -x "$(JAVA21)/bin/java" ] && [ -d web/node_modules ]; then \
	  cd web && JAVA_HOME="$(JAVA21)" PATH="$(JAVA21)/bin:$$PATH" npm run --silent test:rules; \
	else echo "(rules: brew install openjdk@21 to run the Firestore rules tests)"; fi

eval: ## Test set through base models, David and Goliath -> evals/report.md
	$(UV) python evals/run_eval.py $(EVAL_ARGS)

test-set: ## Build test pairs from real web usage examples and validate them against the term bank
	$(UV) python scripts/build_test_set.py
	$(UV) python scripts/validate_test_set.py

STT_CORPUS := data/.cache/stt_all.json
ambiguous-terms: ## Flag term-bank entries that are also ordinary words (general-speech corpus, CC BY 4.0)
	@[ -f $(STT_CORPUS) ] || curl -sL https://huggingface.co/datasets/shraavb/spanish-slang-stt-data/resolve/main/splits/all.json -o $(STT_CORPUS)
	$(UV) python scripts/flag_ambiguous_terms.py $(STT_CORPUS)

real-pairs: ## Training pairs anchored in real web sentences (both directions), validated against the term bank
	$(UV) python scripts/build_real_pairs.py

pairs: ## Generate synthetic training pairs with GEMINI_MODEL (paid, ~1,500 pairs)
	$(UV) python scripts/generate_pairs.py

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

train-data: ## Render approved training pairs into chat JSONL
	$(UV) python scripts/build_train_set.py

train: train-data ## Fine-tune on a Cloud Run GPU job (L4): make train TAG=genlingo-2027-03 [GEMMA_BASE_MODEL=…] [TRAIN_ARGS=…]
	$(UV) python train/submit_job.py --app genlingo --tag $(TAG) --data data/train/chat.jsonl -- $(TRAIN_ARGS)

train-local: train-data ## Same training on this Mac (MPS), for experiments
	uv run --python 3.12 --with-requirements train/requirements.txt --with torch==2.14.0 \
	  python train/train_local.py $(TAG) data/train/chat.jsonl

train-finish: ## Merge + GGUF a cloud-trained adapter on this Mac and publish it: make train-finish TAG=…
	uv run --python 3.12 --with-requirements train/requirements.txt --with torch==2.14.0 \
	  python train/finish_local.py $(TAG)

quant-sweep: ## Q5/Q6/Q8 + imatrix-calibrated Q4/Q5 from a David's f16 GGUF, registered in Ollama
	train/setup_llama_cpp.sh >/dev/null && uv run --project duel python train/quant_sweep.py $(TAG)

pull-model: ## Download a trained David into Ollama: make pull-model TAG=... [FP16=1]
	MODELS_BUCKET=$(MODELS_BUCKET) train/pull_model.sh $(TAG)

deploy: ## Deploy the audience web app to Cloud Run (min-instances=1)
	bash infra/04-web-service-account.sh
	bash infra/05-deploy-web.sh
