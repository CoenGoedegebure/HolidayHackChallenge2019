import requests
import json
import base64
from sklearn.neighbors import KNeighborsClassifier
from sklearn.model_selection import train_test_split
from imutils import paths
import numpy as np
import cv2
import os
import pickle
from shutil import copy2

# Translation table between requested image types and the labels in the model
model_translate = {'Presents': 'present', 'Santa Hats': 'hat', 'Candy Canes': 'cane', 'Ornaments': 'ball',
                   'Christmas Trees': 'tree', 'Stockings': 'sock'}

# Used to check whether the application is running with the default email address. If so, generate an error
default_email = 'xxxx@xxx.xxx'


def image_to_feature_vector(image):
    return cv2.resize(image, (32, 32)).flatten()


# Call in a loop to create terminal progress bar
# @params:
#     iteration   - Required  : current iteration (Int)
#     total       - Required  : total iterations (Int)
#     prefix      - Optional  : prefix string (Str)
#     suffix      - Optional  : suffix string (Str)
#     decimals    - Optional  : positive number of decimals in percent complete (Int)
#     length      - Optional  : character length of bar (Int)
#     fill        - Optional  : bar fill character (Str)
#     printEnd    - Optional  : end character (e.g. "\r", "\r\n") (Str)
def print_progress_bar(iteration, total, prefix='Progress: ', suffix='', decimals=1, length=80, fill='█', printEnd="\r"):
    percent = ("{0:." + str(decimals) + "f}").format(100 * (iteration / float(total)))
    filled_length = int(length * iteration // total)
    bar = fill * filled_length + '-' * (length - filled_length)
    print('\r%s |%s| %s%% %s' % (prefix, bar, percent, suffix), end=printEnd)
    # Print New Line on completion
    if iteration == total:
        print()


# Rename all images in a base bath to the format {img_type}.{sequence_number}.ext
# This is the format required for the model training
def move_path(basepath, image_type, output_path):
    model_image_type = model_translate[image_type]
    image_paths = list(paths.list_images(os.path.join(basepath, image_type)))

    num = 1
    for source_path in image_paths:
        file_name, file_extension = os.path.splitext(source_path)
        destination_path = f'{output_path}/{model_image_type}.{num}{file_extension}'
        copy2(source_path, destination_path)
        num += 1


# We received a training set of 12000 images separated in categories. Each subfolder of set_path has all images from
# that category. Our training set expects filenames like <category>.<sequence_number>.<extension> (e.g. ball.45.png)
# from which the labels can be derived.
# This restructure method copies all images in the initial training set to the training path renaming the images to the
# the proper naming convention
# raw_set_path: The path containing the 12000 images from the training set
# train_path: The path to which the normalized files will be copied
def initialize_training_set(raw_set_path, train_path):
    print('Initializing the model training set from the raw KringleCon images')
    print(f'Input set path: {raw_set_path}')
    print(f'Model training set path: {train_path}')
    print('------------------------------------------------------------------')

    if not os.path.isdir(train_path):
        os.makedirs(train_path)

    sub_dirs = next(os.walk(raw_set_path))[1]
    for image_type in sub_dirs:
        print(f'Preparing images in subfolder {image_type}')
        move_path(raw_set_path, image_type, train_path)

    print('Initialisation of image training set completed')


# Train the model
# training_set_path: The path containing the normalized image filenames (this should be the train_path of the
#                    initialize_training_set method)
# model_save_filename: The filename to which the model should be saved
def train_model(training_set_path, model_save_filename):
    print(f"Training model based on images in directory {training_set_path}")
    image_paths = list(paths.list_images(training_set_path))
    total_images = len(image_paths)
    print(f"Extracting raw pixel info from {total_images} images")

    raw_images = []
    labels = []
    # loop over the input images
    for (i, image_path) in enumerate(image_paths):
        # load the image and extract the class label (assuming that our
        # path as the format: /path/to/dataset/{class}.{image_num}.jpg
        image = cv2.imread(image_path, -1)
        label = image_path.split(os.path.sep)[-1].split(".")[0]

        # extract raw pixel intensity "features"
        pixels = image_to_feature_vector(image)

        if i % 100 == 0:
            print_progress_bar(i, total_images)

        # update the raw images and labels matrices
        raw_images.append(pixels)
        labels.append(label)

    print_progress_bar(100, 100)

    raw_images = np.array(raw_images)
    labels = np.array(labels)

    # Partition the data into training and testing splits, using 90%
    # of the data for training and the remaining 10% for testing
    (trainRI, testRI, trainRL, testRL) = train_test_split(raw_images, labels, test_size=0.10, random_state=42)

    # train and evaluate a k-NN classifer on the raw pixel intensities
    model = KNeighborsClassifier(n_neighbors=1, n_jobs=1)
    print("Training model...")
    model.fit(trainRI, trainRL)

    print("Evaluating raw pixel accuracy...")
    acc = model.score(testRI, testRL)
    print("Raw pixel accuracy: {:.2f}%".format(acc * 100))
    print(f"Saving model to {model_save_filename}")
    pickle.dump(model, open(model_save_filename, 'wb'))


# Classify a given image and return the image type
def classify(b64data, model):
    img_str = base64.b64decode(b64data)
    pixel_array = np.frombuffer(img_str, dtype=np.uint8)
    image = cv2.imdecode(pixel_array, flags=cv2.IMREAD_UNCHANGED)
    raw_image = np.array([image_to_feature_vector(image)])
    return model.predict(raw_image)


# Using the json obtained from the capteha, determine which images match the requested categories
# returns an array of matching uuids
def determine_matches(capteha_json, ml_model):
    # map between the challenge names and the labels in the model
    raw_types = capteha_json['select_type'].replace('and ', '').split(', ')
    requested_types = []
    for t in raw_types:
        requested_types.append(model_translate[t])

    print(f'Requested types: {requested_types}')
    matches = []
    for img in capteha_json['images']:
        uuid = img['uuid']
        classification = classify(img['base64'], ml_model)[0]

        if classification in requested_types:
            matches.append(uuid)
            print(f'MATCH: {uuid} is a {classification}')
        else:
            print(f'       {uuid} is a {classification}')

    return matches


def crack_capteha(model_file_name):
    # Fill in your personal email address. Note this is the email address on which you will receive the challenge code
    email_address = "xxxx@xxx.xxx"
    if email_address == default_email:
        print('You need to change the default email address in the crack_capteha() method')

    print('Loading model')
    ml_model = pickle.load(open(model_file_name, 'rb'))

    # Creating a session to handle cookies
    session = requests.Session()
    url = "https://fridosleigh.com/"

    json_resp = json.loads(session.get(f"{url}api/capteha/request").text)

    # Process the images from the CAPTEHA through the machine learning model and
    # return uuids of the images matching the requested image types
    matches = determine_matches(json_resp, ml_model)

    # submit the result
    body = {'answer': ','.join(matches)}
    json_resp = json.loads(session.post(f"{url}api/capteha/submit", data=body).text)
    if not json_resp['request']:
        # If it fails just run again. ML might get one wrong occasionally
        print('FAILED MACHINE LEARNING GUESS')
        print('--------------------\nOur ML Guess:\n--------------------\n{}'.format(body))
        print('--------------------\nServer Response:\n--------------------\n{}'.format(json_resp['data']))
        return

    print('CAPTEHA Solved!')

    # If we get to here, we are successful and can submit a bunch of entries till we win
    userinfo = {
        'name': 'Krampus Hollyfeld',
        'email': email_address,
        'age': 180,
        'about': "Cause they're so flippin yummy!",
        'favorites': 'thickmints'
    }

    # If we win the once-per minute drawing, it will tell us we were emailed.
    # Should be no more than 200 times before we win. If more, somethings wrong.
    entry_response = ''
    entry_count = 1
    while email_address not in entry_response and entry_count < 200:
        print('Submitting lots of entries until we win the contest! Entry #{}'.format(entry_count))
        entry_response = session.post("{}api/entry".format(url), data=userinfo).text
        entry_count += 1

    print(entry_response)


def main():
    training_set_path = './training_set'   # The path where the prepared images are stored
    capteha_images_path = '/home/coen/frido/capteha_images'  # This is the path you extracted the training images to
    model_file_name = 'sklearn_model.mod'   # The filename for the trained model

    # 1) First step: Run the initialize_training_set to prepare the images for training
    # initialize_training_set(capteha_images_path, training_set_path)

    # 2) Second step: Train the model with the prepared images
    # train_model(training_set_path, model_file_name)

    # 3) Crack the capteha using the trained model
    # crack_capteha(model_file_name)


if __name__ == '__main__':
    main()
