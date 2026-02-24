let video = document.getElementById('video');
let canvas = document.getElementById('canvas');
let ctx = canvas.getContext('2d');
let statusDiv = document.getElementById('status');

let streaming = false;
let processing = false;

async function startCamera() {
    try {
        const stream = await navigator.mediaDevices.getUserMedia({
            video: { facingMode: 'user' }
        });
        video.srcObject = stream;
        streaming = true;
        statusDiv.textContent = "Camera started. Looking for face...";
        video.onloadedmetadata = () => {
            canvas.width = video.videoWidth;
            canvas.height = video.videoHeight;
            requestAnimationFrame(processFrame);
        };
    } catch (err) {
        statusDiv.textContent = "Camera error: " + err.message;
        console.error(err);
    }
}

function processFrame() {
    if (!streaming || processing) {
        requestAnimationFrame(processFrame);
        return;
    }

    processing = true;
    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);

    // Send frame to server every ~1.5 seconds (adjust as needed)
    if (Math.random() < 0.35) {   // ~ every 3 frames
        canvas.toBlob(async (blob) => {
            let formData = new FormData();
            formData.append('image', blob, 'frame.jpg');

            try {
                const response = await fetch(markUrl, {
                    method: 'POST',
                    body: formData
                });
                const data = await response.json();

                if (data.success) {
                    statusDiv.textContent = "Attendance marked successfully!";
                    statusDiv.style.color = "green";
                    // Optionally stop after success
                    // video.srcObject.getTracks().forEach(track => track.stop());
                } else {
                    statusDiv.textContent = data.message || "Not recognized yet...";
                    statusDiv.style.color = data.success ? "green" : "#d32f2f";
                }
            } catch (err) {
                statusDiv.textContent = "Error connecting to server";
                console.error(err);
            }

            processing = false;
        }, 'image/jpeg', 0.85);
    } else {
        processing = false;
    }

    requestAnimationFrame(processFrame);
}

// Auto-start or button
if (navigator.mediaDevices) {
    startCamera();
} else {
    document.getElementById('startBtn').style.display = 'block';
    document.getElementById('startBtn').onclick = startCamera;
}