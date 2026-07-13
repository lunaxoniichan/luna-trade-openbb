"""Commodity Futures Trading Commission (CFTC) Router.

Fork note — null-guard in ``build_choices``. The CFTC catalog drifts and can
return ``None`` for ``name`` / ``code`` / ``subcategory``. Upstream reads those
via ``getattr(d, "x", "")``, whose default applies only when the attribute is
ABSENT — a present-but-``None`` value still reaches ``.strip()`` and raises
``AttributeError``. That runs inside the router lifespan, so it crashed platform
startup and port 6900 never bound. Coerce with ``or ""`` and skip rows with no
usable label/value.
"""

# pylint: disable=W0212,W0613

from contextlib import asynccontextmanager
from typing import Any

from openbb_core.app.model.command_context import CommandContext
from openbb_core.app.model.example import APIEx
from openbb_core.app.model.obbject import OBBject
from openbb_core.app.provider_interface import (
    ExtraParams,
    ProviderChoices,
    StandardParams,
)
from openbb_core.app.query import Query
from openbb_core.app.router import Router

router = Router(prefix="")
COT_CHOICES: list[dict[str, str | dict[str, str | None]]] = []


@asynccontextmanager
async def _cot_router_lifespan(_):
    await build_choices()
    yield


async def build_choices():
    """Build the choices for Workspace."""
    # pylint: disable=import-outside-toplevel
    from openbb_cftc.models.cot_search import CftcCotSearchFetcher

    contracts = await CftcCotSearchFetcher.fetch_data({}, {})
    choices: list[dict[str, str | dict[str, str | None]]] = []

    for d in contracts:
        name = (getattr(d, "name", "") or "").strip()
        code = (getattr(d, "code", "") or "").strip()
        subcategory = (getattr(d, "subcategory", "") or "").strip()
        commodity_name = (getattr(d, "commodity_name", "") or "").strip()
        # A row with no label or no value cannot be selected in Workspace.
        if not name or not code:
            continue
        description = f"{subcategory or commodity_name}  | {code}"
        choice: dict[str, str | dict[str, str | None]] = {
            "label": name,
            "value": code,
            "extraInfo": {
                "description": description,
                "rightOfDescription": "",
            },
        }
        choices.append(choice)

    global COT_CHOICES  # noqa: PLW0603  # pylint: disable=W0603

    COT_CHOICES = choices


router.api_router.lifespan_context = _cot_router_lifespan


async def get_cot_choices() -> list[dict[str, str | dict[str, str | None]]]:
    """Get the choices for the COT command in Workspace."""
    return COT_CHOICES


router._api_router.add_api_route(
    path="/get_cot_choices",
    endpoint=get_cot_choices,
    methods=["GET"],
    include_in_schema=False,
)


@router.command(
    model="COTSearch",
    examples=[
        APIEx(parameters={"provider": "cftc"}),
        APIEx(parameters={"query": "gold", "provider": "cftc"}),
    ],
    widget_config={
        "name": "Commitment of Traders Search",
        "description": "Search for CFTC Commitment of Traders (COT) report series.",
        "category": "CFTC",
        "subCategory": "COT",
        "refetchInterval": False,
    },
)
async def cot_search(
    cc: CommandContext,
    provider_choices: ProviderChoices,
    standard_params: StandardParams,
    extra_params: ExtraParams,
) -> OBBject:
    """Search current Commitment of Traders Reports."""
    return await OBBject.from_query(Query(**locals()))


@router.command(
    model="COT",
    examples=[
        APIEx(parameters={"provider": "ctfc"}),
        APIEx(
            description="Get the latest report for all items classified as, GOLD.",
            parameters={"code": "CFTC_088691", "limit": 1, "provider": "cftc"},
        ),
        APIEx(
            description="Get the report for futures only.",
            parameters={
                "code": "CFTC_088691",
                "futures_only": True,
                "limit": 1,
                "provider": "cftc",
            },
        ),
        APIEx(
            description="Filter the report down to a specific section.",
            parameters={
                "code": "CFTC_088691",
                "futures_only": True,
                "measure": "changes",
                "limit": 1,
                "provider": "cftc",
            },
        ),
    ],
    widget_config={
        "name": "Commitment of Traders",
        "description": "CFTC Commitment of Traders (COT) reports.",
        "category": "CFTC",
        "subCategory": "COT",
        "refetchInterval": False,
    },
)
async def cot(
    cc: CommandContext,
    provider_choices: ProviderChoices,
    standard_params: StandardParams,
    extra_params: ExtraParams,
) -> OBBject:
    """Get Commitment of Traders Reports."""
    return await OBBject.from_query(Query(**locals()))


async def get_cftc_apps_json() -> list[dict[str, Any]]:
    """Get the CFTC apps.json file.

    This endpoint serves the apps.json file containing OpenBB Workspace app configurations.
    It is automatically merged with any existing apps.json files in the Workspace and API.

    Returns
    -------
    list[dict[str, Any]]
        A list of OpenBB Workspace app configurations.
    """
    # pylint: disable=import-outside-toplevel
    import json
    from pathlib import Path

    apps_file = Path(__file__).parent / "apps.json"

    try:
        with apps_file.open("r", encoding="utf-8") as f:
            apps_json = json.load(f)
            return apps_json
    except Exception:
        return []


router._api_router.add_api_route(
    path="/apps.json",
    endpoint=get_cftc_apps_json,
    methods=["GET"],
    include_in_schema=False,
)
