from flask import Flask, request, jsonify
import os
import numpy as np
from tensorflow.keras.preprocessing.image import load_img, img_to_array
from tensorflow.keras.models import load_model

app = Flask(__name__)
UPLOAD_FOLDER = r'D:\Desktop\sws3009\received_image'  
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)


model = load_model(r'D:\Desktop\sws3009\pro\cat.hd5')  

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    if file:
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(filepath)
        
        
        result = classify_image(filepath)
        
        
        os.remove(filepath)
        
        return jsonify({'result': result}), 200

def classify_image(image_path):
    img = load_img(image_path, target_size=(249, 249))
    img_array = img_to_array(img)
    img_array = np.expand_dims(img_array, axis=0)
    img_array = img_array / 255.0 

    print("Start classifying")
    prediction = model.predict(img_array)

    class_idx = prediction.argmax(axis=-1)[0]
    class_labels = ['Pallas cats', 'Persian cats', 'Ragdolls', 'Singapura cats', 'Sphynx cats']
    print({'class': class_labels[class_idx], 'probability': float(prediction[0][class_idx])})
    return {'class': class_labels[class_idx], 'probability': float(prediction[0][class_idx])}

if __name__ == '__main__':
    app.run(host='172.25.110.117', port=5000)
