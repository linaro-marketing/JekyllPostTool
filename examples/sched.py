from slugify import slugify
from urllib import request
import sys
import os
import re
from urllib.parse import urlparse
sys.path.insert(0, os.path.abspath(
    os.path.join(os.path.dirname(__file__), '..')))
import requests
import datetime

from jekyll_post_tool import JekyllPostTool
from secrets import SCHED_API_KEY

class ConnectSchedJekyllPosts:

    """
    This class handles the creation of Jekyll posts based on the sched.com API.
    """

    def __init__(self, sched_url, output_path="san19/"):
        # Import API Secret
        self.API_KEY = SCHED_API_KEY
        # Connect Code
        self.connect_code = "san19"
        # Sched.com url
        self.sched_url = sched_url
        # Speaker image path
        self.speaker_image_path = "/assets/images/speakers/san19/"
        # Location of posts
        self.output_path = output_path
        self.posts_output_path = output_path + "posts/"
        self.images_output_path = output_path + "images/"
        # Blacklisted tracks to ignore when creating pages/resources.json
        self.blacklistedTracks = ["Food & Beverage", "Informational"]

        # Setup a new instance of the JekyllPostTool
        self.post_tool = JekyllPostTool(
            {"output": self.output_path + "posts/" })

        # Main Method
        self.main()

    def main(self):
        """
        Main method for the JekyllSchedExportTool
        """
        # Get the results from sched api
        self.sessions_data = self.get_api_results(
            "/api/session/list?api_key={0}&since=1282755813&format=json")
        # self.generate_resources_json_file(self.sessions_data)
        self.users_data = self.get_api_results(
            "/api/user/list?api_key={0}&format=json")
        # Create Update Delete the Jekyll event posts
        self.crud_jekyll_posts(self.sessions_data, self.users_data)

        # self.generate_resources_json_file(self.sessions_data)

    def get_api_results(self, endpoint):
        """
            Gets the results from a specified endpoint
        """
        endpoint = self.sched_url + endpoint.format(self.API_KEY)
        try:
            resp = requests.get(url=endpoint)
            data = resp.json()
            return data
        except Exception as e:
            print(e)
            return False

    def crud_jekyll_posts(self, sessions_data, users_data):
        """
            This method creates/updates/deletes jekyll posts based on api results
        """
        for session in sessions_data:
            # Grab the relevant data from the sessions results
            sched_event_id = session["event_key"]
            session_active = session["active"]
            session_title = session["name"]
            session_start_time = session["event_start"]
            session_end_time = session["event_end"]
            try:
                session_track = session["event_type"]
            except Exception as e:
                session_track = None
            try:
                session_sub_track = session["event_subtype"]
            except KeyError as e:
                session_sub_track = None
            try:
                session_abstract = session["description"]
            except Exception as e:
                session_abstract = "Coming soon..."
            session_attendee_num = session["goers"]
            session_private = session["invite_only"]
            try:
                session_room = session["venue"]
            except Exception as e:
                session_room = None
            try:
                session_venue_id = session["venue_id"]
            except Exception as e:
                pass
            session_id_hash = session["id"]
            try:
                session_speakers = session["speakers"].split(",")
            except KeyError as e:
                session_speakers = None

            if session_track not in self.blacklistedTracks:
                # Get the session id from the title
                try:
                    session_id_regex = re.compile(
                        'SAN19-[A-Za-z]*[0-9]+K*[0-9]*')
                    session_id = session_id_regex.findall(session_title)[0]
                    session_name = re.sub(
                        "SAN19-[A-Za-z]*[0-9]+K*[0-9]*", "", session_title).strip()

                    skipping = False

                # Check to see if a session id exists in the title
                # if not then skip this session - marking as invalid if no session id is present.
                except Exception as e:
                    skipping = True
            else:
                skipping = True

            if skipping == False:
                # Gather the session speakers details
                if session_speakers is not None:
                    session_speakers_arr = []
                    for speaker in session_speakers:
                        speaker_name = speaker.strip()
                        for speaker_object in users_data:
                            if speaker_object["name"] == speaker_name:
                                session_speakers_arr.append(speaker_object)
                    session_speakers_arr = self.download_speaker_images(
                        session_speakers_arr)
                else:
                    with open("missing_speakers.txt", "a+") as my_file:
                        my_file.write(session["name"] + "\n")
                    session_speakers_arr = None

                revised_speakers = []
                if session_speakers_arr != None:
                    for speaker in session_speakers_arr:
                        # Gets the speaker bio
                        speaker_details = self.get_speaker_bio(speaker)
                        try:
                            speaker_url = speaker['url']
                        except KeyError:
                            speaker_url = ""
                        revised_speakers.append({
                            "speaker_name": speaker_details["name"],
                            "speaker_username": speaker_details["username"],
                            "speaker_url": speaker_details['url'],
                            "speaker_company": speaker_details["company"],
                            "speaker_position": speaker_details["position"],
                            "speaker_location": speaker_details["location"],
                            "speaker_image": speaker_details["image"],
                            "speaker_bio":  "{}".format(speaker_details["bio"]).replace("'", ""),
                        })

                session_image = {
                    "path": "/assets/images/featured-images/san19/" + session_id + ".png",
                    "featured": "true",
                }

                session_slot = {
                    "start_time": session_start_time,
                    "end_time": session_end_time,
                }
                # Session Tracks
                if session_sub_track != None:
                    session_tracks = session_sub_track.split(",")
                if session_track != None:
                    main_track = session_track.strip()

                post_frontmatter = {
                    "title": session_id + " - " + session_name,
                    "session_id": session_id,
                    "session_speakers": revised_speakers,
                    "description": "{}".format(session_abstract).replace("'", ""),
                    "image": session_image,
                    "session_room": session_room,
                    "session_slot": session_slot,
                    "tags": session_tracks,
                    "categories": [self.connect_code],
                    "session_track": session_track,
                    "session_attendee_num": session_attendee_num,
                    "tag": "session",
                }

                post_file_name = datetime.datetime.now().strftime(
                    "%Y-%m-%d") + "-" + session_id.lower() + ".md"

                post_file_path = self.posts_output_path + post_file_name

                if os.path.exists(post_file_path):
                    edited = self.post_tool.edit_post(post_frontmatter, "", post_file_name)
                    if edited:
                        print("{} has been edited!".format(post_file_name))
                    else:
                        print("{} has not been edited!".format(post_file_name))
                else:
                    created = self.post_tool.create_post(post_frontmatter, "", post_file_name)
                    if created:
                        print("{} has been written!".format(post_file_name))
            else:
                print("Skipping {}".format(session_title))


    def get_speaker_bio(self, speaker):
        """
        Gets a speaker bio given a speaker speaker object
        """
        # Construct the API Query with the username added.
        api_query = "/api/user/get?api_key={0}&by=username&term=" + \
            speaker["username"] + "&format=json"
        # Get the speaker details
        speaker_details = self.get_api_results(api_query)

        speaker["bio"] = speaker_details["about"]
        try:
            speaker_url = speaker_details['url']
        except KeyError as e:
            speaker_url = ""
        speaker["url"] = speaker_url

        return speaker

    def download_speaker_images(self, session_speakers_arr):
        """
            Downloads the session speaker images based on an array of speakers passed in
            Returns: speakers array with downloaded image paths
        """
        for speaker in session_speakers_arr:
            speaker_avatar_url = speaker["avatar"]
            if len(speaker_avatar_url) < 3:
                speaker["image"] = "/assets/images/speakers/placeholder.jpg"
            else:
                file_name = self.grab_photo(
                    speaker_avatar_url, slugify(speaker["name"]))
                speaker["image"] = self.speaker_image_path + file_name
        return session_speakers_arr

    def grab_photo(self, url, output_filename):
        """Fetches attendee photo from the pathable data"""
        speaker_image_dest = self.images_output_path

        if not os.path.exists(speaker_image_dest):
            os.makedirs(speaker_image_dest)
        # Get the filename parsed in
        file_name = output_filename
        # Extract the path from the URL
        path = urlparse(url).path
        # Get the Extension from the path using os.path.splitext
        ext = os.path.splitext(path)[1]
        # Add output folder to output path
        output = speaker_image_dest + file_name + ext
        # Try to download the image and Except errors and return as false.
        try:
            opener = request.build_opener()
            opener.addheaders = [('User-agent', 'Mozilla/5.0')]
            request.install_opener(opener)
            image = request.urlretrieve(url, output)
        except Exception as e:
            print(e)
            image = False
        return(file_name + ext)


if __name__ == "__main__":
    ConnectSchedJekyllPosts("https://linaroconnectsandiego.sched.com")
