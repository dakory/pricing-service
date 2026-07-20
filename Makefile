ECR=870388460670.dkr.ecr.us-east-1.amazonaws.com
APP=pricing-service
REGION=us-east-1

login:
	aws ecr get-login-password --region $(REGION) | \
	docker login --username AWS --password-stdin $(ECR)

build:
	docker buildx build --platform linux/amd64 -t $(APP) .

tag:
	docker tag $(APP):latest $(ECR)/$(APP):latest

push: login tag
	docker push $(ECR)/$(APP):latest

deploy: build push