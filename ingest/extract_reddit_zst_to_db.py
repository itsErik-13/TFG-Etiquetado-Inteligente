"""
extract_reddit_zst_to_db.py

This script processes compressed `.zst` files from Pushshift dumps and filters them based on specific criteria. 
It uses multiple processes to decompress, analyze, and store the data in a database. 
It also allows configuring parameters such as date range, comparison field and value, and comment depth.

Main functions:
- Filter files based on a date range and specific criteria.
- Process files using multiple processes for efficiency.
- Log progress and errors during processing.
- Save results to a database.

Usage:
    python extract_reddit_zst_to_db.py <input_folder> [options]

Arguments:
    input: Input folder containing `.zst` files.
    --output: Output folder for processed files (optional).
    --working: Folder to store temporary files (default: "temp_files").
    --field: Field to compare lines (default: "subreddit").
    --value: Value(s) to compare the field against (default: "mentalhealth").
    --processes: Number of processes to use (default: 10).
    --debug: Enable debug logging.
    --start_date: Start date in YYYY-MM format.
    --end_date: End date in YYYY-MM format.
    --database: Name of the database to store results (default: "reddit_bc").
    --comment_depth: Maximum depth of comments to process (-1 for no comments, 0 for direct comments, etc., default -1).

Author:
- Erik Pereira
"""

import os
import sys
import time
import argparse
import re
import multiprocessing
import logging  


sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utils import setup_logging, FileConfig, Queue, save_file_list, load_file_list, process_file

# Setup the logger to both the console and file
log = setup_logging()

# Connect to the database

if __name__ == '__main__':
    """
    Main entry point of the script.

    Configures command-line arguments, initializes logging, filters files based on specified criteria, 
    and uses multiple processes to process the files. Logs progress and errors during processing.

    Output:
        - Files processed based on specified criteria.
        - Detailed logs of progress and errors.
        - Results stored in the specified database.
    """
    parser = argparse.ArgumentParser(description="Use multiple processes to decompress and iterate over Pushshift dump files")
    parser.add_argument("input", help="The input folder to recursively read files from")
    parser.add_argument("--output", help="Put the output files in this folder", default="")
    parser.add_argument("--working", help="The folder to store temporary files in", default="temp_files")
    parser.add_argument("--field", help="When deciding what lines to keep, use this field for comparisons", default="subreddit")
    parser.add_argument("--value", help="When deciding what lines to keep, compare the field to this value. Supports a comma separated list. This is case sensitive", default="mentalhealth")
    parser.add_argument("--processes", help="Number of processes to use", default=10, type=int)
    parser.add_argument("--debug", help="Enable debug logging", action='store_const', const=True, default=False)
    parser.add_argument("--start_date", help="Start date in YYYY-MM format", default=None)
    parser.add_argument("--end_date", help="End date in YYYY-MM format", default=None)
    parser.add_argument("--database", help="The database to write to", default="reddit_bc")
    parser.add_argument("--comment_depth", help="The maximum depth of comments to process (-1 no comments, 0 comments whose parent is the post, 1 comments whose parent is a comment with 0 depth and so on.)", type=int, default=-1)
    script_type = "split"

    args = parser.parse_args()
    arg_string = f"{args.field}:{(args.value if args.value else None)}"

    if args.debug:
        log.setLevel(logging.DEBUG)

    log.info(f"Loading files from: {args.input}")
    if args.output:
        log.info(f"Writing output to: {args.output}")
    else:
        log.info(f"Writing output to working folder")

    values = set(args.value.split(","))
    values = {value.strip().lower() for value in values}

    if len(values) > 5:
        val_string = f"any of {len(values)} values"
    elif len(values) == 1:
        val_string = f"the value {(','.join(values))}"
    else:
        val_string = f"any of the values {(','.join(values))}"
    log.info(f"Checking if any of {val_string} exactly match field {args.field}")

    multiprocessing.set_start_method('spawn')
    queue = multiprocessing.Manager().Queue()
    status_json = os.path.join(args.working, "status.json")
    input_files, saved_arg_string, saved_type, completed_prefixes = load_file_list(status_json)
    if saved_arg_string and saved_arg_string != arg_string:
        log.warning(f"Args don't match args from JSON file. Delete working folder")
        sys.exit(0)

    if saved_type and saved_type != script_type:
        log.warning(f"Script type doesn't match type from JSON file. Delete working folder")
        sys.exit(0)
    # First time running, build the list of files to process
    if input_files is None:
        input_files = []
        for subdir, dirs, files in os.walk(args.input):
            for file_name in files:
                if file_name.endswith(".zst") and re.search("^RC_|^RS_", file_name) is not None:
                    file_date = re.search(r"(\d{4}-\d{2})", file_name)
                    if file_date:
                        file_date = file_date.group(1)
                        if (args.start_date and file_date < args.start_date) or (args.end_date and file_date > args.end_date):
                            continue
                    input_path = os.path.join(subdir, file_name)
                    output_extension = ".zst"
                    output_path = os.path.join(args.working, f"{file_name[:-4]}{output_extension}")
                    input_files.append(FileConfig(input_path, output_path=output_path))

        save_file_list(input_files, args.working, status_json, arg_string, script_type)
    else:
        log.info(f"Existing input file was read, if this is not correct you should delete the {args.working} folder and run this script again")
  
    log.info(f"Filtered {len(input_files)} files based on the provided date range {args.start_date if args.start_date else 'None'} to {args.end_date if args.end_date else 'None'}")
 
    if len(input_files) == 0:
        log.info("No files to process, exiting")
        sys.exit(0)

    files_processed, total_bytes, total_bytes_processed, total_lines_processed, total_lines_matched, total_lines_errored = 0, 0, 0, 0, 0, 0
    files_to_process = []
 
    # Calculate the size for progress reports
    for file in sorted(input_files, key=lambda item: item.file_size, reverse=True):
        total_bytes += file.file_size
        if file.complete:
            files_processed += 1
            total_lines_processed += file.lines_processed
            total_lines_matched += file.lines_matched
            total_bytes_processed += file.file_size
            total_lines_errored += file.error_lines
        else:
            files_to_process.append(file)

    log.info(f"Processed {files_processed} of {len(input_files)} files with {(total_bytes_processed / (2**30)):.2f} of {(total_bytes / (2**30)):.2f} gigabytes")

    start_time = time.time()

    # Check if there are files pending processing
    if len(files_to_process):
        # Queue to track processing progress
        progress_queue = Queue(40)
        progress_queue.put([start_time, total_lines_processed, total_bytes_processed])
        
        # Queue to calculate processing speed
        speed_queue = Queue(40)
        
        # Iterate over files to be processed
        for file in files_to_process:
            log.info(f"Processing file: {file.input_path}")
   
        # Start parallel processes using a multiprocessing pool
        with multiprocessing.Pool(processes=min(args.processes, len(files_to_process))) as pool:
            log.info(f"Starting {len(files_to_process)} files with {args.processes} processes")
            
            # Assign tasks to processes and define a callback for handling errors
            workers = pool.starmap_async(
                process_file, 
                [(file, queue, args.field, values, args.database, args.comment_depth) for file in files_to_process], 
                chunksize=1, 
                error_callback=lambda e: log.error(f"Worker error: {e}")
            )
            
            # While processes are not finished or the queue is not empty
            while not workers.ready() or not queue.empty():
                # Get updates from workers
                file_update = queue.get()
                
                # Log a warning if there was an error processing a file
                if file_update.error_message is not None:
                    log.warning(f"File failed {file_update.input_path}: {file_update.error_message}")

                # Log debug information if the file just started processing
                if file_update.lines_processed == 0:
                    log.debug(f"Starting file: {file_update.input_path} : {file_update.file_size:,}")
                    continue

                # Update global processing statistics
                total_lines_processed, total_lines_matched, total_bytes_processed, total_lines_errored, files_processed, files_errored, i = 0, 0, 0, 0, 0, 0, 0
                for file in input_files:
                    if file.input_path == file_update.input_path:
                        input_files[i] = file_update
                        file = file_update
                    total_lines_processed += file.lines_processed
                    total_lines_matched += file.lines_matched
                    total_bytes_processed += file.bytes_processed
                    total_lines_errored += file.error_lines
                    files_processed += 1 if file.complete or file.error_message is not None else 0
                    files_errored += 1 if file.error_message is not None else 0
                    i += 1
                
                # Save updated state if the file is completed or failed
                if file_update.complete or file_update.error_message is not None:
                    save_file_list(input_files, args.working, status_json, arg_string, script_type)
                    log.debug(f"Finished file: {file_update.input_path} : {file_update.file_size:,}")
                
                # Calculate progress and processing speed
                current_time = time.time()
                progress_queue.put([current_time, total_lines_processed, total_bytes_processed])

                # Calculate processing speed in bytes per second
                first_time, first_lines, first_bytes = progress_queue.peek()
                bytes_per_second = int((total_bytes_processed - first_bytes) / (current_time - first_time))
                speed_queue.put(bytes_per_second)
                
                # Calculate estimated remaining time
                seconds_left = int((total_bytes - total_bytes_processed) / int(sum(speed_queue.list) / len(speed_queue.list)))
                minutes_left = int(seconds_left / 60)
                hours_left = int(minutes_left / 60)
                days_left = int(hours_left / 24)

                # Log current progress
                log.info(
                    f"{total_lines_processed:,} lines at {(total_lines_processed - first_lines)/(current_time - first_time):,.0f}/s, {total_lines_errored:,} errored, {total_lines_matched:,} matched : "
                    f"{(total_bytes_processed / (2**30)):.2f} gb at {(bytes_per_second / (2**20)):,.0f} mb/s, {(total_bytes_processed / total_bytes) * 100:.0f}% : "
                    f"{files_processed}({files_errored})/{len(input_files)} files : "
                    f"{(str(days_left) + 'd ' if days_left > 0 else '')}{hours_left - (days_left * 24)}:{minutes_left - (hours_left * 60):02}:{seconds_left - (minutes_left * 60):02} remaining"
                )

    # Log total processing time
    log.info(f"Total time: {int(time.time() - start_time)} seconds : {total_lines_matched:,} matched/{total_lines_processed:,} total lines")
