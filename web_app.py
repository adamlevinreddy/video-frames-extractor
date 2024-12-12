
from flask import Flask, render_template, request, send_from_directory
from werkzeug.utils import secure_filename
import os
from pathlib import Path
from frame_extractor_multithread import FrameExtractor
import settings

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Ensure upload and output directories exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(settings.OUTDIR, exist_ok=True)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'video' not in request.files:
        return 'No video file uploaded', 400
    
    file = request.files['video']
    if file.filename == '':
        return 'No selected file', 400
        
    filename = secure_filename(file.filename)
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)
    
    # Process video
    frame_extractor = FrameExtractor(
        settings.OUTDIR,
        settings.REQUIRED_IMAGE_FORMAT,
        settings.REQUIRED_FRAME_RATE,
        settings.START_FROM_SECOND,
        settings.REQUIRED_IMAGE_WIDTH,
        True
    )
    frame_extractor.extract_frames(Path(filepath))
    
    return 'Video processed successfully', 200

@app.route('/frames')
def view_frames():
    orig_frames = os.listdir(os.path.join(settings.OUTDIR, 'orig_size_frames'))
    resized_frames = os.listdir(os.path.join(settings.OUTDIR, 're_size_frames'))
    return render_template('frames.html', orig_frames=orig_frames, resized_frames=resized_frames)

@app.route('/frames/<path:filename>')
def serve_frame(filename):
    directory = 'orig_size_frames' if 'orig' in filename else 're_size_frames'
    return send_from_directory(os.path.join(settings.OUTDIR, directory), filename)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
