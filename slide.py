import os, dotenv, requests, random
import tkinter as tk
from PIL import Image, ImageTk, ExifTags
from datetime import datetime

class SlideShow(tk.Tk):
    def __init__(self, directory: str = "."):
        """
        Main slideshow window without controls and max screen size
        """
        self.directory = directory.replace("/", os.sep).replace("\\", os.sep)

        tk.Tk.__init__(self)

        self.attributes("-fullscreen", True)

        self.overrideredirect(True)

        self.screen_w, self.screen_h = self.winfo_screenwidth(), self.winfo_screenheight()
        self.geometry("{}x{}+{}+{}".format(self.screen_w, self.screen_h, 0, 0))

        self.image_list = []
        self.current_image = None
        self.current_id = 0

        self.canvas = tk.Canvas(self, background="black", highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)

        self.get_images()

    def get_images(self):
        """
        Get all images from the directory and shuffle them
        """
        for root, _, files in os.walk(self.directory):
            for file in files:
                if any(file.lower().endswith(x) for x in [".jpg", ".jpeg", ".png", ".gif"]):
                    img_path = os.path.join(root, file)
                    self.image_list.append(img_path)

        random.shuffle(self.image_list)

    def start_slideshow(self, delay: int = 4):
        """
        Select an image from the list and display it with a delay
        """
        image = self.image_list[self.current_id]
        # Select next image using its shuffle id (non repeatable until looping is complete)
        self.current_id = (self.current_id + 1) % len(self.image_list)
        self.show_image(image)
        self.after(delay * 1000, self.start_slideshow)

    def parse_image_data(self, image_obj: Image) -> dict:
        """
        Get image data from exif
        """
        exif = image_obj._getexif()

        if not exif:
            return {}

        return {ExifTags.TAGS[k]: v for k, v in exif.items() if k in ExifTags.TAGS}

    def get_image_date(self, image_path: str, image_date: str) -> str:
        """
        Parse date using exif data if exists, else use file modification date
        """
        if image_date:
            date = datetime.strptime(image_date, "%Y:%m:%d %H:%M:%S")
        else:
            date = datetime.fromtimestamp(os.stat(image_path).st_mtime)

        return date.strftime("%d/%m/%Y %H:%M:%S")

    def get_image_coords(self, gps_info: dict) -> str:
        """
        Get the image coordinates as latitude, longitude and altitude
        """
        # Convert the GPS coordinates stored in the EXIF to degrees in float format
        dms_to_decimal = lambda dms: float(dms[0]) + float(dms[1]) / 60 + float(dms[2]) / 3600

        coords_data = {ExifTags.GPSTAGS[k]: v for k, v in gps_info.items() if k in ExifTags.GPSTAGS}

        if coords_data:
            lat = + dms_to_decimal(coords_data.get("GPSLatitude"))
            lon = + dms_to_decimal(coords_data.get("GPSLongitude"))
            alt = round(coords_data.get("GPSAltitude"))

            if coords_data.get("GPSLatitudeRef") != "N":
                lat *= -1
            if coords_data.get("GPSLongitudeRef") != "E":
                lon *= -1

        return lat, lon, alt

    def get_image_location(self, lat, lon):
        """
        Get the place at which the image was taken using latitude and longitude
        """
        key = os.environ.get("API_KEY")
        url = f"http://api.positionstack.com/v1/reverse?access_key={key}&query={lat},{lon}&limit=1"
        req = requests.get(url)

        return req.json()["data"][0]["name"] + ", " + req.json()["data"][0]["locality"]

    def show_image(self, filepath: str):
        """
        Resize the image to fit the screen without exceeding the original image size / specified size
        """
        image = Image.open(filepath)

        filename = filepath.split(os.sep)[-1]
        image_data = self.parse_image_data(image)
        image_date = self.get_image_date(filepath, image_data.get("DateTimeOriginal", image_data.get("DateTime")))
        if image_data.get("GPSInfo"):
            image_coords = self.get_image_coords(image_data.get("GPSInfo"))
            image_alt = "Altitude : " + str(image_coords[2]) + "m"
            image_loc = self.get_image_location(image_coords[0], image_coords[1])
        else:
            image_coords = (0, 0, 0)
            image_alt = None
            image_loc = "Lieu non défini"

        image.thumbnail((self.screen_w, self.screen_h), Image.Resampling.LANCZOS)

        self.current_image = ImageTk.PhotoImage(image)
        self.canvas.delete("all")
        self.canvas.create_image(self.screen_w / 2, self.screen_h / 2, anchor="center", image=self.current_image)

        # Image date top left
        self.canvas.create_text(20, 10, text=image_date, fill="white", font=("Ubuntu", 12), anchor="nw")
        # Image location bottom left
        self.canvas.create_text(20, self.screen_h - (30 if image_alt else 10), text=image_loc, fill="white", font=("Ubuntu", 12), anchor="sw")
        self.canvas.create_text(20, self.screen_h - 10, text=image_alt, fill="white", font=("Ubuntu", 12), anchor="sw")
        # Image name bottom right
        self.canvas.create_text(self.screen_w - 20, self.screen_h - 10, text=filename, fill="white", font=("Ubuntu", 12), anchor="se")



if __name__ == "__main__":
    dotenv.load_dotenv()

    slideShow = SlideShow(directory="img/")
    slideShow.start_slideshow(delay=2)
    slideShow.mainloop()