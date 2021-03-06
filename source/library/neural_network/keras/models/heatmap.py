import keras.models as km
import keras.layers as kl


def simple_model(channels=3, weight_decay=None):
    model = km.Sequential()
    model.add(kl.Conv2D(input_shape=(None, None, channels), filters=32, kernel_size=[3, 3], padding='same'))
    model.add(kl.Activation('relu'))
    model.add(kl.Conv2D(filters=64, kernel_size=[3, 3], padding='same', activation='relu',
                        kernel_regularizer=weight_decay))
    model.add(kl.Conv2D(filters=128, kernel_size=[3, 3], padding='same', activation='relu',
                        kernel_regularizer=weight_decay))
    model.add(kl.Conv2D(filters=256, kernel_size=[3, 3], padding='same', activation='relu',
                        kernel_regularizer=weight_decay))
    model.add(kl.Conv2D(filters=128, kernel_size=[3, 3], padding='same', activation='relu',
                        kernel_regularizer=weight_decay))
    model.add(kl.Conv2D(filters=64, kernel_size=[3, 3], padding='same', activation='relu',
                        kernel_regularizer=weight_decay))
    model.add(kl.MaxPooling2D())
    model.add(kl.Conv2D(filters=16, kernel_size=[3, 3], padding='same', activation='relu',
                        kernel_regularizer=weight_decay))
    model.add(kl.MaxPooling2D())
    model.add(kl.Conv2D(filters=1, kernel_size=[3, 3], padding='same', kernel_regularizer=weight_decay))
    # model.add(Softmax4D(axis=1, name='softmax4D'))
    model.add(kl.Activation('sigmoid'))

    return model


def simple_model2(channels=3, weight_decay=None):
    model = km.Sequential()
    model.add(kl.Conv2D(input_shape=(None, None, channels), filters=32, kernel_size=[3, 3], padding='same'))
    model.add(kl.Activation('relu'))
    model.add(kl.Conv2D(filters=64, kernel_size=[3, 3], padding='same', activation='relu',
                        kernel_regularizer=weight_decay))
    model.add(kl.Conv2D(filters=128, kernel_size=[3, 3], padding='same', activation='relu',
                        kernel_regularizer=weight_decay))
    model.add(kl.Conv2D(filters=256, kernel_size=[3, 3], padding='same', activation='relu',
                        kernel_regularizer=weight_decay))
    model.add(kl.Conv2D(filters=128, kernel_size=[3, 3], padding='same', activation='relu',
                        kernel_regularizer=weight_decay))
    model.add(kl.Conv2D(filters=64, kernel_size=[3, 3], padding='same', activation='relu',
                        kernel_regularizer=weight_decay))
    model.add(kl.MaxPooling2D())
    model.add(kl.Conv2D(filters=16, kernel_size=[3, 3], padding='same', activation='relu',
                        kernel_regularizer=weight_decay))
    model.add(kl.MaxPooling2D())
    model.add(kl.Conv2D(filters=1, kernel_size=[3, 3], padding='same', kernel_regularizer=weight_decay))
    # model.add(Softmax4D(axis=1, name='softmax4D'))
    model.add(kl.Activation('sigmoid'))

    return model


def high_fov_model(channels=3, weight_decay=None):
    model = km.Sequential()
    model.add(kl.Conv2D(input_shape=(None, None, channels), filters=32, kernel_size=[5, 5], padding='same'))
    model.add(kl.Activation('relu'))
    # FOV: 5
    model.add(kl.Conv2D(filters=64, kernel_size=[5, 5], padding='same', activation='relu',
                        kernel_regularizer=weight_decay))
    # FOV: 9
    model.add(kl.Conv2D(filters=128, kernel_size=[3, 3], padding='same', activation='relu',
                        kernel_regularizer=weight_decay))
    # FOV: 11
    model.add(kl.Conv2D(filters=128, kernel_size=[3, 3], padding='same', activation='relu',
                        kernel_regularizer=weight_decay))
    # FOV: 13
    model.add(kl.MaxPooling2D())
    # FOV: 26
    model.add(kl.Conv2D(filters=128, kernel_size=[3, 3], padding='same', activation='relu',
                        kernel_regularizer=weight_decay))
    # FOV: 30
    model.add(kl.Conv2D(filters=128, kernel_size=[3, 3], padding='same', activation='relu',
                        kernel_regularizer=weight_decay))
    # FOV: 34
    model.add(kl.Conv2D(filters=128, kernel_size=[3, 3], padding='same', activation='relu',
                        kernel_regularizer=weight_decay))
    # FOV: 38
    model.add(kl.MaxPooling2D())
    # FOV: 76

    model.add(kl.Conv2D(filters=64, kernel_size=[3, 3], padding='same', activation='relu',
                        kernel_regularizer=weight_decay))
    # FOV: 84
    model.add(kl.Conv2D(filters=32, kernel_size=[3, 3], padding='same', activation='relu',
                        kernel_regularizer=weight_decay))
    # FOV: 92
    model.add(kl.Conv2D(filters=1, kernel_size=[3, 3], padding='same', kernel_regularizer=weight_decay))
    # model.add(Softmax4D(axis=1, name='softmax4D'))
    model.add(kl.Activation('sigmoid'))
    # FOV: 100

    return model


def incremental_predictor_1(channels=4, weight_decay=None, name='incremental_predictor_1'):
    model = km.Sequential(name=name)
    model.add(kl.Conv2D(input_shape=(None, None, channels), filters=64, kernel_size=[5, 5], padding='same'))
    model.add(kl.Activation('relu'))
    model.add(kl.Conv2D(filters=128, kernel_size=[5, 5], padding='same', activation='relu',
                        kernel_regularizer=weight_decay))
    model.add(kl.Conv2D(filters=256, kernel_size=[5, 5], padding='same', activation='relu',
                        kernel_regularizer=weight_decay))
    model.add(kl.MaxPooling2D())
    model.add(kl.Conv2D(filters=128, kernel_size=[3, 3], padding='same', activation='relu',
                        kernel_regularizer=weight_decay))
    model.add(kl.Conv2D(filters=128, kernel_size=[3, 3], padding='same', activation='relu',
                        kernel_regularizer=weight_decay))
    model.add(kl.Conv2D(filters=256, kernel_size=[5, 5], padding='same', activation='relu',
                        kernel_regularizer=weight_decay))
    model.add(kl.MaxPooling2D())
    model.add(kl.Conv2D(filters=128, kernel_size=[3, 3], padding='same', activation='relu',
                        kernel_regularizer=weight_decay))
    model.add(kl.Conv2D(filters=64, kernel_size=[3, 3], padding='same', activation='relu',
                        kernel_regularizer=weight_decay))
    model.add(kl.Conv2D(filters=32, kernel_size=[3, 3], padding='same', activation='relu',
                        kernel_regularizer=weight_decay))
    model.add(kl.Conv2D(filters=1, kernel_size=[3, 3], padding='same', kernel_regularizer=weight_decay))
    model.add(kl.Activation('sigmoid'))

    return model
