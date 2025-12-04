import os
import shutil
import time

import gradio as gr
import requests

API_URL = os.getenv("API_URL", "http://localhost:8000")


def predict(video):
    if video is None:
        return None

    print(f"Uploading video: {video}")
    try:
        with open(video, "rb") as f:
            files = {"file": f}
            response = requests.post(f"{API_URL}/api/v1/detect", files=files)

        if response.status_code != 202:
            print(f"API Error: {response.text}")
            return None

        task_id = response.json()["task_id"]
        print(f"Task ID: {task_id}")
    except Exception as e:
        print(f"Connection Error: {e}")
        return None

    while True:
        time.sleep(2)
        try:
            res = requests.get(f"{API_URL}/api/v1/status/{task_id}")
            if res.status_code != 200:
                print(f"Status check failed: {res.status_code}")
                continue

            data = res.json()
            status = data["status"]
            print(f"Status: {status}")

            if status == "completed":
                raw_url = data["result_url"]

                if raw_url.startswith("http"):
                    download_url = raw_url
                else:
                    download_url = f"{API_URL}{raw_url}"

                local_filename = f"result_{task_id}.mp4"

                print(f"Downloading result from: {download_url}")

                with requests.get(download_url, stream=True) as r:
                    r.raise_for_status()
                    with open(local_filename, "wb") as f:
                        shutil.copyfileobj(r.raw, f)

                print("Done!")
                return local_filename

            elif status == "failed":
                print(f"Processing failed: {data.get('error_message')}")
                return None

        except Exception as e:
            print(f"Polling Error: {e}")


iface = gr.Interface(
    fn=predict, inputs=gr.Video(), outputs=gr.Video(), title="Traffic AI Master"
)

if __name__ == "__main__":
    iface.launch(server_name="0.0.0.0", server_port=7860)
