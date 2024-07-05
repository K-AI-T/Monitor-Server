from flask import Flask, Response, render_template
import cv2
import threading
import datetime
import time

app = Flask(__name__)

# 각 스트림의 URL을 리스트로 정의
rtsp_urls = [
    "rtsp://210.99.70.120:1935/live/cctv007.stream",
    "rtsp://210.99.70.120:1935/live/cctv002.stream",
    "rtsp://210.99.70.120:1935/live/cctv003.stream",
    "rtsp://210.99.70.120:1935/live/cctv004.stream",
    "rtsp://210.99.70.120:1935/live/cctv005.stream",
    "rtsp://210.99.70.120:1935/live/cctv006.stream"
]

# 각 카메라의 프레임을 저장할 딕셔너리
frames = {i: None for i in range(len(rtsp_urls))}

def capture_frames(camera_index, rtsp_url):
    print(f"Starting capture thread for camera {camera_index}")
    cap = cv2.VideoCapture(rtsp_url)
    while True:
        success, frame = cap.read()
        if not success:
            print(f"Error capturing frame from camera {camera_index}")
            break
        ret, buffer = cv2.imencode('.jpg', frame)
        frames[camera_index] = buffer.tobytes()

# 각 카메라의 프레임을 생성하는 제너레이터 함수
def generate_frames(camera_index):
    while True:
        frame = frames[camera_index]
        if frame is None:
            continue
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/video_feed/<int:camera_index>')
def video_feed(camera_index):
    return Response(generate_frames(camera_index), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/time')
def time_feed():
    def generate():
        while True:
            try:
                time.sleep(0.1)  # 100밀리초마다 업데이트
                current_time = datetime.datetime.now().strftime("%H:%M:%S.%f")[:-3]  # 밀리초까지 포함한 현재 시각
                print(f"Sending time: {current_time}")
                yield f"data: {current_time}\n\n"
            except Exception as e:
                print(f"Error updating time: {e}")
    return Response(generate(), mimetype='text/event-stream')

if __name__ == '__main__':
    # 각 카메라 스트림을 별도의 스레드에서 캡처
    for i, rtsp_url in enumerate(rtsp_urls):
        threading.Thread(target=capture_frames, args=(i, rtsp_url)).start()
    
    app.run(host='0.0.0.0', port=5000)
