# friendly-octo-funicular
Small repository for Appfollow python-dev test

## Run
```
    docker-compose up
```
## Test
```
    curl -X GET http://localhost:8000/posts
```
## 

## TO DO
1. add method GET /update
2. refactor app -> make something like:
├── docker-compose.yaml
├── Dockerfile
├── hackerngrabber
│ ├── app.py
│ ├── __init__.py
│ ├── routes.py
│ ├── utils.py
│ └── views.py
└── setup.py
