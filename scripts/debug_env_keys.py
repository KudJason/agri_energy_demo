from dotenv import dotenv_values
import os

env_path = "/Users/jasonjia/Documents/industry_policy/secret/.env"

if not os.path.exists(env_path):
    print(f"File not found: {env_path}")
else:
    config = dotenv_values(env_path)
    print("Keys found in .env:", list(config.keys()))
