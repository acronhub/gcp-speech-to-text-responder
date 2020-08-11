import responder
import re
import os
import codecs
import ffmpeg
import datetime
import subprocess

from google.cloud import storage
from google.cloud import speech_v1p1beta1 as speech
from google.cloud.speech_v1p1beta1 import enums
from google.cloud.speech_v1p1beta1 import types

INPUT_FOLDER = './data/input_file'
CONVERT_PROGRESS = './data/convert_progress.txt'
CONVERTED_FOLDER = './data/convert_file'
OUTPUT_FOLDER = './data/output_text'
REGEXP_FOLDER = './data/regexp_text'

GCS_BUCKET_NAME = 'example-bucket'

ALLOWED_EXTENSIONS = ['mp4', 'm4a', 'mp3', 'wav']
SELECTED_HERTZ = [48000, 44100, 22100,]
SELECTED_CHANNEL = [1, 2, 4,]
SELECTED_PHRASES = []

api = responder.API()

convertfile_timedelta = datetime.timedelta()

@api.route('/')
async def api_response(req, resp):
    resp.content = api.template(
        'index.html',
        select_input=list_files(INPUT_FOLDER),
        select_convert=list_files(CONVERTED_FOLDER),
        select_transcribe=list_gcs(),
        select_regexp=list_files(OUTPUT_FOLDER),
        select_hertz=set(SELECTED_HERTZ),
        select_channels=set(SELECTED_CHANNEL)
    )

@api.route('/convert')
async def api_response(req, resp):
    if req.method == "post":
        data = await req.media()
        filename = data.get('filename')
        if filename == '':
            print('ファイルを選択してください')
        if allwed_file(filename):
            try:
                os.remove(CONVERT_PROGRESS)
            except OSError as e:
                print(e)
            convert_flac(filename)
            print('FLACファイルを作成しました')
    api.redirect(resp, '/')

@api.route('/upload')
async def api_response(req, resp):
    if req.method == "post":
        data = await req.media()
        filename = data.get('filename')
        if filename == '':
            print('ファイルを選択してください')
        if filename.rsplit('.', 1)[1].lower() in 'flac':
            upload_gcs(filename)
            print('ストレージにアップロードしました')
    api.redirect(resp, '/')

@api.route('/transcribe')
async def api_response(req, resp):
    if req.method == "post":
        data = await req.media()
        filename = data.get('filename')
        if filename == '':
            print('ファイルを選択してください')
        gcs_uri = os.path.join("gs://", GCS_BUCKET_NAME, filename)
        transcribe_gcs(gcs_uri, data.get('hertz'), data.get('channel'))
        print('文字起こししました')
    api.redirect(resp, '/')

@api.route('/regexp')
async def api_response(req, resp):
    if req.method == "post":
        data = await req.media()
        filename = data.get('filename')
        if filename == '':
            print('ファイルを選択してください')
        if filename.rsplit('.', 1)[1].lower() in 'txt':
            regexp_text(filename)
            print('改行しました')
    api.redirect(resp, '/')

@api.route('/progress')
async def api_response(req, resp):
    remaining_time = -1

    try:
        # 変換ログを抽出
        line = subprocess.check_output(['tail', '-9', CONVERT_PROGRESS])
        result = re.findall(r'out_time_ms=(-?[\d]+)', line.decode('utf-8'))
        if result is not None and result != []:
            out_time_ms = float(result[0])
            if out_time_ms > 0:
                timedelta = datetime.timedelta(microseconds=out_time_ms)

                # 経過割合
                remaining_time = timedelta / convertfile_timedelta * 100

                # 完了チェック
                if remaining_time >= 100:
                    os.remove(CONVERT_PROGRESS)
    except subprocess.CalledProcessError:
        pass

    resp.media = {"status": 200, "time": remaining_time}


# .があるかどうかのチェックと、拡張子の確認
def allwed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# FLACファイルに変換
@api.background.task
def convert_flac(filename):
    inputfilepath = os.path.join(INPUT_FOLDER, filename)

    outputfile = filename.rsplit('.', 1)[0].lower()
    today = datetime.datetime.today().strftime("%Y%m%d-%H%M%S")
    outputfilename = '{0}-{1}.flac'.format(today, outputfile)
    outputfilepath = os.path.join(CONVERTED_FOLDER, outputfilename)

    probe = subprocess.check_output(['ffprobe', inputfilepath, '-hide_banner',  '-show_entries', 'format=duration'])
    result = re.findall(r'duration=([\d.]+)', probe.decode('utf-8'))
    if result is not None:
        global convertfile_timedelta
        convertfile_timedelta = datetime.timedelta(seconds=float(result[0]))

    # 変換＆保存
    (
        ffmpeg
        .input(inputfilepath)
        .output(outputfilepath)
        .global_args('-progress', CONVERT_PROGRESS)
        .overwrite_output()
        .run()
    )
    return outputfilepath, outputfilename

# 文字起こし
@api.background.task
def transcribe_gcs(gcs_uri, hertz, channel):
    client = speech.SpeechClient()

    audio = types.RecognitionAudio(uri=gcs_uri)
    config = types.RecognitionConfig(
        encoding=enums.RecognitionConfig.AudioEncoding.FLAC, # flacの設定
        sample_rate_hertz=int(hertz), # ヘルツは音声ファイルに合わせる
        audio_channel_count = int(channel),
        language_code='ja-JP', # 日本語音声の場合
        enable_speaker_diarization=True, # 異なる話者の分離
        enable_automatic_punctuation=True, # 句読点
        speech_contexts=SELECTED_PHRASES # 音声適応ブースト
    )
    operation = client.long_running_recognize(config, audio)

    print('Waiting for operation to complete...')
    operationResult = operation.result()

    filename = gcs_uri.rsplit('/', 1)[1].split('.')[0] + ".txt"
    outputfilepath = os.path.join(OUTPUT_FOLDER, filename)
    fout = codecs.open(outputfilepath, 'a', 'utf-8')
    for result in operationResult.results:
        for alternative in result.alternatives:
            fout.write(u'{}\n'.format(alternative.transcript))
    fout.close()

# 文末改行
def regexp_text(filename):
    inputfilepath = os.path.join(OUTPUT_FOLDER, filename)
    filename = inputfilepath.rsplit('/', 1)[1].split('.')[0] + ".txt"
    outputfilepath = os.path.join(REGEXP_FOLDER, filename)

    fout = codecs.open(outputfilepath, 'a', 'utf-8')
    with open(inputfilepath) as f:
        while True:
            line = f.readline()
            line = re.sub(r'です(?![か|が|ね|けど])', "です。\n", line)
            line = re.sub(r'ます(?![が|ね|ので|こと|と|し])', "ます。\n", line)
            line = re.sub(r'(?![く|と])した(?![ち|い|が|ところ|こと|もの|から|よう])', "した。\n", line)
            fout.write(u'{}'.format(line))
            if not line:
                break
    fout.close()

# フォルダ内のファイル取得
def list_files(path):
    files = os.listdir(path)
    files_file = [
        f for f in files
            if os.path.isfile(os.path.join(path, f)) and not f.startswith('.')
    ]
    return files_file

# GCS ファイル取得
def list_gcs():
    storage_client = storage.Client()
    blobs = storage_client.list_blobs(GCS_BUCKET_NAME)
    return blobs

# GCS ファイルアップロード
def upload_gcs(filename):
    inputfilepath = os.path.join(CONVERTED_FOLDER, filename)

    storage_client = storage.Client()
    bucket = storage_client.get_bucket(GCS_BUCKET_NAME)
    blob = bucket.blob(filename)
    blob.upload_from_filename(filename=inputfilepath)
