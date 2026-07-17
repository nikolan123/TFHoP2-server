from urllib.parse import parse_qs, quote

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from content import AUDIO_PREVIEWS, POLLS, YOUTUBE_ARCHIVE_BASE, YOUTUBE_VIDEOS
from database import get_comments, get_vote_counts, record_comment, record_vote


app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

@app.get("/", include_in_schema=False)
def homepage(request: Request):
    return templates.TemplateResponse(request=request, name="index.html")


@app.get("/TFHoP2_assets/howto/diagram.html")
def original_portal_diagram():
    return FileResponse("static/TFHoP2_assets/howto-original/diagram.html")


@app.get("/TFHoP2_assets/howto/revival-diagram.html")
def revival_portal_diagram(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="diagram.html",
    )


app.mount(
    "/TFHoP2_assets/howto",
    StaticFiles(directory="static/TFHoP2_assets/howto-original", html=True),
    name="original-diagram-assets",
)
app.mount(
    "/TFHoP2_assets/interactive",
    StaticFiles(directory="static/TFHoP2_assets/interactive", html=True),
    name="wheatley-360",
)
app.mount(
    "/TFHoP2_assets/oddcouple",
    StaticFiles(directory="static/TFHoP2_assets/oddcouple", html=True),
    name="odd-couple-360",
)
app.mount(
    "/TFHoP2_assets/companioncube",
    StaticFiles(directory="static/TFHoP2_assets/companioncube", html=True),
    name="companion-cube-360",
)


@app.get("/apiplayer")
@app.get("/youtube/apiplayer.swf")
def youtube_player(version: int = 3):
    return FileResponse(
        "static/apiplayer.swf",
        media_type="application/x-shockwave-flash",
        headers={"Cache-Control": "no-store, max-age=0"},
    )


@app.get("/youtube/player-event/{event}", status_code=204)
def youtube_player_event(event: str):
    return


@app.get("/youtube/{video_id}.mp4")
def youtube_video(video_id: str):
    archive_path = YOUTUBE_VIDEOS.get(video_id)
    if archive_path is None:
        raise HTTPException(status_code=404, detail="Video not found")
    return RedirectResponse(
        YOUTUBE_ARCHIVE_BASE + quote(archive_path, safe="/"),
        status_code=302,
    )

@app.get("/us/{legacy_path:path}")
def audio_preview(legacy_path: str):
    preview_url = AUDIO_PREVIEWS.get("/us/" + legacy_path.strip())
    if preview_url is None:
        raise HTTPException(status_code=404, detail="Audio preview not found")
    return RedirectResponse(preview_url, status_code=302)


@app.api_route("/p2/index.php5", methods=["GET", "POST"])
async def comments(request: Request):
    try:
        page = max(1, int(request.query_params.get("page", "1")))
    except ValueError:
        page = 1

    error = None
    name = ""
    comment = ""
    if request.method == "POST":
        form = parse_qs((await request.body()).decode("utf-8"))
        name = form.get("name", [""])[0].strip()
        comment = form.get("comment", [""])[0].strip()

        if not name or not comment:
            error = "Please enter your name and a comment."
        elif len(name) > 80:
            error = "Your name must be 80 characters or fewer."
        elif len(comment) > 2000:
            error = "Your comment must be 2,000 characters or fewer."
        else:
            submitter_ip = request.client.host if request.client else "unknown"
            record_comment(name, comment, submitter_ip)
            return RedirectResponse("/p2/index.php5?posted=1", status_code=303)

    page_comments, total_comments = get_comments(page)
    total_pages = max(1, (total_comments + 9) // 10)
    if page > total_pages:
        page = total_pages
        page_comments, total_comments = get_comments(page)

    return templates.TemplateResponse(
        request=request,
        name="comments.html",
        context={
            "comments": page_comments,
            "page": page,
            "total_pages": total_pages,
            "posted": request.query_params.get("posted") == "1",
            "error": error,
            "name": name,
            "comment": comment,
        },
    )


@app.api_route("/p2polls/poll{poll_id}.php5", methods=["GET", "POST"])
async def poll(request: Request, poll_id: int):
    poll_data = POLLS.get(poll_id)
    if poll_data is None:
        raise HTTPException(status_code=404, detail="Poll not found")

    show_results = request.query_params.get("results") == "1"
    if request.method == "POST":
        form = parse_qs((await request.body()).decode("utf-8"))
        try:
            option_index = int(form.get("vote", [""])[0])
        except ValueError:
            option_index = -1

        if 0 <= option_index < len(poll_data["options"]):
            submitter_ip = request.client.host if request.client else "unknown"
            record_vote(poll_id, option_index, submitter_ip)
            show_results = True

    vote_counts = get_vote_counts(poll_id, len(poll_data["options"]))

    total_votes = sum(vote_counts)
    percentages = [
        round(count * 100 / total_votes) if total_votes else 0
        for count in vote_counts
    ]

    return templates.TemplateResponse(
        request=request,
        name="poll.html",
        context={
            "poll_id": poll_id,
            "poll": poll_data,
            "show_results": show_results,
            "vote_counts": vote_counts,
            "total_votes": total_votes,
            "percentages": percentages,
        },
    )


@app.api_route("/p2polls/poll.php5", methods=["GET", "POST"])
@app.api_route("/p2polls/subscribe/index.php5", methods=["GET", "POST"])
def unrecovered_content(request: Request, id: int | None = None):
    if request.url.path.endswith("/poll.php5") and id not in {20, 21}:
        raise HTTPException(status_code=404, detail="Poll not found")

    return templates.TemplateResponse(
        request=request,
        name="unimplemented.html",
    )
