# Run this in a Google Colab cell to launch the Streamlit app via ngrok.
#
# Before running, set your ngrok auth token as an environment variable /
# Colab secret instead of hardcoding it in the notebook:
#   from google.colab import userdata
#   os.environ["NGROK_AUTH_TOKEN"] = userdata.get("NGROK_AUTH_TOKEN")
# (Colab -> key icon in the left sidebar -> "Secrets" -> add NGROK_AUTH_TOKEN)
#
# Get/rotate a token at https://dashboard.ngrok.com/get-started/your-authtoken

# Step 1: Install all required Python packages
!pip install streamlit pyngrok numpy pandas matplotlib plotly reportlab -q

import os
from pyngrok import ngrok

# Step 2: Read the ngrok auth token from the environment (never hardcode it)
auth_token = os.environ.get("NGROK_AUTH_TOKEN")
if not auth_token:
    raise RuntimeError(
        "NGROK_AUTH_TOKEN is not set. Set it via a Colab secret or "
        "os.environ before running this cell."
    )
ngrok.set_auth_token(auth_token)

# Step 3: Stop any previous running instances to prevent port conflicts
os.system("pkill streamlit")
ngrok.kill()

# Step 4: Start Streamlit in the background
os.system("streamlit run app.py &")

# Step 5: Generate the public URL
public_url = ngrok.connect(8501)
print(f"Your Interactive Colab App is Live at: {public_url}")
