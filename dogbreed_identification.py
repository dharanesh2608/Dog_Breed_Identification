# -*- coding: utf-8 -*-
"""DOGBREED_identification.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1-S2g_WjB2DhhM5VdP8E5eYRYX1eN3h6B

#**End to end multi-class Dog Breed Classisication**

this notebook builds an end to end multi class image classifier using Tensorflo 2.0 and Tensor Hub.

##1.Problem
Identifying the bread of a dog given an image of a dog.
##2.Data
The data is from kaggle's dog breed identification competetion.

https://www.kaggle.com/c/dog-breed-identification/data

##3.Evaluation

The evaluation is a file with prediction probabilities for each dog breed of each test image.

www.kaggle.com/competitions/dog-breed-identification/overview/evaluation

##4.Features
Some information about the data:
.We are dealing with images(unstructured data) so it is probably best we use deep learning/transfer learning.

.There are 120 breeds of dogs (this means there are 120 different classes).

.There are around 10000+ images in the training set(these images have labels).

.there are around 10000+ images in the test set(these images have no labels,beacuse we'll want to prfedict them).
"""



"""###Get the work space ready
.import tensorflow

.import tensorflow hub

.Make sure of using GPU
"""



# Importing tensor flow
import tensorflow as tf
import tensorflow_hub as hub
print(tf.__version__)
print(hub.__version__)

#check for GPU availability
print("GPU","available(Yess!)" if tf.config.list_physical_devices("GPU") else "not available")

from google.colab import files      #choose kaggle.json api downloaded from kaggle website
uploaded=files.upload()

from google.colab import drive
drive.mount('/content/drive')

import os
os.makedirs('/root/.kaggle',exist_ok=True)
!mv kaggle.json /root/.kaggle/
!chmod 600 /root/.kaggle/kaggle.json

!kaggle competitions download -c dog-breed-identification

!unzip dog-breed-identification.zip -d dog_breed_data

"""##getting our data ready(turning into tensors)
With all machine learning models,our data has to be in numerical format.So thats what we will be doing first.Turning our images into Tensors(numerical representations)
"""

#check the labels of the our data
import pandas as pd
labels_csv=pd.read_csv("/content/dog_breed_data/labels.csv")
print(labels_csv.describe())

labels_csv.head()

labels_csv["breed"].value_counts().plot.bar(figsize=(20,10))

#median number of images per class
labels_csv["breed"].value_counts().median()

#Lets view an image
from IPython.display import Image
Image("/content/dog_breed_data/test/00225dcd3e4d2410dd53239f95c0352f.jpg")

"""###Getting images and their labels
lets get a list of all of  our image pathnames
"""

labels_csv.head()

#create pathnames from image id
filenames=["/content/dog_breed_data/train/" + fname +".jpg"for fname in labels_csv["id"]]
filenames[:15]

#check whether number of filenames matches number of actual image files
import os
if len(os.listdir("/content/dog_breed_data/train/"))==len(filenames):
  print("OFF course matcheed!")

Image(filenames[8000])

labels_csv["breed"][8000]

"""We got training image filepaths in a list.lets prepare our labels"""

import numpy as np
labels=labels_csv["breed"].to_numpy()
labels

if len(labels)==len(filenames):
  print("number of labels matches file name")

#Find the unique label values
unique_breeds=np.unique(labels)
unique_breeds

len(unique_breeds)

#Turn a single label into an array of booleans
print(labels[0])
labels[0]==unique_breeds

#Turn every label into boolean array
boolean_labels=[label==unique_breeds for label in labels]
boolean_labels[:2]

#Example:Turning boolean array into integers
print(labels[0]) #original label
print(np.where(unique_breeds==labels[0]))#index where label occurs
print(boolean_labels[0].argmax())#index where label occurs in boolean array
print(boolean_labels[0].astype(int))#there will be a 1 where the sample label occurs

""" ##Creating our own validation set


 since the dataset from kaggle doesnt come with a validation set,we are going to create our own.
"""

#setup x&y variables

x=filenames
y=boolean_labels

"""We are going to start off experimenting with ~1000 images and increase as needed"""

#Set number of images to use for experimenting
NUM_IMAGES=1000 #@param{type:"slider",min:1000,max:11000}

#Lets split the data into train and validation sets
from sklearn.model_selection import train_test_split

#Split them into training and validation of total size NUM_IMAGES
x_train,x_val,y_train,y_val=train_test_split(x[:NUM_IMAGES],y[:NUM_IMAGES],
                                             test_size=0.2,
                                             random_state=20)
len(x_train),len(y_train),len(x_val),len(y_val)

"""###Preprocessing Images(turning images into Tensors)

To preprocess our images into Tensors we are going to write a function which does few things:

1. Take an image filepath as input
2. Use TensorFlow to read the file and
   save it to a variable,image
3. Turn our image into tensors
4. Normalize our image(convert colour channel values from 0-255 to 0-1)
5. Resize the image to be shape of(224,
  224)
6. Return the modified image
"""

#Convert image to NUmpy array
from matplotlib.pyplot import imread
image=imread(filenames[42])
image.shape

image[:2]

import tensorflow as tf
tf.constant(image)[:2]

"""we have seen what an image looks like as a Tensor,lets make a function to preprocess them."""

#Define image size
IMG_SIZE=224

#create a function for preprocessing images
def process_image(image_path, img_size=IMG_SIZE):
  """
  Takes an image file path and turns the image into a Tensor.

  """
#Read in an image file
  image=tf.io.read_file(image_path)

#Turn the jpeg image into numerical Tensor with 3 colour channels(Red,Green,Blue)
  image=tf.image.decode_jpeg(image,channels=3)

  #convert the color channel values from 0-255 to 0-1 values
  image=tf.image.convert_image_dtype(image,tf.float32)

  #Resize the image to our desired value(224,224)
  image=tf.image.resize(image,size=[IMG_SIZE,IMG_SIZE])

  return image

tensor=tf.io.read_file(filenames[26])
tensor

tf.image.decode_jpeg(tensor,channels=3)

"""###Turning our data into batches
why turn our data into batches?

if we try to process 10,000+ images in one go.....they all might not fit into memory.

So thats why we do about 32(this is the batch size) images at a time(you can manually adjust the batch)
In order to use TensorFlow effecticely,we need our data in the form of Tensor tuples which look like:'(image,label)'
"""

#Create a simple function to return a tuple (image,label)
def get_image_label(image_path,label):
  """Takes image file path names and the associated label,
     process the image and returns a type of (image,label)."""
  image=process_image(image_path)
  return image,label

(process_image(x[40]),tf.constant(y[40]))

"""Now we got a way to turn data into tuples of Tensors in the form: `(image,label)`,let us make a function to turn all the data into batches!

"""

#Define the batch size,32 is a good start
BATCH_SIZE=32

#create a function to turn data into batches
def create_data_batches(x,y=None,batch_size=BATCH_SIZE,valid_data=False,test_data=False):
  """Creates batches of data out of image x and label y pairs.
     shuffles the data if it is training data but doesn't shufflew if it validation data.
     Also accepts test data as input(no labels).
     """
  #if the data is  a test dataset,we dont have labels
  if test_data:
    print("creating test data batches......")
    data=tf.data.Dataset.from_tensor_slices((tf.constant(x))) #only filepaths (no labels)
    data_batch=data.map(process_image).batch(BATCH_SIZE)
    return data_batch
  #if the data is a valid dataset,we dont need to shuffle it
  elif valid_data:
    print("Creating valid data batches....")
    data=tf.data.Dataset.from_tensor_slices((tf.constant(x),#File paths
                                             tf.constant(y))) #labels
    data_batch=data.map(get_image_label).batch(BATCH_SIZE)
    return data_batch

  else:
    print("Creating training data batches....")
    #Turn filepaths and labels into tensors
    data=tf.data.Dataset.from_tensor_slices((tf.constant(x),tf.constant(y)))
    #Shuffling pathnames and labels before mapping image processor function is faster than shuffle
    data=data.shuffle(buffer_size=len(x))

    #create (image,label) tuples (this also turns the image path into a preprocessed image)
    data=data.map(get_image_label)

    #Turn the training data into batches

    data_batch=data.batch(BATCH_SIZE)

  return data_batch

#Create training and validation data batches
train_data=create_data_batches(x_train,y_train)
val_data=create_data_batches(x_val,y_val,valid_data=True)

#Check out the different attributes of our data batches
train_data.element_spec,val_data.element_spec



"""##Visualizing data batches
Our data is now in batches,however,these can be a little hard to understtand/comprehend,lets visualize the batches
"""

import matplotlib.pyplot as plt

#Create a function for viewing images in a data batch
def show_25_images(images,labels):
  """
  Displays a plot of 25 images and their labels from a data batch.
  """
  #Setup the figure
  plt.figure(figsize=(10,10))

  #Loop through 25(for displaying 25 images)
  for i in range(25):
    #Create subplots (5rows,5columns)
    ax=plt.subplot(5,5,i+1)

    #Display an image
    plt.imshow(images[i])

    #Add the image label as the title
    plt.title(unique_breeds[labels[i].argmax()])
    #Turn the grid lines off
    plt.axis("off")

train_data

train_images,train_labels=next(train_data.as_numpy_iterator())
train_images,train_labels

unique_breeds[y[0].argmax()]

unique_breeds

#Now lets visualize the data in a training batch
show_25_images(train_images,train_labels)

#Now lets visualize the data in a training batch
train_images,train_labels=next(train_data.as_numpy_iterator())
show_25_images(train_images,train_labels)

"""# Building a model
Before we build a model,there are few things we need to define:
*The input shape(our images shape,in the form of Tensors) to our model.
*The output shape(image labels,in the form of Tensors) of our model.
*The URL of the model we want to use.
"""

#Setup input shape to the model
INPUT_SHAPE=[None,IMG_SIZE,IMG_SIZE,3]  #batch,height,width,colour channels

#Setup output shape of our model
OUTPUT_SHAPE=len(unique_breeds)

#Setup model URL from TensorFlow Hub
MODEL_URL="https://tfhub.dev/google/imagenet/mobilenet_v2_130_224/classification/4"

"""#Now we got our inputs,outputs and model ready to go.
Lets put them together into a keras deep learning model!

Knowing this,lets create a funcion which:
*Takes the input shape,output shape and the model we have choosen as parameters.

*Defines the layers in a keras model in sequential fashion(do this first,then this,then that).

*Compiles the model (says it should be evaluated and improved).

*Builds the model(tells the model the input shape it will be getting).

*Returns the model.

All of these steps can be found at https://www.tensorflow.org/guide/keras/overview

"""

from tensorflow.keras import layers
#Create a function which builds a keras model
def create_model(input_shape=INPUT_SHAPE,output_shape=OUTPUT_SHAPE,model_url=MODEL_URL):
  print("Building model with :",MODEL_URL)

  #setup the model layers
  model=tf.keras.Sequential([
      hub.keras_layer.KerasLayer(MODEL_URL), #Layer 1(input_layer)
      tf.keras.layers.Dense(units=OUTPUT_SHAPE,
      activation="softmax") #Layer2(output layer)
  ])

#compile the model
  model.compile(
      loss=tf.keras.losses.CategoricalCrossentropy(),
      optimizer=tf.keras.optimizer.Adam(),
      metrics=["accuracy"]
)


#Build the model
  model.build(INPUT_SHAPE)

  return model

import tensorflow as tf
import tensorflow_hub as hub

def create_model(input_shape=[224, 224, 3], output_shape=1001, model_url="https://tfhub.dev/google/imagenet/mobilenet_v2_130_224/feature_vector/4"):
    print("Building model with:", model_url)

    # Setup the model layers
    model = tf.keras.Sequential([
        # Explicitly define an input layer with the correct shape
        tf.keras.layers.InputLayer(input_shape=input_shape),

        # Load the TF Hub model - wrapping it in a Lambda layer to avoid compatibility issues
        tf.keras.layers.Lambda(
            lambda x: hub.load(model_url)(x)
        ),

        # Add a classification layer
        tf.keras.layers.Dense(units=output_shape, activation="softmax")  # Output layer
    ])

    # Compile the model
    model.compile(
        loss=tf.keras.losses.CategoricalCrossentropy(),
        optimizer=tf.keras.optimizers.Adam(),
        metrics=["accuracy"]
    )

    # Build the model
    model.build([None] + input_shape)

    return model

model=create_model()
model.summary()

import tensorflow as tf
import tensorflow_hub as hub
from tensorflow.keras import layers

def create_model(input_shape=[224, 224, 3], output_shape=120, model_url="https://tfhub.dev/google/imagenet/mobilenet_v2_130_224/feature_vector/4"):
    print("Building model with:", model_url)

    # Define inputs explicitly
    inputs = tf.keras.Input(shape=input_shape)

    # Use the hub module in a Lambda layer for better compatibility
    hub_layer = hub.load(model_url)
    x = tf.keras.layers.Lambda(lambda x: hub_layer(x))(inputs)

    # Add classification layer
    outputs = tf.keras.layers.Dense(units=output_shape, activation="softmax")(x)

    # Create the model using the functional API
    model = tf.keras.Model(inputs=inputs, outputs=outputs)

    # Compile the model
    model.compile(
        loss=tf.keras.losses.CategoricalCrossentropy(),
        optimizer=tf.keras.optimizers.Adam(),
        metrics=["accuracy"]
    )

    return model

model=create_model()
model.summary()

"""##Creating  callbacks

callbacks are helper functions a model can use during training to do such things as save its progress,check its progress or stop training early if a model stops improving

Here we'll create two callbacks,one for TensorBoard which helps track our models progress and another for early stopping which prevents our model from training for too long.

###TensorBoard callback
To setup a TensorBoard callback,we need to do 3 things:
1. Load the TensorBoard notebook extension
2. Create a Tensorboard callback which is able to save logs to a directory and pass it to our models `fit()` function.

3. Visualize our models training logs with the %tensorboard magic function(we,ll do this after model training).
"""

# Commented out IPython magic to ensure Python compatibility.
#load Tensorboard notebook extension
# %load_ext tensorboard

import datetime
#Create a function to build a TensorBoard callback
def create_tensorboard_callback():
  #Create a log directory for storing TensorBoard logs
  logdir=os.path.join("drive/MyDrive/Dog_vision/logs",
                     #Make it so the logs get tracked whenever we run an experiment
                      datetime.datetime.now().strftime("%Y%m%d-%H%M%S"))
  return tf.keras.callbacks.TensorBoard(logdir)

"""###EarlyStopping callback

Early stopping helps stop our model from overfitting by stopping training if a evaluation metrics stops
https://www.tensorflow.org/api_docs/python/tf/keras/callbacks/EarlyStopping
"""

#Create early stopping callback
early_stopping=tf.keras.callbacks.EarlyStopping(monitor="val_accuracy",patience=3)

"""##Training a model(on subset of data)
Our first model is only going on train on 1000 images, to make sure everything is working.
"""

NUM_EPOCHS=100 #@param{type:"slider",min:1,max:100,step:10}

"""Lets create a function which trains a model.

.Create a model using create_model()

.Setup a TensorBoard callback using create_tensorboard_callback()

.Call the fit() function on our model passing it the training data,validation data,number of epochs to train

.Return the model
"""

#Build the function to train and return a trained model
def train_model():
  """
  Trains a given model and returns the trained version
  """
  #create a model
  model=create_model()

  #Create new TensorBoard session every time we train a model
  tensorboard=create_tensorboard_callback()

  #Fit the model to the data passing it the callbacks we created
  model.fit(x=train_data,epochs=NUM_EPOCHS,validation_data=val_data,
            validation_freq=1,callbacks=[tensorboard,early_stopping])
  #Return the fitted model
  return model

#Fit the model to the data
model=train_model()

"""It looks like our model is overfitting because its performing far better on the training dataset than thevalidation dataset,What are some ways to prevent model overfitting in deep learning neural networks?"""



"""##Checking the TensorBoard logs
The TensorBoard magic function (%tensorboard) will access the logs directory we created earlier and visualize its contents.
"""

# Commented out IPython magic to ensure Python compatibility.
# %tensorboard --logdir drive/MyDrive/Dog_vision/logs

"""Making and evaluating predictions using a trained model"""

#Make predictions on the validation data(not used to train on)
predictions=model.predict(val_data,verbose=1)
predictions

predictions.shape

len(y_val),len(unique_breeds)

np.sum(predictions[190])

#First prediction
index=99
print(predictions[index])
print(f"Max value (probability of prediction):{np.max(predictions[index])}")
print(f"Sum: {np.sum(predictions[index])}")
print(f"Max index:{np.argmax(predictions[index])}")
print(f"Predicted label:{unique_breeds[np.argmax(predictions[index])]}")

unique_breeds

"""it would be even better if we could see the image the prediction is being made on!
**NOTE**:Prediction probabilities are also known as confidence levels.
"""

#Turn prediction probabilities into their respective label(easier to understand)
def get_pred_label(prediction_probabilities):
  """
  Turns an array of prediction probabilities into a label.
  """
  return unique_breeds[np.argmax(prediction_probabilities)]

#Get a predicted label based on an array of prediction probabilities
pred_label=get_pred_label(predictions[120])
pred_label

"""Now since our validation data is still in a batch dataset,we'll have to unbatchify it to make predictions on the validation images and then compare those predictions to the validation labels(truth labels)."""

val_data

#Create a function to unbatch the dataset.
def unbatchify(data):
  """
  Takes a batched dataset of (image,label) Tensors and returns seperate arrays of images and labels.
  """
  images=[]
  labels=[]
  #Loop through unbatched data
  for image,label in data.unbatch().as_numpy_iterator():
    images.append(image)
    labels.append(unique_breeds[np.argmax(label)])
  return images,labels

#Unbatchify the validation dataset
val_images,val_labels=unbatchify(val_data)
val_images[0],val_labels[0]

get_pred_label(val_labels[12])

images_=[]
labels_=[]

#Loop through unbatched data
for image,label in val_data.unbatch().as_numpy_iterator():
  images_.append(image)
  labels_.append(label)

images_[0],labels_[0]

"""Now we've got ways to get:
  . Prediction labels
  . Validation labels(truth labels)
  . validation images

Let's make some function to make these all a bit more visualize.

We'll create a funcgtion which:

* Takes an array of prediction probabilities,an array of truth labels and an array of images and integers.
* Convert the prediction probabilities to predict a label.
* Plot the predicted label,its predicted probability,the truth label and the target image on a single plot.
"""

def plot_pred(prediction_probabilities,labels,images,n=1):
  """

   View the prediction,ground Truth and image for sample n
  """
  pred_prob,true_label,image=prediction_probabilities[n],labels[n],images[n]

  #Get the pred label
  pred_label=get_pred_label(pred_prob)

  #Plot image & remove ticks
  plt.imshow(image)
  plt.xticks([])
  plt.yticks([])
  #Changes the colour of the title depending on if the prediction is right or wrong
  if pred_label==true_label:
    color="green"
  else:
    color="red"


  #Change plot title to be predicted,probability of prediction and truth label
  plt.title("{} {:2.0f}% {}".format(pred_label,np.max(pred_prob)*100,
                                                true_label),color=color)

plot_pred(prediction_probabilities=predictions,labels=val_labels,images=val_images
          ,n=20)

"""Now we got one function to visualize our models top predictions,lets make another to view our models top 10 predictions

This function will:
* Take an input of prediction probabilities array and a ground truth array and an integer
* Find the prediction using `get_pred_label()`
*Find the top 10:
    *prediction probabailities indexes
    
    *prediction probabilities values
    
    *Prediction labels

*Plot the top 10 prediction probability value and labels,colouring the true label green
"""

def plot_pred_conf(prediction_probabilities,labels,n=1):
  """
  Plus the top 10 highest prediction confidences along with the truth label for sample n.
  """
  pred_prob,true_label=prediction_probabilities[n],labels[n]

  #get the predicted label
  pred_label=get_pred_label(pred_prob)

  #Find the top 10 prediction confidence indexes
  top_10_pred_indexes=pred_prob.argsort()[-10:][::-1]
  #find the top 10 predictions confidence values
  top_10_pred_values=pred_prob[top_10_pred_indexes]
  #Find the top 10 prediction labels
  top_10_pred_labels=unique_breeds[top_10_pred_indexes]

  #Setup plot
  top_plot=plt.bar(np.arange(len(top_10_pred_labels)),
                     top_10_pred_values,
                    color="grey")
  plt.xticks(np.arange(len(top_10_pred_labels)),
             labels=top_10_pred_labels,
             rotation="vertical")
  #Change the color of true label
  if np.isin(true_label,top_10_pred_labels):
    top_plot[np.argmax(top_10_pred_labels==true_label)].set_color("green")
  else:
    pass

plot_pred_conf(prediction_probabilities=predictions,
               labels=val_labels,
               n=9)

predictions[0]

predictions[0].argsort()

predictions[0][predictions[0].argsort()[-10:][::-1]]

predictions[0].argsort()[-10:]

predictions[0].max()

"""Now we got some functions to help us visualize our predictions and evaluate our model,lets check out a few."""

#Lets check out a few predictions and their different values
i_multiplier=5

num_rows=3
num_cols=2
num_images=num_rows*num_cols
plt.figure(figsize=(10*num_cols,5*num_rows))
for i in range(num_images):
  plt.subplot(num_rows,2*num_cols,2*i+1)
  plot_pred(prediction_probabilities=predictions,
              labels=val_labels,
            images=val_images,
            n=i+i_multiplier)
  plt.subplot(num_rows,2*num_cols,2*i+2)
  plot_pred_conf(prediction_probabilities=predictions,
                 labels=val_labels,
                 n=i+i_multiplier)

plt.show()

"""How would we create a confusion matrix with our model predictions and true labels?

##Saving and reloading a trained model
"""

#Create a function to save the model
import os
import datetime
import tensorflow as tf
import tensorflow_hub as hub

def save_model(model, suffix=None):
    """
    Saves a given model in a models directory and appends a suffix (string).
    Compatible with Keras 3 saving format.
    """
    # Create a model directory pathname with current time
    base_dir = "drive/MyDrive/Dog_vision/models"
    timestamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")

    if suffix:
        base_name = f"{timestamp}-{suffix}"
    else:
        base_name = f"{timestamp}"

    # Make sure the directory exists
    os.makedirs(base_dir, exist_ok=True)

    # Full path to save the model (without extension yet)
    base_path = os.path.join(base_dir, base_name)

    # First try saving as TF SavedModel (a directory)
    tf_saved_model_path = f"{base_path}_saved_model"
    print(f"Trying to save model as TensorFlow SavedModel to: {tf_saved_model_path}...")

    try:
        # Use tf.saved_model.save directly
        tf.saved_model.save(model, tf_saved_model_path)
        print(f"Model saved successfully as TensorFlow SavedModel to {tf_saved_model_path}")
        return tf_saved_model_path
    except Exception as e:
        print(f"Error saving as SavedModel: {e}")

    # Try saving as Keras model
    keras_path = f"{base_path}.keras"
    print(f"Trying to save as Keras model to: {keras_path}...")

    try:
        model.save(keras_path)
        print(f"Model saved successfully to {keras_path}")
        return keras_path
    except Exception as e:
        print(f"Error saving as Keras model: {e}")

    # Finally try to save weights only with the correct extension
    weights_path = f"{base_path}.weights.h5"
    print(f"Attempting to save weights only to {weights_path}")

    try:
        model.save_weights(weights_path)
        print(f"Model weights saved to {weights_path}")
        return weights_path
    except Exception as e:
        print(f"Error saving weights: {e}")
        raise e

def load_model(model_path):
    """
    Loads a saved model from a specified path
    """
    print(f"Loading saved model from: {model_path}")

    if model_path.endswith('.weights.h5'):
        print("This is a weights-only file. You need to recreate the model architecture first.")
        return None

    if os.path.isdir(model_path) and "_saved_model" in model_path:
        print("Loading TensorFlow SavedModel...")
        try:
            model = tf.saved_model.load(model_path)
            return model
        except Exception as e:
            print(f"Error loading SavedModel: {e}")

    # Try loading as regular Keras model
    try:
        model = tf.keras.models.load_model(
            model_path,
            custom_objects={"KerasLayer": hub.KerasLayer}
        )
        return model
    except Exception as e:
        print(f"Error loading model: {e}")
        raise e

"""Now we have got functions to save and load a trained model,lets make sure they work!"""

#Save our model trained on 1000 images
save_model(model,suffix="1000-images-mobilenetv2-Adam")

#Load a trained model
loaded_1000_image_model=load_model('/content/drive/MyDrive/Dog_vision/models/20250408-124028-1000-images-mobilenetv2-Adam.weights.h5')

#Evaluate the pre-saved model
model.evaluate(val_data)

# Step 1: Define your model parameters with the correct output shape
INPUT_SHAPE = [224, 224, 3]
OUTPUT_SHAPE = 120  # Changed from 1001 to 120 based on the error message
MODEL_URL = "https://tfhub.dev/google/imagenet/mobilenet_v2_130_224/feature_vector/4"

# Step 2: Recreate the model with the correct architecture
def create_model(input_shape=INPUT_SHAPE, output_shape=OUTPUT_SHAPE, model_url=MODEL_URL):
    print("Building model with:", model_url)

    # Define inputs explicitly
    inputs = tf.keras.Input(shape=input_shape)

    # Use the hub module in a Lambda layer for better compatibility
    hub_layer = hub.load(model_url)
    x = tf.keras.layers.Lambda(lambda x: hub_layer(x))(inputs)

    # Add classification layer with the correct output shape
    outputs = tf.keras.layers.Dense(units=output_shape, activation="softmax")(x)

    # Create the model using the functional API
    model = tf.keras.Model(inputs=inputs, outputs=outputs)

    # Compile the model
    model.compile(
        loss=tf.keras.losses.CategoricalCrossentropy(),
        optimizer=tf.keras.optimizers.Adam(),
        metrics=["accuracy"]
    )

    return model

# Step 3: Create the model with the correct output shape
recreated_model = create_model(INPUT_SHAPE, OUTPUT_SHAPE, MODEL_URL)

# Step 4: Load the weights
weights_path = "/content/drive/MyDrive/Dog_vision/models/20250413-091239-1000-images-mobilenetv2-Adam.weights.h5"
recreated_model.load_weights(weights_path)

# Step 5: Now you can evaluate the model
loaded_1000_image_model = recreated_model
results = loaded_1000_image_model.evaluate(val_data)
print(f"Validation loss: {results[0]:.4f}")
print(f"Validation accuracy: {results[1]:.4f}")

loaded_1000_image_model.evaluate(val_data)

"""#Training a big dog model (on the full data)"""

len(x),len(y)

#Create a data batch with the full data set
full_data=create_data_batches(x,y)

full_data

#Create a model for full model
full_model=create_model()

#Create full model callbacks
full_model_tensorboard=create_tensorboard_callback()

#No validation set when training on all the data,so we cant monitor validation accuracy
full_model_early_stopping=tf.keras.callbacks.EarlyStopping(monitor="accuracy",patience=3)

"""Running the cell below will take a little while(maybe upto 30 minutes for the first epoch) because the GPU we are using in the runtime has to load all of the images into memory."""

#Fit the full model to the full data
full_model.fit(x=full_data,
               epochs=NUM_EPOCHS,
               callbacks=[full_model_tensorboard,full_model_early_stopping])

save_model(full_model,suffix="full-image-set-mobilenetv2-Adam")      #17 epochs

#Load in the full model
import tensorflow as tf
import tensorflow_hub as hub

# Define the correct parameters for your model
INPUT_SHAPE = [224, 224, 3]
OUTPUT_SHAPE = 120  # Using 120 classes as determined earlier
MODEL_URL = "https://tfhub.dev/google/imagenet/mobilenet_v2_130_224/feature_vector/4"

# Function to load a model from weights
def load_from_weights(weights_path, input_shape=INPUT_SHAPE, output_shape=OUTPUT_SHAPE, model_url=MODEL_URL):
    print(f"Recreating model architecture and loading weights from: {weights_path}")

    # Create model with same architecture
    inputs = tf.keras.Input(shape=input_shape)

    # Use the hub module in a Lambda layer
    hub_layer = hub.load(model_url)
    x = tf.keras.layers.Lambda(lambda x: hub_layer(x))(inputs)

    # Add classification layer
    outputs = tf.keras.layers.Dense(units=output_shape, activation="softmax")(x)

    # Create the model
    model = tf.keras.Model(inputs=inputs, outputs=outputs)

    # Compile the model
    model.compile(
        loss=tf.keras.losses.CategoricalCrossentropy(),
        optimizer=tf.keras.optimizers.Adam(),
        metrics=["accuracy"]
    )

    # Load weights
    try:
        model.load_weights(weights_path)
        print("Weights loaded successfully!")
    except Exception as e:
        print(f"Error loading weights: {e}")
        return None

    return model

# Now load your full model with the correct path
full_model_weights_path = "drive/MyDrive/Dog_vision/models/20250409-133537-full-image-set-mobilenetv2-Adam.weights.h5"
loaded_full_model = load_from_weights(full_model_weights_path)

# Test the model
if loaded_full_model is not None:
    print("Model loaded successfully and ready to use!")
    # You can now evaluate or make predictions with this model
    # results = loaded_full_model.evaluate(val_data)
    # print(f"Validation loss: {results[0]:.4f}")
    # print(f"Validation accuracy: {results[1]:.4f}")

"""##Making predictions on the test dataset
Since our model has been trained on images in the form of Tensor batches,to make predictions on the test data,we'll have to get it into the same format.

Luckily we created `create_data_batches()` earlier which can take a list of filename as input and conver them into Tensor batches.

To make predictions on the test data,we'll:
* Get the test image filenames
* Convert the filenames into test data batches using "create_date_batches()" and
  setting the test_data parameter to True(since the test data doesn't have labels).
* Make a predictions array by passing the test batches to the predict() method called on our model.
"""

#Load test image filenames
test_path="/content/dog_breed_data/test/"
test_filenames =[test_path + fname for fname in os.listdir(test_path)]
test_filenames[:10]



len(test_filenames)

#Create test data batch
test_data=create_data_batches(test_filenames,test_data=True)

test_data

"""**NOte** Calling `predict()` on our full model and passing it the test data batch will take a long time to run(about an ~1hr)."""

#Make predictions on test data batch using the loaded full model
test_predictions=loaded_full_model.predict(test_data,verbose=1)

#Save predictions (Numpy array)to csv file (for access later)
np.savetxt("/content/drive/MyDrive/Dog_vision/preds_array.csv",test_predictions,delimiter=",")

#Load predictions (Numpy array) from csv file

test_predictions=np.loadtxt("/content/drive/MyDrive/Dog_vision/preds_array.csv",delimiter=",")

test_predictions[:10]

test_predictions.shape

"""##Preparing the test dataset predictions for kaggle

Looking at the kaggle sample submission,we find that it wants our model prediction probability outputs in a DataFrame with an ID and a column for each different dog breed.

https://www.kaggle.com/c/dog-breed-identification/overview/evaluation

To get the data in this format,we'll:
*Create a pandas DataFrame with an ID column as well as acolumn for each dog breed

*Add data to the ID column as well as a column for each dog breed.

*Add data(the prediction probabilities) to each of the dog breed columns.

*Export the DataFrame as a CSV to submit it to kaggle.
"""

#Create a pandas DataFrame with empty columns
preds_df=pd.DataFrame(columns=["id"] + list(unique_breeds))

preds_df.head()

#Appennd test image ID's to prediction DataFrame
test_ids=[os.path.splitext(path)[0] for path in os.listdir(test_path)]
preds_df["id"]=test_ids

preds_df.head()

#add the prediction probabilities to each dog breed column
preds_df[list(unique_breeds)]=test_predictions
preds_df.head()

#Save our prediction dataframe to CSV for submission to kaggle
preds_df.to_csv("drive/MyDrive/Dog_vision/full_model_predictions_submission_1_mobilenetv2.csv",index=False)

"""##Making predictions on custom images
To make predictions on custom images,we'll:

* Get the filepaths of our own images.

* Turn the filepaths into data batches using `create_data_batches()`.And since our custom images won't have labels, we set the `test_data` parameter to `True`.

* Pass the custom image data batch to our model's `predict()` method.

* Convert the prediction output probabilities to predictions labels.

* Compare the predicted labels to the custom images.
"""

#Get custom image filepaths
custom_path="drive/MyDrive/Dog_vision/my-dog-photos/"
custom_image_paths=[custom_path + fname for fname in os.listdir(custom_path)]

custom_image_paths

#Turn Custom images into batch datasets
custom_data=create_data_batches(custom_image_paths,test_data=True)
custom_data

#Make predictions on the custom data
custom_preds=loaded_full_model.predict(custom_data)

custom_preds.shape

#Get custom image prediction label(s
custom_pred_labels=[get_pred_label(custom_preds[i]) for i in range (len(custom_preds)) ]
custom_pred_labels



#Get custom images (Our unbatchify() function won't work since ther aren't labels...)
custom_images=[]
#Loop through unbatched data
for image in custom_data.unbatch().as_numpy_iterator():
  custom_images.append(image)

#Check custom image predictions
plt.figure(figsize=(10,10))
for i,image in enumerate(custom_images):
  plt.subplot(1,4,i+1)
  plt.xticks([])
  plt.yticks([])
  plt.title(custom_pred_labels[i])
  plt.imshow(image)

