help:
	@echo "  test        		run tests"
	@echo "  migrations        	run makemigrations and migrate"
	@echo "  runserver        	run a develop server"

dev:
	docker-compose run -p 8000:8000 --rm web python manage.py runserver 0.0.0.0:8000

test: 
	docker-compose run --rm web python manage.py test

migrations: 
	docker-compose run --rm web python manage.py makemigrations 
	docker-compose run --rm web python manage.py migrate 

server:
	docker-compose up

superuser:
	docker-compose run --rm web python manage.py createsuperuser

service:
	docker-compose run --rm web python manage.py runscript services
