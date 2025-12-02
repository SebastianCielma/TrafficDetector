import gradio as gr
import requests
import time
import os

API_URL = os.getenv("API_URL", "http://localhost:8000")


def predict(video):
    with open(video, "rb") as f:
        files = {"file": f}
        response = requests.post(f"{API_URL}/api/v1/detect", files=files)
        task_id = response.json()["task_id"]

    while True:
        time.sleep(1)
        res = requests.get(f"{API_URL}/api/v1/status/{task_id}").json()
        status = res["status"]

        if status == "completed":
            return f"{API_URL}/results/{task_id}.mp4"
        elif status == "failed":
            return None


iface = gr.Interface(
    fn=predict,
    inputs=gr.Video(),
    outputs=gr.Video(),
    title="Traffic AI Master",
    allow_flagging="never"
)

if __name__ == "__main__":
    iface.launch(server_name="0.0.0.0", server_port=7860)