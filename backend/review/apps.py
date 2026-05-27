from django.apps import AppConfig


class ReviewConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "review"
    verbose_name = "Analyst Review"

    # Workflow logic lives in review.services (Phase 3–4).
    # No separate ReviewAction model — state lives on NormalizedEmissionRecord.
