# Multimodal Embodied Conversational Agent
This project is an interactive Conversational Agent with a 3D avatar animated in Unreal Engine 5, and controlled with Python. You can converse and learn with the agent about 4 artworks.

## Table of Content
 - Overview
 - Features
 - Requirements
 - Installation
 - Usage
 - License
 - Acknowledgments

##Project Overview
This project is the accomplishement of 2 years of work for my Master Thesis on Embodied Conversational Agents. I am now releasing it on GitHub in hope that researchers and other interested parties can try it out.

## Features
- 

## Requirements
- Unreal Engine 5.3.2
- Python 3.10
- Microsoft Azure Speech Services

## Installation
1. Create a "main" folder that will contain both Python scripts and the UE5 project
2. Download compiled FFMPEG from builds available on [GitHub](https://github.com/BtbN/FFmpeg-Builds/releases). Extract ffmpeg.exe into the main folder
3. To add OpenFace, download it from [official releases](https://github.com/TadasBaltrusaitis/OpenFace/releases/tag/OpenFace_2.2.0). Put the Unzipped file inside the main folder
4. Git clone or download and unzip this repository to the main folder. Create a new UE5.3.2 project inside it, with the parameters: *Blank Game, no starter content, Blueprint-based*
5. In the UE5 project, install plugins: *Runtime Audio Importer* (From Epic Market), *TCP Socket Plugin* (From Epic Market), *Groom*, *Apple ARKit Face Support*, *Link link Control Rig*. Close the project.
6. Copy-paste the ECA_Project/Content/Research folder inside <Your_UE5_Project>/Content/
7. Create a Python 3.10 project with all the files of the main folder, install all required librairies from the requirements.txt. Open the UE5 project
8. Open the Quixel Bridge window, log in if necessary, and download the MetaHuman of your choice. Import it in your project, it should appear in a new folder called MetaHumans. If your MetaHuman is Ada, you don't have to do anything. Else, you just need to adapt the BP_MetaHuman components' assets and materials to be the same as your selected metahuman's
9. In the project parameters->Maps&Mods, set the default map and startup map to Research_level and set default game mode to MR_FameMode
10. In the Python project, create a .env file with your Microsoft Azure API key and zone for SpeechServices. Take .env.example as example for syntaxe.
  ```
  Microsoft Azure Password and Keys
  API_ZONE=
  API_KEY=
  ```

## Usage
1. Open both the UE5 project and Python project
2. Launch the main.py script in your Python project. Wait for the **Launch the game** signal.
3. Launch the Game from the Editor. Alternatively you can compile the game and directly launch the .exe.
4. Select the artwork you want to talk about
5. Engage with the agent and ask questions about the artwork.

## License
This project is licensed under the MIT License. See the [LICENSE](LICENSE.md) file for details.

## Acknowledgments
I would like to express my deepest gratitude to my Master tutor and professors for their invaluable guidance and encouragements throughout the development of this project.
Special thanks to:
- Professor Akinori ITO for his mentorship and continuous feedback that were critical for the success of the project
- Assistant professor Takashi NOSE for his help with speech synthesis and advice
- Professor Shinichiro OMACHI & Professor Yoshifumi KITAMURA for their feedback before the master thesis defense
