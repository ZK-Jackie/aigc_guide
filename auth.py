import os
import jwt
import time
from fastapi import Header, HTTPException, Request
from dotenv import load_dotenv

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"
BLACKLIST_FILE = "blacklist.txt"

def verify_token(req: Request, token: str=Header()):
    """
    验证token
    :param req:  请求
    :param token:  token
    :return:  None
    """
    try:
        decoded_payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        print(f"INFO:     {req.client.host} | {time.asctime()} | Decode Success: ", decoded_payload)
    except jwt.ExpiredSignatureError:
        print(f"INFO:     {req.client.host} | {time.asctime()} | Token Expired")
        raise HTTPException(status_code=401, detail="Expired Token")
    except jwt.InvalidTokenError:
        print(f"INFO:     {time.asctime()} | Invalid Token from {req.client.host}")
        # 不合法，添加到黑名单中
        save_to_blacklist(req.client.host)
        raise HTTPException(status_code=401, detail="Expired Token")


def generate_token(params: dict) -> str:
    """
    生成token
    :param params:  参数
    :return:  token
    """
    return jwt.encode(params, SECRET_KEY, algorithm=ALGORITHM)

def verify_host(req: Request):
    """
    验证请求来源
    :param req:  请求
    :return:  是否验证通过
    """
    client_ip = req.client.host
    blacklist = load_blacklist()
    # ip 在黑名单中
    if client_ip in blacklist:
        raise HTTPException(status_code=401, detail="Expired Token")
    # ip 不在黑名单中
    else:
        return True


def load_blacklist():
    if not os.path.exists(BLACKLIST_FILE):
        return set()
    with open(BLACKLIST_FILE, "r") as file:
        return set(line.strip() for line in file)


def save_to_blacklist(client_ip):
    blacklist = load_blacklist()
    if client_ip in blacklist:
        print(f"INFO:     {client_ip} | {time.asctime()} | {client_ip} is already in blacklist")
        return
    with open(BLACKLIST_FILE, "a") as file:
        print(f"INFO:     {client_ip} | {time.asctime()} | {client_ip} has added to blacklist")
        file.write(f"{client_ip}\n")



if __name__ == "__main__":
    test_dict = {
        "session_id": "test",
        "input": "你好你好你好",
        "output": ""
    }
    test_token = generate_token(test_dict)
    print(test_token)
    test_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1dWlkIjoiZTFlZTc4NTMtMzQxNi00OTE1LTkyYzgtYzZjYjg5MzkzMTkyIiwiaWF0IjoxNzI0NjUwNjcxLCJleHAiOjE3MjQ2NTA5NzF9.AYMCkEs-wlb635FiKpcGF-VAX7V0tozzW2GjncMzbUQ"
    verify_token(None, test_token)
