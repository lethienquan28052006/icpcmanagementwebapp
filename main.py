# main.py
from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import httpx
from backend.models import Base, Contest, Solver, Problem, Standing  # Import Standing model
from backend.sign_url import build_signed_url

app = FastAPI()
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

DATABASE_URL = "sqlite:///./contests.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
Session = sessionmaker(bind=engine)
Base.metadata.create_all(bind=engine)

API_KEY = "12b0d3dffa133a35baf0468e1593f8af729030c5"
API_SECRET = "9dd282d3b9afcc3973a9e15865fbae9e94098ca8"

CONTEST_IDS = [567974, 558527, 556749, 554579, 553549, 552568]

def fetch_contest_info(contest_id: int):
    """
    Fetch contest information from the Codeforces API for a given contest ID.

    Args:
        contest_id (int): The ID of the contest to fetch.

    Returns:
        dict or None: The contest information dictionary if successful, otherwise None.
    """
    # Fetch contest data from the Codeforces API
    method = "contest.standings"
    params = {
        "contestId": contest_id,
        "from": 1,
        "count": 1,
        "showUnofficial": "true"
    }
    signed_url = build_signed_url(method, params)

    try:
        response = httpx.get(signed_url)
        print(f"📡 Fetching contest {contest_id}: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            if data["status"] == "OK":
                return data["result"]["contest"]
            else:
                print("❌ Lỗi API:", data)
        else:
            print(f"❌ Status: {response.status_code}")
    except Exception as e:
        print(f"❌ Exception: {e}")
    return None

@app.post("/update-contests")
def update_contests():
    """
    Update contests and standings in the database from the Codeforces API.

    Returns:
        dict: A message indicating how many contests were added or updated.
    """
    # Update contests and standings in the database
    db = Session()
    added = 0
    updated = 0

    for contest_id in CONTEST_IDS:
        # Fetch contest data from the Codeforces API
        contest_data = fetch_contest_info(contest_id)
        if contest_data:
            # Check if the contest already exists
            existing_contest = db.query(Contest).filter(Contest.id == contest_id).first()
            if existing_contest:
                # Update existing contest details
                existing_contest.name = contest_data["name"]
                existing_contest.type = contest_data["type"]
                existing_contest.phase = contest_data["phase"]
                existing_contest.durationSeconds = contest_data["durationSeconds"]
                db.commit()
                updated += 1
                print(f"🔄 Updated contest {contest_data['name']}.")
            else:
                # Add new contest to the database
                new_contest = Contest(
                    id=contest_data["id"],
                    name=contest_data["name"],
                    type=contest_data["type"],
                    phase=contest_data["phase"],
                    durationSeconds=contest_data["durationSeconds"]
                )
                db.add(new_contest)
                db.commit()
                added += 1
                print(f"✅ Added contest {contest_data['name']}.")

            # Fetch and update/add standings for the contest
            standings = fetch_contest_standings(contest_id)
            if standings:
                # Delete existing standings for the contest
                db.query(Standing).filter(Standing.contest_id == contest_id).delete()
                db.commit()

                # Add updated standings
                for standing in standings:
                    new_standing = Standing(
                        handle=standing["handle"],
                        rank=standing["rank"],
                        problems_solved=standing["problems_solved"],
                        contest_id=contest_id
                    )
                    db.add(new_standing)
                db.commit()
                print(f"🔄 Updated standings for contest {contest_data['name']}.")

    db.close()
    return {"message": f"Added {added} new contests, updated {updated} existing contests."}


@app.get("/update-contests")
def update_contests_get():
    """
    HTTP GET endpoint to trigger updating contests and standings.

    Returns:
        dict: A message indicating how many contests were added or updated.
    """
    return update_contests()


@app.get("/contest/{contest_id}/standings", response_class=HTMLResponse)
async def contest_standings(request: Request, contest_id: int):
    """
    Render the standings page for a specific contest.

    Args:
        request (Request): The incoming HTTP request.
        contest_id (int): The ID of the contest.

    Returns:
        TemplateResponse: The rendered standings.html template.
    """
    db = Session()
    contest = db.query(Contest).filter(Contest.id == contest_id).first()
    if not contest:
        db.close()
        return templates.TemplateResponse("error.html", {"request": request, "message": "Contest not found"})

    standings = db.query(Standing).filter(Standing.contest_id == contest_id).all()
    db.close()

    # Convert standings to a list of dictionaries for the template
    standings_data = [
        {
            "handle": standing.handle,
            "rank": standing.rank,
            "problems_solved": standing.problems_solved
        }
        for standing in standings
    ]

    return templates.TemplateResponse("standings.html", {
        "request": request,
        "contest": contest,
        "standings": standings_data
    })

def fetch_contest_standings(contest_id: int):
    """
    Fetch standings for a given contest from the database.

    Args:
        contest_id (int): The ID of the contest.

    Returns:
        list: A list of dictionaries containing handle, rank, and problems solved.
    """
    db = Session()
    try:
        # Query the standings for the given contest ID
        standings = db.query(Standing).filter(Standing.contest_id == contest_id).all()

        # Convert the standings to a list of dictionaries
        standings_data = [
            {
                "handle": standing.handle,
                "rank": standing.rank,
                "problems_solved": standing.problems_solved
            }
            for standing in standings
        ]
        return standings_data
    except Exception as e:
        print(f"❌ Exception while fetching standings from the database: {e}")
        return []
    finally:
        db.close()

@app.get("/member/{handle}", response_class=HTMLResponse)
@app.get("/member", response_class=HTMLResponse)
async def member_info(request: Request, handle: str = None):
    """
    Render the statistics page for a specific member (user).

    Args:
        request (Request): The incoming HTTP request.
        handle (str, optional): The handle (username) of the member.

    Returns:
        TemplateResponse: The rendered member.html template with member statistics.
    """
    # this function will provide the statistic of each member.
    if not handle:
        handle = request.query_params.get("handle")  # Get handle from query parameters

    db = Session()

    # Fetch contests and standings for the member
    contests = db.query(Contest).all()
    member_data = []
    for contest in contests:
        standings = fetch_contest_standings(contest.id)
        for row in standings:
            if row["handle"] == handle:
                member_data.append({
                    "contest_name": contest.name,
                    "rank": row.get("rank", None),  # Add rank if available
                    "problems_solved": row["problems_solved"]
                })

    db.close()

    # Pass the member data to the template
    return templates.TemplateResponse("member.html", {
        "request": request,
        "handle": handle,
        "member_data": member_data
    })


# get problems name

def fetch_problem_names(contest_id: int):
    """
    Fetch all problem names for a given contest from the database.

    Args:
        contest_id (int): The ID of the contest.

    Returns:
        list: A list of problem names for the contest.
    """
    db = Session()
    try:
        # Query the problems for the given contest ID
        problems = db.query(Problem).filter(Problem.contest_id == contest_id).all()

        # Extract problem names
        problem_names = [problem.name for problem in problems]
        return problem_names
    except Exception as e:
        print(f"❌ Exception while fetching problems from the database: {e}")
        return []
    finally:
        db.close()


from sqlalchemy import func

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """
    Render the home page with contest list, top solvers, and problems for each contest.

    Args:
        request (Request): The incoming HTTP request.

    Returns:
        TemplateResponse: The rendered home.html template.
    """
    db = Session()
    contests = db.query(Contest).all()  # Fetch all contests

    # Aggregate problems solved by each solver across all contests
    solver_stats = {}
    contest_problems = {}  # Dictionary to store problem names for each contest

    for contest in contests:
        # Fetch standings for the contest
        standings = fetch_contest_standings(contest.id)
        for row in standings:
            handle = row["handle"]
            problems_solved = row["problems_solved"]
            if handle not in solver_stats:
                solver_stats[handle] = 0
            solver_stats[handle] += problems_solved

        # Fetch problem names for the contest
        contest_problems[contest.id] = fetch_problem_names(contest.id)

    # Sort solvers by total problems solved and get the top 10
    top_solvers = sorted(solver_stats.items(), key=lambda x: x[1], reverse=True)[:10]

    db.close()
    return templates.TemplateResponse("home.html", {
        "request": request,
        "contests": contests,
        "top_solvers": top_solvers,
        "contest_problems": contest_problems  # Pass problem names to the template
    })