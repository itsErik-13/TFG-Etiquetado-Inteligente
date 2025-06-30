"""
file_util.py

This module provides utility classes and functions for file handling and processing, 
including file configuration, reading, writing, and decompression.

Classes:
- FileType: Enum for different file types (COMMENT, SUBMISSION).
- FileConfig: Configuration class for managing file processing details.
- FileHandle: Class for handling file operations such as reading, writing, and decompression.
- Queue: A simple queue class for managing running averages.

Author:
- Erik Pereira
"""

from enum import Enum
import os
import zstandard

class FileType(Enum):
    """
    Enumeration for different types of files.

    Attributes:
        COMMENT (int): Represents a comment file type.
        SUBMISSION (int): Represents a submission file type.
    """
    COMMENT = 1
    SUBMISSION = 2

    @staticmethod
    def to_str(file_type):
        """
        Converts a FileType enum member to its corresponding string representation.

        Args:
            file_type (FileType): The FileType enum member to convert.

        Returns:
            str: The string representation of the file type.
        """
        if file_type == FileType.COMMENT:
            return "comments"
        elif file_type == FileType.SUBMISSION:
            return "submissions"
        return "other"


class FileConfig:
    """
    Configuration class for handling file processing details.

    Attributes:
        input_path (str): Path to the input file.
        output_path (str): Path to the output file (optional).
        file_size (int): Size of the input file in bytes.
        complete (bool): Indicates if the file processing is complete.
        bytes_processed (int): Number of bytes processed.
        lines_processed (int): Number of lines processed.
        error_message (str): Error message if an error occurred during processing.
        error_lines (int): Number of lines that caused errors during processing.
        lines_matched (int): Number of lines that matched a specific criterion during processing.
        file_type (FileType): Type of the file based on its name.
    """
    def __init__(self, input_path, output_path=None, complete=False, lines_processed=0, error_lines=0, lines_matched=0):
        """
        Initializes the FileConfig instance.

        Args:
            input_path (str): Path to the input file.
            output_path (str, optional): Path to the output file. Defaults to None.
            complete (bool, optional): Indicates if the file processing is complete. Defaults to False.
            lines_processed (int, optional): Number of lines processed. Defaults to 0.
            error_lines (int, optional): Number of lines that caused errors. Defaults to 0.
            lines_matched (int, optional): Number of lines that matched a criterion. Defaults to 0.

        Raises:
            ValueError: If the file type cannot be determined from the file name.
        """
        self.input_path = input_path
        self.output_path = output_path
        self.file_size = os.stat(input_path).st_size
        self.complete = complete
        self.bytes_processed = self.file_size if complete else 0
        self.lines_processed = lines_processed if complete else 0
        self.error_message = None
        self.error_lines = error_lines
        self.lines_matched = lines_matched
        file_name = os.path.split(input_path)[1]
        if file_name.startswith("RS"):
            self.file_type = FileType.SUBMISSION
        elif file_name.startswith("RC"):
            self.file_type = FileType.COMMENT
        else:
            raise ValueError(f"Unknown working file type: {file_name}")

    def __str__(self):
        """
        Returns a string representation of the FileConfig instance.

        Returns:
            str: String representation of the instance.
        """
        return f"{self.input_path} : {self.output_path} : {self.file_size} : {self.complete} : {self.bytes_processed} : {self.lines_processed}"


class FileHandle:
    """
    Class for handling file operations, including reading, writing, and processing files.

    Attributes:
        newline_encoded (bytes): Encoded newline character.
        ext_len (int): Length of the file extension.
        path (str): Path to the file or directory.
        handles (dict): Dictionary to store file handles for writing.
    """
    newline_encoded = "\n".encode('utf-8')
    ext_len = 4

    def __init__(self, path):
        """
        Initializes the FileHandle instance.

        Args:
            path (str): Path to the file or directory.
        """
        self.path = path
        self.handles = {}

    def get_paths(self):
        """
        Returns a list of file paths.

        Returns:
            list: List of file paths.
        """
        return [self.path]

    def get_count_files(self):
        """
        Returns the count of files based on the paths.

        Returns:
            int: Number of files.
        """
        return len(self.get_paths())

    @staticmethod
    def read_and_decode(reader, chunk_size, max_window_size, previous_chunk=None, bytes_read=0):
        """
        Reads and decodes chunks of data from the file.

        Args:
            reader (io.BufferedReader): File reader.
            chunk_size (int): Size of each chunk to read.
            max_window_size (int): Maximum window size for decompression.
            previous_chunk (bytes, optional): Previous chunk of data. Defaults to None.
            bytes_read (int, optional): Number of bytes read so far. Defaults to 0.

        Returns:
            str: Decoded chunk of data.

        Raises:
            UnicodeError: If unable to decode the frame after reading the maximum window size.
        """
        chunk = reader.read(chunk_size)
        bytes_read += chunk_size
        if previous_chunk is not None:
            chunk = previous_chunk + chunk
        try:
            return chunk.decode()
        except UnicodeDecodeError:
            if bytes_read > max_window_size:
                raise UnicodeError(f"Unable to decode frame after reading {bytes_read:,} bytes")
            return FileHandle.read_and_decode(reader, chunk_size, max_window_size, chunk, bytes_read)

    def yield_lines(self, character_filter=None):
        """
        Yields lines from the file, optionally filtered by character.

        Args:
            character_filter (str, optional): Filter to apply to file names.

        Yields:
            tuple: Line from the file and the current file position.
        """
        path = self.path
        if os.path.exists(path):
            with open(path, 'rb') as file_handle:
                buffer = ''
                reader = zstandard.ZstdDecompressor(max_window_size=2**31).stream_reader(file_handle)
                while True:
                    chunk = FileHandle.read_and_decode(reader, 2**27, (2**29) * 2)
                    if not chunk:
                        break
                    lines = (buffer + chunk).split("\n")

                    for line in lines[:-1]:
                        yield line, file_handle.tell()

                    buffer = lines[-1]
                reader.close()

    def get_write_handle(self):
        """
        Returns a write handle for the file.

        Returns:
            zstandard.ZstdCompressor: Write handle for the file.
        """
        handle = self.handles.get(1)
        if handle is None:
            path = self.path
            handle = zstandard.ZstdCompressor().stream_writer(open(path, 'wb'))
            self.handles[path] = handle
        return handle

    def write_line(self, line, value=None):
        """
        Writes a line to the file.

        Args:
            line (str): The line to write.
        """
        handle = self.get_write_handle()
        handle.write(line.encode('utf-8'))
        handle.write(FileHandle.newline_encoded)

    def close(self):
        """
        Closes all open file handles.
        """
        for handle in self.handles.values():
            handle.close()


class Queue:
    """
    A simple queue class used for calculating the running average of read speed.

    Attributes:
        list (list): The list to store items.
        max_size (int): The maximum size of the queue.

    Methods:
        put(item): Adds an item to the queue. If the queue is full, removes the oldest item.
        peek(): Returns the first item in the queue without removing it. Returns None if the queue is empty.
    """
    def __init__(self, max_size):
        """
        Initializes the Queue instance.

        Args:
            max_size (int): Maximum size of the queue.
        """
        self.list = []
        self.max_size = max_size

    def put(self, item):
        """
        Adds an item to the queue. If the queue is full, removes the oldest item.

        Args:
            item: The item to add to the queue.
        """
        if len(self.list) >= self.max_size:
            self.list.pop(0)
        self.list.append(item)

    def peek(self):
        """
        Returns the first item in the queue without removing it.

        Returns:
            The first item in the queue, or None if the queue is empty.
        """
        return self.list[0] if len(self.list) > 0 else None