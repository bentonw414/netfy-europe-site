# This file contains classes used for building the site

# Class should contain something about imageData

from __future__ import annotations
from ctypes import Union
from email.mime import image
from re import I
from typing import Any, Dict, List, Optional, Type
from smugmug_api import get_smugmug_data
from pathlib import Path
import datetime
from utils import read_paragraph_elements, paragraph_to_markdown, dict_to_frontmatter_string

class DocumentSection:
    """
    Represents things with a SECTION_STYLE_NAMED_STYLETYPE style and all content until the next SECTION_STYLE_NAMED_STYLETYPE
    """
    _id_counter = 0

    # _text_elements is the document object text just under the section description
    # _title_element is the title element of the object
    # _document_entries is the entries of the days within a document
    # _finalized --> once true, all of the mutators to the abstract value will fail (makes the object effectively immutable at runtime)

    def __init__(self) -> None:
        self._text_elements = []
        self._document_entries: List[DocumentEntry] = []
        self._title_element = None
        self._finalized = False
        self._section_id = None

    def add_paragraph_element(self, element) -> None:
        """
        Adds a paragraph element to the description of the document section; shouldn't be called once finalized
        """
        if self._finalized:
            raise ValueError("document section has already been finalized")
        self._text_elements.append(element)

    def add_document_entry(self, entry: DocumentEntry) -> None:
        """
        Adds a document entry to the DocumentSection; shouldn't be called once finalized
        """
        if self._finalized:
            raise ValueError("document section has already been finalized")
        self._document_entries.append(entry)

    def add_title_element(self, element):
        """
        Adds the title paragraph element to the document
        """
        if self._finalized:
            raise ValueError("document section has already been finalized")
        if self._title_element is not None:
            raise ValueError("document section has already had it's title element set")
        self._title_element = element

    def finalize(self):
        """
        Makes the object runtime immutable; useful for once the object has been fully initialized; should only be called once
        """
        if self._finalized == True:
            raise ValueError("document section has already been finalized; shouldn't need to refinalize")
        self._section_id = DocumentSection._id_counter
        DocumentSection._id_counter += 1
        self._finalized = True

    def title_text(self) -> str:
        return read_paragraph_elements(self._title_element).strip("\n")
    
    def title_text_elements(self) -> str:
        return self._title_element.copy()

    def entries(self) -> List[DocumentEntry]:
        return self._document_entries.copy()

    def get_description(self) -> List[str]:
        out = []
        for paragraph in self._text_elements:
            out.append(read_paragraph_elements(paragraph))
        return out

    def get_description_elements(self) -> List[Any]:
        return self._text_elements.copy()

    @property
    def section_id(self):
        return self._section_id

    def __eq__(self, __o: object) -> bool:
        if isinstance(__o, DocumentSection):
            return __o.section_id == self.section_id
        return False

    def __ne__(self, __o: object) -> bool:
        return not (__o == self)
    
    def __hash__(self) -> int:
        return self.section_id


class DocumentEntry:
    "Represents things with a ENTRY_STYLE_NAMED_STYLETYPE and all content until the next ENTRY_STYLE_NAMED_STYLETYPE"

    DATE_STRING_LENGTH = 11 # number of characters that make up the date

    def __init__(self) -> None:
        self._text_elements = []
        self._entry_title_element = None
        self._finalized = False

    def add_paragraph_element(self, element) -> None:
        """
        Adds a paragraph element to the description of the document entry; shouldn't be called once finalized
        """
        if self._finalized:
            raise ValueError("document entry has already been finalized")
        self._text_elements.append(element)

    def add_entry_title_element(self, element):
        """
        Adds the title paragraph element to the entry; shouldnt be called once finalized
        """
        if self._finalized:
            raise ValueError("document entry has already been finalized")
        if self._entry_title_element is not None:
            raise ValueError("document entry has already had it's title element set")
        self._entry_title_element = element

    def finalize(self):
        """
        Makes the object runtime immutable; useful for once the object has been fully initialized; should only be called once
        """
        if self._finalized == True:
            raise ValueError("document entry has already been finalized; shouldn't need to refinalize")
        self._finalized = True
    
    def _full_entry_title_text(self) -> str:
        # Google api tends to include the newlines, so remove those
        return read_paragraph_elements(self._entry_title_element).strip("\n")

    def entry_title_text(self) -> str:
        if self.has_date_in_title():
            return self._full_entry_title_text()[DocumentEntry.DATE_STRING_LENGTH:].strip(": ")
        else:
            return self._full_entry_title_text()

    def has_date_in_title(self) -> bool:
        """
        Hacky but works
        """
        try:
            dt_format =  "%d-%b-%Y"
            date_string = self._full_entry_title_text()[:DocumentEntry.DATE_STRING_LENGTH + 1].strip(": ")
            date = datetime.datetime.strptime(date_string, dt_format).date()
            return True
        except:
            return False


    def entry_date(self) -> datetime.date:
        dt_format =  "%d-%b-%Y"
        date_string = self._full_entry_title_text()[:DocumentEntry.DATE_STRING_LENGTH + 1].strip(": ")

        return datetime.datetime.strptime(date_string, dt_format).date()

    def entry_title_text_elements(self) -> List[Any]:
        return self._entry_title_element.copy()
    
    def get_paragraphs(self) -> List[str]:
        out = []
        for paragraph in self._text_elements:
            out.append(read_paragraph_elements(paragraph))
        return out
    
    def _get_paragraph_elements(self) -> List[Any]:
        return self._text_elements.copy()

    def get_markdown_content(self) -> str:
        return "\n\n".join(map(lambda paragraph: paragraph_to_markdown(paragraph), self._get_paragraph_elements()))   


class SmugMugImageData:
    """
    Tiny class representing smugmug image data
    """

    def __init__(self):
        """
        Makes a call to the smugmug api to initialize the class
        """
        favs_out, all_out, key_to_metadata = get_smugmug_data()
        self.favs_out = favs_out
        self.image_date_to_key = all_out
        self.key_to_metadata = key_to_metadata

class SwarmCheckinData:
    """
    Tiny class holding the swarm checkin data
    """
    def __init__(self, swarm_data_cleaned: Dict) -> None:
        self.checkin_data = swarm_data_cleaned


class WebSectionBuilder:
    """
    Maybe this is something that takes in a section, a type (or some other parameter), and the writes the data to it
    """
    def __init__(self, image_data: SmugMugImageData,
                       checkin_data: SwarmCheckinData,
                       health_data: Dict[str, Any]) -> None:
        self._document_section: Optional[DocumentSection] = None
        self._image_data = image_data
        self._health_data = health_data
        self._checkin_data = checkin_data

    def add_document_section(self, document_section: DocumentSection) -> None:
        """
        For sections builds that have an associated document section
        """
        self._document_section = document_section

    def run_section_build(self) -> None:
        """
        Actually outputs the section to the content folder
        """
        if self._document_section is None:
            raise ValueError("the document section has not been set for this standard section, which expects it too be set")
        
        section_folder_path = self.section_parent_path.joinpath(
            self._document_section.title_text())
        section_folder_path.mkdir()

        section_index_frontmatter = {
            "draft" : False,
            "title" : self._document_section.title_text()
        }

        with open(section_folder_path.joinpath("_index.md"), "w") as index_f:
            index_f.write(dict_to_frontmatter_string(section_index_frontmatter))


        image_date_to_key = self._image_data.image_date_to_key
        image_key_to_metadata = self._image_data.key_to_metadata
        for entry in self._document_section.entries():
            date_string = entry.entry_date().strftime("%Y-%m-%d")
            images_data = []
            if date_string in image_date_to_key:
                for image_key in image_date_to_key[date_string]:
                    images_data.append({"largestUri": image_key_to_metadata[image_key]["largest_uri"],
                                       "thumbnailUri": image_key_to_metadata[image_key]["thumbnail_uri"],
                                       "largewidth": int(image_key_to_metadata[image_key]["largewidth"]),
                                       "largeheight": int(image_key_to_metadata[image_key]["largeheight"]),
                                       "titlestr": image_key_to_metadata[image_key]["title"],
                                       "captionstr": image_key_to_metadata[image_key]["caption"]})

            frontmatter = {
                "draft": False,
                "title": entry.entry_title_text(),
                "images": images_data,
                "date": date_string,
                "healthData": self._health_data[date_string],
                "checkin_data": self._checkin_data.checkin_data[date_string]
            }

            with open(section_folder_path.joinpath(date_string + ".md"), "w") as f:
                f.write(dict_to_frontmatter_string(frontmatter))
                markdown_content = entry.get_markdown_content()
                f.write(markdown_content)

    @property
    def section_parent_path(self):
        """
        Gets the folder withing the /content directory that this section folder should go inside
        i.e. content/post/
        """
        parent_path = WebContentBuilder.CONTENT_FOLDER_PATH.joinpath("post/")
        if not parent_path.exists():
            parent_path.mkdir()

        return parent_path


class SearchSectionBuilder(WebSectionBuilder):

    def add_document_section(self, document_section: DocumentSection) -> None:
        raise RuntimeError("A document section was added to the search section builder; this shouldn't happen")

    def run_section_build(self) -> None:
        with open(WebContentBuilder.CONTENT_FOLDER_PATH.joinpath("search.md"), "w") as search_f:
            search_frontmatter = {
                "title": "Search", # in any language you want
                "layout": "search", # is necessary
                "summary": "search page",
                "placeholder": "search for content here",
            }
            search_f.write(dict_to_frontmatter_string(search_frontmatter))


class MiscellanySectionBuilder(WebSectionBuilder):

    def run_section_build(self) -> None:
        
        section_folder_path = self.section_parent_path.joinpath(
            self._document_section.title_text())
        section_folder_path.mkdir()

        section_index_frontmatter = {
            "draft" : False,
            "title" : self._document_section.title_text(),
            "healthData": self._health_data,
        }

        with open(section_folder_path.joinpath("_index.md"), "w") as index_f:
            index_f.write(dict_to_frontmatter_string(section_index_frontmatter))

        for entry_number, entry in enumerate(self._document_section.entries()):
            frontmatter = {
                "draft": False,
                "title": entry.entry_title_text(),
                "layout" : "miscellany_single",
            }

            with open(section_folder_path.joinpath(str(entry_number) + ".md"), "w") as f:
                f.write(dict_to_frontmatter_string(frontmatter))
                f.write(entry.get_markdown_content())

    @property
    def section_parent_path(self):
        """
        Gets the folder withing the /content directory that this section folder should go inside
        i.e. content/post/
        """
        parent_path = WebContentBuilder.CONTENT_FOLDER_PATH
        if not parent_path.exists():
            parent_path.mkdir()

        return parent_path

class OverviewSectionBuilder(WebSectionBuilder):
    
    def run_section_build(self) -> None:
        images_data = []

        image_key_to_metadata = self._image_data.key_to_metadata
        for image_key in image_key_to_metadata:
            images_data.append({"largestUri": image_key_to_metadata[image_key]["largest_uri"],
                                        "thumbnailUri": image_key_to_metadata[image_key]["thumbnail_uri"],
                                        "largewidth": int(image_key_to_metadata[image_key]["largewidth"]),
                                        "largeheight": int(image_key_to_metadata[image_key]["largeheight"]),
                                        "titlestr": image_key_to_metadata[image_key]["title"],
                                        "captionstr": image_key_to_metadata[image_key]["caption"]})
        overview_frontmatter = {
                "title" : "Europe Trip 2022",
                "layout": "all_posts",
                "url" : "/", # this makes it the home page
                "aliases" : "/post", # redirect so this isn't just an empty page
                "images": images_data
            }
        with open(self.section_parent_path.joinpath("_index.md"), "w") as index_f:
            index_f.write(dict_to_frontmatter_string(overview_frontmatter))
            total_content_size = 0
            for paragraph in self._document_section.get_description_elements():
                new_content = paragraph_to_markdown(paragraph) + "\n\n"
                index_f.write(new_content)
                total_content_size += len(new_content)
            assert total_content_size > 500, no_overview_debug_str(total_content_size, self._document_section.get_description_elements())
            print("total size of content in overview section is: " + str(total_content_size))


def no_overview_debug_str(total_content_size, document_description_elements):
    import json
    return f"not enough content; content size is {total_content_size}; document_dump is {json.dumps(document_description_elements, indent=4)}"

class WebContentBuilder:

    CONTENT_FOLDER_PATH = Path("./content")
    
    def __init__(self, image_data: SmugMugImageData,
                       checkin_data: SwarmCheckinData,
                       health_data: Dict[str, Any],
                       document_sections: List[DocumentSection]) -> None:
        self._image_data = image_data
        self._checkin_data = checkin_data
        self._health_data = health_data
        self._document_sections = document_sections.copy()
        self._special_sections: Dict[Any, Type[WebSectionBuilder]] = {}
        if not self.CONTENT_FOLDER_PATH.exists():
            self.CONTENT_FOLDER_PATH.mkdir()

    def set_special_section(self, section_key: Any, section_builder_type: Type[WebSectionBuilder]):
        """
        Tells the content builder to use a specific section builder class for a given section
        The key can either be a string or a document section

        Anything added here will build the section given (even if there isn't)
        actually a DocumentSection associated with the "special section" (i.e. Search has no content
        but does need a builder)
        """
        if section_key in self._special_sections:
            raise ValueError("something has gone wrong and this section is being added twice to special sections")
        self._special_sections[section_key] = section_builder_type


    def build_content(self) -> None:
        """
        Uses the current settings to build the documentation
        """
        # First, run the special builds
        for section_key in self._special_sections: 
            section_builder = self._special_sections[section_key](self._image_data, self._checkin_data, self._health_data)
            if section_key in self._document_sections:
                self._document_sections.remove(section_key)
                section_builder.add_document_section(section_key)
            section_builder.run_section_build()

        # All the remaining sections use the standard builder
        for document_section in self._document_sections:
            section_builder = WebSectionBuilder(self._image_data, self._checkin_data, self._health_data)
            section_builder.add_document_section(document_section)
            section_builder.run_section_build()
