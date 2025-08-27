import cv2
import face_recognition
import numpy as np
import os
import csv
from datetime import datetime
from db_handler import create_table, insert_face, get_all_faces, update_deduction, mark_absent, get_payroll, mark_attendance

# ----------------- Initialization -----------------
print("🔍 Initializing Attendance System...")

# Ensure DB tables exist
create_table()
print("✅ Database tables ensured.")

# Load known faces from DB
faces = get_all_faces()
known_face_names = [f[0] for f in faces]
known_face_encodings = [f[1] for f in faces]
print(f"✅ Loaded {len(known_face_names)} faces from DB.")

# Create attendance folder and today's CSV
os.makedirs("attendance_records", exist_ok=True)
current_date = datetime.now().strftime("%Y-%m-%d")
csv_filename = os.path.join("attendance_records", f"{current_date}.csv")

# Open CSV file in append mode
f = open(csv_filename, 'a', newline='')
lnwriter = csv.writer(f)

# Add header if file is empty
if os.stat(csv_filename).st_size == 0:
    lnwriter.writerow(["Name", "Time", "Status"])

# Track students already marked present
marked_students = set()

# Load previously marked students from CSV (if system restarts)
if os.path.exists(csv_filename):
    with open(csv_filename, 'r') as existing_csv:
        reader = csv.reader(existing_csv)
        next(reader, None)  # skip header
        for row in reader:
            if row:
                marked_students.add(row[0])

# ----------------- Function to mark attendance in CSV -----------------
def write_attendance_csv(name):
    if name not in marked_students:
        current_time = datetime.now().strftime("%H:%M:%S")
        current_time_obj = datetime.strptime(current_time, "%H:%M:%S").time()
        
        office_start = datetime.strptime("10:00:00", "%H:%M:%S").time()
        cutoff_time = datetime.strptime("11:00:00", "%H:%M:%S").time()

        # Determine status
        if current_time_obj <= office_start:
            status = "Present"
        elif office_start < current_time_obj < cutoff_time:
            late_minutes = (datetime.combine(datetime.today(), current_time_obj) -
                            datetime.combine(datetime.today(), office_start)).seconds // 60
            status = f"Late by {late_minutes} mins"
        else:
            status = "Absent"

        lnwriter.writerow([name, current_time, status])
        f.flush()
        marked_students.add(name)
        print(f"✅ {name} marked at {current_time} with status: {status}")

        # Payroll logic based on status
        if "Late" in status:
            update_deduction(name, 50)
            print(f"⚠ {name} was late! ₹50 deducted.")
        elif "Whole Day Absent" in status:
            mark_absent(name)
            print(f"❌ {name} is Absent! 1 day salary deducted.")

        # Show updated payroll info
        payroll_info = get_payroll(name)
        print(f"📊 Payroll Updated: {payroll_info}")
    else:
        print(f"ℹ {name} is already marked in CSV. Skipping.")

# ----------------- Open webcam -----------------
video_capture = cv2.VideoCapture(0)
if not video_capture.isOpened():
    print("❌ Error: Could not open camera.")
    exit()

print("✅ Camera started.")
print("👉 Press 'a' to add a new student face, 'q' or ESC to quit.")

# ----------------- Main Loop -----------------
while True:
    ret, frame = video_capture.read()
    if not ret:
        print("❌ Error: Failed to grab frame.")
        break

    # Resize frame for faster recognition
    small_frame = cv2.resize(frame, (0, 0), fx=0.5, fy=0.5)
    rgb_small_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)

    # Detect faces
    face_locations = face_recognition.face_locations(rgb_small_frame)
    face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)
    print(f"📷 Detected {len(face_encodings)} face(s) in frame.")

    face_names = []

    for face_encoding in face_encodings:
        name = "Unknown"
        if len(known_face_encodings) > 0:
            matches = face_recognition.compare_faces(known_face_encodings, face_encoding)
            face_distances = face_recognition.face_distance(known_face_encodings, face_encoding)
            best_match_index = np.argmin(face_distances)
            if matches[best_match_index]:
                name = known_face_names[best_match_index]
                face_names.append(name)
                print(f"🔍 Match result: {name}")

        # ✅ Attendance logic (skip if already marked)
        if name != "Unknown":
            db_result = mark_attendance(name)  # DB logic should prevent duplicates
            if db_result:
                print(f"✅ {name} marked in database.")
            else:
                print(f"ℹ {name} already present in DB.")

            # Mark in CSV
            write_attendance_csv(name)

    # Draw rectangles and labels
    for (top, right, bottom, left), name in zip(face_locations, face_names):
        top *= 2
        right *= 2
        bottom *= 2
        left *= 2

        color = (0, 255, 0) if name != "Unknown" else (0, 0, 255)
        cv2.rectangle(frame, (left, top), (right, bottom), color, 2)
        cv2.putText(frame, name, (left, top - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, color, 2)

    # Show video
    cv2.imshow("Face Attendance System", frame)

    # Handle keys
    key = cv2.waitKey(1)

    if key == ord('a'):
        if len(face_encodings) == 1:
            new_name = input("Enter student name: ").strip()
            if new_name:
                insert_face(new_name, face_encodings[0])
                known_face_names.append(new_name)
                known_face_encodings.append(face_encodings[0])
                print(f"✅ New student '{new_name}' added to database.")
            else:
                print("⚠ No name entered, skipping.")
        else:
            print("⚠ Please ensure only one face is visible to add.")

    if key == ord('q') or key == 27:
        print("👋 Exiting...")
        break

# ----------------- Cleanup -----------------
video_capture.release()
f.close()
cv2.destroyAllWindows()
print("✅ Attendance session ended.")
