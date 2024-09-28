import tkinter as tk
from tkinterdnd2 import TkinterDnD, DND_FILES
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk
from pydub import AudioSegment
from array import array

def encode_image_lsb(cover_image_path, payload_path, output_path, num_lsb):
    try:
        # Load cover image and convert to RGB mode if necessary
        img = Image.open(cover_image_path)
        if img.mode != 'RGB':
            img = img.convert('RGB')
        pixels = img.load()

        # Load payload (text)
        with open(payload_path, 'r') as file:
            payload = file.read()

        # Convert payload into binary
        binary_payload = ''.join([format(ord(char), '08b') for char in payload])
        # Append a unique terminator (to indicate the end of the payload)
        binary_payload += '1111111111111110'  # 16-bit terminator

        # Ensure we are using the appropriate number of LSBs
        payload_idx = 0
        width, height = img.size

        for y in range(height):
            for x in range(width):
                pixel = list(pixels[x, y])
                for i in range(3):  # Modify R, G, B channels
                    if payload_idx < len(binary_payload):
                        # Modify LSB(s) based on num_lsb
                        pixel[i] = (pixel[i] & ~(2**num_lsb - 1)) | int(binary_payload[payload_idx:payload_idx + num_lsb], 2)
                        payload_idx += num_lsb
                pixels[x, y] = tuple(pixel)

                # Stop if we've encoded the entire payload
                if payload_idx >= len(binary_payload):
                    break
            if payload_idx >= len(binary_payload):
                break

        # Save the modified image (ensure valid output path)
        img.save(output_path)
        print(f"Stego image saved as {output_path}")
    
    except Exception as e:
        print(f"Error during encoding: {e}")


def decode_image_lsb(stego_image_path, num_lsb):
    try:
        # Load stego image
        img = Image.open(stego_image_path)
        pixels = img.load()

        binary_payload = ""
        width, height = img.size

        # Extract LSBs from the image pixels
        for y in range(height):
            for x in range(width):
                pixel = list(pixels[x, y])
                for i in range(3):  # Read R, G, B channels
                    # Extract num_lsb bits from each channel
                    binary_payload += format(pixel[i] & (2**num_lsb - 1), f'0{num_lsb}b')

        # Group binary into 8-bit chunks (bytes)
        byte_chunks = [binary_payload[i:i+8] for i in range(0, len(binary_payload), 8)]

        # Convert binary to string and look for the terminator
        decoded_message = ""
        for byte in byte_chunks:
            # If we encounter the terminator, stop decoding
            if byte == '11111110':  # 8 bits of the terminator
                break
            decoded_message += chr(int(byte, 2))

        print(f"Decoded message: {decoded_message}")
        return decoded_message
    
    except Exception as e:
        print(f"Error during decoding: {e}")
        return ""

def encode_audio_lsb(audio_path, payload_path, output_path, num_lsb):
    try:
        # Load the audio file (use WAV for lossless encoding)
        audio = AudioSegment.from_wav(audio_path)
        samples = audio.get_array_of_samples()

        # Load payload (text)
        with open(payload_path, 'r') as file:
            payload = file.read()

        # Convert payload into binary
        binary_payload = ''.join([format(ord(char), '08b') for char in payload])
        binary_payload += '1111111111111110'  # 16-bit terminator

        # Ensure enough samples are available
        total_bits_needed = len(binary_payload)
        total_lsb_capacity = len(samples) * num_lsb
        if total_bits_needed > total_lsb_capacity:
            raise ValueError("The audio file is not large enough to hold the payload.")

        # Encode the message into the audio samples
        samples = list(samples)  # Convert samples to a list for mutation
        payload_idx = 0

        for i in range(len(samples)):
            for bit_pos in range(num_lsb):
                if payload_idx < len(binary_payload):
                    # Modify the LSB(s) of the sample
                    samples[i] = (samples[i] & ~(1 << bit_pos)) | (int(binary_payload[payload_idx]) << bit_pos)
                    payload_idx += 1
                else:
                    break
            if payload_idx >= len(binary_payload):
                break

        # Convert the modified samples back into the appropriate array type
        modified_samples = array(audio.array_type, samples)

        # Create a new audio segment with the modified samples
        modified_audio = audio._spawn(modified_samples.tobytes())
        modified_audio.export(output_path, format="wav")
        print(f"Stego audio saved as {output_path}")

    except Exception as e:
        print(f"Error during encoding: {e}")


def decode_audio_lsb(audio_path, num_lsb):
    try:
        # Load the audio file (use WAV for lossless decoding)
        audio = AudioSegment.from_wav(audio_path)
        samples = audio.get_array_of_samples()

        binary_payload = ""
        terminator = '1111111111111110'  # 16-bit terminator to signify the end of the payload
        terminator_found = False

        # Extract the LSBs from the audio samples
        for sample in samples:
            for bit_pos in range(num_lsb):
                binary_payload += str((sample >> bit_pos) & 1)

            # Check if the terminator is found in the binary payload
            if terminator in binary_payload:
                binary_payload = binary_payload[:binary_payload.index(terminator)]  # Cut off at the terminator
                terminator_found = True
                break

        if not terminator_found:
            print("Warning: Terminator not found, payload may be incomplete.")
        
        # Group binary into 8-bit chunks (bytes)
        byte_chunks = [binary_payload[i:i+8] for i in range(0, len(binary_payload), 8)]

        # Convert binary to string (ASCII text)
        decoded_message = "".join([chr(int(byte, 2)) for byte in byte_chunks if len(byte) == 8])

        print(f"Decoded message: {decoded_message}")
        return decoded_message

    except Exception as e:
        print(f"Error during decoding: {e}")
        return ""


class SteganographyApp(TkinterDnD.Tk):
    def __init__(self):
        super().__init__()
        self.title("LSB Steganography with Drag and Drop")

        # Frame for the cover object (image or wav)
        self.cover_frame = tk.Frame(self)
        self.cover_frame.pack(pady=10)

        self.cover_label = tk.Label(self.cover_frame, text="Select Cover Object (Image or wav):")
        self.cover_label.grid(row=0, column=0, padx=10)

        self.cover_button = tk.Button(self.cover_frame, text="Browse", command=self.load_cover_file)
        self.cover_button.grid(row=0, column=1)

        # Placeholder for cover image
        self.cover_image_label = tk.Label(self.cover_frame, text="Drag & Drop Cover Object Here", width=40, height=5, bg="lightgray")
        self.cover_image_label.grid(row=1, columnspan=2, pady=10)
        
        # Reset button to clear cover object
        self.reset_cover_object_button = tk.Button(self.cover_frame, text="Reset", command=self.reset_cover_image)
        self.reset_cover_object_button.grid(row=2, columnspan=2, pady=10)

        # Frame for the payload (text)
        self.payload_frame = tk.Frame(self)
        self.payload_frame.pack(pady=10)

        self.payload_label = tk.Label(self.payload_frame, text="Select Payload (Text):")
        self.payload_label.grid(row=0, column=0, padx=10)

        self.payload_button = tk.Button(self.payload_frame, text="Browse", command=self.load_payload_file)
        self.payload_button.grid(row=0, column=1)

        # Placeholder for payload text
        self.payload_text_label = tk.Label(self.payload_frame, text="Drag & Drop Payload Here", width=40, height=5, bg="lightgray")
        self.payload_text_label.grid(row=1, columnspan=2, pady=10)
        
        # Reset button to clear payload text
        self.reset_payload_button = tk.Button(self.payload_frame, text="Reset", command=self.reset_payload_text)
        self.reset_payload_button.grid(row=2, columnspan=2, pady=10)

        # Frame for LSB selection and Encode/Decode buttons
        self.controls_frame = tk.Frame(self)
        self.controls_frame.pack(pady=20)

        self.lsb_label = tk.Label(self.controls_frame, text="Select number of LSBs:")
        self.lsb_label.grid(row=0, column=0, padx=10)

        self.lsb_var = tk.IntVar(value=1)
        self.lsb_spinbox = tk.Spinbox(self.controls_frame, from_=1, to=8, textvariable=self.lsb_var)
        self.lsb_spinbox.grid(row=0, column=1)

        self.encode_button = tk.Button(self.controls_frame, text="Encode", command=self.encode)
        self.encode_button.grid(row=1, column=0, pady=20)

        self.decode_button = tk.Button(self.controls_frame, text="Decode", command=self.decode)
        self.decode_button.grid(row=1, column=1, pady=20)

        # Variables for storing paths
        self.cover_file_path = None
        self.payload_file_path = None
        
        # Enable drag and drop for the cover object
        self.cover_image_label.drop_target_register(DND_FILES)
        self.cover_image_label.dnd_bind('<<Drop>>', self.on_drop_cover)
        
        self.payload_text_label.drop_target_register(DND_FILES)
        self.payload_text_label.dnd_bind('<<Drop>>', self.on_drop_payload)
   
    def on_drop_cover(self, event):
        # Handle file drop for cover object (image or wav)
        self.cover_file_path = event.data
        if self.cover_file_path.endswith(('.png', '.bmp')):
            img = Image.open(self.cover_file_path)
            img = img.resize((600, 600))
            img_tk = ImageTk.PhotoImage(img)
            self.cover_image_label.config(image=img_tk, text="")
            self.cover_image_label.image = img_tk  # Keep a reference
        elif self.cover_file_path.endswith('.wav'):
            self.cover_image_label.config(text=f"wav File selected: {self.cover_file_path}", image="")  # Clear image
            messagebox.showinfo("wav File", f"wav File selected: {self.cover_file_path}")
        else:
            messagebox.showwarning("Invalid File", "Please drop a valid image or wav file.")
    

    def on_drop_payload(self, event):
        # Handle file drop for payload (text)
        self.payload_file_path = event.data
        if self.payload_file_path.endswith('.txt'):
            self.payload_text_label.config(text=f"Text file selected: {self.payload_file_path}")
            messagebox.showinfo("Text File", f"Text file selected: {self.payload_file_path}")
        else:
            messagebox.showwarning("Invalid File", "Please drop a valid text file.")

    def load_cover_file(self):
        self.cover_file_path = filedialog.askopenfilename(title="Select Cover Image or wav", filetypes=[("Image files", "*.png;*.bmp"), ("wav files", "*.wav")])
        self.display_cover_file(self.cover_file_path)
        
        if self.cover_file_path.endswith(('.png', '.bmp')):
            try:
                img = Image.open(self.cover_file_path)
                img = img.resize((600, 600))  # Resize for display
                img_tk = ImageTk.PhotoImage(img)
                self.cover_image_label.config(image=img_tk, text="")
                self.cover_image_label.image = img_tk  # Keep a reference to avoid garbage collection
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load image: {e}")
    
        # Check if it's an wav
        elif self.cover_file_path.endswith('.wav'):
            self.cover_image_label.config(text=f"wav File selected: {self.cover_file_path}", image="")  # Clear image
            messagebox.showinfo("wav File", f"wav File selected: {self.cover_file_path}")
    
        # Invalid file type
        else:
            messagebox.showwarning("Invalid File", "Please select a valid image or wav file.")

    def load_payload_file(self):
        self.payload_file_path = filedialog.askopenfilename(title="Select Text File", filetypes=[("Text files", "*.txt")])
        if self.payload_file_path:
            messagebox.showinfo("Payload", f"Payload selected: {self.payload_file_path}")

    def encode(self):
        if self.cover_file_path and self.payload_file_path:
            lsb_bits = self.lsb_var.get()

            # Check if the cover file is an image or wav and provide appropriate file dialog options
            if self.cover_file_path.endswith(('.png', '.bmp')):
                output_path = filedialog.asksaveasfilename(defaultextension=".png", filetypes=[("PNG files", "*.png")])
                if output_path:
                    encode_image_lsb(self.cover_file_path, self.payload_file_path, output_path, lsb_bits)
                    messagebox.showinfo("Success", f"Encoded stego image saved as {output_path}")
                else:
                    messagebox.showwarning("Error", "Failed to save the image.")

            elif self.cover_file_path.endswith('.wav'):
                output_path = filedialog.asksaveasfilename(defaultextension=".wav", filetypes=[("wav files", "*.wav")])
                if output_path:
                    encode_audio_lsb(self.cover_file_path, self.payload_file_path, output_path, lsb_bits)
                    messagebox.showinfo("Success", f"Encoded stego audio saved as {output_path}")
                else:
                    messagebox.showwarning("Error", "Failed to save the audio.")
            else:
                messagebox.showwarning("Error", "Invalid cover object format. Please select a valid image or wav file.")
        else:
            messagebox.showwarning("Error", "Please select both cover object and payload.")
        
    def decode(self):
        if self.cover_file_path:
            if self.cover_file_path.endswith(('.png', '.bmp')):
                decoded_message = decode_image_lsb(self.cover_file_path, self.lsb_var.get())
                messagebox.showinfo("Decoded Message", decoded_message)
            elif self.cover_file_path.endswith('.wav'):
                decoded_message = decode_audio_lsb(self.cover_file_path, self.lsb_var.get())
                messagebox.showinfo("Decoded Message", decoded_message)
        else:
            messagebox.showwarning("Error", "Please select a cover object first")
            
    def reset_cover_image(self):
        # Reset the cover image label to allow new drag-and-drop or browsing
        self.cover_image_label.config(image="", text="Drag & Drop Cover Object Here")
        self.cover_file_path = None  # Clear the cover file path
        
    def reset_payload_text(self):
        # Reset the payload text label to allow new drag-and-drop or browsing
        self.payload_text_label.config(text="Drag & Drop Payload Here")
        self.payload_file_path = None  # Clear the payload file path

if __name__ == "__main__":
    app = SteganographyApp()
    app.mainloop()

