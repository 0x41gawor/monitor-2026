IMAGE_NAME=monitor-2026
CONTAINER_NAME=monitor-2026
HOST_PORT=$(LUKA)
CONTAINER_PORT=5000
API_KEY_HEADER=X-API-Key: $$(grep '^API_KEY=' .env | cut -d= -f2-)

docker-build:
	docker build -t $(IMAGE_NAME) .

docker-run:
	docker run -d \
		--name $(CONTAINER_NAME) \
		--restart unless-stopped \
		--env-file .env \
		-p $(HOST_PORT):$(CONTAINER_PORT) \
		-v $(CURDIR)/run/secrets/credentials.json:/run/secrets/credentials.json:ro \
		-v $(CURDIR)/data/.fitbit_tokens.json:/data/.fitbit_tokens.json \
		-v $(CURDIR)/data/.withings_tokens.json:/data/.withings_tokens.json \
		-v $(CURDIR)/data/runs:/data/runs \
		$(IMAGE_NAME)

docker-run-once:
	docker run --rm \
		--env-file .env \
		-v $(CURDIR)/run/secrets/credentials.json:/run/secrets/credentials.json:ro \
		-v $(CURDIR)/data/.fitbit_tokens.json:/data/.fitbit_tokens.json \
		-v $(CURDIR)/data/.withings_tokens.json:/data/.withings_tokens.json \
		-v $(CURDIR)/data/runs:/data/runs \
		$(IMAGE_NAME) \
		python -m app.cli

docker-run-date:
	docker run --rm \
		--env-file .env \
		-v $(CURDIR)/run/secrets/credentials.json:/run/secrets/credentials.json:ro \
		-v $(CURDIR)/data/.fitbit_tokens.json:/data/.fitbit_tokens.json \
		-v $(CURDIR)/data/.withings_tokens.json:/data/.withings_tokens.json \
		-v $(CURDIR)/data/runs:/data/runs \
		$(IMAGE_NAME) \
		python -m app.cli --date $(DATE)

docker-logs:
	docker logs -f $(CONTAINER_NAME)

docker-shell:
	docker run --rm -it \
		--env-file .env \
		-p $(HOST_PORT):$(CONTAINER_PORT) \
		-v $(CURDIR)/run/secrets/credentials.json:/run/secrets/credentials.json:ro \
		-v $(CURDIR)/data/.fitbit_tokens.json:/data/.fitbit_tokens.json \
		-v $(CURDIR)/data/.withings_tokens.json:/data/.withings_tokens.json \
		$(IMAGE_NAME) \
		/bin/bash

docker-stop:
	-docker stop $(CONTAINER_NAME)

docker-rm:
	-docker rm $(CONTAINER_NAME)

docker-restart: docker-stop docker-rm docker-run

curl-live:
	curl http://localhost:$(HOST_PORT)/api/v1/health/live

curl-ready:
	curl http://localhost:$(HOST_PORT)/api/v1/health/ready

curl-run-today:
	curl -X GET -H "$(API_KEY_HEADER)" http://localhost:$(HOST_PORT)/api/v1/run

curl-run-date:
	curl -X GET -H "$(API_KEY_HEADER)" "http://localhost:$(HOST_PORT)/api/v1/run?date=$(DATE)"

curl-runs:
	curl -H "$(API_KEY_HEADER)" http://localhost:$(HOST_PORT)/api/v1/runs
