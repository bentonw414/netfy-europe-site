from __future__ import annotations
import os.path
import ruamel.yaml as yaml

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google.oauth2 import service_account
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from typing import Any, List, Dict

# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/documents.readonly']

# The ID of a sample document.
DOCUMENT_ID = '1BBUVAmdXC16AYoWBKpDOQXb_QfvBd0vXp6qS_SCyHuE'

SECTION_STYLE_NAMED_STYLETYPE = "HEADING_1"
ENTRY_STYLE_NAMED_STYLETYPE = "HEADING_2"


def read_paragraph_element(element):
    """Returns the text in the given ParagraphElement.

        Args:
            element: a ParagraphElement from a Google Doc.
    """
    text_run = element.get('textRun')
    if not text_run:
        return ''
    return text_run.get('content')


def read_structural_elements(elements):
    """Recurses through a list of Structural Elements that are paragraphs to read a document's text where text may not be
        in nested elements.

        Args:
            elements: a list of Structural Elements.
    """
    text = ''
    for value in elements:
        if 'paragraph' in value and value['paragraph']['paragraphStyle']['namedStyleType'] == 'HEADING_2':
            elements = value.get('paragraph').get('elements')
            for elem in elements:
                text += read_paragraph_element(elem)
    return text


def extract_document_sections(document) -> List[DocumentSection]:
    """
    Splits the contents of the document into the information needed to extract the text
    """
    from classes import DocumentSection, DocumentEntry
    all_elements = document.get('body').get('content')
    sections: List[DocumentSection] = []
    next_section: DocumentSection = None
    next_entry: DocumentEntry = None

    for value in all_elements:
        if 'paragraph' in value:
            style = value['paragraph']['paragraphStyle']['namedStyleType']
            elements = value.get('paragraph').get('elements')
            is_bullet = 'bullet' in value.get('paragraph')
            elements[0]["is_bullet"] = is_bullet # TODO this is stupid hack

            if style == SECTION_STYLE_NAMED_STYLETYPE:
                # style is a section: this means the previous section is done
                if next_section is not None:
                    sections.append(next_section)
                    if next_entry is not None:
                        next_entry.finalize()
                        next_section.add_document_entry(next_entry)
                        next_entry = None
                    next_section.finalize()
                next_section = DocumentSection()
                next_section.add_title_element(elements)
            elif style == ENTRY_STYLE_NAMED_STYLETYPE:
                # we are a a new entry, but not a new section
                if next_entry is not None:
                    next_entry.finalize()
                    next_section.add_document_entry(next_entry)
                next_entry = DocumentEntry()
                next_entry.add_entry_title_element(elements)

            else:
                if next_entry is not None:
                    next_entry.add_paragraph_element(elements)
                elif next_section is not None:
                    next_section.add_paragraph_element(elements)
                else:
                    print("somewhere there is a paragraph not in a section START OF ELEM\n", read_paragraph_elements(elements), "\n END OF ELEM")

    if next_section is not None:
        sections.append(next_section)
        if next_entry is not None:
            next_entry.finalize()
            next_section.add_document_entry(next_entry)
        next_section.finalize()

    return sections

def make_google_api_request(mock=False):
    creds = None

    if os.environ.get('APP_LOCATION') == 'netlify':
        with open("./gcp_key.json", "w") as gcp_json_f:
            gcp_json_f.write(os.environ.get("GCP_KEY_JSON"))
        creds = service_account.Credentials.from_service_account_file('gcp_key.json')
    elif not mock:
        creds = service_account.Credentials.from_service_account_file('gcp_key.json')
    else:
        # mock is true
        pass 

    try:
        if not mock:
            service = build('docs', 'v1', credentials=creds)

            # Retrieve the documents contents from the Docs service.
            document = service.documents().get(documentId=DOCUMENT_ID).execute()
        else:
            import pickle
            with open("./mock_api_return.pkl", "rb") as f:
                document = pickle.load(f)


        return document

    except HttpError as err:
        print(err)

# The ID of the trip log google doc
DOCUMENT_ID = '1BBUVAmdXC16AYoWBKpDOQXb_QfvBd0vXp6qS_SCyHuE'

def dict_to_frontmatter_string(input_dict: Dict) -> str:
    """
    Takes in a dictionary and returns the corresponding frontmatter string in yaml format
    """
    output = yaml.round_trip_dump(input_dict, explicit_start=False)
    return "---\n" + output + "---\n"

def paragraph_to_markdown(paragraph_elements) -> str:
    is_bullet = paragraph_elements[0]['is_bullet']
    if is_bullet:
        output = "- "
    else:
        output = ""

    for element in paragraph_elements:
        text_run = element.get('textRun')
        if text_run:
            is_bold = 'bold' in text_run.get('textStyle') and text_run.get('textStyle').get('bold')
            is_italic = 'italic' in text_run.get('textStyle') and text_run.get('textStyle').get('italic')
            is_link = 'link' in text_run.get('textStyle') and "url" in text_run.get('textStyle').get('link')
            if is_link:
                url_link = text_run.get('textStyle').get('link').get('url')

            # special case for handling google empty format sections
            # as it doesn't convert to markdown nicely
            if text_run.get('content').strip("\n") == "":
                continue

            # enclose opening
            if is_link:
                output += "["
            if is_italic:
                output += "*"
            if is_bold:
                output += "**"
            
            # add in the actual text
            output += text_run.get('content').strip("\n")

            # enclose closing
            if is_bold:
                output += "**"
            if is_italic:
                output += "*"
            if is_link:
                output += "](" + url_link + ")"

    return output

def read_paragraph_elements(elements):
    output = ""
    for element in elements:
        output += read_paragraph_element(element)
    return output


