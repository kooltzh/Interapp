from keras.models import load_model
import cv2
from scipy import misc
import numpy as np
import json

class FERModel:
    """
    Pretrained deep learning model for facial expression recognition.

    :param target_emotions: set of target emotions to classify
    :param verbose: if true, will print out extra process information

    **Example**::

        from fermodel import FERModel

        target_emotions = ['happiness', 'disgust', 'surprise']
        model = FERModel(target_emotions, verbose=True)

    """

    POSSIBLE_EMOTIONS = ['anger', 'fear', 'calm', 'sadness', 'happiness', 'surprise', 'disgust']
      

    def __init__(self, target_emotions, cascPath, verbose=False):
        self.target_emotions = target_emotions
        self.emotion_index_map = {
            'anger': 0,
            'disgust': 1,
            'fear': 2,
            'happiness': 3,
            'sadness': 4,
            'surprise': 5,
            'calm': 6
        }
        self._check_emotion_set_is_supported()
        self.verbose = verbose
        self.target_dimensions = (48, 48)
        self.channels = 1
        #file path for face detection
        self.cascPath = cascPath
        # Create the haar cascade
        self.faceCascade = cv2.CascadeClassifier(self.cascPath)
        self._initialize_model()

    def _initialize_model(self):
        print('Initializing FER model parameters for target emotions: %s' % self.target_emotions)
        self.model, self.emotion_map = self._choose_model_from_target_emotions()

    def predict_file(self, image_file):
        """
        Predicts discrete emotion for given image.

        :param images: image file (jpg or png format)
        """
        image = misc.imread(image_file)
        self.predict(image)

    def predict(self, image):
        """
        Predicts discrete emotion for given image.

        :param images: image file (jpg or png format)
        """
        gray_image = image
        #image.shape format height, width, channels, so if exist channels, change to gray
        if len(image.shape) > 2: 
            gray_image = cv2.cvtColor(image, code=cv2.COLOR_BGR2GRAY)
        #capture out the face
        # Equalize the histogram
        cv2.equalizeHist(gray_image, gray_image)
        faces = self.faceCascade.detectMultiScale(
            gray_image,
            scaleFactor=1.1,
            minNeighbors=5,
            minSize=(30, 30)
        )
        
        if len(faces):
            print("Found {0} faces!".format(len(faces)))
            for (x, y, w, h) in faces:
                cropped = gray_image[y:y+h, x:x+w]
                cv2.imshow("Faces cropped", cropped)
                resized_image = cv2.resize(cropped, self.target_dimensions, interpolation=cv2.INTER_LINEAR)
                final_image = np.array([np.array([resized_image]).reshape(list(self.target_dimensions)+[self.channels])])
                prediction = self.model.predict(final_image)
                print(prediction)
                #self._print_prediction(prediction[0])

                #self defined function of output.
                self._self_edit_print_image(gray_image, faces, prediction[0])

    def _check_emotion_set_is_supported(self):
        """
        Validates set of user-supplied target emotions.
        """
        supported_emotion_subsets = [
            set(['anger', 'fear', 'surprise', 'calm']),
            set(['happiness', 'disgust', 'surprise']),
            set(['anger', 'fear', 'surprise']),
            set(['anger', 'fear', 'calm']),
            set(['anger', 'happiness', 'calm']),
            set(['anger', 'fear', 'disgust']),
            set(['calm', 'disgust', 'surprise']),
            set(['sadness', 'disgust', 'surprise']),
            set(['anger', 'happiness'])
        ]
        if not set(self.target_emotions) in supported_emotion_subsets:
            error_string = 'Target emotions must be a supported subset. '
            error_string += 'Choose from one of the following emotion subset: \n'
            possible_subset_string = ''
            for emotion_set in supported_emotion_subsets:
                possible_subset_string += ', '.join(emotion_set)
                possible_subset_string += '\n'
            error_string += possible_subset_string
            raise ValueError(error_string)

    def _choose_model_from_target_emotions(self):
        """
        Initializes pre-trained deep learning model for the set of target emotions supplied by user.
        """
        model_indices = [self.emotion_index_map[emotion] for emotion in self.target_emotions]
        sorted_indices = [str(idx) for idx in sorted(model_indices)]
        model_suffix = ''.join(sorted_indices)
        model_file = './models/conv_model_%s.hdf5' % model_suffix
        emotion_map_file = './models/conv_emotion_map_%s.json' % model_suffix
        emotion_map = json.loads(open(emotion_map_file).read())
        return load_model(model_file), emotion_map

    def _print_prediction(self, prediction):
        normalized_prediction = [x/sum(prediction) for x in prediction]
        for emotion in self.emotion_map.keys():
            print('%s: %.1f%%' % (emotion, normalized_prediction[self.emotion_map[emotion]]*100))
        dominant_emotion_index = np.argmax(prediction)
        for emotion in self.emotion_map.keys():
            if dominant_emotion_index == self.emotion_map[emotion]:
                dominant_emotion = emotion
                break
        print('Dominant emotion: %s' % dominant_emotion)
        print()

        #self written function of put back the emotion to face
    def _self_edit_print_image(self, image, faces, prediction): 
        # Draw a rectangle around the faces
        if len(faces):
            for (x, y, w, h) in faces:
                cv2.rectangle(image, (x, y), (x + w, y + h), (0, 255, 0), 2)

        cv2.imshow("Faces found", image)

        normalized_prediction = [x/sum(prediction) for x in prediction]
        for emotion in self.emotion_map.keys():
            print('%s: %.1f%%' % (emotion, normalized_prediction[self.emotion_map[emotion]]*100))
        dominant_emotion_index = np.argmax(prediction)
        for emotion in self.emotion_map.keys():
            if dominant_emotion_index == self.emotion_map[emotion]:
                dominant_emotion = emotion
                break
        print('Dominant emotion: %s' % dominant_emotion)
        print()
