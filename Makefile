#This makefile handles the common commands from the project
TAG := $$(git rev-parse --short HEAD)

.PHONY: pull clean install tests run migrate collectstatic backend all

pull:
	git fetch --all && git checkout ${GITHUB_REF_NAME} && git pull origin ${GITHUB_REF_NAME}

clean:
	sudo find . -type f -name '*.pyc' -delete
	sudo find . -type f -name '*.log' -delete
	prospector
		
install:
	pip3 install -r requirements.txt

tests:
	python3 manage.py test

#This command will run the project using concurrent package from npm
run:
	python3 manage.py runserver 8000

vevn:
	source ../main/bin/activate

backend:
	python3 manage.py runserver 8080

migrate:
	python3 manage.py migrate

collectstatic:
	python3 manage.py collectstatic --noinput

docker-be:
	docker build -t backend:$(TAG) -f deploy/Dockerfile.toolshub .


#This uses docker-compose and docker to build the entire project and run it within containers\
this is the preferred way if you have a good system that can handle multiple containers\
this will try to use a local database which you already have on your system (mysql)
down:
	export TAG=${TAG} && docker-compose -f deploy/docker-compose.yml down

start-backend:
	export TAG=${TAG} && docker-compose -f deploy/docker-compose.yml up -d --no-deps --build backend

reload:
	docker exec -i nginx nginx -s reload

deploy-backend:
	export TAG=${TAG} && ./deploy/backend.sh

deploy-all:
	export TAG=${TAG} && ./deploy/backend.sh && ./deploy/frontend.sh

restart-backend:
	docker-compose -f deploy/docker-compose.yml restart backend

clear:
	sudo sh -c 'truncate -s 0 /var/lib/docker/containers/*/*-json.log'

up:
	export TAG=${TAG} && docker-compose -f deploy/docker-compose.yml up -d
logs:
	export TAG=${TAG} && docker-compose -f deploy/docker-compose.yml logs -f

login-ecr:
	aws ecr get-login-password --region ap-south-1 | docker login --username AWS --password-stdin 006562472852.dkr.ecr.ap-south-1.amazonaws.com

ecr-tag:
	export TAG=${TAG} && docker tag backend:$(TAG) 006562472852.dkr.ecr.ap-south-1.amazonaws.com/cnext:backend-$(TAG) && docker tag frontend:$(TAG) 006562472852.dkr.ecr.ap-south-1.amazonaws.com/cnext:frontend-$(TAG)

push-ecr:
	export TAG=${TAG} && docker push 006562472852.dkr.ecr.ap-south-1.amazonaws.com/cnext:backend-$(TAG) && docker push 006562472852.dkr.ecr.ap-south-1.amazonaws.com/cnext:frontend-$(TAG)
#This is the main command to run the project without using docker, if you have an environment\
and database setup use this command
all: clean install run
