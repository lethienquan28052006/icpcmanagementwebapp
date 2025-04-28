import time
import random
import string
import hashlib
import httpx
from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse

# ==== Khởi tạo app FastAPI ====

global_contest_id = [599051, 570856]

app = FastAPI()
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

# ==== Codeforces API key/secret ====
API_KEY = "12b0d3dffa133a35baf0468e1593f8af729030c5"
API_SECRET = "9dd282d3b9afcc3973a9e15865fbae9e94098ca8"

# ==== Hàm hỗ trợ ký API ====

def generate_random_string(length=6):
    letters = string.ascii_lowercase + string.digits
    return ''.join(random.choice(letters) for _ in range(length))

def build_signed_url(method_name, params):
    params["apiKey"] = API_KEY
    params["time"] = str(int(time.time()))
    sorted_params = sorted(params.items())
    param_str = '&'.join(f"{k}={v}" for k, v in sorted_params)

    random_str = generate_random_string()
    string_to_hash = f"{random_str}/{method_name}?{param_str}#{API_SECRET}"
    hash_object = hashlib.sha512(string_to_hash.encode('utf-8'))
    apiSig = random_str + hash_object.hexdigest()

    full_url = f"https://codeforces.com/api/{method_name}?{param_str}&apiSig={apiSig}"
    return full_url

# ==== Hàm lấy dữ liệu standings có xác thực ====

async def get_private_scoreboard(contest_id: int):
    method_name = "contest.standings"
    params = {
        "contestId": contest_id,
        "from": 1,
        "count": 200,
        "showUnofficial": "true"
    }
    url = build_signed_url(method_name, params)
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        return response.json()

async def get_group_members(group_id):
    method_name = "group.listMembers"
    params = {
        "groupId": group_id
    }
    url = build_signed_url(method_name, params)
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(url)
        return response.json()

# ==== Route chính ====

# Hàm lấy danh sách thành viên của nhóm Codeforces
async def get_group_members(group_id: int):
    with open("member.txt", "r", encoding="utf-8") as f:
        members = [line.strip() for line in f if line.strip()]
    return members


@app.get("/overall_ranking", response_class=HTMLResponse)
async def overall_ranking(request: Request):
    contest_ids = global_contest_id  # ví dụ: danh sách contest mà bạn quan tâm
    user_scores = defaultdict(int)  # mapping: handle -> số bài solved
    group_id = "your_group_id_here"  # ID của nhóm Codeforces, không cần thiết lắm
    group_members_data = await get_group_members(group_id)

    # Lấy danh sách thành viên của nhóm
    group_members_set = set(member.lower() for member in group_members_data)

    for contest_id in contest_ids:
        data = await get_private_scoreboard(contest_id)
        if data["status"] == "OK":
            rows = data["result"]["rows"]
            for row in rows:
                members = row["party"].get("members", [])
                if members:
                    handle = members[0]["handle"]
                    if handle.lower() in group_members_set:
                        problems_solved = sum(1 for problem in row["problemResults"] if problem["points"] > 0)
                        user_scores[handle] += problems_solved

    sorted_users = sorted(user_scores.items(), key=lambda x: x[1], reverse=True)

    return templates.TemplateResponse("overall_ranking.html", {"request": request, "ranking": sorted_users})


# === contest detail ===

@app.get("/contest_detail", response_class=HTMLResponse)
async def contests_list(request: Request):
    contest_ids = global_contest_id  # <-- List các contest ID

    contest_infos = []
    for contest_id in contest_ids:
        data = await get_private_scoreboard(contest_id)
        if data["status"] == "OK":
            contest_name = data["result"].get("contest", {}).get("name", f"Contest {contest_id}")
            contest_infos.append({
                "id": contest_id,
                "name": contest_name
            })
    
    return templates.TemplateResponse("contest_list.html", {
        "request": request,
        "contests": contest_infos
    })

@app.get("/contest/{contest_id}", response_class=HTMLResponse)
async def contest_detail(contest_id: int, request: Request):
    data = await get_private_scoreboard(contest_id)
    if data["status"] == "OK":
        rows = data["result"]["rows"]
        problems = data["result"]["problems"]
    else:
        rows = []
        problems = []

    return templates.TemplateResponse("contest_detail.html", {
        "request": request,
        "rows": rows,
        "problems": problems,
        "contest_id": contest_id
    })

# Bảng tổng chỉ số sức mạnh

from collections import defaultdict
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    contest_ids = global_contest_id
    user_scores = defaultdict(int)

    try:
        for contest_id in contest_ids:
            data = await get_private_scoreboard(contest_id)
            if data.get("status") == "OK":
                rows = data["result"]["rows"]
                for row in rows:
                    members = row.get("party", {}).get("members", [])
                    if members:
                        handle = members[0].get("handle", "unknown")
                        problems = row.get("problemResults", [])
                        solved = sum(1 for p in problems if p.get("points", 0) > 0)
                        user_scores[handle] += solved
            else:
                print(f"Error fetching contest {contest_id}: {data}")
    except Exception as e:
        print(f"Error: {e}")

    # Đảm bảo sorted_users là list of tuples (handle, solved)
    sorted_users = sorted(user_scores.items(), key=lambda x: x[1], reverse=True)

    # Kiểm tra lại xem sorted_users có đúng định dạng không
    print("Sorted Users:", sorted_users)

    return templates.TemplateResponse("scoreboard.html", {
        "request": request,
        "ranking": sorted_users
    })

# Thêm đoạn này để chạy app khi file này được gọi trực tiếp
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
