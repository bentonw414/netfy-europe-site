"""
This is the script that builds the content for the hugo to run
After running this script, running hugo should build the static website
"""

from classes import MiscellanySectionBuilder, SmugMugImageData, SwarmCheckinData, WebContentBuilder, SearchSectionBuilder, MiscellanySectionBuilder, OverviewSectionBuilder
from pathlib import Path

CONTENT_FOLDER_PATH = Path("./content")
if CONTENT_FOLDER_PATH.exists():
    raise RuntimeError("run \"rm -r content/\" to delete the content folder before running this script; this prevents accidentally manually overriding edits to content")

from utils import make_google_api_request, extract_document_sections
from cleaning_swarm_checkins import clean_swarm_data
# Google docs log data
document = make_google_api_request()
document_sections = extract_document_sections(document)

# Smugmug data
image_data = SmugMugImageData()

# Checkin data
checkin_data = SwarmCheckinData(clean_swarm_data())

# Health data
import json
HEALTH_DATA_PATH = "./site_building_data/europe_health.json"
with open(HEALTH_DATA_PATH, "r") as health_data_f:
    all_health_data = json.load(health_data_f)

content_builder= WebContentBuilder(image_data, checkin_data, all_health_data, document_sections)

# Search section needs to be built
content_builder.set_special_section(
    section_key="search",
    section_builder_type=SearchSectionBuilder,
)

# Miscellany Section is last maybe don't hardcode this but for now its fine
content_builder.set_special_section(
    section_key=document_sections[-1],
    section_builder_type=MiscellanySectionBuilder
)

# The Overview Section Also needs to be handled seperately, and it is the first section
content_builder.set_special_section(
    section_key=document_sections[0],
    section_builder_type=OverviewSectionBuilder
)

content_builder.build_content()