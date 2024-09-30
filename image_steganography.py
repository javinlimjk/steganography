from PIL import Image
import numpy as np
import os

def text_to_binary(text):
    # Convert the text into a binary string
    return ''.join(format(ord(char), '08b') for char in text)

def convert_to_png(image_path):
    # Load the image using PIL
    image = Image.open(image_path)
    
    # Check if the image is already a PNG
    if image_path.lower().endswith('.png'):
        return image_path  # No conversion needed if it's already PNG
    
    # Convert to PNG
    base_name = os.path.splitext(image_path)[0]  # Get the file name without extension
    png_image_path = base_name + '.png'  # Change the extension to .png
    image.save(png_image_path, 'PNG')  # Save the image as PNG
    print(f"Converted {image_path} to {png_image_path}")
    
    return png_image_path

def save_encoded_image(image_array, output_image):
    output_dir = "encoded"
    
    # Ensure the output directory exists
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Combine directory and file name to get the full path
    output_path = os.path.join(output_dir, output_image)

    # Convert the NumPy array back into a PIL image object
    encoded_image = Image.fromarray(image_array)

    # Save the encoded image as a PNG (lossless format)
    encoded_image.save(output_path, format='PNG')

    return output_path

def encode_image(image_path, text_file, output_image, lsb_count=1):
    if lsb_count < 1 or lsb_count > 8:
        raise ValueError("LSB count must be between 1 and 8.")
    
    # Convert the input image to PNG if it's not already in PNG format
    png_image_path = convert_to_png(image_path)

    image = Image.open(png_image_path)
    image_array = np.array(image)

    # Read the text to be encoded from the file
    with open(text_file, 'r') as file:
        text = file.read()
    
    # Append the end marker to the text
    text += "###END###"
    binary_text = text_to_binary(text)
    binary_index = 0
    binary_len = len(binary_text)
    
    # Calculate the number of bits we can store per pixel
    bits_per_pixel = 3 * lsb_count  # 3 channels, each using lsb_count bits

    for row in image_array:
        for pixel in row:
            # Modify R, G, B channels of the pixel
            for channel in range(3):  # 3 channels: Red, Green, Blue
                if binary_index < binary_len:
                    # Extract the next bits to encode (depending on lsb_count)
                    bits_to_encode = binary_text[binary_index:binary_index+lsb_count]
                    if len(bits_to_encode) < lsb_count:
                        bits_to_encode = bits_to_encode.ljust(lsb_count, '0')
                    
                    # Clear the least significant bits in the pixel's channel
                    pixel[channel] &= ~( (1 << lsb_count) - 1 )
                    
                    # Encode the bits in the pixel's channel
                    pixel[channel] |= int(bits_to_encode, 2)
                    
                    # Move to the next bits in the binary text
                    binary_index += lsb_count

            if binary_index >= binary_len:
                break  # Stop if the whole message has been encoded

    if binary_index < binary_len:
        raise ValueError("The message is too long to be encoded in the image.")

    # Save the encoded image
    original_image_size = os.path.getsize(png_image_path)  # Get original image size
    encoded_image_path = save_encoded_image(image_array, output_image)  # Save encoded image as PNG
    encoded_image_size = os.path.getsize(encoded_image_path)  # Get encoded image size

    # Check if the encoded image is smaller than the original
    if encoded_image_size < original_image_size:
        print(f"Warning: The encoded image size ({encoded_image_size} bytes) is smaller than the original image size ({original_image_size} bytes).")
        print("This could indicate unintended compression or data loss.")

    print(f"Encoded image saved to: {encoded_image_path} ({encoded_image_size} bytes)")
    return encoded_image_path

def binary_to_text(binary_data):
    # Convert binary string to text, 8 bits at a time
    text = ''
    for i in range(0, len(binary_data), 8):
        byte = binary_data[i:i+8]
        text += chr(int(byte, 2))
    return text

def decode_image(image_path, lsb_count=1):
    if lsb_count < 1 or lsb_count > 8:
        raise ValueError("LSB count must be between 1 and 8.")
    
    # Convert the input image to PNG if it's not already in PNG format
    png_image_path = convert_to_png(image_path)

    image = Image.open(png_image_path)
    image_array = np.array(image)

    binary_data = ""
    end_marker = "###END###"
    binary_end_marker = text_to_binary(end_marker)

    for row in image_array:
        for pixel in row:
            for channel in range(3):  # R, G, B channels
                # Extract the least significant bits from the channel value
                bits_from_channel = format(pixel[channel], '08b')[-lsb_count:]
                
                # Append the bits to the binary data string
                binary_data += bits_from_channel
                
                # Check if we've reached the end of the marker
                if len(binary_data) >= len(binary_end_marker):
                    decoded_text = binary_to_text(binary_data)
                    if end_marker in decoded_text:
                        return decoded_text[:decoded_text.index(end_marker)]

    # If no end marker is found, return the decoded text up to the marker
    return binary_to_text(binary_data)
'''
# TESTING CODE
# Encode the text file into the image
encoded_image = encode_image("C:/Users/javin/Documents/SIT/sadas.png", "C:/Users/javin/Documents/SIT/test2.txt", "encoded_cat.png", lsb_count=8)
print(f"Encoded image saved at: {encoded_image}")

# Decode the text from the encoded image
decoded_text = decode_image(encoded_image, lsb_count=8)
print(f"Decoded text: {decoded_text}")
'''