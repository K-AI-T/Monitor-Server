from http.client import HTTPException
from flask import Flask, Response, render_template, request, jsonify, send_from_directory
from flask_restx import Api, Resource, fields
from werkzeug.exceptions import BadRequest, NotFound, InternalServerError
import cv2
import threading
import time
import datetime
from werkzeug.serving import run_simple

app = Flask(__name__)
api = Api(app, version='1.0', title='Emergency Response System API',
          description='API for monitoring and responding to emergencies in a subway station.')

ns = api.namespace('monitor', description='Monitoring operations')

cctv_model = api.model('CCTV', {
    'id': fields.Integer(required=True, description='The CCTV camera identifier'),
    'location': fields.String(required=True, description='The location of the CCTV camera'),
    'status': fields.String(required=True, description='The current status of the CCTV camera'),
    'stream_url': fields.String(required=True, description='The stream URL of the CCTV camera'),
})

drone_model = api.model('Drone', {
    'id': fields.Integer(required=True, description='The drone identifier'),
    'station': fields.String(required=True, description='The station where the drone is located'),
    'status': fields.String(required=True, description='The current status of the drone (flying or standby)'),
    'battery': fields.Integer(required=True, description='The remaining battery percentage of the drone'),
    'position': fields.String(required=True, description='The current position of the drone'),
})

alert_model = api.model('Alert', {
    'cctv_id': fields.Integer(required=True, description='The identifier of the CCTV camera'),
    'location': fields.String(required=True, description='The location where the alert was triggered'),
    'timestamp': fields.String(required=True, description='The time the alert was triggered'),
    'drone_eta': fields.String(required=True, description='The estimated time of arrival for the drone'),
})

status_model = api.model('Status', {
    'cctvs': fields.List(fields.Nested(cctv_model), description='List of CCTV statuses'),
    'drones': fields.List(fields.Nested(drone_model), description='List of drone statuses'),
})
rtsp_urls = [
    "rtsp://210.99.70.120:1935/live/cctv007.stream",  # CAM1
    "rtsp://210.99.70.120:1935/live/cctv002.stream",  # CAM2
    "",  # CAM3 (비활성화)
    "",  # CAM4 (비활성화)
    "",  # CAM5 (비활성화)
    ""   # CAM6 (비활성화)
]

# 각 카메라의 프레임을 저장할 딕셔너리 (CAM1과 CAM2만)
frames = {i: None for i in range(len(rtsp_urls))}

def capture_frames(camera_index, rtsp_url):
    if not rtsp_url:
        return  # URL이 빈 경우 아무 작업도 수행하지 않음
    cap = cv2.VideoCapture(rtsp_url)
    while True:
        success, frame = cap.read()
        if not success:
            break
        ret, buffer = cv2.imencode('.jpg', frame)
        frames[camera_index] = buffer.tobytes()

# 각 카메라의 프레임을 생성하는 제너레이터 함수
def generate_frames(camera_index):
    while True:
        frame = frames[camera_index]
        if frame is None:
            frame = cv2.imencode('.jpg', cv2.imread('black.jpg'))[1].tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

@app.route('/main')
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
                yield f"data: {current_time}\n\n"
            except Exception as e:
                print(f"Error updating time: {e}")
    return Response(generate(), mimetype='text/event-stream')

@app.route('/static/<path:filename>')
def static_files(filename):
    return send_from_directory('static', filename)


@ns.route('/status')
class Status(Resource):
    '''Fetch the status of all CCTVs and drones'''
    @ns.doc('get_status')
    @ns.marshal_with(status_model)
    def get(self):
        '''Get the status of all CCTVs and drones'''
        try:
            # 실제 메인 서버에서 CCTV와 드론 상태 정보를 가져옵니다.
            return {
                'cctvs': [
                    {'id': 1, 'location': 'Station A', 'status': 'active', 'stream_url': 'http://example.com/stream1'},
                    {'id': 2, 'location': 'Station B', 'status': 'inactive', 'stream_url': 'http://example.com/stream2'},
                    {'id': 3, 'location': 'Station C', 'status': 'active', 'stream_url': 'http://example.com/stream3'},
                    {'id': 4, 'location': 'Station D', 'status': 'active', 'stream_url': 'http://example.com/stream4'},
                    {'id': 5, 'location': 'Station E', 'status': 'inactive', 'stream_url': 'http://example.com/stream5'},
                    {'id': 6, 'location': 'Station F', 'status': 'active', 'stream_url': 'http://example.com/stream6'},
                ],
                'drones': [
                    {'id': 1, 'station': 'Station A', 'status': 'standby', 'battery': 80, 'position': 'A1'},
                    {'id': 2, 'station': 'Station B', 'status': 'flying', 'battery': 60, 'position': 'B1'},
                    {'id': 3, 'station': 'Station C', 'status': 'standby', 'battery': 90, 'position': 'C1'},
                    {'id': 4, 'station': 'Station D', 'status': 'flying', 'battery': 50, 'position': 'D1'},
                ]
            }
        except Exception as e:
            api.abort(500, "Internal Server Error: {}".format(e))

@ns.route('/alerts')
class Alert(Resource):
    '''Fetch emergency alerts'''
    @ns.doc('get_alerts')
    @ns.marshal_list_with(alert_model)
    def get(self):
        '''Get emergency alerts'''
        try:
            # 실제 메인 서버에서 비상 경고 정보를 가져옵니다.
            return [
                {'cctv_id': 1, 'location': 'Station A', 'timestamp': '2024-07-02T12:34:56', 'drone_eta': '5 minutes'},
                # 추가 경고 데이터
            ]
        except NotFound as e:
            api.abort(404, "Alerts not found: {}".format(e))
        except Exception as e:
            api.abort(500, "Internal Server Error: {}".format(e))

@ns.route('/report')
class Report(Resource):
    '''Report the current situation to the emergency services (e.g., 119)'''
    @ns.doc('report_situation')
    @ns.expect(status_model)
    def post(self):
        '''Report the current situation to the emergency services'''
        try:
            # 여기서 현재 상황을 119 상황실로 전송합니다.
            data = request.json
            # 실제 데이터 전송 로직 추가
            return {'message': 'Reported successfully'}, 200
        except BadRequest as e:
            api.abort(400, "Bad Request: {}".format(e))
        except Exception as e:
            api.abort(500, "Internal Server Error: {}".format(e))

@api.errorhandler
def default_error_handler(error):
    message = 'An unhandled exception occurred.'
    print(str(error))
    if not isinstance(error, HTTPException):
        return {'message': message}, 500

@api.errorhandler(NotFound)
def not_found_error_handler(error):
    return {'message': 'Resource not found'}, 404

@api.errorhandler(BadRequest)
def bad_request_error_handler(error):
    return {'message': 'Bad request'}, 400

api.add_namespace(ns)

if __name__ == '__main__':
    # 각 카메라 스트림을 별도의 스레드에서 캡처
    for i, rtsp_url in enumerate(rtsp_urls):
        threading.Thread(target=capture_frames, args=(i, rtsp_url)).start()
    
    # Flask 서버를 werkzeug의 run_simple로 실행
    app.run(host='0.0.0.0', port=5000, debug=True)