# Filtering Proxy Example
This proxy example uses a svm linear classifier to reject possible sql strings found in the query string. The model was trained from a variety of sources, all of which can be found in the data folder.

### Reasons & Assumptions
This app was built in python, as it's the language I could complete the project in the fastest. 

Originally I was going to write a series of regex patterns, but as I looked more at the problem, it didn't seem like an affective solution. I opted instead to train a machine learning classifier on samples of sql injection. I choose svm as it's effective with a small set of data, and if the problem turned out to be non-linear, I can make use of a polynomial kernel. 

Everything is run in docker, because my dev environment is not your dev environment. With docker I can be certain that you are running everything exactly as I built it.

Since this is just a sample project, the following things where assumed

* It didn't need to be highly performant. It is neither memory efficient, nor as fast as possible.
* No other http methods other than get was configured.
* I do not check for obfuscation of any kind in the query parameters.
* I did not tune the model to prevent over-fitting, which it almost certainly is.

# Running this example

### Run Wordpress
This container will be our upstream server, that we are attempting to protect. In this example we're using wordpress, but it can be any container.

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

### Run the filtering proxy container
Now we run the proxy app. You don't have to, but I prefer to run containers I'm debugging in an interactive session. Port 8080 is bound to localhost obviously, if you need to access this from a remote machine, be aware.

```
docker run -it \
  --name filterproxy_app \
  --rm \
  -p 127.0.0.1:8080:8080 \
  --link filterproxy_wordpress:upstream \
  jmizell/filtering-proxy-example:0.2
```

### Using the example
You won't be able to do much with the proxy, and wordpress. Since the http get method is the only one allowed, you cannot get past the configuration screen. 

To trigger a rejection, pass any parameters in the browser. The following examples should have the following result.

* 403 Forbidden, http://127.0.0.1:8080/?test=105%20OR%201=1
* 403 Forbidden, http://127.0.0.1:8080/?test=105;%20DROP%20TABLE%20Suppliers
* 403 Forbidden, http://127.0.0.1:8080/?test="%20or%20""="
* 403 Forbidden, http://127.0.0.1:8080/?test=select%20*%20from%20users%20where%20username=%s
* 200 OK, http://127.0.0.1:8080/?test=hello,%20world!
* 200 OK, http://127.0.0.1:8080/?test=Google%20announces%20last%20security%20update%20dates

# Building this example
Building is as simple as docker build

```
docker build -t filter-proxy-example .
```

# Train the model
A script is provided under data to easily train a new model. Just cd to data, and run python train.py. A new classifier, and vectorizor will be trained, and written to disk.

The model's data can be updated by adding new samples in the positive, or negative folders. Entries should be one line in a text file, with the extension, txt.

# Unit Test
Unit tests are ran during the container build, if they fail, the build will fail.

