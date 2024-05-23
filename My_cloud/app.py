import os
from flask import Flask, request, jsonify, render_template
from werkzeug.utils import secure_filename
import boto3
import pypandoc
import time

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['CONVERTED_FOLDER'] = 'converted'
app.config['ALLOWED_INPUT_FORMATS'] = {'txt', 'doc', 'docx'}
app.config['ALLOWED_OUTPUT_FORMATS'] = {'doc', 'docx', 'pdf'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_INPUT_FORMATS']

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/convert', methods=['POST'])
def convert_file():
    if 'file' not in request.files:
        return jsonify(error='No file part'), 400

    file = request.files['file']
    input_format = request.form.get('input_format')
    output_format = request.form.get('output_format')

    if not input_format or not output_format:
        return jsonify(error='Input and output formats must be specified'), 400

    if file.filename == '':
        return jsonify(error='No selected file'), 400

    if file and allowed_file(file.filename):
        try:
            start_time = time.time()
            os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
            os.makedirs(app.config['CONVERTED_FOLDER'], exist_ok=True)

            file.save(os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(file.filename)))
            input_path = os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(file.filename))
            output_filename = secure_filename(file.filename.rsplit('.', 1)[0] + '.' + output_format)
            output_path = os.path.join(app.config['CONVERTED_FOLDER'], output_filename)

            pypandoc.convert_file(input_path, output_format, outputfile=output_path)

            # AWS credentials configuration
            s3 = boto3.client(
                's3',
                aws_access_key_id='AKIA4MTWL7VCLFPZDT7H',
                aws_secret_access_key='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',
                region_name='us-east-1'
            )

            with open(output_path, 'rb') as f:
                s3.upload_fileobj(f, 'document-conversion-buckett', output_filename)

            end_time = time.time()
            conversion_time = end_time - start_time

            return jsonify(message='File converted successfully', output_file=output_filename, conversion_time=conversion_time), 200
        except Exception as e:
            return jsonify(error=str(e)), 500
    else:
        return jsonify(error='File not allowed'), 400

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
