ECR=870388460670.dkr.ecr.us-east-1.amazonaws.com
APP=pricing-service
REGION=us-east-1
RELEASE_SHA ?= $(shell git rev-parse --short=12 HEAD)

login:
	aws ecr get-login-password --region $(REGION) | \
	docker login --username AWS --password-stdin $(ECR)

build:
	docker buildx build --load --platform linux/amd64 --build-arg BUILD_SHA=$(RELEASE_SHA) -t $(APP):api-$(RELEASE_SHA) .

build-dashboard:
	docker buildx build --load --platform linux/amd64 --build-arg BUILD_SHA=$(RELEASE_SHA) -t $(APP):dashboard-$(RELEASE_SHA) ./dashboard

tag:
	docker tag $(APP):api-$(RELEASE_SHA) $(ECR)/$(APP):api-$(RELEASE_SHA)
	docker tag $(APP):dashboard-$(RELEASE_SHA) $(ECR)/$(APP):dashboard-$(RELEASE_SHA)

push: login tag
	docker push $(ECR)/$(APP):api-$(RELEASE_SHA)
	docker push $(ECR)/$(APP):dashboard-$(RELEASE_SHA)
	@echo "Release $(RELEASE_SHA) published; deploy both images with IMAGE_TAG=$(RELEASE_SHA)."

release: build build-dashboard push

deploy: release
