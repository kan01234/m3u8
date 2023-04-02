import requests
import os
import threading
import tempfile
import shutil
import subprocess
import pathlib
import uuid

from AtomicInteger import AtomicInt
from config import headers

# Define the M3U8 URL and custom header
m3u8_url = 'https://javday.space/videos/63728722e0e879f52274b36c/02ecf4/index.m3u8'

def read_m3u8(m3u8_contents, headers = {}):
  m3u8_contents = requests.get(m3u8_url, headers=headers)
  video_urls = []
  for line in m3u8_contents.split('\n'):
    if line.startswith('#'):
      continue
    video_urls.append(line.strip())
  return video_urls

def worker(array, start_idx, end_idx, dir, count, headers = {}):
  for i in range(start_idx, end_idx):
    video_url = array[i]
    # get ts files
    with open(f'{os.path.join(dir, f"{i}.ts")}', 'wb') as f:
      response = requests.get(video_url, headers=headers)
      f.write(response.content)
    print(f'finish {count} of {len(array)}\n')

def download_ts_multi_thread(video_urls, headers, dir, num_threads = 10):
  if (len(video_urls) <= 0):
    return

  # calc chunk size
  chunk_size = int(len(video_urls) / num_threads)

  # create threads
  threads = []
  count = AtomicInt()
  for i in range(num_threads):
    start_idx = i * chunk_size
    end_idx = start_idx + chunk_size
    if i == num_threads - 1:
        end_idx = len(video_urls)
    t = threading.Thread(target=worker, args=(video_urls, start_idx, end_idx, dir, count, headers))
    threads.append(t)
    t.start()

  # join all threads
  for t in threads:
    t.join()

  # join ts files
  with open(f'{os.path.join(dir, "input.txt")}', 'w') as f:
    for i in range(len(video_urls)):
      f.write(f"file '{os.path.join(os.getcwd(), dir, f'{i}.ts')}'\n")
  
def m3u8_to_mp4():
  try:
    # make tmp directory
    tmpdir = f'{str(uuid.uuid4())[:8]}-tmp'
    output_file = 'output.mp4'
    os.mkdir(tmpdir)

    # load m3u8 file
    video_urls = read_m3u8(m3u8_url, headers)

    # load ts files
    ts_files = download_ts_multi_thread(video_urls, headers, tmpdir)

    # convert to mp4 with ffmpeg
    subprocess.call(f'ffmpeg -f concat -safe 0 -i {os.path.join(tmpdir, "input.txt")} -c copy {output_file}', shell=True)
  finally:
    shutil.rmtree(tmpdir)
    print()

if __name__ == '__main__':
  m3u8_to_mp4()