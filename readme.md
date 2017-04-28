# Filtering Proxy Example
This proxy example uses a svm linear classifier to reject possible sql strings found in the query string. The model was trained from a variety of sources, all of which can be found in the data folder, including attribution.

# Running this example

## Run a wordpress container
In this example where using wordpress, but it can be any container really
```
docker run -d \
  --name filterproxy_mysql \
  -e MYSQL_ROOT_PASSWORD=somewordpress \
  -e MYSQL_DATABASE=wordpress \
  -e MYSQL_USER=wordpress \
  -e MYSQL_PASSWORD=wordpress \
  mysql:5.7

docker run -d \
  --name filterproxy_wordpress \
  -e WORDPRESS_DB_HOST=db:3306 \
  -e WORDPRESS_DB_USER=wordpress \
  -e WORDPRESS_DB_PASSWORD=wordpress \
  --link filterproxy_mysql:db \
  wordpress:latest
```

Now we run the proxy app. You don't have to, but I perfer to run containers I'm debugging in an interactive session.

```
docker run -it \
  --name filterproxy_app \
  --rm \
  -p 127.0.0.1:8080:8080 \
  --link filterproxy_wordpress:upstream \
  filterproxy
```

# Building this example
Building is as simple as docker build

```
docker build -t filter-proxy-example .
```

# Train the model
A script is provided under data to easily train a new model. Just cd to data, and run python train.py. A new classifier, and vectorizor will be trained, and written to disk.

The model's data can be updated by adding new samples in the positive, or negative folders. Entries should be one line in a text file, with the extension, txt.
