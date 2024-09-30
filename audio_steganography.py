import wave
from PIL import Image

def encode_audio_lsb(cover_audio_path, payload_path, output_audio_path, lsb_count=1):
    try:
        # Validate the lsb_count value
        if lsb_count < 1 or lsb_count > 8:
            raise ValueError("LSB count must be between 1 and 8.")

        # Open cover audio file in binary read mode
        with wave.open(cover_audio_path, 'rb') as audio:
            params = audio.getparams()
            frames = bytearray(audio.readframes(audio.getnframes()))

        # Load the payload text and convert to binary
        with open(payload_path, 'r') as file:
            payload = file.read()

        binary_payload = ''.join([format(ord(char), '08b') for char in payload])
        # Append a unique terminator (e.g., 16-bit terminator)
        binary_payload += '1111111111111110'

        # Calculate maximum capacity for the payload
        max_capacity_bits = len(frames) * lsb_count  # lsb_count bits per audio sample

        # Check if the payload is too large for the audio cover file
        if len(binary_payload) > max_capacity_bits:
            raise ValueError("Payload too large for the selected audio cover object.")

        # Modify LSBs of the audio samples
        payload_idx = 0
        for i in range(len(frames)):
            if payload_idx < len(binary_payload):
                # Modify LSB(s)
                bits_to_modify = binary_payload[payload_idx:payload_idx + lsb_count]
                bits_to_modify = bits_to_modify.ljust(lsb_count, '0')
                # Clear the LSB(s) and set the new bits
                frames[i] = (frames[i] & (~((1 << lsb_count) - 1))) | int(bits_to_modify, 2)
                payload_idx += lsb_count

        # Save the modified audio file in binary write mode
        with wave.open(output_audio_path, 'wb') as output_audio:
            output_audio.setparams(params)  # Use the same parameters
            output_audio.writeframes(frames)

        print(f"Stego audio saved as {output_audio_path}")

    except ValueError as ve:
        print(f"Error: {ve}")

    except Exception as e:
        print(f"Error during audio encoding: {e}")

def decode_audio_lsb(stego_audio_path, lsb_count=1):
    try:
        # Validate the lsb_count value
        if lsb_count < 1 or lsb_count > 8:
            raise ValueError("LSB count must be between 1 and 8.")
        
        # Open stego audio file
        with wave.open(stego_audio_path, 'rb') as audio:
            frames = bytearray(list(audio.readframes(audio.getnframes())))

        binary_payload = ""
        for i in range(len(frames)):
            # Extract the LSB of each byte
            binary_payload += format(frames[i] & ((1 << lsb_count) - 1), f'0{lsb_count}b')

        # Group binary into 8-bit chunks (bytes)
        byte_chunks = [binary_payload[i:i + 8] for i in range(0, len(binary_payload), 8)]

        # Convert binary to string and look for the terminator
        terminator = '1111111111111110'
        decoded_message = ""
        for i in range(0, len(binary_payload), 8):
            byte = binary_payload[i:i+8]
            if len(binary_payload) >= i + 16 and binary_payload[i:i+16] == terminator:
                break
            decoded_message += chr(int(byte, 2))


        print(f"Decoded message: {decoded_message}")
        return decoded_message

    except Exception as e:
        print(f"Error during audio decoding: {e}")
        return ""