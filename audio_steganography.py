import wave
from PIL import Image

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