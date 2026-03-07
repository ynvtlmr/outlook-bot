"""CLI entry point for the Outlook Bot."""

from __future__ import annotations

import argparse
import time
import traceback

from outlook_bot.core.config import Config, Paths
from outlook_bot.email.outlook_mac import OutlookMacClient
from outlook_bot.providers.registry import ProviderRegistry
from outlook_bot.utils.dates import get_current_date_context
from outlook_bot.workflows.cold_outreach import run_cold_outreach
from outlook_bot.workflows.follow_up import run_follow_up


def _wait_for_outlook_ready(client: OutlookMacClient, timeout: int = 60) -> bool:
    """Wait for Outlook to become responsive by polling its version."""
    print(f"Waiting for Outlook to be ready (timeout: {timeout}s)...")
    start_time = time.time()

    while (time.time() - start_time) < timeout:
        version = client.get_version()
        if version:
            print(f"  -> Outlook ({version}) is ready.")
            return True
        print("  -> Waiting for Outlook...")
        time.sleep(2)

    print("  -> Error: Timeout waiting for Outlook to start.")
    return False


def _load_system_prompt(paths: Paths) -> str:
    """Load the system prompt from file."""
    try:
        return paths.system_prompt_path.read_text()
    except OSError as e:
        print(f"  -> Warning: Could not read system prompt: {e}")
        return "You are a helpful assistant."


def _setup() -> dict | None:
    """Initialize Outlook, load config, and create providers.

    Returns context dict, or None on failure.
    """
    print("--- Outlook Bot Setup ---")

    paths = Paths()
    config = Config.load(paths)

    client = OutlookMacClient(paths.applescripts_dir)
    print("Launching/Focusing Outlook...")
    client.activate()

    if not _wait_for_outlook_ready(client):
        return None

    print(
        f"Configuration Loaded: Days Threshold={config.days_threshold}, "
        f"Preferred Model={config.preferred_model}, BCC={config.salesforce_bcc}, "
        f"Cold Outreach={'ON' if config.cold_outreach_enabled else 'OFF'}"
    )

    base_prompt = _load_system_prompt(paths)
    date_context = get_current_date_context()
    system_prompt = f"{date_context}\n\n{base_prompt}"
    print(f"System Prompt Context: {date_context}")

    try:
        registry = ProviderRegistry(ssl_mode=config.ssl_mode)
    except Exception as e:
        print(f"Error initializing LLM Service: {e}")
        return None

    return {
        "client": client,
        "config": config,
        "paths": paths,
        "system_prompt": system_prompt,
        "registry": registry,
    }


def cmd_follow_up() -> None:
    """Run the follow-up workflow."""
    print("--- Outlook Bot: Follow Up ---")
    try:
        ctx = _setup()
        if ctx is None:
            return
        config = ctx["config"]
        run_follow_up(
            client=ctx["client"],
            registry=ctx["registry"],
            system_prompt=ctx["system_prompt"],
            days_threshold=config.days_threshold,
            preferred_model=config.preferred_model,
            salesforce_bcc=config.salesforce_bcc,
        )
    except Exception as e:
        print(f"Error during execution: {e}")
        traceback.print_exc()


def cmd_cold_outreach() -> None:
    """Run the cold outreach workflow."""
    print("--- Outlook Bot: Cold Outreach ---")
    try:
        ctx = _setup()
        if ctx is None:
            return
        config = ctx["config"]
        paths = ctx["paths"]

        if not config.cold_outreach_enabled:
            print("Cold outreach is disabled in configuration. Skipping.")
            return

        cold_prompt = ""
        if paths.cold_outreach_prompt_path.exists():
            cold_prompt = paths.cold_outreach_prompt_path.read_text()

        if not cold_prompt:
            print("Warning: Cold outreach prompt is empty. Skipping.")
            return

        run_cold_outreach(
            client=ctx["client"],
            registry=ctx["registry"],
            cold_prompt=cold_prompt,
            preferred_model=config.preferred_model,
            csv_path=config.cold_outreach_csv_path,
            daily_limit=config.cold_outreach_daily_limit,
            salesforce_bcc=config.salesforce_bcc,
            user_data_dir=paths.user_data_dir,
        )
    except Exception as e:
        print(f"Error during cold outreach: {e}")
        traceback.print_exc()


def cmd_run_all() -> None:
    """Run both follow-up and cold outreach."""
    print("--- Outlook Bot: Run All ---")
    try:
        ctx = _setup()
        if ctx is None:
            return
        config = ctx["config"]
        paths = ctx["paths"]

        run_follow_up(
            client=ctx["client"],
            registry=ctx["registry"],
            system_prompt=ctx["system_prompt"],
            days_threshold=config.days_threshold,
            preferred_model=config.preferred_model,
            salesforce_bcc=config.salesforce_bcc,
        )

        if config.cold_outreach_enabled:
            cold_prompt = ""
            if paths.cold_outreach_prompt_path.exists():
                cold_prompt = paths.cold_outreach_prompt_path.read_text()

            if cold_prompt:
                run_cold_outreach(
                    client=ctx["client"],
                    registry=ctx["registry"],
                    cold_prompt=cold_prompt,
                    preferred_model=config.preferred_model,
                    csv_path=config.cold_outreach_csv_path,
                    daily_limit=config.cold_outreach_daily_limit,
                    salesforce_bcc=config.salesforce_bcc,
                    user_data_dir=paths.user_data_dir,
                )
    except Exception as e:
        print(f"Error during execution: {e}")
        traceback.print_exc()


def main() -> None:
    """CLI entry point with argument parsing."""
    parser = argparse.ArgumentParser(description="Outlook Bot - LLM-powered email automation")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--follow-up", action="store_true", help="Run follow-up reply workflow")
    group.add_argument("--cold-outreach", action="store_true", help="Run cold outreach workflow")
    group.add_argument("--run-all", action="store_true", help="Run all workflows")
    args = parser.parse_args()

    if args.follow_up:
        cmd_follow_up()
    elif args.cold_outreach:
        cmd_cold_outreach()
    else:
        cmd_run_all()


if __name__ == "__main__":
    main()
