import re
import glob
import time
from sklearn import svm
from sklearn.externals import joblib
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer

data_set_labels = []
data_set_values = []
labels = ['negative', 'positive']
classifier_file = 'svm_linear_classifier.pkl'
vectorizer_file = 'vectorizer.pkl'

# read the training data in
for label in labels:
    for dataset_file in glob.glob("%s/*.txt" % label):
        with open(dataset_file, 'r') as f:
            data_text = f.read().splitlines()
        # remove any line that begins with a hash symbol
        data_text = filter(None, map(lambda x: None if re.search(r"^#", x) else x, data_text))
        data_set_values += data_text
        data_set_labels += [label] * len(data_text)

for label in labels:
    print("Loaded %i %s examples" % (data_set_labels.count(label), label))

# split a third in to test, and train sets
label_train, label_test, values_train, values_test = train_test_split(
    data_set_labels,
    data_set_values,
    test_size=0.33,
    random_state=0)

print("Data split, training: %s, test: %s" % (len(values_train), len(values_test)))

# Create feature vectors
vectorizer = TfidfVectorizer(sublinear_tf=True,
                             lowercase=True,
                             use_idf=True)
train_vectors = vectorizer.fit_transform(values_train)
test_vectors = vectorizer.transform(values_test)

# Train the model
t0 = time.time()
classifier_liblinear = svm.LinearSVC(C=1, verbose=True).fit(train_vectors, label_train)
train_time = time.time() - t0
accuracy = classifier_liblinear.score(test_vectors, label_test)
print("Training time: %fs" % train_time)
print("Test Accuracy %s" % accuracy)
if accuracy > 0.95:
    print("Warning, this model may be over fit")

# Test a few examples
test_examples = [
    'select value1, value2, num_value3 from database',
    'hello, world!',
    'test message',
    'GRANT ALL ON TABLE metadatacollectionschema.altidcollection TO omerouser',
    'select * from users where username=%s']
sample_vector = vectorizer.transform(test_examples)
for i, prediction in enumerate(classifier_liblinear.predict(sample_vector)):
    print(prediction, test_examples[i])

# write the model, and vectorizor to disk
joblib.dump(classifier_liblinear, classifier_file, compress=True)
print("Wrote classifier to %s" % classifier_file)
joblib.dump(vectorizer, vectorizer_file, compress=True)
print("Wrote vectorizer to %s" % vectorizer_file)
