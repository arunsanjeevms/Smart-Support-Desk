"""
Sends the deployment status e-mail for the Deploy workflow.

Only the standard library is used. Everything comes from environment variables
set in .github/workflows/deploy.yml:

    DEPLOY_STATUS     started | success | failure | cancelled
    MAIL_USERNAME     SMTP login (also the sender address)
    MAIL_PASSWORD     SMTP password (for Gmail: an App Password)
    MAIL_TO           comma separated recipients
    SMTP_HOST         default smtp.gmail.com
    SMTP_PORT         default 465 (implicit TLS); 587 uses STARTTLS
    GITHUB_TOKEN      used to read the commit message and which jobs failed
    DEPLOY_LOG        optional tail of the server-side deploy output
    plus the usual GITHUB_* variables and PROJECT_NAME / PRODUCTION_URL
"""

import html
import json
import os
import smtplib
import ssl
import sys
import urllib.request
from datetime import datetime, timedelta, timezone
from email.message import EmailMessage

IST = timezone(timedelta(hours=5, minutes=30), "IST")

STATUS_LABELS = {
    "started": ("Deployment started", "#2563eb"),
    "success": ("Deployment successful", "#16a34a"),
    "failure": ("Deployment failed", "#dc2626"),
    "cancelled": ("Deployment cancelled", "#6b7280"),
}


def env(name: str, default: str = "") -> str:
    return os.environ.get(name, default).strip()


def github_api(path: str):
    token = env("GITHUB_TOKEN")
    api = env("GITHUB_API_URL", "https://api.github.com")
    if not token:
        return None
    request = urllib.request.Request(
        f"{api}{path}",
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            return json.load(response)
    except Exception as error:  # the e-mail should still go out without these extras
        print(f"::warning::GitHub API request failed for {path}: {error}")
        return None


def commit_message(repository: str, sha: str) -> str:
    message = env("COMMIT_MESSAGE")
    if not message:
        commit = github_api(f"/repos/{repository}/commits/{sha}")
        message = (commit or {}).get("commit", {}).get("message", "")
    return message or "(not available)"


def failed_jobs(repository: str, run_id: str, attempt: str) -> list[str]:
    data = github_api(f"/repos/{repository}/actions/runs/{run_id}/attempts/{attempt}/jobs?per_page=100")
    lines = []
    for job in (data or {}).get("jobs", []):
        if job.get("conclusion") not in {"failure", "timed_out", "cancelled"}:
            continue
        steps = [step["name"] for step in job.get("steps", []) if step.get("conclusion") in {"failure", "timed_out"}]
        detail = f" - failed step: {', '.join(steps)}" if steps else ""
        lines.append(f"{job['name']} ({job['conclusion']}){detail}")
    return lines


def main() -> int:
    username, password = env("MAIL_USERNAME"), env("MAIL_PASSWORD")
    recipients = [address.strip() for address in env("MAIL_TO").split(",") if address.strip()]
    if not (username and password and recipients):
        print("::notice::Deployment e-mail skipped - add the MAIL_USERNAME and MAIL_PASSWORD repository secrets to enable it.")
        return 0

    status = env("DEPLOY_STATUS", "started")
    label, colour = STATUS_LABELS.get(status, (f"Deployment {status}", "#6b7280"))

    project = env("PROJECT_NAME", "Predigle")
    repository = env("GITHUB_REPOSITORY")
    branch = env("GITHUB_REF_NAME")
    sha = env("GITHUB_SHA")
    run_id, attempt = env("GITHUB_RUN_ID"), env("GITHUB_RUN_ATTEMPT", "1")
    run_url = f"{env('GITHUB_SERVER_URL', 'https://github.com')}/{repository}/actions/runs/{run_id}"
    production_url = env("PRODUCTION_URL")
    now = datetime.now(timezone.utc)
    timestamp = f"{now.astimezone(IST):%d %b %Y, %I:%M:%S %p} IST ({now:%Y-%m-%d %H:%M:%S} UTC)"
    message = commit_message(repository, sha)
    title_line = message.splitlines()[0] if message else ""

    rows = [
        ("Project", project),
        ("Status", label),
        ("Repository", repository),
        ("Branch", branch),
        ("Commit", sha),
        ("Commit message", message),
        ("Triggered by", f"{env('GITHUB_ACTOR')} ({env('GITHUB_EVENT_NAME')})"),
        ("Timestamp", timestamp),
        ("Production URL", production_url),
        ("Workflow run", run_url),
    ]

    errors: list[str] = []
    if status == "failure":
        errors = failed_jobs(repository, run_id, attempt) or ["See the workflow run for details."]
    deploy_log = env("DEPLOY_LOG")

    # ---- plain text ----
    text = [f"{project}: {label}", ""]
    text += [f"{name}: {value}" for name, value in rows]
    if errors:
        text += ["", "What failed:"] + [f"  - {line}" for line in errors]
    if deploy_log:
        text += ["", "Server output (last lines):", deploy_log]

    # ---- HTML ----
    def cell(name: str, value: str) -> str:
        shown = html.escape(value).replace("\n", "<br>")
        if value.startswith("https://"):
            shown = f'<a href="{html.escape(value)}" style="color:#2563eb">{shown}</a>'
        return (
            '<tr><td style="padding:6px 12px 6px 0;color:#6b7280;white-space:nowrap;vertical-align:top">'
            f"{html.escape(name)}</td><td style=\"padding:6px 0;color:#111827\">{shown}</td></tr>"
        )

    body = [
        '<div style="font-family:Segoe UI,Arial,sans-serif;font-size:14px;max-width:640px">',
        f'<div style="background:{colour};color:#fff;padding:14px 18px;border-radius:8px 8px 0 0;font-size:17px;font-weight:600">'
        f"{html.escape(project)} &middot; {html.escape(label)}</div>",
        '<div style="border:1px solid #e5e7eb;border-top:0;border-radius:0 0 8px 8px;padding:12px 18px">',
        '<table style="border-collapse:collapse;width:100%">',
        *(cell(name, value) for name, value in rows),
        "</table>",
    ]
    if errors:
        body.append('<p style="margin:16px 0 6px;font-weight:600;color:#dc2626">What failed</p><ul style="margin:0;padding-left:20px">')
        body += [f"<li>{html.escape(line)}</li>" for line in errors]
        body.append("</ul>")
    if deploy_log:
        body.append(
            '<p style="margin:16px 0 6px;font-weight:600">Server output (last lines)</p>'
            '<pre style="background:#111827;color:#e5e7eb;padding:12px;border-radius:6px;font-size:12px;'
            f'white-space:pre-wrap;overflow-wrap:anywhere">{html.escape(deploy_log)}</pre>'
        )
    body.append("</div></div>")

    email = EmailMessage()
    email["Subject"] = f"[{project}] {label} - {branch} @ {sha[:7]}: {title_line[:80]}"
    email["From"] = f"{project} Deployments <{username}>"
    email["To"] = ", ".join(recipients)
    email.set_content("\n".join(text))
    email.add_alternative("".join(body), subtype="html")

    host, port = env("SMTP_HOST", "smtp.gmail.com"), int(env("SMTP_PORT", "465"))
    context = ssl.create_default_context()
    if port == 465:
        with smtplib.SMTP_SSL(host, port, context=context, timeout=30) as smtp:
            smtp.login(username, password)
            smtp.send_message(email)
    else:
        with smtplib.SMTP(host, port, timeout=30) as smtp:
            smtp.starttls(context=context)
            smtp.login(username, password)
            smtp.send_message(email)

    print(f"Sent '{label}' e-mail to {len(recipients)} recipient(s).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
