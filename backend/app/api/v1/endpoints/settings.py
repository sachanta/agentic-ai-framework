"""
Settings management endpoints.
"""
import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status

from app.core.security import get_current_user, require_admin
from app.db.repositories.settings import get_settings_repository, SettingsRepository
from app.schemas.settings import (
    AllSettingsResponse,
    SettingsCategoryResponse,
    UpdateSettingsRequest,
    GeneralSettings,
    ApiSettings,
    LLMSettings,
    SecuritySettings,
    NotificationSettings,
)

logger = logging.getLogger(__name__)

router = APIRouter()


def get_repo() -> SettingsRepository:
    """Get the settings repository."""
    return get_settings_repository()


@router.get("", response_model=AllSettingsResponse)
async def get_settings(
    repo: SettingsRepository = Depends(get_repo),
):
    """
    Get all application settings.

    Returns all settings organized by category.
    """
    settings = await repo.get_all()

    return AllSettingsResponse(
        general=GeneralSettings(**settings.get("general", {})),
        api=ApiSettings(**settings.get("api", {})),
        llm=LLMSettings(**settings.get("llm", {})),
        security=SecuritySettings(**settings.get("security", {})),
        notifications=NotificationSettings(**settings.get("notifications", {})),
    )


@router.get("/{category}", response_model=SettingsCategoryResponse)
async def get_settings_category(
    category: str,
    repo: SettingsRepository = Depends(get_repo),
):
    """
    Get settings for a specific category.

    Args:
        category: The settings category (general, api, llm, security, notifications)

    Returns:
        Settings for the specified category
    """
    result = await repo.get_category(category)

    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Settings category '{category}' not found",
        )

    return SettingsCategoryResponse(
        category=result["category"],
        settings=result["settings"],
        updated_at=result.get("updated_at"),
        updated_by=result.get("updated_by"),
    )


@router.put("", response_model=AllSettingsResponse)
async def update_settings(
    request: UpdateSettingsRequest,
    current_user: dict = Depends(require_admin),
    repo: SettingsRepository = Depends(get_repo),
):
    """
    Update multiple settings categories at once.

    Requires admin privileges.

    Args:
        request: Settings to update (category -> settings mapping)

    Returns:
        Updated settings
    """
    user_id = current_user.get("id")

    await repo.update_all(request.settings, updated_by=user_id)
    logger.info(f"Settings updated by user '{current_user.get('username')}'")

    # Return updated settings
    settings = await repo.get_all()

    return AllSettingsResponse(
        general=GeneralSettings(**settings.get("general", {})),
        api=ApiSettings(**settings.get("api", {})),
        llm=LLMSettings(**settings.get("llm", {})),
        security=SecuritySettings(**settings.get("security", {})),
        notifications=NotificationSettings(**settings.get("notifications", {})),
    )


@router.put("/{category}", response_model=SettingsCategoryResponse)
async def update_settings_category(
    category: str,
    request: UpdateSettingsRequest,
    current_user: dict = Depends(require_admin),
    repo: SettingsRepository = Depends(get_repo),
):
    """
    Update settings for a specific category.

    Requires admin privileges.

    Args:
        category: The settings category
        request: Settings to update

    Returns:
        Updated settings for the category
    """
    # Validate category exists
    existing = await repo.get_category(category)
    if existing is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Settings category '{category}' not found",
        )

    user_id = current_user.get("id")
    result = await repo.update_category(category, request.settings, updated_by=user_id)

    logger.info(f"Settings category '{category}' updated by user '{current_user.get('username')}'")

    return SettingsCategoryResponse(
        category=result["category"],
        settings=result["settings"],
        updated_at=result.get("updated_at"),
        updated_by=result.get("updated_by"),
    )


@router.post("/{category}/reset", response_model=SettingsCategoryResponse)
async def reset_settings_category(
    category: str,
    current_user: dict = Depends(require_admin),
    repo: SettingsRepository = Depends(get_repo),
):
    """
    Reset a settings category to defaults.

    Requires admin privileges.

    Args:
        category: The settings category

    Returns:
        Default settings for the category
    """
    result = await repo.reset_category(category)

    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Settings category '{category}' not found",
        )

    logger.info(f"Settings category '{category}' reset by user '{current_user.get('username')}'")

    return SettingsCategoryResponse(
        category=result["category"],
        settings=result["settings"],
        updated_at=result.get("updated_at"),
        updated_by=result.get("updated_by"),
    )


@router.post("/reset", response_model=AllSettingsResponse)
async def reset_all_settings(
    current_user: dict = Depends(require_admin),
    repo: SettingsRepository = Depends(get_repo),
):
    """
    Reset all settings to defaults.

    Requires admin privileges.

    Returns:
        Default settings
    """
    settings = await repo.reset_all()

    logger.info(f"All settings reset by user '{current_user.get('username')}'")

    return AllSettingsResponse(
        general=GeneralSettings(**settings.get("general", {})),
        api=ApiSettings(**settings.get("api", {})),
        llm=LLMSettings(**settings.get("llm", {})),
        security=SecuritySettings(**settings.get("security", {})),
        notifications=NotificationSettings(**settings.get("notifications", {})),
    )
