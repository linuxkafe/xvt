"""Main application entry point."""

import json as json_lib
import logging
import sys
from datetime import datetime
from typing import Any

import click

from src.xvt.fingerprints import load_fingerprints, match_fingerprint
from src.xvt.scanner import NetworkScanner


class JSONFormatter(logging.Formatter):
    """JSON lines formatter for structured logging."""

    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if hasattr(record, "operation"):
            log_data["operation"] = record.operation
        if hasattr(record, "params"):
            log_data["params"] = record.params
        if hasattr(record, "result"):
            log_data["result"] = record.result
        return json_lib.dumps(log_data)


def setup_logging(verbose: bool = False, json_logs: bool = False) -> logging.Logger:
    """Configure application logging."""
    logger = logging.getLogger("xvt")
    logger.setLevel(logging.DEBUG if verbose else logging.INFO)
    logger.handlers.clear()

    handler = logging.StreamHandler(sys.stderr)
    if json_logs:
        handler.setFormatter(JSONFormatter())
    else:
        handler.setFormatter(logging.Formatter(
            "%(asctime)s | %(levelname)-8s | %(message)s",
            datefmt="%H:%M:%S"
        ))
    logger.addHandler(handler)
    return logger


def log_operation(
    logger: logging.Logger,
    operation: str,
    params: dict[str, Any],
    result: str | None = None,
    level: int = logging.INFO,
) -> None:
    """Log an operation with structured data."""
    extra = {"operation": operation, "params": params}
    if result:
        extra["result"] = result
    logger.log(level, operation, extra=extra)


def confirm_action(prompt: str, dry_run: bool, confirm: bool) -> bool:
    """Handle dry-run and confirmation logic."""
    if dry_run:
        click.echo(f"[DRY-RUN] Would execute: {prompt}")
        return False
    if not confirm and not click.confirm(f"Confirm: {prompt}?"):
        click.echo("Aborted.")
        return False
    return True


@click.group()
@click.version_option(version="0.1.0")
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose logging")
@click.option("--quiet", "-q", is_flag=True, help="Suppress non-error output")
@click.option("--json-logs", is_flag=True, help="Output logs as JSON lines")
@click.pass_context
def cli(ctx: click.Context, verbose: bool, quiet: bool, json_logs: bool):
    """XVT - Xiaomi Vacuum/Vale Tudo: Root access toolchain."""
    ctx.ensure_object(dict)
    ctx.obj["logger"] = setup_logging(
        verbose=verbose and not quiet, json_logs=json_logs
    )
    ctx.obj["quiet"] = quiet


@cli.command()
@click.option("--interface", "-i", help="Network interface to scan")
@click.option("--timeout", "-t", default=5.0, help="Scan timeout in seconds")
@click.option("--json/--no-json", default=True, help="Output as JSON")
@click.pass_context
def scan(ctx: click.Context, interface: str | None, timeout: float, json: bool):
    """Discover Xiaomi vacuums on the local network."""
    logger = ctx.obj["logger"]
    scanner = NetworkScanner(interface=interface, timeout=timeout)
    devices = scanner.discover_all()

    log_operation(
        logger,
        "scan",
        {"interface": interface, "timeout": timeout},
        f"found {len(devices)} devices",
    )

    if json:
        output = [d.__dict__ for d in devices]
        click.echo(json_lib.dumps(output, indent=2))
    else:
        for d in devices:
            click.echo(
                f"{d.ip} | {d.mac} | {d.model} | "
                f"{d.firmware} | {d.hardware_rev} | token={d.token}"
            )


@cli.command()
@click.argument("device_ip")
@click.argument("key_path", type=click.Path(exists=True, path_type=str))
@click.option(
    "--vector",
    type=click.Choice(["uart", "dustbin", "ota"]),
    help="Exploit vector (auto-selected if not specified)",
)
@click.option(
    "--dry-run/--no-dry-run",
    default=True,
    help="Dry run mode (default: true)",
)
@click.option(
    "--confirm",
    is_flag=True,
    help="Explicitly confirm execution (bypass prompt)",
)
@click.pass_context
def inject(
    ctx: click.Context,
    device_ip: str,
    key_path: str,
    vector: str | None,
    dry_run: bool,
    confirm: bool,
):
    """Inject SSH key into device via exploit vector."""
    logger = ctx.obj["logger"]
    params = {
        "device_ip": device_ip,
        "key_path": key_path,
        "vector": vector,
        "dry_run": dry_run,
    }

    if not confirm_action(
        f"Inject SSH key into {device_ip} via {vector or 'auto'} vector",
        dry_run,
        confirm,
    ):
        return

    log_operation(logger, "inject", params, "not_implemented")
    click.echo("Not implemented yet - exploit vectors in T006-T008", err=True)


@cli.command()
@click.argument("firmware_path", type=click.Path(exists=True, path_type=str))
@click.argument("output_path", type=click.Path(path_type=str))
@click.option(
    "--keys",
    type=click.Path(exists=True, path_type=str),
    help="Authorized keys file",
)
@click.option(
    "--dry-run/--no-dry-run",
    default=True,
    help="Dry run mode (default: true)",
)
@click.option(
    "--confirm",
    is_flag=True,
    help="Explicitly confirm execution (bypass prompt)",
)
@click.pass_context
def patch(
    ctx: click.Context,
    firmware_path: str,
    output_path: str,
    keys: str | None,
    dry_run: bool,
    confirm: bool,
):
    """Patch firmware to enable persistent root (dropbear, su, authorized_keys)."""
    logger = ctx.obj["logger"]
    params = {
        "firmware_path": firmware_path,
        "output_path": output_path,
        "keys": keys,
        "dry_run": dry_run,
    }

    if not confirm_action(
        f"Patch firmware {firmware_path} -> {output_path}",
        dry_run,
        confirm,
    ):
        return

    log_operation(logger, "patch", params, "not_implemented")


@cli.command()
@click.argument("device_ip")
@click.argument("firmware_path", type=click.Path(exists=True, path_type=str))
@click.option(
    "--method",
    type=click.Choice(["ota", "uart"]),
    default="ota",
    help="Flash method",
)
@click.option(
    "--dry-run/--no-dry-run",
    default=True,
    help="Dry run mode (default: true)",
)
@click.option(
    "--confirm",
    is_flag=True,
    help="Explicitly confirm execution (bypass prompt)",
)
@click.pass_context
def flash(
    ctx: click.Context,
    device_ip: str,
    firmware_path: str,
    method: str,
    dry_run: bool,
    confirm: bool,
):
    """Flash modified firmware to device."""
    logger = ctx.obj["logger"]
    params = {
        "device_ip": device_ip,
        "firmware_path": firmware_path,
        "method": method,
        "dry_run": dry_run,
    }

    if not confirm_action(
        f"Flash {firmware_path} to {device_ip} via {method}",
        dry_run,
        confirm,
    ):
        return

    log_operation(logger, "flash", params, "not_implemented")


@cli.command()
@click.option("--model", help="Device model (e.g., viomi.vacuum.v8)")
@click.option("--firmware", help="Firmware version (e.g., 30081)")
@click.option("--ip", help="Device IP to auto-detect model/firmware")
@click.option("--json/--no-json", default=False, help="Output as JSON")
@click.pass_context
def vectors(
    ctx: click.Context,
    model: str | None,
    firmware: str | None,
    ip: str | None,
    json: bool,
):
    """Show exploit vectors for a device model/firmware."""
    logger = ctx.obj["logger"]
    db = load_fingerprints()

    if ip:
        scanner = NetworkScanner(timeout=3.0)
        devices = scanner.discover_all()
        device = next((d for d in devices if d.ip == ip), None)
        if not device:
            click.echo(f"Device at {ip} not found", err=True)
            return
        model = device.model
        firmware = device.firmware
        click.echo(f"Detected: {model} fw={firmware}")

    if not model or not firmware:
        click.echo("Must provide --model and --firmware, or --ip", err=True)
        return

    fp = match_fingerprint(db, model, firmware)
    if not fp:
        click.echo(f"No fingerprint for {model} firmware {firmware}", err=True)
        return

    log_operation(
        logger,
        "vectors",
        {"model": model, "firmware": firmware},
        f"found {len(fp.vectors)} vectors",
    )

    if json:
        output = {
            "model": fp.model,
            "name": fp.name,
            "vendor": fp.vendor,
            "firmware": firmware,
            "vectors": [
                {
                    "type": v.type.value,
                    "description": v.description,
                    "difficulty": v.difficulty,
                    "requirements": v.requirements,
                    "persistent": v.persistent,
                    "requires_opening": v.requires_opening,
                }
                for v in fp.vectors
            ],
            "notes": fp.notes,
        }
        click.echo(json_lib.dumps(output, indent=2))
    else:
        click.echo(f"Device: {fp.name} ({fp.model})")
        click.echo(f"Vendor: {fp.vendor}")
        click.echo(f"Firmware: {firmware}")
        click.echo(f"Notes: {fp.notes}")
        click.echo("Available exploit vectors:")
        for v in fp.vectors:
            reqs = ", ".join(v.requirements)
            click.echo(f"  - {v.type.value.upper()}: {v.description}")
            click.echo(f"    Difficulty: {v.difficulty}")
            click.echo(f"    Requirements: {reqs}")
            click.echo(f"    Persistent: {'Yes' if v.persistent else 'No'}")
            click.echo(f"    Requires opening: {'Yes' if v.requires_opening else 'No'}")


if __name__ == "__main__":
    cli()

