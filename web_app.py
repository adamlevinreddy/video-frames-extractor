from flask import Flask, render_template, request, send_from_directory, jsonify
from pathlib import Path
import os
import traceback
from frame_extractor_multithread import FrameExtractor
import settings
from dotenv import load_dotenv
from PIL import Image

load_dotenv()

app = Flask(__name__, static_folder=None)
app.config['UPLOAD_FOLDER'] = 'videos'
app.config['OUTPUT_FOLDER'] = str(settings.OUTDIR)

@app.route('/static/<path:filename>')
def serve_static(filename):
    return send_from_directory(app.config['OUTPUT_FOLDER'], filename)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    try:
        if 'video' not in request.files:
            return 'No video file uploaded', 400
        
        file = request.files['video']
        if file.filename == '':
            return 'No selected file', 400

        import time
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        video_name = file.filename.rsplit('.', 1)[0]
        
        # Create directories if they don't exist
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
        # Create timestamp-based directory for chronological sorting
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        frame_dir = os.path.join(app.config['OUTPUT_FOLDER'], f"{timestamp}_{video_name}")
        os.makedirs(frame_dir, exist_ok=True)
        os.makedirs(os.path.join(frame_dir, 'orig_size_frames'), exist_ok=True)
        os.makedirs(os.path.join(frame_dir, 're_size_frames'), exist_ok=True)
        
        video_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(video_path)
        
        from concurrent.futures import ThreadPoolExecutor
        frame_extractor = FrameExtractor(
            out_dir=Path(frame_dir),
            img_frmt=settings.REQUIRED_IMAGE_FORMAT,
            required_frame_rate=settings.REQUIRED_FRAME_RATE,
            start_from_seconds=settings.START_FROM_SECOND,
            img_width=settings.REQUIRED_IMAGE_WIDTH,
            verbose=True
        )
        
        with ThreadPoolExecutor() as executor:
            executor.submit(frame_extractor.extract_frames, Path(video_path))
        return 'Video processed successfully', 200
    except Exception as e:
        print(f"Error processing video: {str(e)}")
        print(traceback.format_exc())
        return f'Error processing video: {str(e)}', 500

@app.route('/frames')
def view_frames():
    try:
        output_dir = app.config['OUTPUT_FOLDER']
        extractions = sorted([d for d in os.listdir(output_dir) 
                            if os.path.isdir(os.path.join(output_dir, d))])
        return render_template('frames.html', extractions=extractions)
    except Exception as e:
        print(f"Error viewing frames: {str(e)}")
        return f'Error viewing frames: {str(e)}', 500

@app.route('/frames/<extraction>')
def view_extraction_frames(extraction):
    try:
        resize_frames_dir = os.path.join(app.config['OUTPUT_FOLDER'], extraction, 're_size_frames')
        if not os.path.exists(resize_frames_dir):
            return 'No frames available', 404
            
        frames = [f for f in os.listdir(resize_frames_dir) if f.endswith(settings.REQUIRED_IMAGE_FORMAT)]
        frames = sorted(frames)
        
        html_dir = os.path.join(app.config['OUTPUT_FOLDER'], extraction, 'html_results')
        html_results = {}
        if os.path.exists(html_dir):
            for frame in frames:
                html_path = os.path.join(html_dir, f"{Path(frame).stem}.html")
                if os.path.exists(html_path):
                    with open(html_path, 'r') as f:
                        html_results[frame] = f.read()
                        
        return render_template('frames.html', 
                             frames=frames, 
                             current_extraction=extraction,
                             frame_type='re_size_frames',
                             html_results=html_results)
    except Exception as e:
        print(f"Error viewing frames: {str(e)}")
        return f'Error viewing frames: {str(e)}', 500

@app.route('/static/<extraction>/<frame_type>/<filename>')
def serve_frame(extraction, frame_type, filename):
    try:
        frame_path = os.path.join(str(settings.OUTDIR), extraction, frame_type)
        if not os.path.exists(frame_path):
            os.makedirs(frame_path, exist_ok=True)
        return send_from_directory(frame_path, filename, as_attachment=False)
    except Exception as e:
        print(f"Error serving frame: {str(e)}")
        return f'Error serving frame: {str(e)}', 500

import gc

@app.route('/save-crops', methods=['POST'])
def save_crops():
    try:
        data = request.json
        frame_path = os.path.join(app.config['OUTPUT_FOLDER'], 
                                data['extraction'],
                                data['frameType'],
                                data['frame'])
                                
        if not os.path.exists(frame_path):
            return jsonify({'success': False, 'error': 'Source image not found'}), 404
            
        img = Image.open(frame_path)
        
        # Create crops directory
        crops_dir = os.path.join(app.config['OUTPUT_FOLDER'],
                               data['extraction'],
                               'crops')
        os.makedirs(crops_dir, exist_ok=True)
        
        # Save each crop
        for i, crop in enumerate(data['crops']):
            # Create crop with PIL
            cropped = img.crop((crop['x'], 
                              crop['y'],
                              crop['x'] + crop['width'],
                              crop['y'] + crop['height']))
                              
            # Save cropped image
            crop_name = f"{os.path.splitext(data['frame'])[0]}_crop_{i+1}.jpg"
            crop_path = os.path.join(crops_dir, crop_name)
            cropped.save(crop_path, 'JPEG')
            
        # Remove original frame if all crops saved successfully
        os.remove(frame_path)
        
        return jsonify({'success': True})
        
    except Exception as e:
        print(f"Error saving crops: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/action-frames/<extraction>')
def view_action_frames(extraction):
    try:
        resize_frames_dir = Path(os.path.join(app.config['OUTPUT_FOLDER'], extraction, 're_size_frames'))
        
        if not resize_frames_dir.exists():
            return f'Frames directory not found: {resize_frames_dir}', 404
            
        # Get all frames in the directory that don't end with _analyzed
        action_frames = sorted([f for f in os.listdir(resize_frames_dir) 
                             if f.endswith(settings.REQUIRED_IMAGE_FORMAT) 
                             and not f.endswith('_analyzed.jpg')])
        
        if not action_frames:
            return 'No action frames available', 404
            
        # Get corresponding original size frames
        orig_frames_dir = Path(os.path.join(app.config['OUTPUT_FOLDER'], extraction, 'orig_size_frames'))
        orig_frames = []
        for frame in action_frames:
            if os.path.exists(os.path.join(orig_frames_dir, frame)):
                orig_frames.append(frame)
        
        orig_frames = sorted(orig_frames)
        print(f"Detected {len(orig_frames)} action frames")
        
        html_dir = os.path.join(app.config['OUTPUT_FOLDER'], extraction, 'html_results')
        html_results = {}
        if os.path.exists(html_dir):
            for frame in orig_frames:
                html_path = os.path.join(html_dir, f"{Path(frame).stem}.html")
                if os.path.exists(html_path):
                    with open(html_path, 'r') as f:
                        html_results[frame] = f.read()
                        
        return render_template('frames.html', 
                             frames=orig_frames, 
                             current_extraction=extraction,
                             frame_type='orig_size_frames',
                             html_results=html_results)
    except Exception as e:
        print(f"Error detecting action frames: {str(e)}")
        return f'Error detecting action frames: {str(e)}', 500

@app.route('/process-frames/<extraction>', methods=['POST'])
def process_frames(extraction):
    try:
        from anthropic_handler import AnthropicHandler
        api_key = os.getenv('ANTHROPIC_API_KEY')
        if not api_key:
            return 'ANTHROPIC_API_KEY not set', 400
            
        frames_dir = Path(os.path.join(app.config['OUTPUT_FOLDER'], extraction, 'orig_size_frames'))
        html_dir = Path(os.path.join(app.config['OUTPUT_FOLDER'], extraction, 'html_results'))
        
        frame_paths = [p for p in frames_dir.glob(f'*.{settings.REQUIRED_IMAGE_FORMAT}')]
        
        handler = AnthropicHandler(api_key)
        results = handler.process_frames(frame_paths, html_dir)
        
        return jsonify(results)
    except Exception as e:
        return f'Error processing frames: {str(e)}', 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3000)