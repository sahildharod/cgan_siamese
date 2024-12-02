# -*- coding: utf-8 -*-
"""EE782_Q1.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/15DA6S5e8px988Fs0g-xxtXJAbm4bJ9gk
"""

## Mounting the google drive on the Colab environment
from google.colab import drive
drive.mount('/content/drive', force_remount=True)

## Importing necessary libraries and modules
import os
import random
import shutil
import tarfile
import itertools

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

import torch
import torch.nn as nn
import torch.nn.functional as F
from torch import optim
from torch.utils.data import Dataset
from torch.utils.data import DataLoader
from torch.optim.lr_scheduler import ExponentialLR
from torch.optim.lr_scheduler import CosineAnnealingLR
from torchvision import transforms
from PIL import Image

## Checking if GPU is available
if torch.cuda.is_available():
    gpu = torch.cuda.get_device_name(0)
    print(f"GPU: {gpu}")
else:
    print("No GPU available.")

## Initializing the path of the zipped file
file_path = '/content/drive/My Drive/lfw.tgz'

## Creating a new directory to extract the images
extraction_dir = '/content/drive/My Drive/Assignment2_Data'

## Extracting the zipped file to the desired location using tarfile
with tarfile.open(file_path, 'r:gz') as tar:
  tar.extractall(path = extraction_dir)

## Randomly shuffling the subdirectories i.e. folders of images before splitting into train/val/test
random.seed(2023)

data_path = '/content/drive/My Drive/Assignment2_Data/lfw'
subdirectories = [d for d in os.listdir(data_path) if os.path.isdir(os.path.join(data_path,d))]

random.shuffle(subdirectories)

## Pre-defining the train/val/test split ratio
train_ratio = 0.7
val_ratio = 0.15
test_ratio = 0.15

## Calculating the number of directories in each of the split
num_train_dirs = int(len(subdirectories) * train_ratio)
num_val_dirs = int(len(subdirectories) * val_ratio)

## Making new directories for all three splits where the corresponding folders will be stored
train_dir = '/content/drive/My Drive/Assignment2_Data/train'
val_dir = '/content/drive/My Drive/Assignment2_Data/val'
test_dir = '/content/drive/My Drive/Assignment2_Data/test'

os.makedirs(train_dir, exist_ok=True)
os.makedirs(val_dir, exist_ok=True)
os.makedirs(test_dir, exist_ok=True)

## Iterating over the subdirectories and moving them from the 'lfw' folder to the respective destination as number of directories for each split using shutil
for i, subdir in enumerate(subdirectories):
  src = os.path.join(data_path,subdir)
  if i < num_train_dirs:
    dest = os.path.join(train_dir, subdir)
  elif num_train_dirs <= i < num_train_dirs + num_val_dirs:
    dest = os.path.join(val_dir, subdir)
  else:
    dest = os.path.join(test_dir, subdir)
  shutil.move(src,dest)

## For simplicity, creating a dictionary with keys as the folders/celebs and values as paths of all the images in that folder
def create_dict(data_path):
  celeb_img_dict = {}
  ## Iterating over all folders
  for dir in os.listdir(data_path):
    folder_path = os.path.join(data_path,dir)
    ## Adding all directories in that folder as a value to the key(folder)
    celeb_img_dict[dir] = [os.path.join(folder_path,d) for d in os.listdir(folder_path)]
  return celeb_img_dict

## Creating the corresponding dictionary for training pairs
celeb_img_dict = create_dict('/content/drive/My Drive/Assignment2_Data/train')

## Creating positive pairs (of the same person)
## Defining a upper threshold on the number of positive pairs to keep the size of the training data appropriate for training
def create_positive_pairs(celeb_img_dict, max_pairs_per_person):
  positive_pairs = []
  ## Iterating over folders and all the image paths for that folder
  for keys, image_paths in celeb_img_dict.items():
    ## Considering only those folders which have more than one image (Atleast 2 images required to make positive pairs)
    if (len(image_paths) > 1) :
      ## Using the combinations function to create all unique pairs of the image paths
      pairs = list(itertools.combinations(image_paths,2))
      random.seed(2023)
      ## Randomly selecting 'max_pairs_per_person' pairs for each folder
      sampled_pairs = random.sample(pairs, min(max_pairs_per_person, len(pairs)))
      positive_pairs.extend(sampled_pairs)
  ## Adding a label (target) = 1 for each pair
  positive_pairs_with_labels = [(pair[0], pair[1], 1) for pair in positive_pairs]
  return positive_pairs_with_labels

## Creating negative pairs (of different persons)
def create_negative_pairs(celeb_img_dict, negative_pairs_per_person):
  random.seed(2023)
  negative_pairs = []
  ## Iterating over folders and all the image paths for that folder
  for person, image_paths in celeb_img_dict.items():
    ## Performing the same operation 'negative_pairs_per_person' number of times
    for _ in range(negative_pairs_per_person):
      while True:
        ## Selecting a random folder that is not the folder we're iterating over (different person)
        random_person = random.choice(list(celeb_img_dict.keys()))
        if (random_person != person):
          break
      ## Selecting a random image from that chose folder
      random_person_image = random.choice(celeb_img_dict[random_person])
      person_image = random.choice(image_paths)
      ## Creating a list of negative pairs with label 0
      negative_pairs.append([person_image, random_person_image,0])
  return negative_pairs

## Creating a dataframe with both negative and positive pairs
def create_dataframe(negative_pairs, positive_pairs):
  negative_pairs_data = pd.DataFrame(negative_pairs, columns=['img1_path', 'img2_path', 'target'])
  positive_pairs_data = pd.DataFrame(positive_pairs, columns=['img1_path', 'img2_path', 'target'])
  df = pd.concat([negative_pairs_data, positive_pairs_data], ignore_index=True)
  return df

## Applying all the defined functions to the training data
positive_pairs = create_positive_pairs(celeb_img_dict,5)
negative_pairs = create_negative_pairs(celeb_img_dict,3)
df = create_dataframe(negative_pairs, positive_pairs)
display(df)

## Applying all the defined functions to the validation data
celeb_img_dict_val = create_dict('/content/drive/My Drive/Assignment2_Data/val')
positive_pairs_val = create_positive_pairs(celeb_img_dict_val,5)
negative_pairs_val = create_negative_pairs(celeb_img_dict_val,3)
df_val = create_dataframe(negative_pairs_val, positive_pairs_val)
display(df_val)

## Applying all the defined functions to the test data
celeb_img_dict_test = create_dict('/content/drive/My Drive/Assignment2_Data/test')
positive_pairs_test = create_positive_pairs(celeb_img_dict_test,5)
negative_pairs_test = create_negative_pairs(celeb_img_dict_test,3)
df_test = create_dataframe(negative_pairs_test, positive_pairs_test)
## Extracting targets to be used while testing
targets = df_test['target'].tolist()
display(df_test)

## Creating a class for making a custom dataset which takes the created Dataframe as the input
class CustomDataset(Dataset):
  ## Initializing the dataframe
  def __init__(self, data):
    self.data = data

  ## Range of indices for the DataLoader is equal to the length of the dataset
  def __len__(self):
    return len(self.data)

  ## Returning the image at the required index
  def __getitem__(self,idx):

    ## Extracting the image using PIL from the path at the given index in the DataFrame
    img1_path = self.data.iloc[idx][0]
    img2_path = self.data.iloc[idx][1]
    target = self.data.iloc[idx][2]

    img1 = Image.open(img1_path)
    img2 = Image.open(img2_path)

    ## Processing the image using transforms like resize, center-crop and normalization
    preprocess = transforms.Compose([
      transforms.Resize(256),
      transforms.CenterCrop(224),
      transforms.ToTensor(),
      transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
    ])

    ## Applying the transforms to the image and returning it as a tensor
    img1 = preprocess(img1)
    img2 = preprocess(img2)
    output = torch.tensor(target)

    return img1,img2,output

## Augmenting the images : Using horizontal flip, color and contrast enhancement
augmentation_transform = transforms.Compose([
  transforms.RandomHorizontalFlip(1),
  transforms.ColorJitter(brightness = 0.1, contrast = 0.5, saturation = 0.5, hue = 0.2),
  transforms.Resize(224)
])

## Creating the dataset suitable for training using the DataLoader class
train_data = CustomDataset(data = df)
train_dataloader = DataLoader(train_data, batch_size = 32 , shuffle = True)

## Creating validation data in a similar manner
val_data = CustomDataset(data = df_val)
val_dataloader = DataLoader(val_data, batch_size = 32 , shuffle = True)

## Defining the Siamese Netowrk class
class SiameseNetwork(nn.Module):
  def __init__(self):
    super(SiameseNetwork,self).__init__()

    ## Using the pretrained resnet18 model from pytorchvision
    self.model = torch.hub.load('pytorch/vision:v0.10.0', 'resnet18', pretrained=True)
    ## Dimension of features in the last layers before passing the image features through the fully connected layer
    self.fc_in_features = self.model.fc.in_features
    ## Removing the last layer which was meant for classification
    self.model = nn.Sequential(*list(self.model.children())[:-1])

    ## Setting requires.grad = True for all the resnet parameters as we dont backprop the gradients through them
    for param in self.model.parameters():
      param.requires_grad = False

    ## Defining a fully connected layer on top of the resnet architecture
    self.fc = nn.Sequential(
        nn.Linear(self.fc_in_features, 128),
        nn.ReLU(inplace = True),
        nn.Linear(128,64),
    )

  ## Defining the forward pass for one image
  def forward_once(self,x):
    x = self.model(x)
    x = x.view(x.size(0), self.fc_in_features)
    x = self.fc(x)
    return x

  ## Performing the forward pass on both the images and returning the output features
  def forward(self,img1,img2):
    out1 = self.forward_once(img1)
    out2 = self.forward_once(img2)
    return out1,out2

  ## Defining the regularization loss (w^2) for parameters of the fully connected layers
  def regularization_loss(self, hyper):
    loss = 0
    for param in self.fc.parameters():
      loss += torch.sum(param**2)
    return 0.5*hyper*loss

## Defining the contrastive loss which tries to bring the positive pairs closer and negative pairs farther in the latent space
class ContrastiveLoss(nn.Module):
  def __init__(self,margin):
    super(ContrastiveLoss, self).__init__()
    self.margin = margin

  ## Compuute the euclidean distance between both outputs
  def forward(self, out1, out2, label):
    euclidean_dist = torch.norm(out1 - out2, dim = 1, p = 2)
    euclidean_dist = euclidean_dist.view(euclidean_dist.size(0), 1)

    ## Define the contrastive loss with a standard margin of 2.0 and normalize it by the latent space dimension
    contrastive_loss =  0.5*label*(torch.pow(euclidean_dist,2)) + 0.5*(1 - label)*torch.pow(torch.clamp(self.margin - euclidean_dist, min = 0.0),2)
    total_loss = torch.sum(contrastive_loss)/64
    return total_loss

## Creating an object of the model and the criterion
net = SiameseNetwork().cuda()
criterion = ContrastiveLoss(2.0)

## Defining the training loop
def train(num_epochs, train_dataloader, val_dataloader, model, hyper):

  ## Iterating over number of epochs
  for epoch in range(num_epochs):
    ## Initializing train and val loss after every epoch
    train_loss = 0
    val_loss = 0
    ## Storing training losses in a list for plotting
    losses = []

    ## Setting the model to training mode
    model.train()

    for img1, img2, labels in train_dataloader:

      ## Moving the images to GPU
      img1, img2, labels = img1.cuda(), img2.cuda(), labels.cuda()

      ## Performing augmentations in every even epoch upon a random sample of 25% of the samples in a batch
      if(epoch % 2 == 0):
        num_augmented = int(0.25*len(img1))
        random_indices = random.sample(range(len(img1)), num_augmented)
        img1[random_indices] = augmentation_transform(img1[random_indices])
        img2[random_indices] = augmentation_transform(img2[random_indices])


      optimizer.zero_grad()
      ## Performing the forward and backward passes
      out1, out2 = model.forward(img1,img2)
      loss = criterion.forward(out1,out2,labels)
      train_loss += loss.item()
      loss += model.regularization_loss(hyper)
      loss.backward()
      ## Updating the parameters and changing the adaptive learning rates
      optimizer.step()

    ## Taking a step of the learning rate scheduler
    scheduler.step()
    ## Setting the model to evaluation mode
    model.eval()

    ## Iterating over all images in the val dataloader
    for img1, img2, labels in val_dataloader:
      ## Performing forward pass and computing the validations loss
      img1, img2, labels = img1.cuda(), img2.cuda(), labels.cuda()
      out1, out2 = model.forward(img1,img2)
      loss = criterion.forward(out1,out2,labels)
      val_loss += loss

    ## Computing the average training and validation loss over a batch
    avg_train_loss = train_loss/len(train_dataloader)
    avg_val_loss = val_loss/len(val_dataloader)

    ## Add the training loss to the defined list
    losses.append(avg_train_loss)

    ## Displaying the training progress (training and validation loss) after every epoch
    print(f"Epoch [{epoch+1}/{num_epochs}], Train Loss: {avg_train_loss}")
    print(f"Epoch [{epoch+1}/{num_epochs}], Validation Loss: {avg_val_loss}")
    print("============================================")

  return losses

## Defining the test function
def test(df, model, targets, threshold):
  ## Setting the model to evaluation mode
  model.eval()
  predictions = []
  eu = []
  ## Extracting the image paths from the dataframe and opening the images using PIL
  for i in df.index:
    img1_path = df.iloc[i][0]
    img2_path = df.iloc[i][1]
    label = df.iloc[i][2]

    img1 = Image.open(img1_path)
    img2 = Image.open(img2_path)

    ## Applying transformations to the images
    preprocess = transforms.Compose([
      transforms.Resize(256),
      transforms.CenterCrop(224),
      transforms.ToTensor(),
      transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
    ])

    img1 = preprocess(img1)
    img1 = img1.unsqueeze(0)
    img2 = preprocess(img2)
    img2 = img2.unsqueeze(0)

    ## Performing the forward pass and computing the euclidean distance between the two image features
    img1, img2 = img1.cuda(), img2.cuda()
    out1, out2 = model.forward(img1,img2)

    euclidean_dist = torch.norm(out1 - out2, dim = 1, p = 2)

    eu.append(euclidean_dist)
    ## Applying the threshold on the euclidean distance to predict whether the images are similar or dissimilar
    ## The threshold of 1.0 was obtained by performing hyperparameter tuning on the validation set
    if(euclidean_dist < threshold):
      predictions.append(1)
    else:
      predictions.append(0)
  ## Computing the accuracy using the targets and the predictions
  correct = sum(1 for t, p in zip(targets, predictions) if t == p)
  accuracy = correct / len(targets)
  return predictions,eu,accuracy

"""I used 2 pairs of optimizers : Adam and SGD and 2 pairs of Learning Rate Schedulers : Exponential LR Scheduler and Cosine Annealing LR Scheduler and thus trained 4 different models to observe the effect of various pairs of schedulers and optimizers"""

## Defining the scheduler and optimizer and performing the training
optimizer = optim.Adam(net.parameters(), lr = 0.001)
scheduler = CosineAnnealingLR(optimizer, T_max = 10, eta_min=0.0001)
adam_cosine_loss = train(num_epochs = 10 ,train_dataloader = train_dataloader,val_dataloader = val_dataloader,model = net, hyper = 0.01)

## Computing the test accuracy for this model
predictions,eu,accuracy = test(df_test, net, targets, threshold = 1)
adam_cosine_acc = accuracy

print(adam_cosine_acc)

## Using another pair of optimizer and scheduler and training the model again
model2 = SiameseNetwork().cuda()
criterion = ContrastiveLoss(2.0)
optimizer = optim.Adam(net.parameters(), lr = 0.001)
scheduler = ExponentialLR(optimizer, gamma=0.9)
adam_exp_loss = train(num_epochs = 10 ,train_dataloader = train_dataloader,val_dataloader = val_dataloader,model = model2, hyper = 0.01)

## Computing the test accuracy for this model
predictions,eu,accuracy = test(df_test, model2, targets, threshold = 1)
adam_exp_acc = accuracy
print(adam_exp_acc)

## Using another pair of optimizer and scheduler and training the model again
model3 = SiameseNetwork().cuda()
criterion = ContrastiveLoss(2.0)
optimizer = optim.SGD(net.parameters(), lr = 0.01, momentum = 0.75, dampening = 0.1, weight_decay = 0, nesterov = False)
scheduler = CosineAnnealingLR(optimizer, T_max = 10, eta_min=0.0001)
sgd_cosine_loss = train(num_epochs = 8 ,train_dataloader = train_dataloader,val_dataloader = val_dataloader,model = model3, hyper = 0.01)

## Computing the test accuracy for this model
predictions,eu,accuracy = test(df_test, model3, targets, threshold = 1)
sgd_cosine_acc = accuracy
print(sgd_cosine_acc)

## Using another pair of optimizer and scheduler and training the model again
model4 = SiameseNetwork().cuda()
criterion = ContrastiveLoss(2.0)
optimizer = optim.SGD(net.parameters(), lr = 0.01, momentum = 0.75, dampening = 0.1, weight_decay = 0, nesterov = False)
scheduler = ExponentialLR(optimizer, gamma=0.9)
sgd_exp_loss = train(num_epochs = 8 ,train_dataloader = train_dataloader,val_dataloader = val_dataloader,model = model4, hyper = 0.01)

## Computing the test accuracy for this model
predictions,eu,accuracy = test(df_test, model4, targets, threshold = 1)
sgd_exp_acc = accuracy
print(sgd_exp_acc)

adam_cosine_loss = [6.549044225700746,6.896730341001627, 6.661356311174309, 6.487543432217724, 6.362525560071133, 6.233699110818859,6.154107312736271, 6.005896743738426]
adam_exp_loss = [5.817670135378088, 5.717049250062907, 5.682052050246632, 5.594239547067718, 5.618351066637339, 5.544408654266933, 5.580662727355957, 5.518635765811433]
sgd_cosine_loss = [5.915101704107641, 5.867130219561499, 5.9188657061858745, 5.852863439723881, 5.921084382998869, 5.869961805563553, 5.912083809730642, 5.863573856073855]
sgd_exp_loss = [5.80592845021054, 5.803733898658672, 5.796491521959285, 5.805175493848149, 5.798778964788409, 5.8040576910822645, 5.810621212363493, 5.803967202234568]

# Define the x-axis (e.g., epochs)
epochs = range(1, 9)

# Plot the training losses for each model
plt.figure(figsize=(10, 6))
plt.plot(epochs, adam_exp_loss, label='Adam and ExponentialLR', marker='o')
plt.plot(epochs, adam_cosine_loss, label='Adam and CosineAnnealingLR', marker='o')
plt.plot(epochs, sgd_exp_loss, label='SGD and ExponentialLR', marker='o')
plt.plot(epochs, sgd_cosine_loss, label='SGD and CosineAnnealingLR', marker='o')

# Add labels and legend
plt.xlabel('Epochs')
plt.ylabel('Training Loss')
plt.title('Training Loss for Different Models')
plt.legend()

# Show the plot
plt.grid()
plt.show()

"""We see that while using the SGD optimizer the loss doesnt change much, this could occur when the loss function fails to converge or the convergence process is stuck at a saddle point, on the other side Adam Optimizer (which updates the weights adaptively) combined with both the CosineAnnealingLR and ExponentialLR works pretty well and we see the training decreasing consistenly as we increase the number of epochs. Among these pairs we can conclude that Adam optimizer coupled with CosineAnnealingLR works the best (Initial instability is due high initial learning rate)"""

## Testing on faces of friends
## Loading images of myself and my friend
my_img1 = Image.open('/content/drive/My Drive/SAHIL1 (1).jpg')
plt.imshow(my_img1)
plt.show()
my_img2 = Image.open('/content/drive/My Drive/Photograph-min.jpg')
plt.imshow(my_img2)
plt.show()
friend_img1 = Image.open('/content/drive/My Drive/pratham.jpg')
plt.imshow(friend_img1)
plt.show()

## Preprocessing the images in a similar manner
preprocess = transforms.Compose([
      transforms.Resize(256),
      transforms.CenterCrop(224),
      transforms.ToTensor(),
      transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
])

## Unsqueezing to add the batch dimension before the forward pass
my_img1 = preprocess(my_img1)
my_img1 = my_img1.unsqueeze(0)
my_img2 = preprocess(my_img2)
my_img2 = my_img2.unsqueeze(0)
friend_img1 = preprocess(friend_img1)
friend_img1 = friend_img1.unsqueeze(0)

## Computing the forward pass and comparing the euclidean distance of the features in both cases
my_img1, my_img2, friend_img1 = my_img1.cuda(), my_img2.cuda(), friend_img1.cuda()
out1, out2 = net.forward(my_img1,my_img2)
eu1 = torch.norm(out1 - out2, dim = 1, p = 2)

out1, out2 = net.forward(my_img1,friend_img1)
eu2 = torch.norm(out1 - out2, dim = 1, p = 2)

print(eu1)
print(eu2)

"""As we can see for similar faces the similarity score is very close to 1 (slightly higher mostly because of the dominant blue background), but for different images the euclidean distance is much greater than similar images"""