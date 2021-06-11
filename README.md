# Translation 
A word-selector translation software by PySide6

## Compile and Distribution
### Windows
1. Install mingw-w64
[MinGW-W64 GCC-8.1.0](https://sourceforge.net/projects/mingw-w64/files/Toolchains%20targetting%20Win64/Personal%20Builds/mingw-builds/8.1.0/threads-posix/sjlj/x86_64-8.1.0-release-posix-sjlj-rt_v6-rev0.7z)
2. Add bin directory to environment variable (e.g. D:\mingw64\bin)
3. Install dependencies
```sh
pip install -r requirements.txt
```
4. 	Run compile and distribution
```sh
python -m nuitka --mingw64 --standalone --plugin-enable=pyside6 --include-data-dir=source_script=source_script --include-data-dir=resource=resource --remove-output --windows-disable-console  --windows-icon-from-ico=resource\translate-main.ico --show-progress translation.py
```
### Other os
...

## Usage
```sh
translation.exe
```

## Feature
- Not limited to the browser(in theory, it can be used in any application that can be copied with ctrl + c)
- Plug-in translation interface, can load custom translation plugins(two translation plugins have been built in, baidu and youdao)
- Hot reload plugin system, easy to debug

## How to achieve
1. Listen mouse events(current project listens to three events, left click and drag, double click with left button, press shitf key and click left button);
2. Backup clipboard content;
3. Copy selected text to clipboard;
4. Take the clipboard text;
5. Restore clipboard;
6. Call API to translate text;
7. Show results;

## Note
The plugin used by the project is the compiled pyd file, which will have a faster loading speed, of course, you can also use the py file directly. I recommend you to use pyd file, similarly, it is also very simple to compile it, you only need to run the following command in the console:
```sh
python -m nuitka --mingw64 --module --output-dir source_script plugins\your_plugin.py
```

## Screenshots
![](https://github.com/walirt/Translation/blob/main/screenshots/1.png?raw=true)
![](https://github.com/walirt/Translation/blob/main/screenshots/2.png?raw=true)
![](https://github.com/walirt/Translation/blob/main/screenshots/3.png?raw=true)

## License
![](https://img.shields.io/badge/License-GPL-orange.svg)
