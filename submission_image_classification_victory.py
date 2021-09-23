# -*- coding: utf-8 -*-
"""Submission - Image Classification - Victory

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1cIYaGs18kSXhlCsw1CKq7_B4uEJ5F4UP

<h2><b>Nama : Victory Herawidatama Esa Putra</b></h2>
<h3><b> Email : 18101105@ittelkom-pwt.ac.id </b></h3>

**Install library kaggle dikarenakan menggunakan dataset dari kaggle yang sudah di split train 80 dan test 20**
<p><b>Link dataset : https://www.kaggle.com/puneet6060/intel-image-classification/ </b></p>
<p><b>Dan membuat fungsi upload untuk api kaggle.json nantinya</b></p>
"""

!pip install -q kaggle
from google.colab import files
files.upload()

"""**Proses membuat directory untuk menampung file kaggle.json pada server**"""

! mkdir ~/.kaggle
! cp kaggle.json ~/.kaggle/
! chmod 600 ~/.kaggle/kaggle.json
! kaggle datasets list  #Test koneksi kaggle dari google colab

"""**Proses Download dataset dari kaggle**"""

! kaggle datasets download -d puneet6060/intel-image-classification

"""**Import semua libraries yang dibutuhkan untuk proses classification**"""

import tensorflow as tf
from tensorflow import keras
from tensorflow.keras.preprocessing.image import ImageDataGenerator
from tensorflow.keras import layers
from tensorflow.keras.callbacks import EarlyStopping
from keras.preprocessing import image
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
import numpy as np
import zipfile,os
import pandas as pd
!pip install seedir #Instalasi seeder treeview
import seedir as sd

"""**Buat directory 'data' untuk unzip file dataset yang sebelumnya sudah didownload**"""

! mkdir data
! unzip intel-image-classification.zip -d data

"""**Mendeklarasikan target directory yang akan diproses**"""

target_dir = '/content/data'

"""**Implementasi penggunaan seedir untuk treeview**"""

sd.seedir(target_dir, style='lines', itemlimit=4, depthlimit=3)

"""**Untuk mempercepat proses modelling hanya akan memanfaatkan 5 klasifikasi yaitu buildings, forest, mountain, sea, dan street**
<p><b>Maka harus menghapus klasifikasi glacier sebelum proses modelling dan proses cek kelas dengan landscape</b></p>
"""

import shutil
shutil.rmtree('/content/data/seg_train/seg_train/glacier', ignore_errors=True)
shutil.rmtree('/content/data/seg_test/seg_test/glacier', ignore_errors=True)

#Cek class folder
landscape_train = os.path.join('/content/data/seg_train/seg_train')
landscape_test = os.path.join('/content/data/seg_test/seg_test')

print(os.listdir(landscape_train))
print(os.listdir(landscape_test))

"""**Proses random image, menggunakan fungsi random 1 image dan random group**
<p><b>Yang nantinya 1 gambar akan dibandingkan dengan beberapa gambar sekaligus yang terdapat pada group</b></p>
"""

import random

#fungsi random 1 image
def one_random(target_path, target_class):
  target_fold = target_path + target_class
  random_image = random.sample(os.listdir(target_fold), 1)
  image = mpimg.imread(target_fold+'/'+random_image[0])
  plt.imshow(image)
  plt.title(target_class)
  plt.axis('off')
  print(f"Image shape {image.shape}")
  return image

#fungsi group random
def group_random(target_path, figure_size=(20,10), group=20):
  plt.figure(figsize=figure_size)
  for i in range(group):
    plt.subplot(4, 5, i+1)
    class_name = random.choice(['buildings', 'forest', 'mountain', 'sea', 'street'])
    image = one_random(target_path=target_path, target_class=class_name)

group_random = group_random(target_path='/content/data/seg_train/seg_train/')

"""**Proses perhitungan dari original dataset dan total setelah train dan validasi set**"""

train_path = '/content/data/seg_train/seg_train/'
test_path = '/content/data/seg_test/seg_test/'
folders_name = ['buildings', 'forest', 'mountain', 'sea', 'street']

train_files = {}
val_files = {}

for i in folders_name:
  train_files[i] = len(os.listdir(train_path+i)) #Cek panjang/banyak data train
  val_files[i] = len(os.listdir(test_path+i)) #Cek panjang/banyak data test

result_split = pd.DataFrame()
result_split = result_split.append(train_files, ignore_index=True)
result_split = result_split.append(val_files, ignore_index=True)
result_split['total'] = result_split.sum(axis=1)
result_split['type'] = ['train', 'val']
result_split = result_split[['type', 'buildings', 'forest', 'mountain', 'sea', 'street', 'total']]
print(result_split)

"""**Mendefinisikan directory untuk menyimpan train dan validation berdasarkan variabel**"""

train_set = '/content/data/seg_train/seg_train/'
val_set = '/content/data/seg_test/seg_test/'

"""**Proses Training dan Augmentasi image, dengan metode rescale, rotation, flip, maupun zoom**"""

train_augmentasi = ImageDataGenerator(
                            rescale=1./255,
                            rotation_range=30,
                            horizontal_flip=True,
                            zoom_range=0.2,
                            shear_range=0.2,
                            fill_mode = 'nearest')
validation_augmentasi = ImageDataGenerator(rescale=1./255)

"""**Train dan Validation data generator menggunakan batchsize dan metode categorical**"""

train_generator = train_augmentasi.flow_from_directory(
        train_set,
        target_size=(150, 150),
        batch_size=128,
        class_mode='categorical')
validation_generator = validation_augmentasi.flow_from_directory(
        val_set,
        target_size=(150, 150),
        batch_size=128,
        class_mode='categorical')

"""**Proses Modelling Sequential**"""

model = keras.Sequential([
      layers.Conv2D(32, (3,3), activation = 'relu', input_shape = (150, 150, 3)),
      layers.MaxPooling2D(pool_size=(2, 2)),
      layers.Conv2D(64,(3,3), activation = 'relu'),
      layers.MaxPooling2D(pool_size=(2,2)),
      layers.Conv2D(128,(3,3), activation='relu'),
      layers.MaxPooling2D(pool_size=(2,2)),
      layers.Flatten(),
      layers.Dropout(0.5),
      layers.Dense(128, activation='relu'),
      layers.Dense(5, activation='softmax')
])

"""**Penggunaan Optimizer adam**"""

model.compile(loss='categorical_crossentropy',
              optimizer='adam',
              metrics=['accuracy'])

"""**Deklarasi Callbacks untuk membatasi akurasi ketika mencapai target**"""

class myCallback(tf.keras.callbacks.Callback):
  def on_epoch_end(self, epoch, logs={}):
    if(logs.get('val_accuracy') >= 0.85):
      self.model.stop_training = True
      print("\nValidation Accuracy dari model sudah >= 85%")
early_stop = myCallback()

"""**Mulai proses Training Model dengan model.fit**"""

history = model.fit(
    train_generator,
    epochs=40,
    steps_per_epoch=20,
    validation_data=validation_generator,
    verbose=1,
    validation_steps=10,
    callbacks=[early_stop],
)

"""**Plotting Loss**

"""

history_df = pd.DataFrame(history.history)
history_df.loc[1:, ['loss', 'val_loss']].plot()
plt.show()

"""**Plotting Akurasi**"""

history_df.loc[1:, ['accuracy', 'val_accuracy']].plot()
plt.show()

print(("\nBest Validation Loss: {:0.2f})" + "\nBest Validation Accuracy:{:0.2f}").format(history_df['val_loss'].min(), history_df['val_accuracy'].max()))

"""**Proses Konversi ke TFLite dan Download model.tflite**"""

convert = tf.lite.TFLiteConverter.from_keras_model(model)
tflite_model = convert.convert()
with tf.io.gfile.GFile('model.tflite', 'wb') as f:
  f.write(tflite_model)

files.download('model.tflite')