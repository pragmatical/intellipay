import argparse
import hmac
import mimetypes
import secrets
from hashlib import sha256
from pathlib import Path
from typing import Annotated

import uvicorn
from fastapi import Depends, FastAPI, Form, HTTPException, Query, Request, status
from fastapi.responses import RedirectResponse, Response
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from intellipay.config import Settings
from intellipay.workflow import InvoiceWorkflow
from intellipay.workflow.models import ReviewAction
from intellipay.workflow.storage import SQLiteStore

PACKAGE_ROOT = Path(__file__).parent


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or Settings()
    if settings.reviewer_password is None:
        raise RuntimeError("INTELLIPAY_REVIEWER_PASSWORD is required to start the review app")

    app = FastAPI(title="IntelliPay Review", docs_url=None, redoc_url=None)
    app.mount("/static", StaticFiles(directory=PACKAGE_ROOT / "static"), name="static")
    templates = Jinja2Templates(directory=PACKAGE_ROOT / "templates")
    security = HTTPBasic()
    password = settings.reviewer_password.get_secret_value()
    workflow = InvoiceWorkflow(settings)
    store = SQLiteStore(settings.database_path)

    def authenticate(
        credentials: Annotated[HTTPBasicCredentials, Depends(security)],
    ) -> str:
        valid_username = secrets.compare_digest(credentials.username, settings.reviewer_username)
        valid_password = secrets.compare_digest(credentials.password, password)
        if not (valid_username and valid_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid reviewer credentials",
                headers={"WWW-Authenticate": "Basic"},
            )
        return credentials.username

    def csrf_token(review_task_id: str) -> str:
        return hmac.new(password.encode(), review_task_id.encode(), sha256).hexdigest()

    app.state.workflow = workflow
    app.state.store = store

    @app.get("/", include_in_schema=False)
    def root() -> RedirectResponse:
        return RedirectResponse("/reviews", status_code=status.HTTP_303_SEE_OTHER)

    @app.get("/reviews", include_in_schema=False)
    def review_queue(
        request: Request,
        queue_status: str = Query("OPEN", alias="status", pattern="^(OPEN|COMPLETED|ALL)$"),
        _: Annotated[str, Depends(authenticate)] = "",
    ):
        tasks = store.list_review_tasks(None if queue_status == "ALL" else queue_status)
        return templates.TemplateResponse(
            request,
            "queue.html",
            {"tasks": tasks, "queue_status": queue_status},
        )

    @app.get("/reviews/{review_task_id}", include_in_schema=False)
    def review_detail(
        review_task_id: str,
        request: Request,
        _: Annotated[str, Depends(authenticate)],
    ):
        try:
            case = workflow.review_case(review_task_id)
        except ValueError as error:
            raise HTTPException(status_code=404, detail=str(error)) from error
        return templates.TemplateResponse(
            request,
            "detail.html",
            {
                "case": case,
                "csrf_token": csrf_token(review_task_id),
                "all_actions": list(ReviewAction),
            },
        )

    @app.get("/reviews/{review_task_id}/source", include_in_schema=False)
    def review_source(
        review_task_id: str,
        _: Annotated[str, Depends(authenticate)],
    ) -> Response:
        try:
            filename, content = workflow.review_source(review_task_id)
        except ValueError as error:
            raise HTTPException(status_code=404, detail=str(error)) from error
        media_type = mimetypes.guess_type(filename)[0] or "application/octet-stream"
        return Response(
            content,
            media_type=media_type,
            headers={"Content-Disposition": f'inline; filename="{Path(filename).name}"'},
        )

    @app.post("/reviews/{review_task_id}/decision", include_in_schema=False)
    def review_decision(
        review_task_id: str,
        action: Annotated[ReviewAction, Form()],
        rationale: Annotated[str, Form(min_length=10, max_length=1000)],
        csrf: Annotated[str, Form()],
        actor: Annotated[str, Depends(authenticate)],
    ) -> RedirectResponse:
        if not secrets.compare_digest(csrf, csrf_token(review_task_id)):
            raise HTTPException(status_code=403, detail="Invalid review form token")
        try:
            workflow.resolve_review(
                review_task_id,
                action=action,
                actor=actor,
                rationale=rationale,
            )
        except ValueError as error:
            raise HTTPException(status_code=409, detail=str(error)) from error
        return RedirectResponse(f"/reviews/{review_task_id}", status_code=status.HTTP_303_SEE_OTHER)

    return app


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the IntelliPay reviewer interface")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--database-path", type=Path, default=None)
    args = parser.parse_args()
    overrides = {"database_path": args.database_path} if args.database_path else {}
    uvicorn.run(create_app(Settings(**overrides)), host=args.host, port=args.port)


if __name__ == "__main__":
    main()
