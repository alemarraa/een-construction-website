"""Click CLI entry point for the EEN Construction outreach system."""

from __future__ import annotations

import sys

import click
from rich.console import Console

console = Console()


@click.group()
def cli() -> None:
    """EEN Construction lead-generation and outreach CLI."""


# ── ingest ────────────────────────────────────────────────────────────────


@cli.command()
@click.option("--county", type=click.Choice(["montgomery", "pgcounty", "all"]), default="all")
@click.option("--dry-run/--no-dry-run", default=None, help="Override DRY_RUN env var")
def ingest(county: str, dry_run: bool | None) -> None:
    """Fetch property data from open-data APIs and populate the database."""
    from .config import get_settings
    from .database import get_db, init_db
    from .models import CrawlRun, utcnow
    from .pipeline.ingest import ingest_raw
    from .sources.montgomery import MontgomeryHousingSource
    from .sources.pgcounty import PGCountySDATSource

    init_db()
    cfg = get_settings()
    effective_dry = cfg.dry_run if dry_run is None else dry_run

    sources = []
    if county in ("montgomery", "all"):
        sources.append(MontgomeryHousingSource())
    if county in ("pgcounty", "all"):
        sources.append(PGCountySDATSource())

    with get_db() as db:
        for source in sources:
            if not source.is_available():
                console.print(f"[yellow]Source {source.__class__.__name__} not available — skipping")
                continue

            run = CrawlRun(source_name=source.__class__.__name__)
            db.add(run)
            db.flush()

            console.print(f"[cyan]Fetching from {source.__class__.__name__}…")
            records = list(source.fetch())
            run.records_fetched = len(records)
            console.print(f"  Fetched {len(records)} records")

            if not effective_dry:
                for raw in records:
                    ingest_raw(db, raw, run)
                run.status = "complete"
                run.finished_at = utcnow()
                db.commit()
                console.print(
                    f"  Ingested: {run.records_new} new, "
                    f"{run.records_updated} updated"
                )
            else:
                run.status = "dry_run"
                run.finished_at = utcnow()
                db.commit()
                console.print(f"  [DRY_RUN] would ingest {len(records)} records")


# ── qualify ───────────────────────────────────────────────────────────────


@cli.command()
def qualify() -> None:
    """Apply 4-100 unit filter and set qualifies flag on all properties."""
    from .database import get_db
    from .pipeline.qualify import qualify_all

    with get_db() as db:
        qualified, rejected, needs_review = qualify_all(db)
        db.commit()

    console.print(f"[green]Qualified: {qualified}")
    console.print(f"[red]Rejected:  {rejected}")
    console.print(f"[yellow]Needs review: {needs_review}")


# ── score ─────────────────────────────────────────────────────────────────


@cli.command()
def score() -> None:
    """Calculate lead scores for all properties."""
    from .database import get_db
    from .pipeline.score import score_all

    with get_db() as db:
        count = score_all(db)
        db.commit()

    console.print(f"[green]Scored {count} properties")


# ── enrich ────────────────────────────────────────────────────────────────


@cli.command()
@click.option("--limit", default=50, show_default=True, help="Max properties to enrich")
def enrich(limit: int) -> None:
    """Discover contacts for qualified properties using Hunter.io."""
    from .config import get_settings
    from .database import get_db
    from .enrichment.hunter import HunterProvider
    from .enrichment.base import BaseEnrichmentProvider
    from .models import Contact, EnrichmentRun, Organization, Property, PropertyOrgRelationship, utcnow

    cfg = get_settings()
    provider: BaseEnrichmentProvider = HunterProvider()

    if not provider.is_configured():
        console.print("[yellow]HUNTER_API_KEY not set — enrichment skipped")
        return

    with get_db() as db:
        props = (
            db.query(Property)
            .filter(Property.qualifies.is_(True))
            .outerjoin(
                PropertyOrgRelationship,
                Property.id == PropertyOrgRelationship.property_id,
            )
            .filter(PropertyOrgRelationship.id.is_(None))
            .order_by(Property.lead_score.desc())
            .limit(limit)
            .all()
        )

        console.print(f"Enriching {len(props)} properties…")
        for prop in props:
            if not prop.owner_entity:
                continue
            contacts = provider.find_contacts_for_company(prop.owner_entity)
            run = EnrichmentRun(
                provider=provider.__class__.__name__,
                property_id=prop.id,
                ran_at=utcnow(),
                success=bool(contacts),
                result_summary=f"found {len(contacts)} contacts",
            )
            db.add(run)

            for ec in contacts:
                org = (
                    db.query(Organization)
                    .filter(Organization.normalized_name == ec.company_name_normalized)
                    .first()
                ) if ec.company_name_normalized else None

                if not org and ec.company_name:
                    from .pipeline.normalize import normalize_org_name
                    org = Organization(
                        name=ec.company_name,
                        normalized_name=normalize_org_name(ec.company_name),
                        website=ec.website,
                        website_domain=ec.domain,
                    )
                    db.add(org)
                    db.flush()
                    rel = PropertyOrgRelationship(
                        property_id=prop.id,
                        organization_id=org.id,
                        relationship_type="manager",
                        is_primary=True,
                        confidence=0.6,
                        source="hunter",
                    )
                    db.add(rel)

                if ec.email and org:
                    existing = db.query(Contact).filter(Contact.email == ec.email).first()
                    if not existing:
                        contact = Contact(
                            first_name=ec.first_name,
                            last_name=ec.last_name,
                            full_name=f"{ec.first_name or ''} {ec.last_name or ''}".strip() or None,
                            job_title=ec.job_title,
                            role=ec.role or "generic",
                            organization_id=org.id,
                            email=ec.email,
                            email_source="hunter",
                            email_confidence=ec.confidence,
                            email_status="unknown",
                        )
                        db.add(contact)

            console.print(f"  {prop.street_address}: {len(contacts)} contacts found")

        db.commit()


# ── verify ────────────────────────────────────────────────────────────────


@cli.command()
@click.option("--limit", default=100, show_default=True)
def verify(limit: int) -> None:
    """Verify email addresses via ZeroBounce."""
    from datetime import datetime, timezone
    from .database import get_db
    from .email_verify.zerobounce import ZeroBounceVerifier
    from .email_verify.base import NullVerifier
    from .models import Contact

    verifier = ZeroBounceVerifier()
    if not verifier.is_configured():
        console.print("[yellow]ZEROBOUNCE_API_KEY not set — using NullVerifier")
        verifier = NullVerifier()

    with get_db() as db:
        pending = (
            db.query(Contact)
            .filter(
                Contact.email.isnot(None),
                Contact.email_status == "unknown",
                Contact.email_verified_at.is_(None),
            )
            .limit(limit)
            .all()
        )
        console.print(f"Verifying {len(pending)} email addresses…")
        for contact in pending:
            result = verifier.verify(contact.email)
            contact.email_status = result.status
            contact.email_confidence = result.confidence
            contact.email_verified_at = datetime.now(timezone.utc)

        db.commit()
    console.print("[green]Done")


# ── compose ───────────────────────────────────────────────────────────────


@cli.command()
@click.option("--min-score", default=None, type=float)
def compose(min_score: float | None) -> None:
    """Compose email drafts for all qualified properties."""
    from .database import get_db
    from .pipeline.compose import compose_all

    with get_db() as db:
        campaigns = compose_all(db, min_lead_score=min_score)

    console.print(f"[green]Composed {len(campaigns)} draft campaigns")


# ── send ──────────────────────────────────────────────────────────────────


@cli.command()
@click.option("--limit", default=None, type=int)
@click.option("--no-hours-check", is_flag=True, default=False)
def send(limit: int | None, no_hours_check: bool) -> None:
    """Send queued email campaigns (respects DRY_RUN and SEND_ENABLED)."""
    from .database import get_db
    from .pipeline.send import send_queued

    with get_db() as db:
        summary = send_queued(
            db,
            limit=limit,
            require_business_hours=not no_hours_check,
        )

    console.print(f"Sent: {summary.sent}  Dry-run: {summary.dry_run}  "
                  f"Skipped: {summary.skipped}  Errors: {summary.errors}")
    if summary.skip_reasons:
        for reason, count in sorted(summary.skip_reasons.items()):
            console.print(f"  [yellow]• {reason}: {count}")


# ── report ────────────────────────────────────────────────────────────────


@cli.command()
@click.option("--format", "fmt", type=click.Choice(["dashboard", "csv", "daily"]), default="dashboard")
@click.option("--output", "-o", default=None, help="Write output to file instead of stdout")
def report(fmt: str, output: str | None) -> None:
    """Display pipeline dashboard or export reports."""
    from .database import get_db
    from .reporting import daily_report_text, export_qualified_csv, print_dashboard

    with get_db() as db:
        if fmt == "dashboard":
            print_dashboard(db, console)
            return
        elif fmt == "csv":
            content = export_qualified_csv(db)
        elif fmt == "daily":
            content = daily_report_text(db)

    if output:
        with open(output, "w") as f:
            f.write(content)
        console.print(f"[green]Written to {output}")
    else:
        print(content)


# ── compliance ────────────────────────────────────────────────────────────


@cli.command()
def compliance() -> None:
    """Print CAN-SPAM compliance checklist."""
    from rich.table import Table
    from .compliance import can_spam_checklist

    checklist = can_spam_checklist()
    t = Table(title="CAN-SPAM Compliance Checklist")
    t.add_column("Item", style="bold")
    t.add_column("Status", justify="center")
    t.add_column("Detail")

    for item, passed, detail in checklist:
        status = "[green]✓[/green]" if passed else "[red]✗[/red]"
        t.add_row(item, status, detail)

    console.print(t)


# ── suppress ──────────────────────────────────────────────────────────────


@cli.command()
@click.argument("email")
@click.option("--reason", default="manual", show_default=True)
def suppress(email: str, reason: str) -> None:
    """Manually add an email address to the suppression list."""
    from .compliance import add_suppression
    from .database import get_db

    with get_db() as db:
        add_suppression(db, email, reason=reason)
        db.commit()
    console.print(f"[green]Suppressed {email} ({reason})")


# ── run-all ───────────────────────────────────────────────────────────────


@cli.command("run-all")
@click.option("--county", type=click.Choice(["montgomery", "pgcounty", "all"]), default="all")
def run_all(county: str) -> None:
    """Run the full pipeline: ingest → qualify → score → enrich → verify → compose → send."""
    from click.testing import CliRunner

    runner = CliRunner()
    steps = [
        (ingest, ["--county", county]),
        (qualify, []),
        (score, []),
        (enrich, []),
        (verify, []),
        (compose, []),
        (send, []),
    ]
    for cmd, args in steps:
        console.rule(f"[bold]{cmd.name}")
        result = runner.invoke(cmd, args)
        console.print(result.output)
        if result.exit_code != 0:
            console.print(f"[red]Step {cmd.name} failed — stopping")
            sys.exit(result.exit_code)

    report_cmd = report
    result = runner.invoke(report_cmd, ["--format", "dashboard"])
    console.print(result.output)


def main() -> None:
    cli()


if __name__ == "__main__":
    main()
