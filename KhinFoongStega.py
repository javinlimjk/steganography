import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk

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


class SteganographyApp:
    def __init__(self, root):
        self.root = root
        self.root.title("LSB Steganography")

        # Frame for file selection
        self.frame = tk.Frame(root)
        self.frame.pack(pady=20)

        self.cover_label = tk.Label(self.frame, text="Select Cover Object:")
        self.cover_label.grid(row=0, column=0, padx=10)

        self.cover_button = tk.Button(self.frame, text="Browse", command=self.load_cover_file)
        self.cover_button.grid(row=0, column=1)

        self.payload_label = tk.Label(self.frame, text="Select Payload (Text):")
        self.payload_label.grid(row=1, column=0, padx=10)

        self.payload_button = tk.Button(self.frame, text="Browse", command=self.load_payload_file)
        self.payload_button.grid(row=1, column=1)

        self.lsb_label = tk.Label(self.frame, text="Select number of LSBs:")
        self.lsb_label.grid(row=2, column=0, padx=10)

        self.lsb_var = tk.IntVar(value=1)
        self.lsb_spinbox = tk.Spinbox(self.frame, from_=1, to=8, textvariable=self.lsb_var)
        self.lsb_spinbox.grid(row=2, column=1)

        self.encode_button = tk.Button(self.frame, text="Encode", command=self.encode)
        self.encode_button.grid(row=3, column=0, pady=20)

        self.decode_button = tk.Button(self.frame, text="Decode", command=self.decode)
        self.decode_button.grid(row=3, column=1, pady=20)

        # Placeholder for cover image
        self.image_label = tk.Label(root)
        self.image_label.pack()

        # Variables for storing paths
        self.cover_file_path = None
        self.payload_file_path = None

    def load_cover_file(self):
        self.cover_file_path = filedialog.askopenfilename(title="Select Cover Image", filetypes=[("Image files", "*.png;*.bmp")])
        if self.cover_file_path:
            img = Image.open(self.cover_file_path)
            img.thumbnail((300, 300))
            img_tk = ImageTk.PhotoImage(img)
            self.image_label.config(image=img_tk)
            self.image_label.image = img_tk  # Keep a reference

    def load_payload_file(self):
        self.payload_file_path = filedialog.askopenfilename(title="Select Text File", filetypes=[("Text files", "*.txt")])
        if self.payload_file_path:
            messagebox.showinfo("Payload", f"Payload selected: {self.payload_file_path}")

    def encode(self):
        if self.cover_file_path and self.payload_file_path:
            lsb_bits = self.lsb_var.get()
            output_path = filedialog.asksaveasfilename(defaultextension=".png", filetypes=[("PNG files", "*.png")])
        if output_path:
            encode_image_lsb(self.cover_file_path, self.payload_file_path, output_path, lsb_bits)
            messagebox.showinfo("Success", f"Encoded stego image saved as {output_path}")
        else:
            messagebox.showwarning("Error", "Please select both cover object and payload")

    def decode(self):
        if self.cover_file_path:
            decoded_message = decode_image_lsb(self.cover_file_path, self.lsb_var.get())
            messagebox.showinfo("Decoded Message", decoded_message)
        else:
            messagebox.showwarning("Error", "Please select a cover object first")

if __name__ == "__main__":
    root = tk.Tk()
    app = SteganographyApp(root)
    root.mainloop()