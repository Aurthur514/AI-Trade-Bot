# CoinSwitch PRO Auto-Trading Bot

This is an auto-trading bot for the CoinSwitch PRO platform. It uses a trend-reversal strategy to place buy orders.

## Features

-   **Trend-Reversal Strategy:** The bot identifies potential buy opportunities by checking for trend reversals in recent candle data.
-   **Secure Configuration:** API keys are managed securely using environment variables, not hardcoded in the script.
-   **Error Handling:** The bot includes retries for API requests and handles potential errors gracefully.

## Prerequisites

-   Python 3.6+
-   `pip` for installing dependencies

## Installation

1.  **Clone the repository:**
    ```bash
    git clone <repository_url>
    cd <repository_directory>
    ```

2.  **Install the required dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

## Configuration

Before running the bot, you must set your CoinSwitch PRO API credentials as environment variables. This is a security best practice that prevents your keys from being exposed in the code.

1.  **Set your API Key:**
    ```bash
    export API_KEY="your_api_key_here"
    ```

2.  **Set your Secret Key:**
    ```bash
    export SECRET_KEY="your_secret_key_here"
    ```

Replace `"your_api_key_here"` and `"your_secret_key_here"` with your actual credentials.

## Usage

To run the trading bot, execute the following command in your terminal:

```bash
python trading_bot.py
```

The bot will then start, connect to your CoinSwitch account, and begin executing the trading strategy.

## Disclaimer

Trading cryptocurrencies involves significant risk. This bot is provided as-is, and the user is solely responsible for any financial losses incurred. Always test with small amounts and understand the code before deploying with significant funds.
