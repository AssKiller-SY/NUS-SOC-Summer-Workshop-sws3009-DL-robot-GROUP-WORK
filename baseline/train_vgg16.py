from tensorflow.keras.applications import VGG16
from tensorflow.keras.preprocessing import image
from tensorflow.keras.models import Model, load_model
from tensorflow.keras.callbacks import ModelCheckpoint, EarlyStopping
from tensorflow.keras.layers import Dense, GlobalAveragePooling2D, Flatten
from tensorflow.keras.preprocessing.image import ImageDataGenerator
from tensorflow.keras.optimizers import SGD

import os.path

MODEL_FILE = "cats.hd5"

def create_model(num_hidden, num_classes):
    base_model = VGG16(include_top=False, weights='imagenet') 
    x = base_model.output
    x = GlobalAveragePooling2D()(x)  
    x = Dense(num_hidden, activation='relu')(x)
    predictions = Dense(num_classes, activation='softmax')(x)

    model = Model(inputs=base_model.input, outputs=predictions)
    
    
    for layer in base_model.layers:
        layer.trainable = False
    
    return model

def train(model_file, train_path, validation_path, num_hidden=10, num_classes=5, num_epochs=100, save_period=1):
    print("\n***Creating new model ***\n\n")
    model = create_model(num_hidden, num_classes)
    
    checkpoint = ModelCheckpoint(model_file, monitor='val_accuracy', save_best_only=True, mode='max')

    train_datagen = ImageDataGenerator(rescale=1./255, shear_range=0.2, zoom_range=0.2, horizontal_flip=True)
    test_datagen = ImageDataGenerator(rescale=1./255)

    train_generator = train_datagen.flow_from_directory(train_path, target_size=(249, 249), batch_size=32, class_mode="categorical")
    validation_generator = test_datagen.flow_from_directory(validation_path, target_size=(249, 249), batch_size=32, class_mode='categorical')

    steps_per_epoch = len(train_generator)
    validation_steps = len(validation_generator)

    model.compile(optimizer=SGD(learning_rate=0.0002, momentum=0.9), loss='categorical_crossentropy', metrics=['accuracy'])
    
    model.fit(
        train_generator,
        steps_per_epoch=steps_per_epoch,
        epochs=num_epochs,
        callbacks=checkpoint,
        validation_data=validation_generator,
        validation_steps=validation_steps,
        verbose=1  
    )

def main():
    train(MODEL_FILE, train_path="/content/drive/MyDrive/pro/Data/cat/train", validation_path="/content/drive/MyDrive/pro/Data/cat/validation")

if __name__ == "__main__":
    main()
