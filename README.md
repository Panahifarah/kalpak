# Kalpak

**Kalpak** is a command-line utility designed for downloading content from URLs. It provides robust features for handling downloads, including retry mechanisms, concurrency management, and support for resuming interrupted downloads. The tool is compatible with various operating systems and includes a man page for UNIX-like systems.

## Features

- **Download Files**: Efficiently download content from a list of URLs.
- **Retry Mechanism**: Automatically retry failed downloads with configurable retry count.
- **Concurrency**: Control the maximum number of simultaneous connections.
- **Resume Capability**: Resume downloads from the last saved position.
- **Colorful Logging**: Enhanced logging with color and emojis for better readability.
- **Man Page**: Documentation for UNIX systems accessible via the `man` command.

## Usage

To use **Kalpak** for downloading files, you can run the following command:

```sh
kalpak -u http://example.com/file1.txt http://example.com/file2.txt -d ~/downloads
```

### Command-Line Options

- `-f`, `--file FILENAME`  
  Input JSON file containing URLs.

- `-d`, `--dest DIRECTORY`  
  Output directory for downloaded content (default is the current directory).

- `-l`, `--log FILENAME`  
  Specify a log file to capture output.

- `-r`, `--retries NUMBER`  
  Number of retries for failed downloads (default is 3).

- `-m`, `--max-connections NUMBER`  
  Maximum number of concurrent connections (default is 10).

- `-c`, `--config FILENAME`  
  Configuration file in YAML format.

- `-u`, `--url URL [URL ...]`  
  Inline URLs to download.

- `-v`, `--version`  
  Display the version of the tool.

- `--resume`  
  Enable resuming of interrupted downloads.

## Examples

1. **Download Files from Specified URLs:**
    ```sh
    kalpak -u http://example.com/file1.txt http://example.com/file2.txt -d ~/downloads
    ```

2. **Use a JSON File for URLs:**
    ```sh
    kalpak -f urls.json -d ~/downloads
    ```

3. **Use a YAML Configuration File:**
    ```sh
    kalpak -c config.yaml -d ~/downloads
    ```

## Troubleshooting

- **Network Errors:** Ensure your internet connection is stable. Check the logs for detailed error messages.
- **Invalid URLs:** Verify that the URLs are correct and accessible.

## License

This project is licensed under the [GPL-3.0 license](LICENSE).

## Contributing

Contributions are welcome! Please submit pull requests or open issues to suggest improvements or report bugs.

## Author

Created by [Amir Husayn Panahifar](mailto:Panahifar.ah@outlook.com).

## Reporting Bugs

For bug reports, please contact [Panahifar.ah@outlook.com](mailto:Panahifar.ah@outlook.com).
