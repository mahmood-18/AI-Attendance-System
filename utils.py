import face_recognition       # ← correct import
import cv2
import numpy as np
import os
from datetime import datetime

# Folder where known student photos are stored (filename = username.jpg)
KNOWN_FACES_DIR = "known_faces"

known_face_encodings = []
known_face_names = []

def load_known_faces():
    global known_face_encodings, known_face_names
    known_face_encodings.clear()
    known_face_names.clear()

    if not os.path.exists(KNOWN_FACES_DIR):
        os.makedirs(KNOWN_FACES_DIR)
        print(f"Created directory: {KNOWN_FACES_DIR}")

    print("Loading known faces...")
    loaded_count = 0

    for filename in os.listdir(KNOWN_FACES_DIR):
        if filename.lower().endswith((".jpg", ".jpeg", ".png")):
            name = os.path.splitext(filename)[0]
            path = os.path.join(KNOWN_FACES_DIR, filename)
            try:
                image = face_recognition.load_image_file(path)
                encodings = face_recognition.face_encodings(image)
                if encodings:
                    known_face_encodings.append(encodings[0])
                    known_face_names.append(name)
                    loaded_count += 1
                    print(f"Loaded face: {name}")
                else:
                    print(f"No face detected in: {filename}")
            except Exception as e:
                print(f"Error loading {filename}: {e}")

    print(f"Total faces loaded: {loaded_count}")

def recognize_face(frame):
    """
    Returns: face_locations, names, confidences
    """
    # Convert BGR (OpenCV) → RGB
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    # Resize for faster processing (1/4 size)
    small_frame = cv2.resize(rgb_frame, (0, 0), fx=0.25, fy=0.25)

    face_locations = face_recognition.face_locations(small_frame)
    face_encodings = face_recognition.face_encodings(small_frame, face_locations)

    names = []
    confidences = []

    for face_encoding in face_encodings:
        # Compare with known faces
        matches = face_recognition.compare_faces(
            known_face_encodings,
            face_encoding,
            tolerance=0.55   # ← tune this: lower = stricter
        )
        name = "Unknown"
        confidence = 0.0

        if True in matches:
            # Get the best match (lowest distance)
            face_distances = face_recognition.face_distance(known_face_encodings, face_encoding)
            best_match_index = np.argmin(face_distances)
            name = known_face_names[best_match_index]
            confidence = 1 - face_distances[best_match_index]  # 0–1 scale

        names.append(name)
        confidences.append(confidence)

    return face_locations, names, confidences


# ────────────────────────────────────────────────
# Example usage (test the functions standalone)
# ────────────────────────────────────────────────

if __name__ == "__main__":
    load_known_faces()

    if not known_face_encodings:
        print("No known faces loaded. Add images to 'known_faces/' folder.")
    else:
        print("\nTesting recognition on webcam...")
        cap = cv2.VideoCapture(0)

        if not cap.isOpened():
            print("Cannot open webcam")
        else:
            while True:
                ret, frame = cap.read()
                if not ret:
                    break

                locs, names, confs = recognize_face(frame)

                # Draw results
                for (top, right, bottom, left), name, conf in zip(locs, names, confs):
                    # Scale back to original size
                    top, right, bottom, left = [int(x * 4) for x in (top, right, bottom, left)]

                    color = (0, 255, 0) if name != "Unknown" else (0, 0, 255)
                    cv2.rectangle(frame, (left, top), (right, bottom), color, 2)
                    label = f"{name} ({conf:.2%})" if conf > 0 else name
                    cv2.putText(frame, label, (left, top-10),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.9, color, 2)

                cv2.imshow("Attendance - Press 'q' to quit", frame)

                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break

            cap.release()
            cv2.destroyAllWindows()