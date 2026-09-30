# Genlingo — David (small local Gemma) vs. Goliath (Gemini). See README.md.
-include .env
export

UV      := uv run --project duel
TAG     ?= genlingo-$(shell date +%Y-%m)
DUEL_PORT ?= 8787
DUEL_URL  := http://127.0.0.1:$(DUEL_PORT)

.PHONY: help up duel reset test eval train train-local train-data pull-model export review-test review-test-apply \
        test-set pairs datasheet data deploy

help:
	@grep -hE '^[a-z-]+:.*## ' Makefile | awk -F':.*## ' '{printf "  make %-18s %s\n", $$1, $$2}'

up: ## Start Ollama + warm David + duel service (works with Wi-Fi off)
	@curl -sf http://127.0.0.1:11434/api/version >/dev/null || (ollama serve >/tmp/genlingo-ollama.log 2>&1 &) ; \
	  for i in $$(seq 1 20); do curl -sf http://127.0.0.1:11434/api/version >/dev/null && break; sleep 0.5; done
	@[ "$(MOCK_AI)" = 1 ] || curl -sf http://127.0.0.1:11434/api/chat -d '{"model":"$(LOCAL_MODEL_TAG)","messages":[],"keep_alive":"30m"}' >/dev/null \
	  || echo "!! David ($(LOCAL_MODEL_TAG)) no está en Ollama: make pull-model TAG=$(LOCAL_MODEL_TAG)"
	@echo "Duel service on $(DUEL_URL) (presenter view: Phase 2)"
	cd duel && uv run uvicorn genlingo_duel.main:create_app --factory --host 127.0.0.1 --port $(DUEL_PORT)

reset: ## Clear rounds, votes and scoreboard (local + this event's Firestore rounds)
	@$(UV) python scripts/reset.py

test: ## Run all tests (no network: MOCK_AI in tests)
	cd duel && MOCK_AI=1 uv run pytest -q
	@if [ -d web/node_modules ]; then cd web && npm test --silent; else echo "(web: npm install first to run its tests)"; fi

eval: ## Test set through base models, David and Goliath -> evals/report.md
	$(UV) python evals/run_eval.py $(EVAL_ARGS)

test-set: ## Build test pairs (pending_review) from real web usage examples
	$(UV) python scripts/build_test_set.py

pairs: ## Generate synthetic training pairs with GEMINI_MODEL (paid, ~1,000 pairs)
	$(UV) python scripts/generate_pairs.py

datasheet: ## Recount data/DATASHEET.md
	$(UV) python scripts/datasheet.py

data: test-set pairs datasheet ## Rebuild all data (test set, synthetic pairs, datasheet)

review-test: ## Export the test set to data/review/test_review.csv for the presenter
	$(UV) python scripts/review_test.py export

review-test-apply: ## Apply the decisions from data/review/test_review.csv
	$(UV) python scripts/review_test.py apply

export: ## Pull presenter-approved audience pairs from Firestore into data/pairs/human.jsonl
	$(UV) python scripts/export_human.py
	$(UV) python scripts/datasheet.py

train-data: ## Render approved training pairs into chat JSONL
	$(UV) python scripts/build_train_set.py

train: train-data ## Fine-tune on Vertex AI (L4, europe-west4) and record cost: make train TAG=genlingo-2027-03
	$(UV) python train/submit_job.py --app genlingo --tag $(TAG) --data data/train/chat.jsonl

train-local: train-data ## Same training on this Mac (MPS) when the cloud GPU is unavailable
	uv run --python 3.12 --with-requirements train/requirements.txt --with torch==2.14.0 \
	  python train/train_local.py $(TAG) data/train/chat.jsonl

pull-model: ## Download a trained David into Ollama: make pull-model TAG=... [FP16=1]
	MODELS_BUCKET=$(MODELS_BUCKET) train/pull_model.sh $(TAG)

deploy: ## Deploy the audience web app to Cloud Run (Phase 2)
	@echo "deploy: the audience app (web/) is deployed in Phase 2 with infra/env.sh deploy_run"
