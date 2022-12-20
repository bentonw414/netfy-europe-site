# netfy-eurosite
Repo for netlify version of the Europe site (using Hugo)

## Setup for development

Netlify is using python 3.8, so in order to setup, the easiest thing is probably the following:
- Make a venv in python3.8
    - `python3.8 -m venv .venv` (might need to install python 3.8 if python3.8 or python3 aren't the correct version, but worst case it should work with 3.9 too)
    - Run `. .venv/bin/activate` to activate the venv (`deactivate` deactivates the venv)

- Install the packages in requirements.txt (after activating venv)
    - `pip install -r requirements.txt`


- Get a `gcp_key.json` file from google cloud. This basically involves making a service account and then giving it access to the Europe trip doc and then downloading the key. (Benton also has this file stored on the mac which might just be easier).
- Make a file called `smugmug_api_key.txt` in the root directory that contains only an api key for smugmug api (Benton also has this stored locally if that is easier)

## To build/run locally

Once completing the above:

- Remove the content from previous builds (if it exists): `rm -r content/`
- Build the site: `python build_site.py`
- Launch a local server: `hugo server`
