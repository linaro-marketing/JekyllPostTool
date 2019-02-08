from urllib import request
import io
import textwrap
import csv
import os
from urllib.parse import urlparse
import frontmatter
from io import BytesIO
import datetime
import re   
import datetime
import glob
import requests
import json
from slugify import slugify


class JekyllSchedExportTool:
    
    """
    This class can create and modifies Jekyll posts for the Connect static website
    based on export data from Pathable.
    """

    def __init__(self, post_location="not-set", sched_url=None):
        self.connect_code = "bkk19"
        # Sched.com url
        self.sched_url = sched_url
        # API Key
        self.API_KEY = "ae421cd949aee2ff3e63a8b3f2712cfe"
        # Speaker image path
        self.speaker_image_path = "/assets/images/speakers/bkk19/"
        # Location of posts
        self._post_location = post_location
        # Local Output path for images
        self.output_path = post_location
        # Main Method
        self.main()

    
    def main(self):
        """
        Main method for the JekyllSchedExportTool
        """

        # Get the results from sched api
        self.sessions_data = self.get_api_results("/api/session/list?api_key={0}&since=1282755813&format=json")
        self.users_data = self.get_api_results("/api/user/list?api_key={0}&format=json")
        # Create Update Delete the Jekyll event posts
        self.crud_jekyll_posts(self.sessions_data, self.users_data)

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
            # Open a default template blog post.
            session_post = frontmatter.loads(open("template.md","r").read())
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

            # Get the session id from the title
            try:
                session_id_regex = re.compile('BKK19-K*[0-9]+')
                session_id = session_id_regex.findall(session_title)[0]
                session_name = re.sub("BKK19-K*[0-9]+", "", session_title).strip()

                print(session_id)
                print(session_name)

                skipping = False

            # Check to see if a session id exists in the title 
            # if not then skip this session - marking as invalid if no session id is present.
            except Exception as e:
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
                    session_speakers_arr =  self.download_speaker_images(session_speakers_arr)
                else:
                    with open("missing_speakers.txt", "a+") as my_file:
                        my_file.write(session["name"] + "\n")
                    session_speakers_arr = None

                revised_speakers = []
                if session_speakers_arr != None:
                    for speaker in session_speakers_arr:
                        # Gets the speaker bio
                        speaker_details = self.get_speaker_bio(speaker)
                        revised_speakers.append({
                            "speaker_name": speaker_details["name"],
                            "speaker_username": speaker_details["username"],
                            "speaker_company": speaker_details["company"],
                            "speaker_position": speaker_details["position"],
                            "speaker_location": speaker_details["location"],
                            "speaker_image": speaker_details["image"],
                            "speaker_bio":  "> {}".format(speaker_details["bio"]).replace("'",""),
                        })

                session_image = {
                    "path": "/assets/images/featured-images/bkk19/" + session_id + ".png",
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

                
                with open("titles.txt", "a+") as my_file:
                    my_file.write(session_name + "\n")

                post_frontmatter = {
                        "title": session_name,
                        "session_id": session_id,
                        "session_speakers": revised_speakers,
                        "description": "> {}".format(session_abstract).replace("'",""),
                        "future_image": session_image,
                        "session_room": session_room,
                        "session_slot": session_slot,
                        "tags": session_tracks,
                        "categories": [self.connect_code],
                        "session_track": session_track,
                        "session_attendee_num": session_attendee_num,
                        "tag": "session",
                }
                session_post.metadata = post_frontmatter
                session_post.content = ""
                post_file_name = datetime.datetime.now().strftime("%Y-%m-%d") + "-" + slugify(session_name)+ ".md"
                post_file_path = self._post_location + post_file_name
                print("Writing {0}".format(post_file_path))
                with open(post_file_path, "w+") as new_post_file:
                    new_post_file.writelines(frontmatter.dumps(session_post))


    def get_speaker_bio(self, speaker):
        """
        Gets a speaker bio given a speaker speaker object
        """
        # Construct the API Query with the username added.
        api_query = "/api/user/get?api_key={0}&by=username&term=" + speaker["username"] + "&format=json"
        # Get the speaker details
        speaker_details = self.get_api_results(api_query)
        
        speaker["bio"] = speaker_details["about"]

        return speaker

    def download_speaker_images(self, session_speakers_arr):
        """
            Downloads the session speaker images based on an array of speakers passed in
            Returns: speakers array with downloaded image paths
        """
        for speaker in session_speakers_arr:
            speaker_avatar_url = speaker["avatar"]
            if len(speaker_avatar_url) < 3:
                speaker["image"] = self.speaker_image_path + "placeholder.png"
            else:
                file_name = self.grab_photo(speaker_avatar_url, speaker["name"].replace(" ", ""))
                speaker["image"] = self.speaker_image_path + file_name
        return session_speakers_arr
                        
    def grab_photo(self, url, output_filename, output_path="speaker_images/"):
        """Fetches attendee photo from the pathable data"""
        # Get the filename parsed in
        file_name = output_filename
        # Extract the path from the URL
        path = urlparse(url).path
        # Get the Extension from the path using os.path.splitext
        ext = os.path.splitext(path)[1]
        # Add output folder to output path
        output =  output_path + file_name + ext
        # Try to download the image and Except errors and return as false.
        try:
            image = request.urlretrieve(url, output)
            print(image)
        except Exception as e:
            print(e)
            image = False
        return(file_name + ext)
        
if __name__ == "__main__":
    
    cards = JekyllSchedExportTool("bkk19/", "https://bkk19.sched.com")
