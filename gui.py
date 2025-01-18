import vlc
import tkinter as tk
from tkinter import filedialog
from tkinter.ttk import Scale
from PIL import Image, ImageTk
import os
from mutagen.mp3 import MP3
from mutagen.id3 import ID3, APIC
from mutagen.flac import FLAC
from urllib.parse import unquote

class VLCMediaPlayer:
    def __init__(self, root):
        self.root = root
        self.root.title("VLC Media Player")
        self.root.geometry("800x600")

        # VLC player instance
        self.instance = vlc.Instance("--no-xlib")  # '--no-xlib' to prevent display errors on some systems
        self.player = self.instance.media_player_new()

        # UI Components
        self.video_frame = tk.Frame(self.root, bg="black")
        self.video_frame.pack(fill=tk.BOTH, expand=1)

        # Create a smaller frame for the cover art (50% of the video frame)
        self.cover_frame = tk.Frame(self.video_frame, bg="black")
        self.cover_frame.place(relx=0.5, rely=0.5, anchor="center")  # Position it in the center

        self.cover_label = tk.Label(self.cover_frame, bg="black")
        self.cover_label.pack(fill=tk.BOTH, expand=1)

        self.controls_frame = tk.Frame(self.root)
        self.controls_frame.pack(fill=tk.X, padx=10, pady=5)

        self.play_button = tk.Button(self.controls_frame, text="Play", command=self.play)
        self.play_button.grid(row=0, column=0, padx=5)

        self.pause_button = tk.Button(self.controls_frame, text="Pause", command=self.pause)
        self.pause_button.grid(row=0, column=1, padx=5)

        self.stop_button = tk.Button(self.controls_frame, text="Stop", command=self.stop)
        self.stop_button.grid(row=0, column=2, padx=5)

        self.open_button = tk.Button(self.controls_frame, text="Open", command=self.open_file)
        self.open_button.grid(row=0, column=3, padx=5)

        self.volume_label = tk.Label(self.controls_frame, text="Volume")
        self.volume_label.grid(row=0, column=4, padx=5)

        self.volume_slider = Scale(self.controls_frame, from_=0, to=100, orient=tk.HORIZONTAL, command=self.set_volume)
        self.volume_slider.set(50)
        self.volume_slider.grid(row=0, column=5, padx=5)
        
       # Create a label for displaying the title next to the volume slider
        self.title_label = tk.Label(self.controls_frame, text="No Song Loaded", fg="Black", font=("Arial", 14))
        self.title_label.grid(row=0, column=8, padx=10, sticky="w", columnspan=2)  # Adjust columnspan for more room
        
        # Add Fast Forward button next to the Pause button
        self.ff_button = tk.Button(self.controls_frame, text="Fast Forward", command=self.fast_forward)
        self.ff_button.grid(row=0, column=2, padx=5)  # Adjust the position as needed

        # Add Rewind button next to the Fast Forward button
        self.rewind_button = tk.Button(self.controls_frame, text="Rewind", command=self.rewind)
        self.rewind_button.grid(row=0, column=3, padx=5)  # Adjust the position as needed

        self.progress_var = tk.DoubleVar()
        self.progress_slider = Scale(self.controls_frame, from_=0, to=100, orient=tk.HORIZONTAL, variable=self.progress_var, command=self.seek)
        self.progress_slider.grid(row=1, column=0, columnspan=6, sticky="ew", pady=5)

        # Replace the previous button definition with the new one
        self.open_button = tk.Button(self.controls_frame, text="Open", command=self.load_new_song)
        self.open_button.grid(row=0, column=7, padx=5)  # Add it in the same place as before

        
        self.update_progress()

    def play(self):
        if self.player.get_media() is None:
            self.open_file()  # Load media if it's not already loaded
        self.cover_label.pack_forget()  # Hide cover when playback starts
        self.player.play()  # Ensure this is called after successful media load
        self.display_cover()

    def pause(self):
        self.player.pause()

    def stop(self):
        self.player.stop()
        self.cover_label.pack(fill=tk.BOTH, expand=1)  # Show cover on stop
        
    def is_playing(self):
        return self.player.is_playing()
    
    def fast_forward(self):
        if self.player.is_playing():
            current_position = self.player.get_position()
            current_time = current_position * self.player.get_length()
            
            # Skip forward by 10 seconds (adjust time units if necessary)
            new_time = current_time + 10000  # Add 10,000 milliseconds (10 seconds)

            # Ensure we don't exceed the track length
            if new_time > self.player.get_length():
                new_time = self.player.get_length()

            # Calculate the new position (0 to 1)
            new_position = new_time / self.player.get_length()

            print(f"Track length: {self.player.get_length()}, Current position = {current_position}, New time = {new_time}, New position = {new_position}")

            # Ensure that we aren't making a change that's too small
            if abs(new_position - current_position) < 0.01:  # If change is too small, skip
                print("Skipping fast forward due to small position change.")
                return

            self.player.set_position(new_position)
            self.update_progress()

    def rewind(self):
        if self.player.is_playing():
            current_position = self.player.get_position()
            current_time = current_position * self.player.get_length()
            
            # Skip backward by 10 seconds (adjust time units if necessary)
            new_time = current_time - 10000  # Subtract 10,000 milliseconds (10 seconds)
            if new_time < 0:
                new_time = 0

            # Calculate the new position (0 to 1)
            new_position = new_time / self.player.get_length()

            print(f"Track length: {self.player.get_length()}, Current position = {current_position}, New time = {new_time}, New position = {new_position}")

            # Ensure that we aren't making a change that's too small
            if abs(new_position - current_position) < 0.01:  # If change is too small, skip
                print("Skipping rewind due to small position change.")
                return

            self.player.set_position(new_position)
            self.update_progress()


    def load_new_song(self):
        """Load a new song and reset the player state."""
        file_path = filedialog.askopenfilename(filetypes=[("Media files", "*.*")])
        if file_path:
            media = self.instance.media_new(file_path)
            self.player.set_media(media)  # Set the new media
            self.player.play()  # Start playback

            # Update cover art
            cover_art_path = self.extract_cover(file_path)
            if cover_art_path:  # Only display if cover art was extracted
                self.display_cover()

            # Update the title
            title = os.path.basename(file_path)  # Extract file name for title display
            self.title_label.config(text=title)  # Update the label with the title

            # Start playback automatically after loading the file
            self.play()


    def open_file(self):
        file_path = filedialog.askopenfilename(filetypes=[("Media files", "*.*")])
        if file_path:
            media = self.instance.media_new(file_path)
            self.player.set_media(media)
            self.player.set_hwnd(self.video_frame.winfo_id())  # Set video output to the video frame

            # Extract and display the cover art
            cover_art_path = self.extract_cover(file_path)
            if cover_art_path:  # Only display if cover art was extracted
                self.display_cover()  # Call without any arguments

            # Extract the title from the file name
            title = os.path.basename(file_path)  # Default to file name if no metadata
            self.title_label.config(text=title)  # Update the title label

            # Force the GUI to update and reflect changes
            self.root.update_idletasks()

            print(f"Song Title: {title}")  # Debugging print statement to check if title is being extracted

            self.play()  # Start playback automatically



    def display_cover(self):
        """Display the extracted cover art in a smaller frame."""
        cover_art_path = "temp_cover.jpg"  # Path where the cover art is saved

        # Check if cover art exists
        if os.path.exists(cover_art_path):
            try:
                img = Image.open(cover_art_path)

                # Resize the image to fit 70% of the video frame size
                video_frame_width = self.video_frame.winfo_width() or 800  # Default size if dimensions are unavailable
                video_frame_height = self.video_frame.winfo_height() or 600

                # Set the size of the cover frame to be 70% of the video frame size
                cover_width = int(video_frame_width * 0.7)
                cover_height = int(video_frame_height * 0.7)

                # Resize the image
                img = img.resize((cover_width, cover_height), Image.Resampling.LANCZOS)

                # Convert the image to a Tkinter PhotoImage object
                photo = ImageTk.PhotoImage(img)

                # Update cover_label with the resized image
                self.cover_label.config(image=photo)  # Update label with image
                self.cover_label.image = photo  # Keep a reference to avoid garbage collection

                # Make sure the cover label is visible
                self.cover_label.pack(fill=tk.BOTH, expand=1)

            except Exception as e:
                print(f"Error displaying cover art: {e}")
        else:
            # If no cover art found, display fallback text
            self.cover_label.config(image="", text="No Cover Art Available", fg="white", font=("Arial", 16))
            self.cover_label.pack(fill=tk.BOTH, expand=1)

    def extract_cover(self, file_path):
        """Extract cover art from audio files and save it to a local file."""
        try:
            # Remove the 'file://' prefix if present
            if file_path.startswith('file://'):
                file_path = file_path[7:]  # Remove the 'file://' part

            # Decode any URL-encoded characters (like %20 for spaces)
            file_path = unquote(file_path)

            # Ensure the path starts correctly for Windows (removes leading slash if it exists)
            if file_path.startswith('/'):
                file_path = file_path[1:]  # Remove leading '/' if it's a Unix-style path

            # Check if the file exists
            if not os.path.exists(file_path):
                print(f"File does not exist: {file_path}")
                return None

            cover_path = "temp_cover.jpg"  # Path where we will save the cover image

            # Extract cover art for MP3 files
            if file_path.lower().endswith('.mp3'):
                audio = MP3(file_path, ID3=ID3)
                for tag in audio.tags.values():
                    if isinstance(tag, APIC):  # Attached picture
                        with open(cover_path, "wb") as img_file:
                            img_file.write(tag.data)
                        print(f"Cover art extracted and saved to: {cover_path}")
                        return cover_path

            # Extract cover art for FLAC files
            elif file_path.lower().endswith('.flac'):
                audio = FLAC(file_path)
                if audio.pictures:
                    with open(cover_path, "wb") as img_file:
                        img_file.write(audio.pictures[0].data)
                    print(f"Cover art extracted and saved to: {cover_path}")
                    return cover_path

        except Exception as e:
            print(f"Error extracting cover art: {e}")

        return None

    def set_volume(self, volume):
        self.player.audio_set_volume(int(float(volume)))

    def seek(self, value):
        if self.player.is_playing():
            pos = float(value) / 100
            self.player.set_position(pos)

    def update_progress(self):
        if self.player.is_playing():
            pos = self.player.get_position() * 100
            self.progress_var.set(pos)
        self.root.after(500, self.update_progress)

if __name__ == "__main__":
    root = tk.Tk()
    player = VLCMediaPlayer(root)
    root.mainloop()
