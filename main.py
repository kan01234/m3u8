import argparse
import random
from urllib.parse import urlparse
import requests
import os
import threading
import shutil
import subprocess
import uuid
from atomic import AtomicLong
from tqdm import tqdm
import json
import copy
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

user_agents = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36',
    'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:54.0) Gecko/20100101 Firefox/54.0',
    'Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:54.0) Gecko/20100101 Firefox/54.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.12; rv:54.0) Gecko/20100101 Firefox/54.0'
]

parser = argparse.ArgumentParser(description='Make a GET request to a URL.')
parser.add_argument('url', type=str, help='the URL to make a request to')
parser.add_argument('--m3u8', type=str, default='', help='location of m3u8 file')
parser.add_argument('--ssl', type=bool, default=True, help='ssl verfiy')
parser.add_argument('--headers', nargs='*', default=[], help='List of HTTP request headers')
args = parser.parse_args()

base_headers = {}
for header in args.headers:
    key, value = header.split(':', maxsplit=1)
    base_headers[key.strip()] = value.strip()

ssl_verify = args.ssl

retry_strategy = Retry(
  total=10,
  backoff_factor=1
)

adapter = HTTPAdapter(max_retries=retry_strategy)
http = requests.Session()
http.mount("https://", adapter)
http.mount("http://", adapter)

# Set up the headers
def build_request_header(url):
    headers = copy.copy(base_headers)
    parsed_url = urlparse(url)
    headers['Host'] = parsed_url.netloc
    # headers['User-Agent'] = random.choice(user_agents)
    # Set up the user agent
    return headers

def get_request(url):
    response = http.get(url, headers=build_request_header(url), verify=ssl_verify)
    return response

# -------------------------------------------------------------------------

def read_m3u8(m3u8_url, m3u8_path):
  if (m3u8_path):
    m3u8_contents = read_local_m3u8(m3u8_path)
  else:
    m3u8_contents = read_m3u8_url(m3u8_url)
  print(m3u8_contents)
  video_urls = []
  base_url = '/'.join(m3u8_url.split('/')[:-1])
  for line in m3u8_contents.split('\n'):
    if not line or line.startswith('#'):
      continue
    if line.startswith('http'):
      video_urls.append(line.strip())
    else:
      video_urls.append(f'{base_url}/{line.strip()}')
  return video_urls

def read_m3u8_url(m3u8_url):
  m3u8_contents = get_request(m3u8_url).text
  return m3u8_contents

def read_local_m3u8(path):
  with open(f'{path}', 'r') as f:
    lines = f.read()
    return lines

def worker(array, start_idx, end_idx, dir, count, process_bar):
  for i in range(start_idx, end_idx):
    video_url = array[i]
    # get ts files
    with open(f'{os.path.join(dir, f"{i}.ts")}', 'wb') as f:
      response = get_request(video_url)
      f.write(response.content)
    count += 1
    process_bar.update(1)

def download_ts_multi_thread(video_urls, dir, num_threads = 5):
  if (len(video_urls) <= 0):
    return

  # calc chunk size
  chunk_size = int(len(video_urls) / num_threads)

  # create threads
  threads = []
  count = AtomicLong(0)
  process_bar = tqdm(total=len(video_urls))
  for i in range(num_threads):
    start_idx = i * chunk_size
    end_idx = start_idx + chunk_size
    if i == num_threads - 1:
        end_idx = len(video_urls)
    t = threading.Thread(target=worker, args=(video_urls, start_idx, end_idx, dir, count, process_bar))
    threads.append(t)
    t.start()

  # join all threads
  for t in threads:
    t.join()

  # join ts files
  with open(f'{os.path.join(dir, "input.txt")}', 'w') as f:
    for i in range(len(video_urls)):
      f.write(f"file '{os.path.join(os.getcwd(), dir, f'{i}.ts')}'\n")
  
  # close process_bar
  process_bar.close()

def m3u8_to_mp4():
  try:
    # make tmp directory
    tmpdir = f'{str(uuid.uuid4())[:8]}-tmp'
    output_file = 'output.mp4'
    os.mkdir(tmpdir)

    # read from args
    url = args.url

    # load m3u8 file
    video_urls = read_m3u8(url, args.m3u8)

    # load ts files
    ts_files = download_ts_multi_thread(video_urls, tmpdir)

    # # convert to mp4 with ffmpeg
    subprocess.call(f'ffmpeg -f concat -safe 0 -i {os.path.join(tmpdir, "input.txt")} -c copy {output_file}', shell=True)
    shutil.rmtree(tmpdir)
  finally:
    print()

if __name__ == '__main__':
  m3u8_to_mp4()