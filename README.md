# Hall Mic Master
This script automatically sends notifications to specific players based on their roles during a match. The script checks the game state periodically and sends a message at the defined time.

ToDo:
Execute the following commands after downloading:
1. Copy the `.env.dist` file to `.env` and enter your values.
2. Run the command `pip install python-dotenv`.
3. Copy `mic-master.service.dist` to `/etc/systemd/system/mic-master.service`
4. Activate and start the service with `sudo systemctl enable mic-master.service` and `sudo systemctl start mic-master.service`.

## Prerequisites
- Python 3.8 or above
- `pip` (Python package installer)
## Installation
1. Clone the repository:
    ```bash
    git clone https://github.com/hackletloose/hall-mic-master.git
    cd hall-mic-master
    ```
2. Install the required dependencies:
    ```bash
    pip install -r requirements.txt
    ```
3. Create a `.env` file in the root directory and add the following variables:
    ```plaintext
    API_TOKEN=your-api-token
    API_BASE_URL=your-api-base-url # http://rcon.example.com:8010
    SLEEPTIMER=2  # Time between API queries (in minutes)
    TARGET_TIME=10  # Time after start of match to send the message (in minutes)
    START_TIME=90  # Duration of a warfare match (in minutes)
    MESSAGE_CONTENT="VOICECHECK!!!\n-------------\nJeder Offizier meldet sich JETZT im Offiziersfunk.\n\nEiner redet nicht?\nSchreib in den Chat:\n!admin Spieler XYZ redet nicht"
    ```
## Usage
1. Run the script:
    ```bash
    python mic-master.py
    ```
The script will monitor the game state and send notifications based on the configuration.
## Configuration
- `SLEEPTIMER`: The interval (in minutes) between each API query.
- `TARGET_TIME`: The time after the match starts when the message should be sent.
- `START_TIME`: The total length of a match (in minutes).
- `MESSAGE_CONTENT`: The content of the message that will be sent to the targeted roles.
## Logging
The script will output relevant information and errors to the console to help you monitor its progress.
## License
This project is licensed under the MIT License. See the `LICENSE` file for more details.
