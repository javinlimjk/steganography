import wave
from PIL import Image

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

        # Calculate the maximum capacity for payload
        width, height = img.size
        max_capacity_bits = width * height * 3 * num_lsb  # 3 channels (R, G, B)

        # Check if payload size exceeds the cover image's capacity
        if len(binary_payload) > max_capacity_bits:
            raise ValueError("Payload too large for the selected image cover object.")

        # Ensure we are using the appropriate number of LSBs
        payload_idx = 0

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
    
    except ValueError as ve:
        print(f"Error: {ve}")
    
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

def encode_audio_lsb(cover_audio_path, payload_path, output_audio_path):
    try:
        # Open cover audio file
        with wave.open(cover_audio_path, 'rb') as audio:
            frames = bytearray(list(audio.readframes(audio.getnframes())))

        # Load the payload text and convert to binary
        with open(payload_path, 'r') as file:
            payload = file.read()

        binary_payload = ''.join([format(ord(char), '08b') for char in payload])
        # Append a unique terminator (e.g., 16-bit terminator)
        binary_payload += '1111111111111110'

        # Calculate maximum capacity for the payload
        max_capacity_bits = len(frames)  # 1 LSB per audio sample

        # Check if the payload is too large for the audio cover file
        if len(binary_payload) > max_capacity_bits:
            raise ValueError("Payload too large for the selected audio cover object.")

        # Modify LSBs of the audio samples
        payload_idx = 0
        for i in range(len(frames)):
            if payload_idx < len(binary_payload):
                # Modify only the LSB
                frames[i] = (frames[i] & 254) | int(binary_payload[payload_idx])  # Replace the LSB
                payload_idx += 1

        # Save the modified audio file
        with wave.open(output_audio_path, 'wb') as output_audio:
            output_audio.setparams(audio.getparams())  # Use the same parameters
            output_audio.writeframes(frames)
        
        print(f"Stego audio saved as {output_audio_path}")

    except ValueError as ve:
        print(f"Error: {ve}")
    
    except Exception as e:
        print(f"Error during audio encoding: {e}")


def decode_audio_lsb(stego_audio_path):
    try:
        # Open stego audio file
        with wave.open(stego_audio_path, 'rb') as audio:
            frames = bytearray(list(audio.readframes(audio.getnframes())))

        binary_payload = ""
        for i in range(len(frames)):
            # Extract the LSB of each byte
            binary_payload += str(frames[i] & 1)

        # Group binary into 8-bit chunks (bytes)
        byte_chunks = [binary_payload[i:i + 8] for i in range(0, len(binary_payload), 8)]

        # Convert binary to string and look for the terminator
        decoded_message = ""
        for byte in byte_chunks:
            if byte == '11111110':  # Stop at the terminator
                break
            decoded_message += chr(int(byte, 2))

        print(f"Decoded message: {decoded_message}")
        return decoded_message

    except Exception as e:
        print(f"Error during audio decoding: {e}")
        return ""