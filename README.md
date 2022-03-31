# HW-11 postgresql & docker
The relationship between the postgresql database docker and the python docker
### current state
Semi functional: items can be added or deleted

### development: docker
To deploy - from the root folder:
```Linux Kernel Module
docker-compose up -d --build
```
Database is available on localhost:5432 <br>
To switch containers off:
```Linux Kernel Module
docker-compose down -v
```

### production: docker
To deploy - from the root folder:
```Linux Kernel Module
docker-compose -f docker-compose.prod.yml up -d --build
```
To build the data base with initial tables & values:
```Linux Kernel Module
docker-compose -f docker-compose.prod.yml exec web python manage.py create_db
docker-compose -f docker-compose.prod.yml exec web python manage.py seed_db
```
To switch containers off:
```Linux Kernel Module
docker-compose -f docker-compose.prod.yml down -v
```

### Adding items / deleting

To add new hero (develompent):
```Linux Kernel Module
docker-compose -f docker-compose.yml exec web python manage.py addhero "Lenin" "Red" "22.02.2022"
```
or (production):
```Linux Kernel Module
docker-compose -f docker-compose.prod.yml exec web python manage.py addhero "Lenin" "Red" "22.02.2022"
```

To add new slogan:
```Linux Kernel Module
docker-compose -f docker-compose.yml exec web python manage.py addslogan "Lenin" "Power to the Soviets!!!"
```
```Linux Kernel Module
docker-compose -f docker-compose.prod.yml exec web python manage.py addslogan "Lenin" "Power to the Soviets!!!"
``` 

To add story:
```Linux Kernel Module
docker-compose -f docker-compose.yml exec web python manage.py addstory "Lenin" "Was a man"
```
```Linux Kernel Module
docker-compose -f docker-compose.prod.yml exec web python manage.py addstory "Lenin" "Was a man"
```

To add clash:
```Linux Kernel Module
docker-compose -f docker-compose.yml exec web python manage.py addclash
```
```Linux Kernel Module
docker-compose -f docker-compose.prod.yml exec web python manage.py addclash
```

To delete hero:
```Linux Kernel Module
docker-compose -f docker-compose.yml exec web python manage.py deletehero "Lenin"
```
```Linux Kernel Module
docker-compose -f docker-compose.prod.yml exec web python manage.py deletehero "Lenin"
```

### Connecting to postgresql data base:

(develompent):
```Linux Kernel Module
docker-compose exec db psql --username=azatnv --dbname=azatnv_db
```
(production):
```Linux Kernel Module
docker-compose exec db psql --username=azatnv --dbname=azatnv_db_prod
```
