from flask import Flask, request, render_template, jsonify
import os

app = Flask(__name__)

@app.route('/')
def index():
    # Render an HTML form to upload an image
    # index_path = os.path.join(os.getcwd(), 'index.html')
    # index_path = '/home/ec2-user/COMP0239-CW/Frontend/index.html'
    # return render_template(index_path)
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_image():
    if 'image' not in request.files:
        return jsonify({'error': 'No image part'}), 400

    file = request.files['image']

    if file.filename == '':
        return jsonify({'error': 'No selected image'}), 400

    if file and file.filename.endswith('.jpg'):
        # Save the image to the server
        filename = 'uploaded_image.jpg'
        file.save(filename)
        
        # TODO: Send the image to the backend and get the caption
        caption = generate_caption(filename)  # Placeholder function

        return jsonify({'caption': caption})

    return jsonify({'error': 'Invalid file format'}), 400

def generate_caption(image_path):
    # Placeholder function to simulate backend processing
    # Replace with actual backend call
    return "This is where the image caption will appear."

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=4506)

