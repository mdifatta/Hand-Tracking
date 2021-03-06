import keras as K
import keras.callbacks as kc
import keras.optimizers as ko
import traceback

from data import *
from library import *
from library.neural_network.keras.callbacks.generalized_image_writer import ImageWriter
from library.neural_network.keras.callbacks.scalar_writer import ScalarWriter
from library.neural_network.keras.sequence import BatchGenerator
from library.neural_network.tensorboard_interface.tensorboard_manager import TensorBoardManager as TBManager
from library.telegram import telegram_bot as tele
from library.utils.visualization_utils import get_image_with_mask
from library.neural_network.batch_processing.processing_plan import ProcessingPlan


def train_model(model_generator, dataset_manager: DatasetManager, loss,
                tb_path=None, tb_plots=None, model_name=None, model_path=None, data_processing_plan: ProcessingPlan=None,
                learning_rate=1e-3, epochs=50, patience=-1,
                additional_callbacks=None, enable_telegram_log=False, class_weight=None):
    """
    Train a model with all kinds of log services and optimizations we could come up with.
    Clears completely the session at each call to have separated training sessions of different models

    :param model_generator: a function returning an instance of the model to be trained
    :param dataset_manager: the DatasetManager providing access to data. See the DatasetManager doc for more
    :param loss: the loss function to be used. Must conform to the keras convention for losses:
                    - must accept two arguments:
                        1) y_true: the ground truth
                        2) y_pred: the network prediction
                    - must return a value to be minimized
    :param tb_path: the path for the tensorboard logging. Avoids tensorboard logging if None.
                    if a model_name is specified, this is appended to the tb_path automatically.
    :param tb_plots: dictionary of {name: function} to specify what images should be plotted.
                        name: the name suffix in the tensorboard view
                        function: a callable that takes one argument feed:
                                feed: a dictionary containing all the entries of the network
                                      using naming conventions. Available keys:
                                      IN(.)         all network inputs
                                      OUT(.)        all network target outputs
                                      NET_OUT(.)    all network corresponding real outputs
                                any extra key in the data_sequence will be added to feed as well.
    :param model_name: the model name used for saving checkpoints and the final model on file.
    :param model_type: a specification of the type of the model to decide its standard destination directory
    :param data_processing_plan: the processing specification to be applied before feeding data to the network.
                                 See ProcessingPlan doc for more.
    :param learning_rate: The learning rate to use on Adam.
    :param epochs:  The maximum number of epochs to perform.
    :param patience: The early stopping patience. If None, disables early stopping.
    :param additional_callbacks: Any additional callbacks to add to the fitting functoin
    :param enable_telegram_log: if True, enables telegram notifications at start and end of training
    :return: The train model, if early stopping is active this is the best model selected.
    """
    K.backend.clear_session()

    train_data = dataset_manager.train()
    valid_data = dataset_manager.valid()

    model = model_generator()

    if model_name is None or model_path is None:
        checkpoint_path = None
        h5model_path = None
    else:
        if tb_path is not None:
            tb_path = os.path.join(tb_path, model_name)
        checkpoint_path = os.path.join(model_path, model_name+".ckp")
        h5model_path = os.path.join(model_path, model_name+".h5")
    log("Model:", level=COMMENTARY)
    model.summary(print_fn=lambda s: log(s, level=COMMENTARY))

    callbacks = []
    if checkpoint_path is not None:
        log("Adding callback for checkpoint...", level=COMMENTARY)
        callbacks.append(kc.ModelCheckpoint(filepath=checkpoint_path,
                                            monitor='val_loss',
                                            verbose=1,
                                            save_best_only=True,
                                            mode='min',
                                            period=1))
    if patience > 0:
        log("Adding callback for early stopping...", level=COMMENTARY)
        callbacks.append(kc.EarlyStopping(patience=patience,
                                          verbose=1,
                                          monitor='val_loss',
                                          mode='min',
                                          min_delta=2e-4))

    if tb_path is not None:
        TBManager.set_path(tb_path)
        log("Setting up tensorboard...", level=COMMENTARY)
        log("Clearing tensorboard files...", level=COMMENTARY)
        TBManager.clear_data()

        log("Adding tensorboard callbacks...", level=COMMENTARY)
        callbacks.append(ScalarWriter())
        if tb_plots is not None:
            callbacks.append(ImageWriter(data_sequence=train_data,
                                         image_generators=tb_plots,
                                         name='train',
                                         max_items=10))
            callbacks.append(ImageWriter(data_sequence=valid_data,
                                         image_generators=tb_plots,
                                         name='validation',
                                         max_items=10))
    if additional_callbacks is not None:
        callbacks += additional_callbacks

    # Training tools
    optimizer = ko.adam(lr=learning_rate)

    log("Compiling model...", level=COMMENTARY)

    model.compile(optimizer=optimizer,
                  loss=loss,
                  metrics=['accuracy'])

    if enable_telegram_log:
        log('Fitting model...', level=COMMENTARY)
        # Notification for telegram
        try:
            tele.notify_training_starting(model_name=model_name,
                                          training_samples=len(train_data) * dataset_manager.batch_size,
                                          validation_samples=len(valid_data) * dataset_manager.batch_size,
                                          tensorboard="handtracking.eastus.cloudapp.azure.com:6006 if active")
        except Exception:
            traceback.print_exc()

    history = model.fit_generator(generator=BatchGenerator(data_sequence=train_data,
                                                           process_plan=data_processing_plan),
                                  epochs=epochs, verbose=1, callbacks=callbacks,
                                  validation_data=BatchGenerator(data_sequence=valid_data,
                                                                 process_plan=data_processing_plan),
                                  class_weight=class_weight)

    if h5model_path is not None:
        log("Saving H5 model...", level=COMMENTARY)
        model = model_generator()
        model.load_weights(checkpoint_path)
        model.save(h5model_path)
        os.remove(checkpoint_path)

    log("Training completed!", level=COMMENTARY)

    if enable_telegram_log:
        log('Fitting completed!', level=COMMENTARY)
        loss_ = "{:.5f}".format(history.history['loss'][-1])
        valid_loss = "{:.5f}".format(history.history['val_loss'][-1])
        if 'acc' in history.history.keys():
            accuracy = "{:.2f}%".format(100 * history.history['acc'][-1])
        else:
            accuracy = "not available"
        if 'val_acc' in history.history.keys():
            valid_accuracy = "{:.2f}%".format(100 * history.history['val_acc'][-1])
        else:
            valid_accuracy = "not available"
        try:
            tele.notify_training_end(model_name=model_name,
                                     final_loss=str(loss_),
                                     final_validation_loss=str(valid_loss),
                                     final_accuracy=str(accuracy),
                                     final_validation_accuracy=str(valid_accuracy))

            if model_path == croppers_path():
                tele.send_message(message="Training samples:")
                img = train_data[0][IN(0)] * 255
                map_ = model.predict(img)
                tele.send_image_from_array(get_image_with_mask(img[0:5], map_[0:5]))
                tele.send_message(message="Validation samples:")
                img = valid_data[0][IN(0)] * 255
                map_ = model.predict(img)
                tele.send_image_from_array(get_image_with_mask(img[0:5], map_[0:5]))
        except Exception:
            traceback.print_exc()

    return model


