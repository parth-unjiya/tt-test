# -*- coding: utf-8 -*-
import os
import time
import json
import base64
import logging

from odoo import http
from odoo.http import request, Response
from PIL import Image
import boto3
from botocore.exceptions import NoCredentialsError, ClientError


_logger = logging.getLogger(__name__)

AWS_ACCESS_KEY = 'AKIA6O54BMKWWVGSP24N'
AWS_SECRET_KEY = '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'
AWS_REGION = 'eu-north-1'
AWS_BUCKET_NAME = 'parthsbucketop'
AWS_SCREENSHOT_FOLDER = 'screenshots/'
LOCAL_TEMP_PATH = '/tmp/capture_images/'


class ImageProcessing(http.Controller):

    @http.route('/capture/capture-image', type='http', auth='none', methods=['POST'], csrf=False)
    def capture_image(self, **kwargs):
        try:
            print("\n\n\n_____________capture-image________________", request.httprequest.headers)
            headers = request.httprequest.headers

            uploaded_files = []
            for key in request.httprequest.files.keys():
                if key.startswith('image'):
                    uploaded_files.append(request.httprequest.files.get(key))

            if not uploaded_files:
                return request.make_response(json.dumps({
                    "responseCode": 400,
                    "responseMessage": "No images uploaded",
                    "responseData": {}
                }), headers=[('Content-Type', 'application/json')])

            # Ensure temp path exists
            if not os.path.exists(LOCAL_TEMP_PATH):
                os.makedirs(LOCAL_TEMP_PATH)

            for uploaded_file in uploaded_files:
                filename = uploaded_file.filename
                base_name = os.path.splitext(filename)[0].replace(' ', '_')
                local_path = os.path.join(LOCAL_TEMP_PATH, base_name + '.jpg')

                with open(local_path, 'wb') as f:
                    uploaded_file.save(f)

                compressed_path = local_path.replace('.jpg', '.jpg')
                self.compress_image(local_path, compressed_path, quality=30)

                s3_path = AWS_SCREENSHOT_FOLDER + os.path.basename(compressed_path)
                uploaded = self.upload_to_s3(compressed_path, s3_path)

                # Cleanup
                if os.path.exists(local_path):
                    os.remove(local_path)
                if os.path.exists(compressed_path):
                    os.remove(compressed_path)

                if not uploaded:
                    return request.make_response(json.dumps({
                         "responseCode": 500,
                         "responseMessage": "Failed to upload to S3",
                         "responseData": {}
                     }), headers=[('Content-Type', 'application/json')])

            return request.make_response(json.dumps({
                "responseCode": 200,
                "responseMessage": "Success",
                "responseData": {}
            }), headers=[('Content-Type', 'application/json')])

        except Exception as e:
            _logger.exception("Error in /capture/capture-image")
            return request.make_response(json.dumps({
                "responseCode": 400,
                "responseMessage": f"Error: {str(e)}",
                "responseData": {}
            }), headers=[('Content-Type', 'application/json')])

    def compress_image(self, input_file, output_file, quality=30):
        """Compress the image and save to output_file."""
        try:
            img = Image.open(input_file)
            # Convert to RGB if PNG or GIF to save as JPEG
            if img.mode in ("RGBA", "P"):
                img = img.convert("RGB")
            img.save(output_file, "JPEG", quality=quality)
        except Exception as e:
            _logger.error(f"Image compression failed: {e}")
            raise

    def upload_to_s3(self, local_file_path, s3_path):
        """Upload a file to AWS S3."""
        s3_client = boto3.client('s3', region_name=AWS_REGION,
                                 aws_access_key_id=AWS_ACCESS_KEY,
                                 aws_secret_access_key=AWS_SECRET_KEY)
        try:
            s3_client.upload_file(local_file_path, AWS_BUCKET_NAME, s3_path)
            _logger.info(f"Uploaded file {local_file_path} to s3://{AWS_BUCKET_NAME}/{s3_path}")
            return True
        except (NoCredentialsError, ClientError) as e:
            _logger.error(f"S3 Upload error: {e}")
            return False



class CaptureDataController(http.Controller):

    @http.route('/capture/store-capture-data', type='http', auth='none', methods=['POST'], csrf=False)
    def store_capture_data(self, **post):
        print("\n\n________store-capture-data__________", request.httprequest.headers)
        try:
            # Parameters
            capture_type = int(post.get("capturetype", 0))
            user_id = int(post.get("userid", 0))
            app_id = int(post.get("applicationId", 0))
            capture_data = post.get("capturedata", "")
            mouse_data = post.get("mouse_capturedata", "")
            machine_detail = post.get("machinedetail", "")

            now = int(time.time())

            def create_capture(type_id, data):
                record = request.env['capture.data'].sudo().create({
                    'capture_type': type_id,
                    'user_id': user_id,
                    'time_tracking_application_id': app_id,
                    'capture_data': data.replace(".png", ".jpg"),
                    'machinedetail': machine_detail,
                    'creation_time': now
                })
                return record

            # Dual Save Flow (capturetype 5 = save 2 + 4)
            if capture_type == 5:
                create_capture(2, capture_data)
                create_capture(4, mouse_data)
            else:
                create_capture(capture_type, capture_data)

            return Response(
                status=200,
                content_type='application/json',
                response=http.json.dumps({
                    "responseCode": 200,
                    "responseMessage": "Success",
                    "responseData": {}
                })
            )
        except Exception as e:
            _logger.exception("Error storing capture data")
            return Response(
                status=500,
                content_type='application/json',
                response=http.json.dumps({
                    "responseCode": 500,
                    "responseMessage": str(e),
                    "responseData": {}
                })
            )

    @http.route('/capture/store-offline-capture-details', type='http', auth='none', csrf=False, methods=['POST'])
    def store_offline_capture_details(self, **post):
        _logger.info("Received Offline Capture Payload")
        print("\n\n________store_offline_capture_details__________")
        try:
            # Read raw POST data as JSON (for app sending raw JSON)
            raw_data = request.httprequest.data
            try:
                data = json.loads(raw_data)
            except Exception:
                return Response(
                    status=400,
                    content_type='application/json',
                    response=json.dumps({
                        "responseCode": 400,
                        "responseMessage": "Invalid JSON format",
                        "responseData": {}
                    })
                )

            # Handle both single dict and list of dicts
            if isinstance(data, dict):
                data = [data]

            now = int(time.time())
            capture_batch = []
            infringement_batch = []
            print("DEBUG: ****** data ******", data)
            """data = [{
                'iCaptureInfoType': '1', 
                'tiCaptureType': '5', 
                'txCaptureData': '0', 
                'mouse_capturedata': '0', 
                'vMachinedetail': '202.131.125.99', 
                'iUserId': '23', 
                'iTimeTrackingApplicationId': '0', 
                'infringementType': '0', 
                'iCreationCount': '240'
            }] """

            for row in data:
                capture_type = int(row.get("iCaptureInfoType", 0))
                user_id = int(row.get("iUserId", 0))
                app_id = int(row.get("iTimeTrackingApplicationId", 0))
                count = int(row.get("iCreationCount", 0))
                creation_time = now - count
                machine_detail = row.get("vMachinedetail", "")

                if capture_type == 1:
                    # Screenshot capture
                    tx_data = row.get("txCaptureData", "")
                    tx_data = tx_data.replace(".png", ".jpg")

                    if int(row.get("tiCaptureType", 0)) == 5:
                        capture_batch.append({
                            'capture_type': 2,
                            'user_id': user_id,
                            'time_tracking_application_id': app_id,
                            'capture_data': tx_data,
                            'machinedetail': machine_detail,
                            'creation_time': creation_time
                        })
                        capture_batch.append({
                            'capture_type': 4,
                            'user_id': user_id,
                            'time_tracking_application_id': app_id,
                            'capture_data': row.get("mouse_capturedata", ""),
                            'machinedetail': machine_detail,
                            'creation_time': creation_time
                        })
                    else:
                        capture_batch.append({
                            'capture_type': int(row.get("tiCaptureType", 0)),
                            'user_id': user_id,
                            'time_tracking_application_id': app_id,
                            'capture_data': tx_data,
                            'machinedetail': machine_detail,
                            'creation_time': creation_time
                        })

                elif capture_type == 2:
                    # Infringement
                    infringement_batch.append({
                        'type_id': int(row.get("infringementType", 0)),
                        'infringement_time': creation_time,
                        'machinedetail': machine_detail,
                        'user_id': user_id
                    })

            print("\nDEBUG: capture_batch", capture_batch)
            print("\nDEBUG: infringement_batch", infringement_batch)

            if capture_batch:
                request.env['capture.data'].sudo().create(capture_batch)

            if infringement_batch:
                request.env['infringement.data'].sudo().create(infringement_batch)

            return Response(
                status=200,
                content_type='application/json',
                response=json.dumps({
                    "responseCode": 200,
                    "responseMessage": "Offline capture data stored successfully",
                    "responseData": {}
                })
            )

        except Exception as e:
            _logger.exception("❌ Error storing offline capture data")
            return Response(
                status=500,
                content_type='application/json',
                response=json.dumps({
                    "responseCode": 500,
                    "responseMessage": str(e),
                    "responseData": {}
                })
            )

    @http.route('/capture/infringement', type='http', auth='none', methods=['POST'], csrf=False)
    def store_infringement_capture(self, **post):
        try:
            headers = request.httprequest.headers
            is_valid, error_response = self._validate_token(headers)
            if not is_valid:
                return Response(
                    status=400,
                    content_type='application/json',
                    response=json.dumps(error_response)
                )

            user_id = int(post.get("userid", 0))
            app_id = int(post.get("applicationId", 0))
            capture_type = int(post.get("capturetype", 0))
            capture_data = post.get("capturedata", "")
            mouse_data = post.get("mouse_capturedata", "")
            machinedetail = post.get("machinedetail", "")
            now = int(time.time())

            def create_record(capture_type, capture_data):
                if ".png" in capture_data:
                    capture_data = capture_data.replace(".png", ".jpg")
                return request.env['capture.data'].sudo().create({
                    'capture_type': capture_type,
                    'user_id': user_id,
                    'time_tracking_application_id': app_id,
                    'capture_data': capture_data,
                    'machinedetail': machinedetail,
                    'creation_time': now,
                })

            # Dual Save if capturetype is 5
            if capture_type == 5:
                rec1 = create_record(2, capture_data)
                rec2 = create_record(4, mouse_data)
                if rec1 and rec2:
                    return Response(
                        status=200,
                        content_type='application/json',
                        response=json.dumps({
                            "responseCode": 200,
                            "responseMessage": "Success",
                            "responseData": {}
                        })
                    )
                else:
                    raise Exception("Failed to save one or both records.")
            else:
                rec = create_record(capture_type, capture_data)
                if rec:
                    return Response(
                        status=200,
                        content_type='application/json',
                        response=json.dumps({
                            "responseCode": 200,
                            "responseMessage": "Success",
                            "responseData": {}
                        })
                    )
                else:
                    raise Exception("Failed to save capture record.")

        except Exception as e:
            _logger.exception("Error in /capture/infringement")
            return Response(
                status=500,
                content_type='application/json',
                response=json.dumps({
                    "responseCode": 500,
                    "responseMessage": str(e),
                    "responseData": {}
                })
            )