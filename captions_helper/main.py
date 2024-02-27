import os
import glob
import base64
import urllib.parse
import streamsync as ss

MAX_IMAGE_FILE_NAMES_DISPLAY = 15

# Its name starts with _, so this function won't be exposed
def _update_image_paths(state):
    image_paths_stage = glob.glob(state["images_path"])
    image_paths = [path for path in image_paths_stage if path.endswith(".jpg") or path.endswith(".png")]
    image_paths.sort()
    state["image_paths"] = image_paths
    if len(image_paths) == 0:
        state.add_notification("warning", "No images found", f"No .png or .jpg files found in path:{state['images_path']}")

def _get_dataurl_for_image(image_path):
    binary_fc = open(image_path, 'rb').read()
    base64_utf8_str = base64.b64encode(binary_fc).decode('utf-8')
    ext = image_path.split('.')[-1]
    dataurl = f'data:image/{ext};base64,{base64_utf8_str}'
    return dataurl

def _update_image_info(state):
    try:
        current_image_path = state["image_paths"][state["current_image_index"]]
        file_uri = urllib.parse.quote(current_image_path)
        state["current_image_url"] = _get_dataurl_for_image(current_image_path)
        state["current_image_name"] = current_image_path.split("/")[-1]
        try:
            with open(_get_caption_file_path_from_image_path(current_image_path), "r") as file:
                state["current_caption"] = file.read()
        except FileNotFoundError:
            # Handle case where caption file doesn't exist yet
            pass
    except IndexError:
        # Handle case where index outside of available images
        state["current_image_url"] = ""
        state["current_image_name"] = ""
        state["current_caption"] = ""

def update_image_file_names_text(state):
    _update_image_paths(state)
    _update_image_info(state)
    file_paths_text_list = []
    for idx, path in enumerate(state["image_paths"]):
        if idx < MAX_IMAGE_FILE_NAMES_DISPLAY:
            file_paths_text_list.append(path.split("/")[-1])
        else:
            file_paths_text_list.append("...")
            break
    
    state["images_file_names_text"] = "\n".join(file_paths_text_list)

def rename_to_trigger(state):
    try:
        for idx, file in enumerate(state["image_paths"]):
            stem = "/".join(file.split("/")[:-1])
            file_name = file.split("/")[-1]
            file_extension = file.split(".")[-1]
            os.rename(file, f"{stem}/{state['trigger_word']} ({idx}).{file_extension}")
        # Refresh current file name text
        update_image_file_names_text(state)
        state.add_notification("success", "Images renamed to trigger", "Success")
    except Exception as e:
        state.add_notification("error", "Images rename error", e)


def add_home_directory_to_images_path(state):
    state["images_path"] += os.path.expanduser("~")

def _get_caption_file_path_from_image_path(image_path):
    image_path_minus_ext = image_path.split(".")[:-1][0]
    caption_file_path = f"{image_path_minus_ext}.txt"
    return caption_file_path

def add_caption_files(state):
    try:
        for file in state['image_paths']:
            new_file_name = _get_caption_file_path_from_image_path(file)
            with open(new_file_name, "w") as f:
                f.write(state["trigger_word"])
        
        state.add_notification("success", "Caption Files Added", "Success")
    except Exception as e:
        state.add_notification("error", "Add caption files error", e)

def next_image(state):
    state["current_image_index"] += 1
    _update_image_info(state)

def previous_image(state):
    state["current_image_index"] -= 1
    _update_image_info(state)

def write_caption_file(state):
    current_image_path = state["image_paths"][state["current_image_index"]]
    caption_file_path = _get_caption_file_path_from_image_path(current_image_path)
    with open(caption_file_path, "w") as file:
        file.write(state["current_caption"])
    
# Initialise the state

# "_my_private_element" won't be serialised or sent to the frontend,
# because it starts with an underscore

initial_state = ss.init_state({
    "my_app": {
        "title": "Caption Helper"
    },
    "images_path": "",
    "image_paths": [],
    "images_file_names_text": "",
    "trigger_word": "",
    "current_image_index": 0,
    "current_image_url": "",
    "current_image_name": "",
    "current_caption": "",
})
