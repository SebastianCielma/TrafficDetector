import os
import shutil
import time

import gradio as gr
import requests

API_URL = os.getenv("API_URL", "http://localhost:8000")


def predict(video):
    if video is None:
        return None

    # 1. Upload
    try:
        with open(video, "rb") as f:
            files = {"file": f}
            response = requests.post(f"{API_URL}/api/v1/detect", files=files)

        if response.status_code != 200:
            return None

        task_id = response.json()["task_id"]
    except Exception as e:
        print(f"Błąd połączenia: {e}")
        return None

    while True:
        time.sleep(1)
        try:
            res = requests.get(f"{API_URL}/api/v1/status/{task_id}").json()
            status = res["status"]

            if status == "completed":
                download_url = f"{API_URL}/results/{task_id}.mp4"
                local_filename = f"temp_result_{task_id}.mp4"

                with requests.get(download_url, stream=True) as r:
                    r.raise_for_status()
                    with open(local_filename, "wb") as f:
                        shutil.copyfileobj(r.raw, f)

                return local_filename

            elif status == "failed":
                print("Przetwarzanie nieudane po stronie API")
                return None

        except Exception as e:
            print(f"Błąd podczas odpytywania API: {e}")
            return None


iface = gr.Interface(
    fn=predict, inputs=gr.Video(), outputs=gr.Video(), title="Traffic AI Master"
)

if __name__ == "__main__":
    iface.launch(server_name="0.0.0.0", server_port=7860)
