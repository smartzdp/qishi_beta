"""
Download test audio files from LibriSpeech dataset
"""
import os
import torch
import torchaudio
import shutil
import soundfile as sf

DEVICE = "cuda" if torch.cuda.is_available() else "cpu"


def download_test_audio(output_dir="test_audio", num_files=3):
    """
    Download test audio files from LibriSpeech
    
    Args:
        output_dir: Directory to save audio files
        num_files: Number of audio files to download
    """
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    print(f"Downloading {num_files} test audio files from LibriSpeech...")
    print(f"Device: {DEVICE}")
    print(f"Output directory: {output_dir}")
    print("-" * 50)
    
    # Load dataset
    try:
        # Create LibriSpeech dataset
        dataset = torchaudio.datasets.LIBRISPEECH(
            root=os.path.expanduser("~/.cache"),
            url="test-clean",
            download=True,
        )
        
        # Get the dataset path and walker items
        dataset_path = dataset._path
        walker_items = dataset._walker[:num_files]
        
        # Download and save audio files
        audio_files = []
        for idx, walker_item in enumerate(walker_items):
            try:
                # LibriSpeech structure: dataset_path/speaker_id/chapter_id/utterance_id.flac
                # walker_item format: speaker_id-chapter_id/utterance_id.flac
                parts = walker_item.split('/')
                if len(parts) == 2:
                    # Format: speaker_id-chapter_id/utterance_id.flac
                    dir_part = parts[0]
                    file_part = parts[1]
                    # Construct full path
                    original_audio_path = os.path.join(dataset_path, dir_part, file_part)
                else:
                    # Try direct path
                    original_audio_path = os.path.join(dataset_path, walker_item)
                    if not os.path.exists(original_audio_path):
                        # Try with .flac extension if not present
                        if not walker_item.endswith('.flac'):
                            original_audio_path = os.path.join(dataset_path, walker_item + '.flac')
                
                # Check if the file exists
                if not os.path.exists(original_audio_path):
                    # Try to find the file in the dataset directory
                    import glob
                    # Search for files matching the utterance ID
                    utterance_id = walker_item.split('/')[-1].replace('.flac', '')
                    search_pattern = os.path.join(dataset_path, '**', f"{utterance_id}.flac")
                    found_files = glob.glob(search_pattern, recursive=True)
                    if found_files:
                        original_audio_path = found_files[0]
                        print(f"  Found file at: {original_audio_path}")
                    else:
                        print(f"✗ File not found: {original_audio_path}")
                        print(f"  Searched for: {search_pattern}")
                        continue
                
                # Read audio using soundfile (supports FLAC directly)
                audio_data, sample_rate = sf.read(original_audio_path)
                
                # Get transcript from the transcript file
                # LibriSpeech stores transcripts in .trans.txt files in the same directory
                audio_dir = os.path.dirname(original_audio_path)
                audio_basename = os.path.basename(original_audio_path).replace('.flac', '')
                
                # Find the transcript file (format: speaker_id-chapter_id.trans.txt)
                transcript_files = [f for f in os.listdir(audio_dir) if f.endswith('.trans.txt')]
                text = "No transcript available"
                
                if transcript_files:
                    transcript_file = os.path.join(audio_dir, transcript_files[0])
                    # Read transcript file - format: utterance_id transcript
                    with open(transcript_file, 'r', encoding='utf-8') as f:
                        for line in f:
                            # Match the utterance ID (format: speaker_id-chapter_id-utterance_id)
                            if line.startswith(audio_basename):
                                text = line.split(' ', 1)[1].strip() if ' ' in line else line.strip()
                                break
                
                # Create output filename (save as WAV for better compatibility)
                output_filename = f"test_audio_{idx}.wav"
                output_path = os.path.join(output_dir, output_filename)
                
                # Save audio as WAV using soundfile
                sf.write(output_path, audio_data, sample_rate)
                
                # Also copy the original FLAC file
                output_path_flac = os.path.join(output_dir, f"test_audio_{idx}.flac")
                shutil.copy2(original_audio_path, output_path_flac)
                
                # Save transcript
                transcript_filename = f"test_audio_{idx}.txt"
                transcript_path = os.path.join(output_dir, transcript_filename)
                with open(transcript_path, 'w', encoding='utf-8') as f:
                    f.write(text)
                
                audio_files.append({
                    'audio_path': output_path,
                    'audio_path_flac': output_path_flac,
                    'transcript_path': transcript_path,
                    'text': text,
                    'sample_rate': sample_rate
                })
                
                print(f"✓ Downloaded: {output_filename}")
                print(f"  Transcript: {text[:60]}...")
                print(f"  Sample rate: {sample_rate} Hz")
                print(f"  File size: {os.path.getsize(output_path) / 1024:.1f} KB")
                print()
                    
            except Exception as e:
                print(f"✗ Error processing file {idx}: {e}")
                import traceback
                traceback.print_exc()
                continue
        
        if audio_files:
            print(f"✓ Successfully downloaded {len(audio_files)} audio files")
            print(f"  Location: {os.path.abspath(output_dir)}")
            return audio_files
        else:
            print("✗ No audio files were downloaded")
            return None
        
    except Exception as e:
        print(f"✗ Error downloading audio files: {e}")
        import traceback
        traceback.print_exc()
        print("\nNote: This requires torchaudio and may take some time to download.")
        print("You can also manually download audio files and place them in the test_audio directory.")
        return None


if __name__ == "__main__":
    # Download test audio files
    audio_files = download_test_audio(output_dir="test_audio", num_files=3)
    
    if audio_files:
        print("\n" + "=" * 50)
        print("Audio files ready for testing!")
        print("=" * 50)
        print("\nYou can now test transcription with these files:")
        for i, af in enumerate(audio_files, 1):
            print(f"{i}. {os.path.basename(af['audio_path'])}")
            print(f"   Expected text: {af['text'][:60]}...")

