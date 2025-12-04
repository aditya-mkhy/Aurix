
def extract_tags_and_cover(path: str, cover_save_path: str = None):
    """
    Extract text tags + embedded cover image from an MP3 file.

    :param path: Path to the .mp3 file
    :param cover_save_path: Optional path to save cover image (e.g. 'cover.jpg')
    :return: (tags_dict, cover_info_dict)
             tags_dict = { 'title': ..., 'artist': ..., ... }
             cover_info_dict = { 'mime': ..., 'data': bytes or None }
    """
    tags = ID3(path)
    path = None

    def _get_text(tag_id):
        frame = tags.get(tag_id)
        if frame and hasattr(frame, "text") and frame.text:
            return str(frame.text[0])
        return None

    info = {
        "title":   _get_text("TIT2"),
        "length":  _get_text("TLEN"),   # usually in ms (string)
        "genre":   _get_text("TCON"),
        "artist":  _get_text("TPE1"),
        "album":   _get_text("TALB"),
        "desc":    _get_text("TDES"),
        "publisher": _get_text("TPUB"),
        "publisher_url": _get_text("WPUB"),
        "release_date": _get_text("TDRL"),
    }

    # ---- Extract cover (APIC frame) ----
    cover_data = None
    cover_mime = None

    # APIC frames can have descriptors like 'APIC:', 'APIC:Cover', etc.
    apic_frame = None
    for frame in tags.values():
        if isinstance(frame, APIC):
            apic_frame = frame
            break

    if apic_frame is not None:
        cover_data = apic_frame.data
        cover_mime = apic_frame.mime

        if cover_save_path:
            filename = f"{make_title_path(info['title'])}.jpg"
            path = os.path.join(cover_save_path, filename)
            with open(path, "wb") as tf:
                tf.write(cover_data)



    return info, path



def get_info() -> list:
    info_list = []


    path = "C:\\Users\\freya\\Music"
    save_dir = "C:\\Users\\freya\\Downloads\\m"

    for file in os.listdir(path):
        _, ext = os.path.splitext(file)

        if ext != ".mp3":
            continue
        
        full_path = os.path.join(path, file)

        info, img_path = extract_tags_and_cover(full_path, save_dir)
        info_list.append([info['title'], info['publisher'], img_path, full_path])

    return info_list
