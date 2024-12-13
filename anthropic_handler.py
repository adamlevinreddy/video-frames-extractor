
import anthropic
import base64
import os
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import imghdr

class AnthropicHandler:
    def __init__(self, api_key):
        self.client = anthropic.Anthropic(api_key=api_key)
        
    def process_single_image(self, image_path):
        print(f"\nProcessing image: {image_path}")
        with open(image_path, 'rb') as image_file:
            image_data = base64.b64encode(image_file.read()).decode('utf-8')
            
        media_type = f"image/{imghdr.what(image_path)}"
        
        try:
            print(f"Sending request to Anthropic API for {image_path}")
            message = self.client.messages.create(
                model="claude-3-sonnet-20240229",
                max_tokens=1024,
                messages=[{
                    "role": "user",
                    "content": [{
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": media_type,
                            "data": image_data,
                        },
                    }, {
                        "type": "text",
                        "text": "Take this image and write an exact replica in HTML. We need the HTML to look as close as possible to the original image."
                    }]
                }]
            )
            print(f"Received response from Anthropic API for {image_path}")
            print(f"Response length: {len(message.content[0].text)} characters")
        
        return message.content[0].text

    def process_frames(self, frame_paths, output_dir):
        os.makedirs(output_dir, exist_ok=True)
        results = {}
        
        with ThreadPoolExecutor() as executor:
            future_to_path = {
                executor.submit(self.process_single_image, str(path)): path 
                for path in frame_paths
            }
            
            for future in future_to_path:
                path = future_to_path[future]
                try:
                    result = future.result()
                    html_path = Path(output_dir) / f"{path.stem}.html"
                    with open(html_path, 'w') as f:
                        f.write(result)
                    results[str(path)] = result
                except Exception as e:
                    error_msg = f"Error processing {path}: {str(e)}"
                    print(error_msg)
                    results[str(path)] = f"Error: {str(e)}"
                    
        return results
