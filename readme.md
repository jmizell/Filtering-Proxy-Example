# Filtering Proxy Example
This proxy example uses a svm linear classifier to reject possible sql strings found in the query string. The model was trained from a variety of sources, all of which can be found in the data folder, including attribution.

# Running this example
```
```

# Building this example
Building is as simple as docker build

```
docker build -t filterproxy-example .
```

# Train the model
A script is provided under data to easily train a new model. Just cd to data, and run python train.py. A new classifier, and vectorizor will be trained, and written to disk.

The model's data can be updated by adding new samples in the positive, or negative folders. Entries should be one line in a text file, with the extension, txt.