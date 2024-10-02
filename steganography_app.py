import tkinter as tk
from tkinterdnd2 import TkinterDnD, DND_FILES
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk
from audio_steganography import encode_audio_lsb, decode_audio_lsb
from image_steganography import encode_image, decode_image
from video_steganography import encode_video, decode_video  # Import video functions

# Global variables for bit sizes
cover_bits = 0
payload_bits = 0

class SteganographyApp(TkinterDnD.Tk):
    def __init__(self):
        super().__init__()
        self.title("LSB Steganography")
        self.configure(bg="#f7f7f7")

        # Frame for file selection
        self.frame = tk.Frame(self, bg="#ffffff", padx=20, pady=20)
        self.frame.pack(pady=20)

        # Cover Object
        self.cover_label = tk.Label(self.frame, text="Cover Object (Image/Audio/Video/Text):", bg="#ffffff", font=("Arial", 12))
        self.cover_label.grid(row=0, column=0, padx=10)

        self.cover_entry = tk.Entry(self.frame, width=40, font=("Arial", 12))
        self.cover_entry.grid(row=0, column=1)

        self.cover_browse_button = tk.Button(self.frame, text="Browse", command=self.load_cover_file, bg="#4CAF50", fg="white", font=("Arial", 12))
        self.cover_browse_button.grid(row=0, column=2, padx=10)

        # Payload Object
        self.payload_label = tk.Label(self.frame, text="Payload (Text):", bg="#ffffff", font=("Arial", 12))
        self.payload_label.grid(row=1, column=0, padx=10)

        self.payload_entry = tk.Entry(self.frame, width=40, font=("Arial", 12))
        self.payload_entry.grid(row=1, column=1)

        self.payload_browse_button = tk.Button(self.frame, text="Browse", command=self.load_payload_file, bg="#4CAF50", fg="white", font=("Arial", 12))
        self.payload_browse_button.grid(row=1, column=2, padx=10)

        # Frame Number for Video
        self.frame_label = tk.Label(self.frame, text="Frame Number (for Video):", bg="#ffffff", font=("Arial", 12))
        self.frame_label.grid(row=2, column=0, padx=10)

        self.frame_entry = tk.Entry(self.frame, width=10, font=("Arial", 12))
        self.frame_entry.grid(row=2, column=1)

        # LSB Selection
        self.lsb_label = tk.Label(self.frame, text="Number of LSBs:", bg="#ffffff", font=("Arial", 12))
        self.lsb_label.grid(row=3, column=0, padx=10)

        self.lsb_var = tk.IntVar(value=1)
        self.lsb_spinbox = tk.Spinbox(self.frame, from_=1, to=8, textvariable=self.lsb_var, font=("Arial", 12))
        self.lsb_spinbox.grid(row=3, column=1)

        # Action Buttons
        self.encode_button = tk.Button(self.frame, text="Encode", command=self.encode, bg="#2196F3", fg="white", font=("Arial", 12))
        self.encode_button.grid(row=4, column=0, pady=20)

        self.decode_button = tk.Button(self.frame, text="Decode", command=self.decode, bg="#2196F3", fg="white", font=("Arial", 12))
        self.decode_button.grid(row=4, column=1, pady=20)

        # Frame for displaying original cover object (initially hidden)
        self.original_frame = tk.Frame(self, bg="#e0e0e0", padx=10, pady=10)
        self.original_frame.pack(pady=20)
        self.original_frame.pack_forget()

        self.cover_image_label = tk.Label(self.original_frame, text="Original Cover Object:", bg="#e0e0e0", font=("Arial", 12))
        self.cover_image_label.pack(pady=5)

        self.cover_display = tk.Label(self.original_frame, bg="#ffffff", borderwidth=2, relief="solid")
        self.cover_display.pack(padx=10, pady=10)

        # Comparison Frame (initially hidden)
        self.comparison_frame = tk.Frame(self, bg="#e0e0e0", padx=10, pady=10)
        self.comparison_frame.pack(pady=20)
        self.comparison_frame.pack_forget()

        # Stego Image Display
        self.stego_image_label = tk.Label(self.comparison_frame, text="Encoded Stego Object:", bg="#e0e0e0", font=("Arial", 12))
        self.stego_image_label.grid(row=0, column=0, padx=10)

        self.stego_display = tk.Label(self.comparison_frame, bg="#ffffff", borderwidth=2, relief="solid")
        self.stego_display.grid(row=1, column=0, padx=10)

        # Variables for storing paths
        self.cover_file_path = None
        self.payload_file_path = None
        self.stego_file_path = None

        # Bind drag-and-drop events
        self.cover_entry.drop_target_register(DND_FILES)
        self.cover_entry.dnd_bind('<<Drop>>', self.on_drop_cover)

        self.payload_entry.drop_target_register(DND_FILES)
        self.payload_entry.dnd_bind('<<Drop>>', self.on_drop_payload)

    def clean_file_path(self, path):
        return path.strip('{}')

    def on_drop_cover(self, event):
        self.cover_file_path = self.clean_file_path(event.data)
        self.cover_entry.delete(0, tk.END)
        self.cover_entry.insert(0, self.cover_file_path)
        self.display_cover()

    def on_drop_payload(self, event):
        self.payload_file_path = self.clean_file_path(event.data)
        self.payload_entry.delete(0, tk.END)
        self.payload_entry.insert(0, self.payload_file_path)

    def load_cover_file(self):
        global cover_bits
        self.cover_file_path = filedialog.askopenfilename(
            title="Select Cover Object (Image/Audio/Video)",
            filetypes=[("All Supported Files", "*.txt;*.png;*.bmp;*.wav;*.mp4;*.avi")]
        )
        if self.cover_file_path:
            self.cover_entry.delete(0, tk.END)
            self.cover_entry.insert(0, self.cover_file_path)
            self.display_cover()
            if self.cover_file_path.endswith('.png') or self.cover_file_path.endswith('.bmp'):
                img = Image.open(self.cover_file_path)
                cover_bits = img.size[0] * img.size[1] * 3 * self.lsb_var.get()  # RGB pixels, 3 channels
            elif self.cover_file_path.endswith('.wav'):
                # WAV files use 16-bit samples, so we estimate total bits as the number of samples * 16
                with open(self.cover_file_path, 'rb') as f:
                    cover_bits = len(f.read()) * 8
            elif self.cover_file_path.endswith('.txt'):
                with open(self.cover_file_path, 'r') as f:
                    cover_bits = len(f.read()) * 8
            elif self.cover_file_path.endswith('.mp4') or self.cover_file_path.endswith('.avi'):
                # For video, we will need to estimate the available bits in the selected frame.
                cover_bits = 0  # Placeholder, needs to be calculated based on video frame selection
            print(f"Coverbit: '{cover_bits}'")

    def display_cover(self):
        if self.cover_file_path.endswith(('.png', '.bmp')):
            img = Image.open(self.cover_file_path)
            img.thumbnail((300, 300))
            img_tk = ImageTk.PhotoImage(img)
            self.cover_display.config(image=img_tk)
            self.cover_display.image = img_tk
            self.original_frame.pack()
        elif self.cover_file_path.endswith('.wav'):
            messagebox.showinfo("Cover Object", "Audio file selected as cover object.")
            self.original_frame.pack_forget()
        elif self.cover_file_path.endswith('.mp4') or self.cover_file_path.endswith('.avi'):
            messagebox.showinfo("Cover Object", "Video file selected as cover object.")
            self.original_frame.pack_forget()
        elif self.cover_file_path.endswith('.txt'):
            messagebox.showinfo("Cover Object", "Text file selected as cover object.")
            self.original_frame.pack_forget()
        else:
            messagebox.showerror("Error", "Unsupported file type selected.")

    def load_payload_file(self):
        global payload_bits
        self.payload_file_path = filedialog.askopenfilename(
            title="Select Payload (Text File)",
            filetypes=[("Text files", "*.txt")]
        )
        if self.payload_file_path:
            self.payload_entry.delete(0, tk.END)
            self.payload_entry.insert(0, self.payload_file_path)
            with open(self.payload_file_path, 'r') as f:
                payload_bits = len(f.read()) * 8  # Each character in text is 1 byte, or 8 bits
            print(f"Payload bit: '{payload_bits}'")

    def check_capacity(self):
        if payload_bits > cover_bits:
            messagebox.showerror("Error", "Payload file is too large for the selected cover object.")
            return False
        return True

    def encode(self):
        if self.cover_file_path and self.payload_file_path:
            lsb_bits = self.lsb_var.get()
            frame_number = self.frame_entry.get()

            if not self.check_capacity():
                return

            if self.cover_file_path.endswith('.png') or self.cover_file_path.endswith('.bmp'):
                output_path = filedialog.asksaveasfilename(defaultextension=".png", filetypes=[("PNG files", "*.png")])
                if output_path:
                    encode_image(self.cover_file_path, self.payload_file_path, output_path, lsb_bits)
                    messagebox.showinfo("Success", f"Encoded stego image saved as {output_path}")
                    self.display_stego_image(output_path)
                    self.comparison_frame.pack()

            elif self.cover_file_path.endswith('.wav'):
                output_path = filedialog.asksaveasfilename(defaultextension=".wav", filetypes=[("WAV files", "*.wav")])
                if output_path:
                    encode_audio_lsb(self.cover_file_path, self.payload_file_path, output_path)
                    messagebox.showinfo("Success", f"Encoded stego audio saved as {output_path}")

            elif self.cover_file_path.endswith('.mp4'):
                if frame_number.isdigit():
                    output_path = filedialog.asksaveasfilename(defaultextension=".avi", filetypes=[("AVI files", "*.avi")])
                    if output_path:
                        encode_video(self.cover_file_path, self.payload_file_path, int(frame_number),lsb_bits, output_path, )
                        messagebox.showinfo("Success", f"Encoded stego video saved as {output_path}")
                else:
                    messagebox.showerror("Error", "Please provide a valid frame number for video encoding.")

            elif self.cover_file_path.endswith('.txt'):
                # Encode in a text file using whitespace encoding
                with open(self.cover_file_path, 'r') as cover_file:
                    cover_data = cover_file.read()
                with open(self.payload_file_path, 'r') as payload_file:
                    payload_data = payload_file.read()
                # Convert payload data to binary string (7 bits for ASCII)
                payload_bits = ''.join(format(ord(char), '07b') for char in payload_data)
                # Create encoded text using whitespace encoding
                encoded_text = ''
                payload_index = 0
                for char in cover_data:
                    encoded_text += char  # Append original character
                    # Add whitespace based on payload bits
                    if payload_index < len(payload_bits):
                        if payload_bits[payload_index] == '1':
                            encoded_text += '\t'  # Use tab for '1'
                        else:
                            encoded_text += ' '  # Use space for '0'
                        payload_index += 1
                # If there are remaining bits to encode, consider appending space or tabs
                while payload_index < len(payload_bits):
                    if payload_bits[payload_index] == '1':
                        encoded_text += '\t'
                    else:
                        encoded_text += ' '
                    payload_index += 1
                output_path = filedialog.asksaveasfilename(defaultextension=".txt",
                                                           filetypes=[("Text files", "*.txt")])
                if output_path:
                    with open(output_path, 'w') as encoded_file:
                        encoded_file.write(encoded_text)
                    messagebox.showinfo("Success", f"Encoded text file saved as {output_path}")
                print(
                    f"Encoded text (truncated): {encoded_text[:100]}...")  # Print first 100 characters for debugging
        else:
            messagebox.showerror("Error", "Please select both a cover object and a payload.")
    def decode(self):
        if self.cover_file_path:
            lsb_bits = self.lsb_var.get()
            frame_number = self.frame_entry.get()

            if self.cover_file_path.endswith('.png') or self.cover_file_path.endswith('.bmp'):
                decoded_message = decode_image(self.cover_file_path, lsb_bits)
                messagebox.showinfo("Decoded Message", decoded_message)

            elif self.cover_file_path.endswith('.wav'):
                decoded_message = decode_audio_lsb(self.cover_file_path)
                messagebox.showinfo("Decoded Message", decoded_message)

            elif self.cover_file_path.endswith('.avi'):
                if frame_number.isdigit():
                    decoded_message = decode_video(self.cover_file_path, int(frame_number), lsb_bits)
                    messagebox.showinfo("Decoded Message", decoded_message)
                else:
                    messagebox.showerror("Error", "Please provide a valid frame number for video decoding.")
            elif self.cover_file_path.endswith('.txt'):
                with open(self.cover_file_path, 'r') as encoded_file:
                    encoded_data = encoded_file.read()
                # Extract bits based on whitespace
                extracted_bits = ''
                for char in encoded_data:
                    if char == '\t':
                        extracted_bits += '1'  # Tab represents '1'
                    elif char == ' ':
                        extracted_bits += '0'  # Space represents '0'
                # Split extracted bits into bytes (7 bits each for ASCII)
                decoded_message = ''
                for i in range(0, len(extracted_bits), 7):
                    byte = extracted_bits[i:i + 7]
                    if len(byte) == 7:  # Only consider complete bytes
                        decoded_message += chr(int(byte, 2))
                # Check for valid extraction
                if decoded_message:
                    messagebox.showinfo("Decoded Message", decoded_message)
                else:
                    messagebox.showwarning("Warning", "No hidden message found in the selected file.")
        else:
            messagebox.showerror("Error", "Please select a cover object.")

    def display_stego_image(self, path):
        img = Image.open(path)
        img.thumbnail((300, 300))
        img_tk = ImageTk.PhotoImage(img)
        self.stego_display.config(image=img_tk)
        self.stego_display.image = img_tk


if __name__ == "__main__":
    app = SteganographyApp()
    app.mainloop()
