from flask import Flask, render_template, request, send_from_directory, jsonify
from pathlib import Path
import os
import traceback
from frame_extractor_multithread import FrameExtractor
import settings
from PIL import Image

app = Flask(__name__, static_folder=str(settings.OUTDIR), static_url_path='/static')
app.config['UPLOAD_FOLDER'] = 'videos'
app.config['OUTPUT_FOLDER'] = str(settings.OUTDIR)

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
        return render_template('frames.html', frames=frames, current_extraction=extraction)
    except Exception as e:
        print(f"Error viewing frames: {str(e)}")
        return f'Error viewing frames: {str(e)}', 500

@app.route('/frame/<filename>')
def frame(filename):
    try:
        resize_frames_dir = os.path.join(app.config['OUTPUT_FOLDER'], 're_size_frames')
        return send_from_directory(resize_frames_dir, filename, as_attachment=False)
    except Exception as e:
        print(f"Error serving frame: {str(e)}")
        return f'Error serving frame: {str(e)}', 500

import gc

@app.route('/action-frames/<extraction>')
def view_action_frames(extraction):
    try:
        from frame_analyzer import FrameAnalyzer
        analyze_frames_dir = Path(os.path.join(app.config['OUTPUT_FOLDER'], extraction, 're_size_frames'))
        
        if not analyze_frames_dir.exists():
            return f'Frames directory not found: {analyze_frames_dir}', 404
            
        analyzer = FrameAnalyzer(analyze_frames_dir, threshold=25, min_area=300, batch_size=20)
        action_frame_names = [f.stem for f in analyzer.detect_changes() if not f.stem.endswith('_analyzed')]
        gc.collect()
        
        if not action_frame_names:
            return 'No action frames detected', 404
            
        # Get corresponding original size frames
        orig_frames_dir = Path(os.path.join(app.config['OUTPUT_FOLDER'], extraction, 'orig_size_frames'))
        action_frames = []
        for name in action_frame_names:
            orig_frame = f"{name}.{settings.REQUIRED_IMAGE_FORMAT}"
            if os.path.exists(os.path.join(orig_frames_dir, orig_frame)):
                action_frames.append(orig_frame)
                
        action_frames = sorted(action_frames)
        print(f"Detected {len(action_frames)} action frames")
        
        return render_template('frames.html', frames=action_frames, current_extraction=extraction, frame_type='orig_size_frames')
    except Exception as e:
        print(f"Error detecting action frames: {str(e)}")
        return f'Error detecting action frames: {str(e)}', 500

@app.route('/save-crops/<extraction>/<image_name>', methods=['POST'])
def save_crops(extraction, image_name):
    try:
        data = request.get_json()
        crops = data['crops']
        output_folder = app.config['OUTPUT_FOLDER']
        frame_type = 'orig_size_frames'  # Assuming we're cropping original size frames
        frame_dir = os.path.join(output_folder, extraction, frame_type)
        image_path = os.path.join(frame_dir, image_name)
        
        # Move original image to 'originals' subfolder
        originals_dir = os.path.join(frame_dir, 'originals')
        os.makedirs(originals_dir, exist_ok=True)
        original_image_path = os.path.join(originals_dir, image_name)
        if not os.path.exists(original_image_path):
            os.rename(image_path, original_image_path)
        else:
            os.remove(image_path)  # Original already moved
        
        # Load the original image
        img = Image.open(original_image_path)

        # Create crops
        for idx, crop in enumerate(crops):
            left = crop['left']
            top = crop['top']
            right = left + crop['width']
            bottom = top + crop['height']
            cropped_img = img.crop((left, top, right, bottom))
            # Save cropped image with new naming convention
            base_name, ext = os.path.splitext(image_name)
            crop_name = f"{base_name}_crop_{idx}{ext}"
            crop_path = os.path.join(frame_dir, crop_name)
            cropped_img.save(crop_path)
        
        # Remove the original image from /action-frames
        # (Already moved to 'originals' subfolder)
        
        return jsonify({'status': 'success'}), 200
    except Exception as e:
        print(f"Error saving crops: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3000)
