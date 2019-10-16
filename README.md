# friendly-octo-funicular
Small repository for Appfollow python-dev test

## Run
```
    docker-compose up
```
## Test
```
    curl -X GET http://localhost:8000/posts
    curl -X GET http://localhost:8000/update
```
## Deployed
https://polar-caverns-52350.herokuapp.com/
## TO DO
1. refactor route /update. Make one session for all request to HackerNews
2. Add more loging
3. refactor app -> make something like

app.py
routes.py
utils.py
views.py

4. Add unit-tests

