# Sports Betting Arbitrage
Sports Betting Arbitrage Calculator. Uses Python and API from The Odds API.

## TO USE:
### 1. Clone the repository.
Run

`git clone https://github.com/YOUR-USERNAME/Sports-Betting-Arbitrage.git`

in your terminal/command line.

### 2. Install the required dependencies:
Run

`pip install -r requirements.txt`

in your terminal/command line.

### 3. Get your API key(s):
Go to https://the-odds-api.com/#get-access and get your API key. The free tier includes 500 requests/month. Note: On average, this program requires ~1500 credits, so more free keys or a paid tier may be required for optimal results.

### 4. Add your API key(s):
Create a new file called `.env` in the project.

If you only have 1 API key:
Add the following line (without the parentheses):

`API_KEY=(your API key)`

Example (these are not real API keys):

`API_KEY=9fe8b8cf71fa38b2a6c954018f23c9f6`

If you have multiple API keys:
Add the following line instead (without the parentheses):

`API_KEYS=(your API keys, comma separated, no spaces, 1 line, no quotes)`

Example (these are not real API keys):

`API_KEYS=9fe8b8cf71fa38b2a6c954018f23c9f6,9fe8b8cf71fa38b2b6c954018f23c9f6,9fe8b8cf71fa38b2a6d954018f23c9f6,9fe8b8cf71fa38b2a6c934018f23c9f6`

### 5. Run the program in the terminal/command line and get your arbitrage opportunities!
