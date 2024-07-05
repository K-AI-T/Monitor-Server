from http.client import HTTPException
from flask import Flask, jsonify, request
from flask_restx import Api, Resource, fields
from werkzeug.exceptions import BadRequest, NotFound, InternalServerError

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
    app.run(debug=True)
