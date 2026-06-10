const upload = document.getElementById('video-upload');
const video = document.getElementById('video-player');
const canvas = document.getElementById('canvas-overlay');
const ctx = canvas.getContext('2d');
const processBtn = document.getElementById('process-btn');

let startX, startY, isDrawing = false;
let boxX = 0, boxY = 0, boxW = 0, boxH = 0;

// Handle video loading
upload.addEventListener('change', (e) => {
    const file = e.target.files[0];
    if (!file) return;

    video.src = URL.createObjectURL(file);
    video.load();

    video.onloadedmetadata = () => {
        // Calculate aspect ratio height for a standard 640px width display
        const calculatedHeight = video.videoHeight * (640 / video.videoWidth);
        canvas.height = calculatedHeight;
        video.height = calculatedHeight;
        
        // Draw the first frame on the canvas background so the user can see what they're doing
        video.currentTime = 0.1; 
    };
});

// Update canvas with video background when it seeks
video.addEventListener('seeked', () => {
    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
});

// Mouse coordinates logic for selecting watermark region
canvas.addEventListener('mousedown', (e) => {
    startX = e.offsetX;
    startY = e.offsetY;
    isDrawing = true;
});

canvas.addEventListener('mousemove', (e) => {
    if (!isDrawing) return;
    
    // Clear and redraw background frame
    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
    
    boxX = startX;
    boxY = startY;
    boxW = e.offsetX - startX;
    boxH = e.offsetY - startY;
    
    // Draw visual bounding box selection
    ctx.strokeStyle = '#ff0000';
    ctx.lineWidth = 3;
    ctx.strokeRect(boxX, boxY, boxW, boxH);
});

canvas.addEventListener('mouseup', () => {
    isDrawing = false;
    if (boxW !== 0 && boxH !== 0) {
        processBtn.disabled = false;
    }
});

// Submit box locations & video to Flask API
processBtn.addEventListener('click', async () => {
    const file = upload.files[0];
    if (!file) return;

    processBtn.innerText = "Processing video... please wait...";
    processBtn.disabled = true;

    // Convert selection sizes relative to the video's actual raw dimensions
    const scaleX = video.videoWidth / canvas.width;
    const scaleY = video.videoHeight / canvas.height;

    const formData = new FormData();
    formData.append('video', file);
    formData.append('x', Math.round(boxX * scaleX));
    formData.append('y', Math.round(boxY * scaleY));
    formData.append('w', Math.round(Math.abs(boxW * scaleX)));
    formData.append('h', Math.round(Math.abs(boxH * scaleY)));

    try {
        let response = await fetch('http://127.0.0.1:5000/api/remove-logo', { 
            method: 'POST', 
            body: formData 
        });

        if (!response.ok) throw new Error("Processing failed server-side.");

        let blob = await response.blob();
        
        // Auto trigger file save file pipeline
        let downloadUrl = URL.createObjectURL(blob);
        let a = document.createElement('a');
        a.href = downloadUrl;
        a.download = "watermark_removed.mp4";
        document.body.appendChild(a);
        a.click();
        a.remove();
    } catch (error) {
        alert("An error occurred during video processing: " + error.message);
    } finally {
        processBtn.innerText = "Erase Logo & Download";
        processBtn.disabled = false;
    }
});