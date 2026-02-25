AI-Based Attendance System using Face Recognition

This is an automated attendance system that uses face recognition to mark students present in real time through a webcam. 
It removes the need for manual roll calls and makes the whole process faster and more accurate with computer vision.

What it does
- Detects and recognizes faces automatically
- Marks attendance in a CSV file with name, roll number, date, time
- Shows a simple web page where you can start the recognition
- Stores student photos in an organized folder
- Uses pre-computed face encodings for quick matching

Technologies used
- Python
- Flask (for the web part)
- OpenCV (for camera and image handling)
- face_recognition library (based on dlib)
- SQLite (optional, if you want to move beyond CSV)
- Basic HTML + CSS + a bit of JavaScript for the webcam view


How to set it up

1. Clone the project
   git clone https://github.com/mahmood-18/AI-Attendance-System.git
   cd AI-Attendance-System

2. Create virtual environment
   python -m venv venv

   On Windows:
   venv\Scripts\activate

   On Mac/Linux:
   source venv/bin/activate

3. Install packages
   pip install -r requirements.txt

4. (If encodings.pkl is missing) Generate face encodings
   Usually you run something like:
   python encode_faces.py
   (If this file doesn't exist yet, you'll need to add a small script to scan known_faces/ and create encodings.pkl)

5. Start the app
   python app.py

   Then open http://127.0.0.1:5000/ in your browser

How to add students
- Put clear, front-facing photos of students in the known_faces/ folder
- Name them something like rollnumber_name.jpg
- Re-run the encoding script if you added new photos
- The system will recognize them when they appear in front of the camera

What's next (planned improvements)
- Add login for admin/teacher
- Show charts and reports of attendance
- Save data to real database instead of just CSV
- Put it online (Heroku, Render, etc.)
- Make it work for different classes/subjects
- Maybe add phone support later

What I learned doing this
- How face recognition actually works
- Streaming video from webcam to browser with Flask
- Working with OpenCV and face_recognition library
- Keeping code organized in small files
- Using git properly
- Building something useful with AI

Made by  
Mahmood Naina M.M
