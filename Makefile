help:
	@echo "  test        		run tests"
	@echo "  migrations        	run makemigrations and migrate"
	@echo "  runserver        	run a develop server"

test: 
	docker-compose run --rm web python manage.py test

migrations: 
	docker-compose run --rm web python manage.py makemigrations 
	docker-compose run --rm web python manage.py migrate 

server:
	docker-compose up
