import os

from indiepitcher import IndiePitcherAsyncClient

_async_client: IndiePitcherAsyncClient | None = None


def create_async_indiepitcher_client() -> None:
    """
    Create the IndiePitcher client using API key from environment variable.
    """
    global _async_client
    if _async_client is None:
        api_key = os.environ.get("INDIE_PITCHER_API_KEY")
        if not api_key:
            raise ValueError("INDIE_PITCHER_API_KEY environment variable is not set")
        _async_client = IndiePitcherAsyncClient(api_key=api_key)


def is_async_indiepitcher_client_initialized() -> bool:
    """
    Check if the IndiePitcher client is initialized.
    """
    return _async_client is not None


def get_async_indiepitcher_client() -> IndiePitcherAsyncClient:
    """
    Get the IndiePitcher client.
    """
    if _async_client is None:
        raise ValueError("IndiePitcher client is not initialized.")
    return _async_client


async def close_async_indiepitcher_client() -> None:
    """
    Close the IndiePitcher client.
    """
    global _async_client
    if _async_client:
        await _async_client.close()
        _async_client = None


__all__ = [
    "create_async_indiepitcher_client",
    "get_async_indiepitcher_client",
    "close_async_indiepitcher_client",
    "is_async_indiepitcher_client_initialized",
    "IndiePitcherAsyncClient",
]
