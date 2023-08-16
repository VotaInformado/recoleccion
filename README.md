# vota-informado-recoleccion
 
Build: 

```
docker compose -f local.yml build --build-arg CACHEBUST=$(openssl rand -base64 32)
```

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


