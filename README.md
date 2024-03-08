# Vota Informado Recoleccion API
Backend API for the [Vota Informado](https://votainformado.com.ar) project.

<div style="text-align: center;">
    <img src="https://www.votainformado.com.ar/static/media/logo.b3817a447af529aca95c3d065b7c48e1.svg" alt="Vota Informado" width="200"/>
</div>


## Development

### Requirements
To run the project you need to have installed:
 - Docker
 - Docker Compose
 
### Running the project
To run the project you need to execute the following command:

```bash
# Build
docker compose -f local.yml build --build-arg CACHEBUST=$(openssl rand -base64 32)
# Run
docker compose -f local.yml run --rm --service-ports django.recoleccion
```
In order to get into the container and run commands, you can use the following command:

```bash
docker exec --user root -it $container_name bash
```
Where `$container_name` is the name of the container.

### Running the tests
Having the project running, connect to the container and run the following command:

```bash
python manage.py test
```

### Running the commands
To run any of the commands to load/update or change the data you should use:

```bash
python manage.py $command_name
```
Where `$command_name` is the name of the command you want to run.

Commands ideal order:  
 - load_law_projects
 - load_external_law_projects
 - load_law_projects_text
 - load_laws
 - load_current_deputies
 - load_current_senators
 - load_senators_history
 - load_deputies_history
 - load_deputies_day_orders
 - load_votes
 - load_senate_votes
 - load_deputies_votes
 - add_persons_from_votes (optional)


