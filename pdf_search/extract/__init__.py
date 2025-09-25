# =============================================================================
# Extract Module
# =============================================================================

from .extract_image import extract_images_from_pdf
from .extract_table import extract_tables_from_pdf

__all__ = ["extract_images_from_pdf", "extract_tables_from_pdf"]
