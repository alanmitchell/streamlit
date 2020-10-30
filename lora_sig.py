import time
from pathlib import Path
import streamlit

last_post_path = '../an-api/lora-data/lora-last.txt'

def run():

    streamlit.markdown("# LoRa Signal Strength Data")


    start_button = streamlit.button('Start Receiving')
    if start_button:
        txt_last_post = streamlit.empty()
        for i in range(3):
            if Path(last_post_path).exists():
                last_post = open(last_post_path).read()
                txt_last_post.text(last_post)
            else:
                txt_last_post.text('No Data')
            time.sleep(2)
        txt_last_post.empty()
