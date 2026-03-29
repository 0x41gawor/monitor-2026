IMAGE_NAME=monitor-2026
CONTAINER_NAME=monitor-2026

docker-build:
	docker build -t $(IMAGE_NAME) .

docker-run:
	docker run -d \
		--name $(CONTAINER_NAME) \
		--restart unless-stopped \
		--env-file .env \
		-v $(PWD)/credentials.json:/run/secrets/credentials.json:ro \
		-v $(PWD)/.fitbit_tokens.json:/data/.fitbit_tokens.json \
		$(IMAGE_NAME)

docker-run-once:
	docker run --rm \
		--env-file .env \
		-v $(PWD)/credentials.json:/run/secrets/credentials.json:ro \
		-v $(PWD)/.fitbit_tokens.json:/data/.fitbit_tokens.json \
		$(IMAGE_NAME) \
		python -m app.cli

docker-run-date:
	docker run --rm \
		--env-file .env \
		-v $(PWD)/credentials.json:/run/secrets/credentials.json:ro \
		-v $(PWD)/.fitbit_tokens.json:/data/.fitbit_tokens.json \
		$(IMAGE_NAME) \
		python -m app.cli --date $(DATE)

docker-logs:
	docker logs -f $(CONTAINER_NAME)

docker-shell:
	docker run --rm -it \
		--env-file .env \
		-v $(PWD)/credentials.json:/run/secrets/credentials.json:ro \
		-v $(PWD)/.fitbit_tokens.json:/data/.fitbit_tokens.json \
		$(IMAGE_NAME) \
		/bin/bash

docker-stop:
	-docker stop $(CONTAINER_NAME)

docker-rm:
	-docker rm $(CONTAINER_NAME)

docker-restart: docker-stop docker-rm docker-run