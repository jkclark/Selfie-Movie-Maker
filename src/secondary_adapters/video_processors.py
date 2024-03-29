"""TODO"""
import os
import subprocess
from pathlib import Path
from tempfile import NamedTemporaryFile

from src.ports.video_processor import VideoProcessor


class FFmpegVP(VideoProcessor):
    """A video processor that uses FFmpeg.

    This link is a concise guide to the ffmpeg flags:
    https://gist.github.com/tayvano/6e2d456a9897f55025e25035478a3a50
    """

    FRAMERATE = 15  # Literally, the number of images to be shown per second

    @staticmethod
    def create_movie_from_images(images_path: Path, output_path: Path) -> None:
        """Create a movie from a folder of images.

        output_path should specify .mp4

        NOTE: In order to specify just a folder (and not a glob pattern),
              the ffmpeg command below already includes "*.jpeg". This means
              we'd have to change this command to use a different extension.

        TODO: Explain ffmpeg options used here
        """
        subprocess.run(
            [
                "ffmpeg",
                "-r",
                f"{FFmpegVP.FRAMERATE}",
                "-f",
                "image2",
                "-s",
                "600x800",
                "-pattern_type",
                "glob",
                "-i",
                f"{images_path}/*.jpeg",
                "-vcodec",
                "libx264",
                "-crf",
                "25",
                f"{output_path}",
            ],
            check=True,
        )

    @staticmethod
    def append_images_to_movie(
        images_path: Path,
        movie_path: Path,
        output_path: Path,
    ) -> None:
        """Add any number of images to the end of a movie.

        The original idea was to use a command like the one found here:
        https://video.stackexchange.com/a/17229, but it turns out that there
        were issues with the video's duration using this method. This method now
        instead uses the concat demuxer to concatenate two separate movies
        together. The first movie is the original movie, and the second movie is
        a movie that is created from the images that are to be appended.

        NOTE: It would seem that the two movies *must* be in the same directory
              in order for this to work.

        TODO: Explain ffmpeg options used here

        TODO: Overwriting the original movie using only FFmpeg does not work. It
              seems that it is trying to overwrite the roiginal movie while it is
              still being used by the concat demuxer. This is why we have to use
              a temporary file to store the concat instructions. Confirmed by this
              answer: https://stackoverflow.com/a/28877452/3801865. This function
              should check if output_path is the same as movie_path or if it is
              omitted.
        """
        # Get the directory where all movies are/will be stored
        movie_dir = movie_path.parent

        # Get the folder where the base movie is located
        temp_movie_path = movie_dir / "temp_new_images.mp4"

        # Name of the temporary output file before it is renamed to output_path
        temp_output_path = movie_dir / "temp_concat_output.mp4"

        # Create a movie from the images to be appended
        FFmpegVP.create_movie_from_images(
            images_path,
            temp_movie_path,
        )

        # Create temporary file to store ffmpeg concat instructions
        with NamedTemporaryFile() as temp_file:
            temp_file.write(
                f"file '{movie_path}'\nfile {temp_movie_path}".encode("utf-8")
            )

            # Reset the file pointer to the beginning of the file
            temp_file.seek(0)

            # Concatenate the two movies
            subprocess.run(
                [
                    "ffmpeg",
                    "-f",
                    "concat",
                    "-safe",
                    "0",
                    "-i",
                    f"{temp_file.name}",
                    "-c",
                    "copy",
                    f"{temp_output_path}",
                ],
                check=True,
            )

        # Delete the temporary movie
        temp_movie_path.unlink()

        # Move the output to the desired location
        os.replace(temp_output_path, output_path or movie_path)
